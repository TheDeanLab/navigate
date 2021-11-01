#!/usr/bin/env python3


import sys
import os
import pytest
import yaml
from io import StringIO
sys.path.append(os.path.abspath("scripts/"))
import update_relations

test_vars = []


@pytest.mark.test_get_update_type
def test_get_update_type(capfd):
    # Verify that a patch type update works
    update_type_out = update_relations.get_update_type("1.0.1", "1.0.0")
    test_out = capfd.readouterr()[0]
    assert update_type_out == "patch"
    assert test_out == "Patch detected, creating new child image paths.\n"
    # Verify that a minor update type works
    update_type_out = update_relations.get_update_type("1.1.0", "1.0.0")
    test_out = capfd.readouterr()[0]
    assert update_type_out == "minor"
    assert test_out == "New minor version number detected, re-versioning and creating new child image paths.\n"
    # Verify that a major update type works
    update_type_out = update_relations.get_update_type("2.0.0", "1.0.0")
    test_out = capfd.readouterr()[0]
    assert update_type_out == "major"
    assert test_out == "New major version number detected, re-versioning and creating new child image paths.\n"
    # Verify failure on invalid patch update change
    with pytest.raises(SystemExit):
        update_relations.get_update_type("1.0.0", "1.0.1")
    test_out = capfd.readouterr()[0]
    assert test_out == "ERROR: New patch version number 0 is less than the previous patch version number 1 under the same major-minor version 1.0, this is not allowed!\nPlease re-version your Docker image.\n"
    # Verify failure on invalid minor update change
    with pytest.raises(SystemExit):
        update_relations.get_update_type("1.0.0", "1.1.0")
    test_out = capfd.readouterr()[0]
    assert test_out == "ERROR: New minor version number 0 is less than the previous minor version number 1 under the same major version 1, this is not allowed!\nPlease re-version your Docker image.\n"
    # Verify failure on invalid minor update change
    with pytest.raises(SystemExit):
        update_relations.get_update_type("1.0.0", "2.0.0")
    test_out = capfd.readouterr()[0]
    assert test_out == "ERROR: New major version number 1 is less than the previous major version number 2, this is not allowed!\nPlease re-version your Docker image.\n"


@pytest.mark.test_is_terminated
def test_is_terminated():
    with open('tests/relations.yaml') as yaml_file:
        update_relations.ORIDATA = yaml.safe_load(yaml_file)
    yaml_file.close()
    assert update_relations.is_terminated('test_image') == False
    assert update_relations.is_terminated('test_image2') == True


@pytest.mark.test_get_children
def test_get_children():
    test_vars.append(update_relations.get_children('18.04', 'ubuntu'))
    assert test_vars[0] == ['base:1.0.0']
    test_vars[0] = update_relations.get_children('1.0.0', 'base')
    assert test_vars[0] == [None]


@pytest.mark.test_get_parents
def test_get_parents():
    update_relations.DOCKERFILE_PATH = 'tests/1.0.0/Test_Dockerfile'
    test_vars.append(update_relations.get_parents())
    assert test_vars[1] == ['ubuntu:18.04']


@pytest.mark.test_build_entry
def test_build_entry():
    with open('tests/relations.yaml') as yaml_file:
        update_relations.NEWDATA = yaml.safe_load(yaml_file)
    yaml_file.close()
    assert update_relations.ORIDATA == update_relations.NEWDATA
    temp_var_ori = update_relations.ORIDATA
    update_relations.build_entry('base', '1.0.1', test_vars[1], [test_vars[0]])
    assert temp_var_ori == update_relations.ORIDATA
    assert '1.0.1' in update_relations.NEWDATA['images']['base']
    assert update_relations.NEWDATA['images']['base']['1.0.1']['children'] == [
        [None]]
    assert update_relations.NEWDATA['images']['base']['1.0.1']['parents'] == [
        'ubuntu:18.04']


@pytest.mark.test_update_ancestor
def test_update_ancestor():
    with open('tests/relations.yaml') as yaml_file:
        update_relations.NEWDATA = yaml.safe_load(yaml_file)
    yaml_file.close()
    update_relations.update_ancestor("ubuntu:18.04", "base:1.0.1")
    assert 'base:1.0.1' in update_relations.NEWDATA['images']['ubuntu']['18.04']['children']


@pytest.mark.test_build_latest
def test_build_latest():
    with open('tests/relations.yaml') as yaml_file:
        update_relations.NEWDATA = yaml.safe_load(yaml_file)
    yaml_file.close()
    temp_var_ori = update_relations.ORIDATA
    update_relations.build_latest('base', '1.0.1')
    assert temp_var_ori != update_relations.NEWDATA
    assert update_relations.NEWDATA['latest']['base'] == "1.0.1"


@pytest.mark.test_list_cleaner
def test_list_cleaner():
    temp_list = update_relations.list_cleaner(['samtools1.11:1.0.1', ['fastqc0.11.9:1.0.1'], ['rseqc4.0.0:1.0.1'], ['deeptools3.5.0:1.0.1'], [['multiqc1.10:1.0.0']], [['java15:1.0.1'], ['deriva1.4:1.0.1']], [[['null']]]])
    assert temp_list == ['deeptools3.5.0:1.0.1', 'deriva1.4:1.0.1', 'fastqc0.11.9:1.0.1', 'java15:1.0.1', 'multiqc1.10:1.0.0', 'rseqc4.0.0:1.0.1', 'samtools1.11:1.0.1']
    temp_list = update_relations.list_cleaner([[[['null']]]])
    assert temp_list == ['null']
