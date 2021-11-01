#!/usr/bin/env python3
"""
Receives a Dockerfile, and adds relevant information to the relations.yaml file including:
    1) The parent image
    2) The child image string for the parent image
    3) Any information found about images downstream to this image
"""
# Imports
import os
import sys
import re
import yaml
import numpy as np
from github import Github

# Global varibles set
RELATION_FILENAME = "relations.yaml"
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_REPO = os.environ['GITHUB_REPOSITORY']

# Subroutines


def get_update_type(image_version, prev_version):
    """
    Verifies the type of update that has been pushed, and returns that to use later in the scripts
    :param image_version: str: the updated image version to be checked
    :param prev_version: str: the version that exists in relations.yaml
    """
    # Split the version numbering to find what type of update was performed
    prev_version_major = int(prev_version.split(sep=".")[0])
    prev_version_minor = int(prev_version.split(sep=".")[1])
    prev_version_patch = int(prev_version.split(sep=".")[2])
    curr_version_major = int(image_version.split(sep=".")[0])
    curr_version_minor = int(image_version.split(sep=".")[1])
    curr_version_patch = int(image_version.split(sep=".")[2])
    # Ensure that the new major version is not less than the old major version
    if curr_version_major < prev_version_major:
        print("ERROR: New major version number {} is less than the previous major version number {}, this is not allowed!\nPlease re-version your Docker image.".format(curr_version_major, prev_version_major))
        exit(1)
    elif curr_version_major > prev_version_major:
        print("New major version number detected, re-versioning and creating new child image paths.")
        return 'major'
    else:
        # Do the same with the minor version
        if curr_version_minor < prev_version_minor:
            print("ERROR: New minor version number {} is less than the previous minor version number {} under the same major version {}, this is not allowed!\nPlease re-version your Docker image.".format(
                curr_version_minor, prev_version_minor, prev_version_major))
            exit(1)
        elif curr_version_minor > prev_version_minor:
            print(
                "New minor version number detected, re-versioning and creating new child image paths.")
            return 'minor'
        else:
            # Finally check the patch version, and default to this
            if curr_version_patch < prev_version_patch:
                print("ERROR: New patch version number {} is less than the previous patch version number {} under the same major-minor version {}.{}, this is not allowed!\nPlease re-version your Docker image.".format(
                    curr_version_patch, prev_version_patch, curr_version_major, curr_version_minor))
                exit(1)
            else:
                print("Patch detected, creating new child image paths.")
                return 'patch'


def is_terminated(image_name):
    """
    Takes an image and checks to see if it has been marked as terminated, returns true if the image has been designated as not to be updated, false otherwise.
    :param image_name: str : Name of the Docker image to be checked for termination
    """
    if image_name in ORIDATA['terminated']:
        return True
    else:
        return False


def update_children(child_list, update_type):
    """
    Takes the image name and version, increments it, and returns an updated child image name
    :param image_name: str : Name of the Docker image to be incrimented
    :param image_version: str : Version number to incriment
    """
    g = Github(GITHUB_TOKEN)
    issue_array = []
    for issue in list(g.get_repo(GITHUB_REPO).get_issues(state='open')):
        issue_array.append(issue.title)
    for child in child_list:
        if child == None:
            continue
        else:
            child_image = re.split(':', child)[0]
            child_version = re.split(':', child)[1]
            # Ensure that the image is not in the terminated list
            if (is_terminated(child_image)):
                print(
                    "This image has been flagged as not to be automatically updated, skipping.")
                continue
            else:
                # Get the versioning information from the previous entry
                child_major = int(child_version.split(sep=".")[0])
                child_minor = int(child_version.split(sep=".")[1])
                child_patch = int(child_version.split(sep=".")[2])
                # Re-set the version number to match the change from the previous image to the new image
                if(update_type == 'major'):
                    child_major += 1
                    child_minor = 0
                    child_patch = 0
                elif(update_type == 'minor'):
                    child_minor += 1
                    child_patch = 0
                else:
                    child_patch += 1
                new_child_version = "{}.{}.{}".format(
                    child_major, child_minor, child_patch)
                position = child_list.index(child)
                new_child = "{}:{}".format(child_image, new_child_version)
                child_list[position] = new_child
                print("Found child image that will require updating: Update {} to {}".format(
                    child, new_child))
                issue_title = "Update {} to {}".format(child, new_child)
                if not issue_title in issue_array:
                    issue_body = "Parent image has been updated, please update the image {} to use the new parent image.  Recommended versioning: {}".format(
                        child, new_child_version)
                    g.get_repo(GITHUB_REPO).create_issue(
                        title=issue_title, body=issue_body)
                else:
                    print("Issue for updating {} to {} already open.".format(
                        child, new_child))
                    continue


def write_yaml():
    """
    Overwrites the existing relations.yaml file with the new information provided, should only\
        be called once per run
    """
    yaml_file = open(RELATION_FILENAME, "w")
    yaml.safe_dump(NEWDATA, yaml_file)
    yaml_file.close()


