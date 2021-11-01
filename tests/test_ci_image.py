#!/usr/bin/env python3


import sys
import os
import pytest
import yaml
from io import StringIO
sys.path.append(os.path.abspath("scripts/"))
import ci_image

test_vars = []


@pytest.mark.test_run_bash_cmd
def test_run_bash_cmd():
    test_out = ci_image.run_bash_cmd('find tests/1.0.0/Test_Dockerfile')
    assert 'tests/1.0.0/Test_Dockerfile\n' == test_out


@pytest.mark.test_get_test_list
def test_get_test_list():
    test_out = ci_image.get_test_list('tests/1.0.0/unittest.yml')
    assert test_out == [('parallel --version | head -n1', 'GNU parallel 20161222\n'), ('pandoc --version | head -n2',
                                                                                       'pandoc 1.19.2.4\nCompiled with pandoc-types 1.17.0.5, texmath 0.9.4.4, skylighting 0.3.3.1\n')]


@pytest.mark.test_run_tests
def test_run_tests():
    test_out = ci_image.run_tests(
        'bicf/base:1.0.0', 'tests/1.0.0/unittest.yml')
    assert test_out == False


@pytest.mark.test_print_test_error
def test_print_test_error(capfd):
    ci_image.print_test_error('test', 'test', 'test')
    test_out = capfd.readouterr()[0]
    assert test_out == "Error running test\nExpected Regex: test\nActual: test\n"


@pytest.mark.test_get_test_file_path
def test_get_test_file_path():
    test_out = ci_image.get_test_file_path('tests/1.0.0/Test_Dockerfile')
    assert test_out == 'tests/1.0.0/unittest.yml'


@pytest.mark.test_get_unittest_file_paths
def test_get_unittest_file_paths():
    test_out = ci_image.get_unittest_file_paths(
        ['tests/1.0.0/Test_Dockerfile'])
    assert test_out == {'tests/1.0.0/unittest.yml'}


@pytest.mark.test_find_and_run_tests
def test_find_and_run_tests():
    test_out = ci_image.find_and_run_tests(os.environ['DOCKERHUB_ORG'], [
                                           'tests/1.0.0/Test_Dockerfile'])
    assert test_out == True
