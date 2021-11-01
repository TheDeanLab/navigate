#!/usr/bin/env python3
"""
Prints out the paths for the unittest.yml files for all latest images to run their pytests
"""

import os
import sys
import re
import subprocess
import yaml
import functions


def load_yaml(master_yaml):
    """
    Loads a yaml file and returns a python yaml object
    :param yaml_file: the yaml file to open and read
    """
    with open(master_yaml) as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    yaml_file.close()
    return yaml_data


def pull_image(docker_image):
    """
    Ensures that the version of the image specified has been pulled
    :param docker_image: str: Docker image to pull in the format '<organization>/<image_name>:<version>'
    """
    if os.system("docker pull " + docker_image) != 0:
        print("ERROR: Unable to pull " + docker_image)
        sys.exit(1)


def main():
    """
    Main method

    """
    if len(sys.argv) < 1:
        print(
            "Usage python3 scripts/ci_latest_images.py <docker_owner> <relations.yaml path>")
        sys.exit(1)
    else:
        owner = sys.argv[1]
        functions.docker_login()
        relations = load_yaml(os.path.abspath(sys.argv[2]))
        latest_images = relations['latest']
        for image in latest_images:
            tag = latest_images[image]
            image_name = "{}/{}:{}".format(owner, image, tag).replace("+", "_")
            if not (str(os.environ.get('DOCKERHUB_URL')).lower() == "none" or str(os.environ.get('DOCKERHUB_URL')).lower() == 'null' or os.environ.get('DOCKERHUB_URL') == None or os.environ.get('DOCKERHUB_URL') == ''):
                image_name = "{}/{}".format(
                    os.environ.get('DOCKERHUB_URL'), image_name)
            pull_image(image_name)
            test_path = "{}/{}/unittest.yml".format(image, tag)
            test_command = "python3 scripts/ci_image.py \"{}\" {}".format(
                owner, test_path).split(" ")
            test_command = subprocess.Popen(test_command)
            test_code = test_command.wait()
            if test_code != 0:
                print("ERROR: Image testing failed for " + image_name)
                sys.exit(1)
            else:
                print("Test for {} successful, purging and restarting for next image.".format(
                    image_name))
                purge_command = "docker system prune -a -f".split(" ")
                purge_command = subprocess.Popen(purge_command)


if __name__ == "__main__":
    main()