def update_ancestor(parent, docker_image):
    """
    Updates any ancestor entries tied with this image to include them in their child tables
    :param parent: The parent image specified for updating
    :param docker_image: The docker image specified for updating in 'image_name:image_version' format
    """
    parent_name = parent.split(':')[0]
    parent_version = parent.split(':')[1]
    grandparent = []
    new_children = []
    if parent in ORIDATA['images']:
        new_children = ORIDATA['images'][parent_name][parent_version]['children']
        if (new_children == 'none') or (new_children == [None]) or (new_children == []):
            new_children = [docker_image]
        elif not docker_image in ORIDATA['images'][parent_name][parent_version]['children']:
            new_children.append([docker_image])
        grandparent = ORIDATA['images'][parent_name][parent_version]['parents']
    else:
        new_children.append(docker_image)
    build_entry(parent_name, parent_version, grandparent, new_children)


def build_entry(image_name, image_version, parent_images, child_images):
    """
    Builds a new yaml entry from the parent and child information
    :param image_name: The name of the image to be updated/created
    :param image_version: The version of above to be updated
    :param parents: The parent information for the enty
    :param children: The children information for the entry
    """
    if image_name in ORIDATA['images']:
        if image_version in ORIDATA['images'][image_name]:
            for parent in ORIDATA['images'][image_name][image_version]['parents']:
                if not parent in parent_images:
                    parent_images.append(parent)
            for child in ORIDATA['images'][image_name][image_version]['children']:
                if not child in child_images:
                    child_images.append(child)
            if (len(child_images) > 1) and (None in child_images):
                child_images.remove(None)
            if (len(child_images) > 1) and ('null' in child_images):
                child_images.remove('null')
            if (len(child_images) > 1) and ([] in child_images):
                child_images.remove([])
            new_image = {
                'parents': parent_images,
                'children': child_images
            }
            NEWDATA['images'][image_name][image_version].update(new_image)
        else:
            new_image = {
                image_version: {
                    'parents': parent_images,
                    'children': child_images
                }
            }
            print(new_image)
            NEWDATA['images'][image_name].update(new_image)
    else:
        new_image = {
            image_name: {
                image_version: {
                    'parents': parent_images,
                    'children': child_images
                }
            }
        }
        NEWDATA['images'].update(new_image)


def get_children(image_version, image_name):
    """
    Finds any children image in the relations.yaml file
    :param image_name: str : Docker image to get the child images from
    :param image_version: str : Specific version of the image to get the child images from
    """
    if image_name in ORIDATA['images']:
        if image_version in ORIDATA['images'][image_name]:
            return ORIDATA['images'][image_name][image_version]['children']
        else:
            versions = np.array(list(ORIDATA['images'][image_name]))
            prev_version = np.array(versions)[-1]
            update_type = get_update_type(image_version, prev_version)
            update_children(ORIDATA['images'][image_name]
                            [prev_version]['children'], update_type)
            return [None]
    else:
        return [None]


def get_parents():
    """
    Gets the parent information from the Dockerfile
    """
    parents = []
    with open(DOCKERFILE_PATH, "r") as dockerfile:
        for line in dockerfile:
            if 'FROM ' in line:
                line = line.split()[1]
                if line.lower() == 'scratch':
                    return None
                else:
                    parents.append(line.split('/')[-1])
    return parents


def load_yaml():
    """
    Loads a yaml file and returns a python yaml object
    """
    with open(RELATION_FILENAME) as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    yaml_file.close()
    return yaml_data


def build_latest(image_name, image_version):
    new_latest = {
        image_name: image_version
    }
    NEWDATA['latest'].update(new_latest)


def list_cleaner(relations_list):
    """
    Takes either a parent or child list and flattens it out, then ensures that no null equivalent values remain
    :param relations_list: List of either parent or child images
    """
    new_relations = []
    for item in relations_list:
        if type(item) == list:
            new_relations.extend(list_cleaner(item))
        else:
            new_relations.append(item)
    if len(new_relations) > 1:
        if 'null' in new_relations:
            new_relations.remove('null')
        if None in new_relations:
            new_relations.remove(None)
        if [] in new_relations:
            new_relations.remove([])
        new_relations.sort()
    new_relations = list(dict.fromkeys(new_relations))
    return new_relations


def main():
    """
    Main method
    """
    global ORIDATA
    global NEWDATA
    global DOCKERFILE_PATH
    if len(sys.argv) < 1:
        print("Usage python3 scripts/update_relations.py <DOCKERFILE_PATH>")
        sys.exit(1)
    else:
        # Setup the global variables
        DOCKERFILE_PATH = os.path.abspath(sys.argv[1])
        image_name = re.split('/|\\\\', DOCKERFILE_PATH)[-3]
        image_version = re.split('/|\\\\', DOCKERFILE_PATH)[-2]
        docker_image = image_name + ':' + image_version
        ORIDATA = load_yaml()
        NEWDATA = load_yaml()
        parents = get_parents()
        children = get_children(image_version, image_name)
    # Start by adding the image to the table
        build_entry(image_name, image_version, parents, children)
        build_latest(image_name, image_version)
    # Update all parent images
        for parent in parents:
            update_ancestor(parent, docker_image)
    # Clean up all parent and child images
        for image_name in NEWDATA['images']:
            for image_version in NEWDATA['images'][image_name]:
                child_images = list_cleaner(
                    NEWDATA['images'][image_name][image_version]['children'])
                parent_images = list_cleaner(
                    NEWDATA['images'][image_name][image_version]['parents'])
                new_image = {
                    'children': child_images,
                    'parents': parent_images
                }
                NEWDATA['images'][image_name][image_version].update(new_image)
    # Write out the new relations.yaml
        write_yaml()


if __name__ == "__main__":
    main()
