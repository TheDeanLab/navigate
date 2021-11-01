#!/usr/bin/env python3
# Receives docker owner and a list of changed files on the command line
# For a changed file isunittest.yml or Dockerfile
#   1) runs tests specified in unittest.yml inside the docker image (assumes images have already been built)
#      a) with default docker settings
#      a) with WORKDIR and USER settings to check for singularity compatibility
# If both unittest.yml and Dockerfile are changed it only tests the image once

import os
import sys
import subprocess
import yaml
import re
import difflib
import functions

UNITTEST_FILENAME = "unittest.yml"
TEST_WORKDIR = "/data"


def run_bash_cmd(command, ignore_non_zero_exit_status=False):
    """
    Run bash command and return output
    :param command: str bash command to run
    :param ignore_non_zero_exit_status: bool: when true returns output no matter the exit status
    :return: str: output from command
    """
    try:
        return str(subprocess.check_output(["bash", "-c", command], encoding='utf-8'))
    except subprocess.CalledProcessError as exc:
        if ignore_non_zero_exit_status:
            return str(exc.output)
        else:
            print("ERROR", exc.returncode, exc.output, exc.stderr)
            raise


def get_test_list(filename):
    """
    Read YAML test configuration from a file
    :param filename: str: path to YAML file with test settings for a single docker file
    :return: [(command, expected_text)]: array of command and expected output pairs
    """
    with open(filename) as infile:
        testinfo_list = []
        unittest_config = yaml.safe_load(infile)
        for testinfo in unittest_config['commands']:
            cmd = testinfo['cmd']
            expect_text = testinfo['expect_text']
            testinfo_list.append((cmd, expect_text))
        return testinfo_list


def run_docker_get_output(image_name, cmd, workdir=None, user=None):
    """
    Launch docker process with run command passing the cmd.
    :param image_name: str: name of the image to run
    :param cmd: str: commmand to run inside the image
    :param workdir: str: optional flag to run in a particular directory
    :param user: str: optional flag to run as a particular user
    :return: str: output of the docker process
    """
    options = ""
    if workdir:
        options += "--workdir {} ".format(workdir)
    if user:
        options += "--user {} ".format(user)
    options += "-i --rm "
    print("Testing image {} with: docker run {} {} {}".format(
        image_name, options, image_name, cmd))
    docker_cmd = "docker run {} {} {}".format(options, image_name, cmd)
    return run_bash_cmd(docker_cmd, ignore_non_zero_exit_status=True)


def run_tests(image_name, unittest_filepath):
    """
    Run all tests contained in a unittest_filename against image_name
    :param image_name: str: name of the image to test
    :param unittest_filepath: str path to unittest.yml file
    :return: bool: true if we had an error
    """
    had_error = False
    for cmd, expect_text in get_test_list(unittest_filepath):
        expect_pattern = re.compile(expect_text, re.DOTALL)
        docker_output = run_docker_get_output(image_name, cmd)
        if not re.match(expect_pattern, docker_output):
            print_test_error(cmd, expect_text, docker_output)
            had_error = True
        docker_output_with_options = run_docker_get_output(
            image_name, cmd, workdir=TEST_WORKDIR)
        if not re.match(expect_pattern, docker_output_with_options):
            print_test_error(cmd + " (with workdir and user options)",
                             expect_text, docker_output_with_options)
            had_error = True
    return had_error


def print_test_error(cmd, expect_text, cmd_output):
    print("Error running {}".format(cmd))
    print("Expected Regex: {}".format(expect_text))
    print("Actual: {}".format(cmd_output))


def get_test_file_path(file_path):
    """
    Given a file path return a path to the associated unittest.yml file.
    This is either the file_path itself if it points to unittest.yml or if a Dockerfile it will
    point to the unittest.yml file(if it exists)
    :param file_path: str: path to a changed file that may have an associated unittest.yml file
    :return: str: a path to a unittest.yml file to test or None if there is no associated test file
    """
    filename = os.path.basename(file_path)
    if filename in ["Dockerfile", UNITTEST_FILENAME] or filename in ["Test_Dockerfile", UNITTEST_FILENAME]:
        parent_directory = os.path.dirname(file_path)
        unittest_filepath = "{}/{}".format(parent_directory, UNITTEST_FILENAME)
        if os.path.exists(unittest_filepath):
            return unittest_filepath
    return None


def get_unittest_file_paths(path_list):
    """
    For a list of paths return any associated unittest.yml files.
    :param path_list: [str]: list of paths
    :return: [str]: list of unitttest.yml paths
    """
    unittest_paths = set()
    for file_path in path_list:
        unittest_path = get_test_file_path(file_path)
        if unittest_path:
            unittest_paths.add(unittest_path)
    return unittest_paths


def find_and_run_tests(owner, changed_paths):
    """
    Find an run tests based on a docker ownername (used to build image name) and a list of paths
    :param owner: str: prefix of docker image_name
    :param changed_paths: [str]: list of paths that were changed and may need to be tested
    :return: bool: true when we had errors
    """
    had_errors = False
    tested_images = 0
    images_with_errors = 0
    for unittest_path in get_unittest_file_paths(changed_paths):
        parts = unittest_path.split(sep="/")
        if len(parts):
            tool, tag, _ = parts
            image_name = "{}/{}:{}".format(owner, tool, tag).replace("+", "_")
            if not (str(os.environ.get('DOCKERHUB_URL')).lower() == "none" or str(os.environ.get('DOCKERHUB_URL')).lower() == 'null' or os.environ.get('DOCKERHUB_URL') == None or os.environ.get('DOCKERHUB_URL') == ''):
                image_name = "{}/{}".format(
                    os.environ.get('DOCKERHUB_URL'), image_name)
            had_error = run_tests(image_name, unittest_path)
            tested_images += 1
            if had_error:
                images_with_errors += 1
                had_errors = True
        else:
            print("Skipping {}".format(unittest_path))
    if tested_images == 0:
        print("ERROR: No images tested, unit test may not have been found correctly.")
        had_errors = True
    else:
        print("Tested {} images. Images with errors: {}".format(
            tested_images, images_with_errors))
    return had_errors


def main():
    if len(sys.argv) < 2:
        print(
            "Usage python3 tests/ci_image.py <docker_owner> [<unittest_or_dockerfile_path>...]")
        sys.exit(1)
    else:
        owner = sys.argv[1]
        changed_paths = sys.argv[2:] if len(sys.argv) > 2 else []
        had_errors = find_and_run_tests(owner, changed_paths)
        if had_errors:
            sys.exit(2)


if __name__ == "__main__":
    main()
