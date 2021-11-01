#!/usr/bin/env python3


import sys
import os
import pytest
from io import StringIO
sys.path.append(os.path.abspath('scripts/'))
import functions

test_output_path = os.path.dirname(os.path.abspath(__file__)) + '/../'
no_image = True
test_vars = []


@pytest.mark.test_check_org
def test_check_org():
    os.environ['DOCKERHUB_ORG'] = 'test_org'
    test_vars.append(functions.check_org())
    assert test_vars[0] == os.environ['DOCKERHUB_ORG']


@pytest.mark.test_get_deploy_branch
def test_get_deploy_branch():
    os.environ['DEPLOY_BRANCH'] = 'test_branch'
    test_vars.append(functions.get_deploy_branch())
    assert test_vars[1] == os.environ['DEPLOY_BRANCH']


@pytest.mark.test_get_compare_range
def test_get_compare_range():
    test_vars.append(functions.get_compare_range())
    assert "origin/{} ".format(test_vars[1]) in test_vars[2]


@pytest.mark.test_changed_paths_in_range
def test_changed_paths_in_range():
    global no_image
    test_vars.append(functions.changed_paths_in_range(test_vars[2]))
    test_vars.append('testing_base_image/0.0.1/Dockerfile')
    test_vars.append('test_testing_base_image/0.0.1/Dockerfile')
    os.makedirs('testing_base_image/0.0.1')
    with open(test_vars[4], 'w') as f:
        f.write(
            "FROM ubuntu:18.04\nENV DEBIAN_FRONTEND=noninteractive\nRUN apt-get update -y --fix-missing")
    f.close()
    for changed_path in test_vars[3]:
        if '/dockerfile' in changed_path.lower():
            test_vars.append(str(changed_path))
            no_image = False
            break
        else:
            no_image = True
    if no_image == True:
        assert test_vars[3] == "No changed paths found."
        test_vars[3] = [test_vars[4], test_vars[5]]
        test_vars.append(test_vars[4])
    assert len(test_vars[3]) != 0


@pytest.mark.test_print_changed
def test_print_changed(capfd):
    functions.print_changed(test_vars[3])
    test_out, test_err = capfd.readouterr()
    print(test_err)
    assert test_vars[6] in test_out


@pytest.mark.test_build_docker_cmd
def build_docker_cmd(capfd):
    test_output = []
    for command in ['build', 'images', 'pull', 'push']:
        functions.build_docker_cmd(
            command, test_vars[0], 'base', '1.0.1')
        test_out, test_err = capfd.readouterr()
        test_output.append(test_out)
        print(test_err)
    assert test_output == ['docker build -f "base/1.0.1/Dockerfile" -t "testing_base/base:1.0.1" "base/1.0.1/"', 'docker images testing_base/base:1.0.1 -q',
                           'docker pull testing_base/base:1.0.1', 'docker push testing_base/base:1.0.1']


@pytest.mark.test_dockerhub_login
def test_dockerhub_login(capfd):
    functions.docker_login()
    test_out, test_err = capfd.readouterr()
    assert test_out == "Login Succeeded\n"


@pytest.mark.test_ensure_local_image
def test_ensure_local_image(capfd):
    tool_name = test_vars[4].split('/')[0]
    tool_version = test_vars[4].split('/')[1]
    functions.ensure_local_image(test_vars[0], tool_name, tool_version)
    test_out, test_err = capfd.readouterr()
    assert "Image \'{}/{}:{}\' successfully built locally!\n".format(
        test_vars[0], tool_name, tool_version) in test_err


@pytest.mark.test_build_image
def test_build_image(capfd):
    tool_name = test_vars[4].split('/')[0]
    tool_version = test_vars[4].split('/')[1]
    test_tool_name = test_vars[5].split('/')[0]
    test_tool_version = test_vars[5].split('/')[1]
    temp_var = functions.build_image(test_vars[0], [test_vars[4]])
    test_out, test_err = capfd.readouterr()
    assert "Dockerfile found: {}\nBuilding changed Dockerfiles...\n\nBuilding {}/{}:{}...\nSuccessfully built {}/{}:{}...\n".format(
        test_vars[4], test_vars[0], tool_name, tool_version, test_vars[0], tool_name, tool_version) in test_err
    run_command = "docker image ls | grep '{}/{}' | grep '{}' | wc -l".format(
        test_vars[0], tool_name, tool_version)
    os.system(run_command)
    test_out, test_err = capfd.readouterr()
    assert "1" in test_out
    assert temp_var == True
    temp_var = functions.build_image(test_vars[0], [test_vars[5]])
    test_out, test_err = capfd.readouterr()
    assert "ERROR: Unable to build image \'{}/{}:{}\'".format(
        test_vars[0], test_tool_name, test_tool_version) in test_out
    assert temp_var == None


@pytest.mark.test_push_images
def test_push_images(capfd):
    tool_name = test_vars[4].split('/')[0]
    tool_version = test_vars[4].split('/')[1]
    test_tool_name = test_vars[5].split('/')[0]
    test_tool_version = test_vars[5].split('/')[1]
    functions.push_images(test_vars[0], [test_vars[4]])
    test_out, test_err = capfd.readouterr()
    assert "\nPushing {}/{}:{}...\n".format(
        test_vars[0], tool_name, tool_version) in test_err
    functions.push_images(test_vars[0], [test_vars[5]])
    test_out, test_err = capfd.readouterr()
    assert "\nTest image found: \'{}/{}:{}\'\n".format(
        test_vars[0], test_tool_name, test_tool_version) in test_err


@pytest.mark.test_check_dockerfile_count
def test_check_dockerfile_count(capfd):
    temp_var = functions.check_dockerfile_count([test_vars[4]])
    test_out, test_err = capfd.readouterr()
    assert "Dockerfile found: {}".format(test_vars[4]) in test_err
    assert temp_var == test_vars[4]
    temp_var = functions.check_dockerfile_count([test_vars[4], test_vars[5]])
    test_out, test_err = capfd.readouterr()
    assert "ERROR: System is currently only setup to handle one Dockerfile changed or added at a time.\n        Currently, you have 2 Dockerfile changes posted\n" in test_err


@pytest.mark.test_check_test_image
def test_check_test_image():
    temp_var = functions.check_test_image(test_vars[4])
    assert temp_var == False
    temp_var = functions.check_test_image(test_vars[5])
    assert temp_var == True


@pytest.mark.test_pytest_cleanup
def test_pytest_cleanup(capfd):
    tool_name = test_vars[4].split('/')[0]
    tool_version = test_vars[4].split('/')[1]
    functions.pytest_cleanup(test_vars[4])
    test_out, test_err = capfd.readouterr()
    assert test_out == "Successfully untagged and removed the image {}:{}\nSuccessfully removed both the temporary testing image directory {}\n".format(
        tool_name, tool_version, tool_name)
