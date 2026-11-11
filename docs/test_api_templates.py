"""API docs checks requiring the docs dependencies and pytest.

Run with ``python -m pytest -o addopts= docs/test_api_templates.py``.
"""

from pathlib import Path
import subprocess
import sys
import zlib


def test_api_templates_preserve_navigate_inheritance(tmp_path: Path) -> None:
    """Keep inherited Navigate APIs without importing instance attributes or Tk APIs."""
    source = Path(__file__).parent / "source"
    inventory = tmp_path / "numpy.inv"
    inventory.write_bytes(
        b"# Sphinx inventory version 2\n# Project: NumPy\n# Version: test\n"
        b"# The remainder of this file is compressed using zlib.\n"
        + zlib.compress(
            b"arrays.ndarray std:label -1 "
            b"reference/arrays.ndarray.html#arrays-ndarray "
            b"The N-dimensional array (ndarray)\n"
        )
    )
    (tmp_path / "conf.py").write_text(
        "import runpy\n"
        f"globals().update(runpy.run_path({str(source / 'conf.py')!r}))\n"
        f"templates_path = [{str(source / '_templates')!r}]\n"
        "extensions = [name for name in extensions if name in "
        "('sphinx.ext.autodoc', 'sphinx.ext.autosummary', "
        "'sphinx.ext.napoleon', 'sphinx.ext.intersphinx')]\n"
        "intersphinx_mapping = {key: (url, "
        f"{str(inventory)!r}) for key, (url, _) in "
        "globals().get('intersphinx_mapping', {}).items()}\n"
        "html_logo = None\n"
        "master_doc = 'index'\n"
    )
    (tmp_path / "index.rst").write_text(
        "API regression\n==============\n\n"
        ".. autosummary::\n"
        "   :toctree: generated\n"
        "   :template: custom_class.rst\n\n"
        "   navigate.controller.sub_controllers.acquire_bar.AcquireBarController\n"
        "   navigate.config.configuration_schema.SettingSpec\n"
        "   navigate.model.concurrency.concurrency_tools.SharedNDArray\n"
        "   navigate.view.configurator_application_window."
        "ConfigurationAssistantWindow\n"
    )
    output = tmp_path / "html"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-E",
            "-a",
            "-W",
            "--keep-going",
            "-b",
            "html",
            str(tmp_path),
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    controller = "navigate.controller.sub_controllers.acquire_bar.AcquireBarController"
    html = (output / "generated" / f"{controller}.html").read_text()
    # Inherited method, inherited property, inherited instance attribute, and override.
    for member in ("register_event_listener", "custom_events", "view", "initialize"):
        assert f'id="{controller}.{member}"' in html
        assert f'href="#{controller}.{member}"' in html

    window = (
        "navigate.view.configurator_application_window.ConfigurationAssistantWindow"
    )
    html = (output / "generated" / f"{window}.html").read_text()
    assert f'id="{window}.__init__"' in html
    assert f'id="{window}.grid_configure"' not in html
    assert f'href="#{window}.grid_configure"' not in html

    spec = "navigate.config.configuration_schema.SettingSpec"
    html = (output / "generated" / f"{spec}.html").read_text()
    for member in ("default", "choice_values"):
        assert f'id="{spec}.{member}"' in html
        assert f'href="#{spec}.{member}"' in html

    array = "navigate.model.concurrency.concurrency_tools.SharedNDArray"
    html = (output / "generated" / f"{array}.html").read_text()
    assert f'id="{array}.strides"' in html
    assert (
        'href="https://numpy.org/doc/stable/reference/arrays.ndarray.html'
        '#arrays-ndarray"' in html
    )
