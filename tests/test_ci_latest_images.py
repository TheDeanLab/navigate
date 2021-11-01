#!/usr/bin/env python3


import sys
import os
import pytest
import yaml
from io import StringIO
sys.path.append(os.path.abspath("scripts/"))
import ci_latest_images

test_vars = []


@pytest.mark.test_load_yaml
def test_load_yaml():
    test_vars.append(ci_latest_images.load_yaml('tests/relations.yaml'))
    assert test_vars[0] == {'images': {'base': {'1.0.0': {'children': [None], 'parents': ['ubuntu:18.04']}}, 'ubuntu': {
        '18.04': {'children': ['base:1.0.0'], 'parents': []}}}, 'latest': {'base': '1.0.0'}, 'terminated': ['test_image2']}


@pytest.mark.test_pull_image
def test_pull_image(capfd):
    ci_latest_images.pull_image('bicf/base:1.0.0')
    test_err = capfd.readouterr()[1]
    assert not "ERROR: Unable to build bicf/base:1.0.0" in test_err
