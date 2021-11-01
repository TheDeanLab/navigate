#!/usr/bin/env python3

import base64
import json
import os
import re
import sys
import subprocess
import tempfile


def get_deploy_branch():
    """
    Returns the current DEPLOY_BRANCH variable, or fails if this is not set.
    """
    if 'DEPLOY_BRANCH' in os.environ:
        print("Deploy branch set to {}...".format(
            os.environ.get('DEPLOY_BRANCH')), file=sys.stderr)
    else:
        print("Error: DEPLOY_BRANCH is empty\nPlease ensure DEPLOY_BRANCH is set to the name of the default branch used for deployment (i.e. 'develop').\n")
        exit(1)
    return os.environ.get('DEPLOY_BRANCH')


def get_current_branch_name():
    """
    Returns the current branch name
    """
    get_branch_cmd = "echo ${GITHUB_REF##*/}".split()
    return subprocess.Popen(get_branch_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()[0]


def fetch_deploy_branch():
    """
    Keep track of which branch we are on, and since we are on a detached head, and we need to be able to go back to it.
    """
    get_build_head_cmd = "git rev-parse HEAD".split()
    build_head = subprocess.Popen(
        get_build_head_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()[0]
    current_branch = get_current_branch_name()
    deploy_branch = get_deploy_branch()
    if (current_branch != deploy_branch):
        # If branch is not deploy branch (e.g. develop)
        # fetch the current develop branch
        git_config_cmd = "git config --replace-all remote.origin.fetch +refs/heads/*:refs/remotes/origin/*;".split()
        git_fetch_cmd = "git fetch origin {}".format(deploy_branch).split()
        git_checkout_dev_cmd = "git checkout -qf {}".format(
            deploy_branch).split()
        git_checkout_build_cmd = "git checkout {}".format(build_head).split()
        git_config_proc = subprocess.Popen(
            git_config_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if git_config_proc.wait() != 0:
            print("""ERROR: Unable to run git config command:
                \'{}\'
                Error Log:
                {}""".format(git_config_cmd, git_config_proc.communicate()[1]))
            exit(1)
        git_fetch_proc = subprocess.Popen(
            git_fetch_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if git_fetch_proc.wait() != 0:
            print("""ERROR: Unable to run git fetch command:
                \'{}\'
                Error Log:
                {}""".format(git_fetch_cmd, git_fetch_proc.communicate()[1]))
            exit(1)
        # create the tracking branch
        git_checkout_dev_proc = subprocess.Popen(
            git_checkout_dev_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if git_checkout_dev_proc.wait() != 0:
            print("""ERROR: Unable to run git config command:
                \'{}\'
                Error Log:
                {}""".format(git_checkout_dev_cmd, git_checkout_dev_proc.communicate()[1]))
            exit(1)
        # finally, go back to where we were at the beginning
        git_checkout_build_proc = subprocess.Popen(
            git_checkout_build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if git_checkout_build_proc.wait() != 0:
            print("""ERROR: Unable to run git config command:
                \'{}\'
                Error Log:
                {}""".format(git_checkout_build_cmd, git_checkout_build_proc.communicate()[1]))
            exit(1)
    else:
        print("Already on deploy branch, exiting.", file=sys.stderr)
        exit(0)


def get_compare_range():
    """
    If the current branch is the deploy branch, return a range representing the two parents of the HEAD's merge commit.
    If not, return a range comparing the current HEAD with the deploy_branch
    """
    current_branch = get_current_branch_name
    deploy_branch = get_deploy_branch
    if (current_branch == deploy_branch):
        # On the deploy branch (e.g. develop)
        range_start = "HEAD^1"  # alias for first parent
        range_end = "HEAD^2"   # alias for second parent
    else:
        # When not on the deploy branch, always compare with the deploy branch
        range_start = "origin/" + get_deploy_branch()
        range_end = "HEAD"
    return (range_start + " " + range_end)


def changed_paths_in_range(compare_range):
    """
    Takes the two branches to compare, and returns a list of all files changed between the two SHAs.
    :param compare_range: List of the start and end SHA to compare
    """
    cmd = "git diff --name-only --diff-filter=d {}".format(
        compare_range).split()
    paths_run = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    out_files = paths_run.communicate()[0].split("\n")[:-1]
    if out_files == []:
        return "No changed paths found."
    else:
        return paths_run.communicate()[0].split("\n")[:-1]


def build_docker_cmd(command, owner, tool, version):
    """
    Given a docker repo owner, image name, and version, produce an appropriate local docker command.
    :param command: The specific Git command to produce
    :param owner: The repo name for the DockerHub that the user is a part of
    :param tool: The Docker image to be built
    :param version: The specific version of the Docker image specified by the 'tools' variable
    """
    # Ensure the command is lower-case
    command = command.lower()
    # Check to see if URL is needed
    if not (str(os.environ.get('DOCKERHUB_URL')).lower() == "none" or str(os.environ.get('DOCKERHUB_URL')).lower() == 'null' or os.environ.get('DOCKERHUB_URL') == None or os.environ.get('DOCKERHUB_URL') == ''):
        owner = "{}/{}".format(os.environ.get('DOCKERHUB_URL'), owner)
    # Generate local build command
    if (command == "build"):
        cmd = "docker build -q -f \"{}/{}/Dockerfile\" -t \"{}/{}:{}\" \"{}/{}/\"".format(
            tool, version, owner, tool, version, tool, version)
        return cmd
    # Generate a command to return the image ID
    elif (command == "images"):
        cmd = "docker images {}/{}:{} -q".format(owner, tool, version)
        return cmd
    # Generate pull command
    elif (command == "pull"):
        cmd = "docker pull {}/{}:{}".format(owner, tool, version)
        return cmd
    # Generate push command
    elif (command == "push"):
        cmd = "docker push {}/{}:{}".format(owner, tool, version)
        return cmd
    # If command not recognized, error out
    else:
        print("Error, command \"{}\" not recognized, please verify it is one of the following: build, images, pull, push\n.".format(command))
        exit(1)


def ensure_local_image(owner, tool, version):
    """
    Given a docker repo owner, image name, and version, check if it exists locally and pull if necessary.
    :param owner: The repo name for the DockerHub that the user is a part of
    :param tool: The Docker image to be built
    :param version: The specific version of the Docker image specified by the 'tools' variable
    """
    image_cmd = build_docker_cmd("images", owner, tool, version).split()
    image_run = subprocess.Popen(
        image_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if image_run.communicate()[0] == '':
        print("Image {}/{}:{} does not exist locally for tagging, building...".format(owner, tool, version))
        build_cmd = build_docker_cmd(
            "build", owner, tool, version).replace('\"', '').split()
        build_run = subprocess.Popen(
            build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if build_run.wait() != 0:
            print("""Error: Unable to build image \'{}/{}:{}\'
                Error Log:
                {}""".format(owner, tool, version, build_run.communicate()[1]))
        else:
            print(
                "Image \'{}/{}:{}\' successfully built locally!".format(owner, tool, version), file=sys.stderr)
    else:
        print(
            "Image \'{}/{}:{}\' already exists locally!".format(owner, tool, version), file=sys.stderr)


def build_image(owner, changed_paths):
    """
    Given a Docker repo owner (e.g. "medforomics") and a list of relative changed_paths to Dockerfiles, execute a Docker 'build' command.
    :param owner: The repo name for the DockerHub that the user is a part of
    :param changed_paths: List of all files that had been changed between two Git SHAs
    """
    dockerfile_path = check_dockerfile_count(changed_paths)
    print(dockerfile_path)
    print("Building changed Dockerfiles...\n", file=sys.stderr)
    tool, version, filename = dockerfile_path.split('/')
    print("Building {}/{}:{}...".format(owner, tool, version), file=sys.stderr)
    build_command = build_docker_cmd(
        "build", owner, tool, version).replace('\"', '').split(" ")
    build_proc = subprocess.Popen(build_command)
    build_code = build_proc.wait()
    if build_code == 0:
        print("Successfully built {}/{}:{}...".format(owner,
                                                      tool, version), file=sys.stderr)
        return True
    else:
        print("""ERROR: Unable to build image \'{}/{}:{}\'
        Error Log:
        {}""".format(owner, tool, version, build_proc.communicate()[1]))


def push_images(owner, changed_paths):
    """
    Given a Docker repo owner and a list of relative path to Dockerfiles, issue a Docker 'push' command for the images built by build_image, as long as it is not prefixed with 'test_'.
    :param owner: The repo name for the DockerHub that the user is a part of
    :param changed_paths: List of all files that had been changed between two Git SHAs
    """
    dockerfile_path = check_dockerfile_count(changed_paths)
    tool, version, filename = dockerfile_path.split('/')
    # Verify that this is not a test image
    if not 'test_' in tool:
        # Ensure the image exists locally before trying to push
        ensure_local_image(owner, tool, version)
        # Once the image is verified, push the image
        print("Pushing {}/{}:{}...".format(owner, tool, version), file=sys.stderr)
        push_command = build_docker_cmd("push", owner, tool, version).replace(
            '\"', '').split(" ")
        push_command = subprocess.Popen(push_command)
        push_code = push_command.wait()
        if push_code == 0:
            print(
                "Successfully pushed new branch based on {}/{}:{}".format(owner, tool, version), file=sys.stderr)
        else:
            print("""ERROR: Image for {}/{}:{} was unable to be pushed.
                Please try again after verifying you have access to {}/{}:{} on DockerHub!""".format(
                owner, tool, version, owner, tool, version))
    elif 'test_' in tool:
        print("""Test image found: \'{}/{}:{}\'
            Skipping push of test image""".format(owner, tool, version), file=sys.stderr)


def print_changed(compare_range):
    """
    Prints the list of all changed files found between the range of SHAs given
    :param compare_range: List of the start and end SHA to compare
    :param changed_paths: List of all files that had been changed between two Git SHAs
    """
    print("Changed files between {}:".format(compare_range))
    changed_paths = changed_paths_in_range(get_compare_range())
    if changed_paths != "No changed paths found.":
        for changed_path in changed_paths:
            print(changed_path)
    else:
        print(changed_paths)


def check_org():
    """
    Verifies that the user's DOCKERHUB_ORG is setup and has a value
    """
    if 'DOCKERHUB_ORG' in os.environ:
        print("Using Docker Hub org as {}...".format(
            os.environ.get('DOCKERHUB_ORG')), file=sys.stderr)
    else:
        print("Error: DOCKERHUB_ORG is empty\nPlease ensure DOCKERHUB_ORG is set to the name of the Docker Hub organization.\n")
        exit(1)
    return os.environ.get('DOCKERHUB_ORG')


def check_dockerfile_count(changed_paths):
    """
    Takes in the list of changed paths and finds the total number of found Dockerfiles
    :param changed_paths: List of the file paths to be checked for a Dockerfile
    """
    # Check for the number of Dockerfiles present in the changed paths
    dockerfile_count = 0
    dockerfile_path = ''
    for changed_path in changed_paths:
        if '/dockerfile' in changed_path.lower():
            dockerfile_count += 1
            dockerfile_path = changed_path
    # Fail if there is more than one Dockerfile to be built
    if dockerfile_count > 1:
        print("""ERROR: System is currently only setup to handle one Dockerfile changed or added at a time.
        Currently, you have {} Dockerfile changes posted""".format(dockerfile_count), file=sys.stderr)
        dockerfile_path = '1'
    # Error if no changes have been made to any Dockerfiles
    elif dockerfile_count == 0:
        print("No changes to Dockerfiles or latest symlinks detected, nothing to build or push.", file=sys.stderr)
        dockerfile_path = '0'
    else:
        print("Dockerfile found: {}".format(dockerfile_path), file=sys.stderr)
    return dockerfile_path


def check_test_image(dockerfile_path):
    if dockerfile_path.lower().startswith('test_'):
        print("Image found at {} is a test image, skipping 'Push to Dockerhub' stage.".format(
            dockerfile_path), file=sys.stderr)
        return True
    else:
        print("Image found at {} is not a test image, proceeding to 'Push to Dockerhub' stage.".format(
            dockerfile_path), file=sys.stderr)
        return False


def pytest_cleanup(dockerfile_path):
    tool, version, filename = dockerfile_path.split('/')
    clean_command = "docker image rm -f {}/{}:{}".format(
        tool, version, filename).split(" ")
    clean_command = subprocess.Popen(clean_command)
    clean_code = clean_command.wait()
    if clean_code == 0:
        print("Successfully untagged and removed the image {}:{}".format(tool, version))
        remove_file_command = "rm -fr {}".format(tool).split(" ")
        remove_file_command = subprocess.Popen(remove_file_command)
        remove_file_code = remove_file_command.wait()
        if remove_file_code == 0:
            print(
                "Successfully removed both the temporary testing image directory {}".format(tool))
        else:
            print(
                "ERROR: Unable to remove the temporary testing image directory {}".format(tool))
    else:
        print("ERROR: Unable to untag the Dockerfile or remove the temporary image directory for {}".format(tool))


def docker_login():
    if str(os.environ.get('DOCKERHUB_URL')).lower() == "none" or str(os.environ.get('DOCKERHUB_URL')).lower() == 'null' or os.environ.get('DOCKERHUB_URL') == None:
        print("DockerHub repository found, logging in.".format(
            os.environ.get('DOCKERHUB_URL')), file=sys.stderr)
        login_command = "docker login -u {} -p {}".format(os.environ.get(
            'DOCKERHUB_UN'), os.environ.get('DOCKERHUB_PW')).split(" ")
    else:
        print("Non-DockerHub repository found, adding URL {} and logging in.".format(
            os.environ.get('DOCKERHUB_URL')), file=sys.stderr)
        login_command = "docker login {} -u {} -p {}".format(os.environ.get(
            'DOCKERHUB_URL'), os.environ.get('DOCKERHUB_UN'), os.environ.get('DOCKERHUB_PW')).split(" ")
    login_command_run = subprocess.Popen(login_command)
    login_code = login_command_run.wait()
    if login_code != 0:
        print("Error logging in to container reposity specified.")
        exit(1)


def main():
    """
    Main method, takes the command to be run
    :param command: the command to be run
    """
    arglen = len(sys.argv)
    if arglen < 1:
        print("Usage python3 scripts/functions.py <command> <list of required variables for the command>")
        sys.exit(1)
    else:
        command = sys.argv[1]
        if command == 'fetch_deploy_branch':
            fetch_deploy_branch()
        elif command == 'build_docker_cmd':
            print(build_docker_cmd(sys.argv[2], sys.argv[3],
                                   sys.argv[5], sys.argv[4]))
        elif command == 'ensure_local_image':
            ensure_local_image(sys.argv[2], sys.argv[3], sys.argv[4])
        elif command == 'build_image':
            print(build_image(check_org(), changed_paths_in_range(get_compare_range())))
        elif command == 'push_images':
            push_images(check_org(), changed_paths_in_range(
                get_compare_range()))
        elif command == 'print_changed':
            print_changed(get_compare_range())
        elif command == 'check_org':
            print(check_org())
        elif command == 'check_dockerfile_count':
            print(check_dockerfile_count(
                changed_paths_in_range(get_compare_range())))
        elif command == 'check_test':
            print(check_test_image(sys.argv[2]))
        elif command == 'login':
            docker_login()
        else:
            print("""ERROR: Command \'{}\' not recognized.  Valid commands and their associated requirements:
                python scripts/functions.py \'fetch_deploy_branch\' - Runs a \'git fetch\' on the deploy branch ID while also tracking the current branch under development
                python scripts/functions.py \'build_docker_cmd\',\'Docker command (ie build, pull, push)\', \'Dockerhub repository\', \'Base directory for tool\', \
                    \'Version subdirectory for tool\' - Returns a valid Docker command that you have specified on the tool requested
                python scripts/functions.py \'esure_local_image\', \'Dockerhub repository\', \'Base directory for tool\', \'Version subdirectory for tool\' \
                    - Checks whether a specified Docker image exists locally for the specified tool
                python scripts/functions.py \'build_image\' - Checks the list provided for a Dockerfile and builds the associated image
                python scripts/functions.py \'push_images\' - Checks the list provided for a Dockerfile, then pushes the image associated with \
                    said Dockerfile
                python scripts/functions.py \'print_changed\' - Returns a printed list of all file paths that are different between the deploy branch and the current branch.
                python scripts/functions.py \'check_org\' - Returns the currently set Dockerhub repository \
                python scripts/functions.py \'check_dockerfile_count\' - Returns either the Dockerfile path, or a code if either no Dockerfiles fdound (\'0\') or if more than one Dockerfile is found (\'1\') \
                python scripts/functions.py \'check_test\' \'Dockerfile path\'- Returns whether or not this image is considered a test image (preceeded by \'test_\'), and will build and test, but then skip the push to Dockerhub.
                """.format(command))
            sys.exit(1)


if __name__ == "__main__":
    main()
