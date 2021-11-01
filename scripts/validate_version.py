#!/usr/bin/env python3
"""
Receives a relations file and a docker image:version combination, and verifies that this image does not already exist in the master branch.
If it exists in master, as these images are meant to be locked down and final, it errors out and tells the user to try another image
version.  Otherwise, it allows procedure as normal.
After this, it should build the image, push to DockerHub, and continue as normal.
"""

import os
import sys
import re
import yaml
import numpy as np


def check_version_info(master_version, image_version):
    """
    Verifies that the versioning follows our guidelines and that it is actually an increment, and not any sort of decrement.
    :param master_version: version of the Dockerfile specified in Master branch
    :param image_version: version of the proposed new Dockerfile
    """
    pattern = re.compile("[0-9]+.[0-9]+.[0-9]+")
    print(image_version)
    print(master_version)
    if pattern.match(image_version):
        if image_version.split(sep=".")[0] < master_version.split(sep=".")[0]:
            print("Error: Proposed major version number {} is less than the current major version number on master {}.\nPlease\
                      incriment the version for this image correctly.".format(image_version.split(sep=".")[0],
                                                                              master_version.split(sep=".")[0]), file=sys.stderr)
            return False
        elif master_version.split(sep=".")[0] == image_version.split(sep=".")[0]:
            if image_version.split(sep=".")[1] < master_version.split(sep=".")[1]:
                print("Error: Proposed minor version revision number {}.{} is less than or equal the current master version: {}.{}\
                         \nPlease incriment the version for this image correctly.".format(image_version.split(sep=".")[0],
                                                                                          image_version.split(sep=".")[1], master_version.split(sep=".")[0], master_version.split(sep=".")[1]), file=sys.stderr)
                return False
            elif image_version.split(sep=".")[1] == master_version.split(sep=".")[1]:
                if image_version.split(sep=".")[2] <= master_version.split(sep=".")[2]:
                    print("Error: Proposed patch version number {} is less than or equal the current master version: {}\nPlease incriment the version for this image correctly.".format(
                        image_version, master_version), file=sys.stderr)
                    return False
                else:
                    print(
                        "Versioning appears to have incrimented, proceeding with build.")
                    return True
            else:
                print("The new image minor version number {}.{} is greater than the existing minor version {}.{}, proceeding.".format(
                    image_version.split(sep=".")[0], image_version.split(
                        sep=".")[1], master_version.split(sep=".")[0],
                    master_version.split(sep=".")[1]), file=sys.stderr)
        else:
            print("New image has greater major version number {} than master {}, proceeding.".format(image_version.split(sep=".")[0],
                                                                                                     master_version.split(sep=".")[0]), file=sys.stderr)
    else:
        print("Error: the version number does not match our default pattern: '0.0.0'.\nPlease re-name the directory to match this \
               structure.", file=sys.stderr)
        return False


def check_exists(master_yaml, image_name, image_version):
    """
    Checks to see if an image exists as an entry in a yaml file
    :param master_yaml: the yaml file to check for the entry
    :param image_name: the name of the Docker image to search for
    :param image_version: the version of said Docker image to search for
    """
    if image_name in master_yaml['images']:
        print("Found an image with the same name, checking for versions.",
              file=sys.stderr)
        if image_version in master_yaml['images'][image_name]:
            print("Error: Found duplicated image and version already present in Master\n\
                     Cannot proceed, please change the image version to avoide overwritting a locked image.", file=sys.stderr)
            return False
        else:
            print("New version of {} found, verifying that this is an updated version number".format(
                image_name), file=sys.stderr)
            previous_version = np.array(
                list(master_yaml['images'][image_name]))[-1]
            print(previous_version)
            return check_version_info(previous_version, image_version)
    else:
        print("New image found, proceeding with build/push, and updating relations.yaml.", file=sys.stderr)
        return True


def load_yaml(master_yaml):
    """
    Loads a yaml file and returns a python yaml object
    :param yaml_file: the yaml file to open and read
    """
    with open(master_yaml) as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    yaml_file.close()
    return yaml_data


def main():
    """
    Main method
    """

    if len(sys.argv) < 2:
        print("Usage python3 scripts/validate_version.py <master relations.yaml> <Dockerfile path>")
        sys.exit(1)
    else:
        master_yaml = load_yaml(os.path.abspath(sys.argv[1]))
        print(os.path.abspath(sys.argv[2]))
        image_name = re.split('/', os.path.abspath(sys.argv[2]))[-3]
        image_version = re.split('/', os.path.abspath(sys.argv[2]))[-2]
        if check_exists(master_yaml, image_name, image_version):
            print("New image found, proceeding to build, push to DockerHub, and add it to the 'relations.yaml' file.", file=sys.stderr)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
