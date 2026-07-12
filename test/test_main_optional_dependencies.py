import builtins
import logging
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import navigate.main as main_module


def test_main_import_does_not_require_opengl_dependencies():
    repository_root = Path(__file__).resolve().parents[1]
    source_root = repository_root / "src"
    script = textwrap.dedent(
        """
        import builtins

        original_import = builtins.__import__
        blocked = {"OpenGL", "glfw", "glm", "tkinterdnd2"}

        def block_optional_imports(name, *args, **kwargs):
            root_name = name.split(".", 1)[0]
            if root_name in blocked:
                raise ModuleNotFoundError(
                    f"No module named '{root_name}'", name=root_name
                )
            return original_import(name, *args, **kwargs)

        builtins.__import__ = block_optional_imports
        import navigate.main
        """
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(source_root), environment.get("PYTHONPATH", "")])
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_load_volume_viewer_reports_actionable_dependency_guidance(
    monkeypatch, capsys, caplog
):
    original_import = builtins.__import__

    def fail_viewer_import(name, *args, **kwargs):
        if name == "navigate.view.display_backends.volume_viewer_standalone":
            raise ModuleNotFoundError(
                "No module named 'tkinterdnd2'", name="tkinterdnd2"
            )
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_viewer_import)

    with caplog.at_level(logging.ERROR, logger="navigate.main"):
        viewer_class = main_module._load_volume_viewer()

    terminal_message = capsys.readouterr().err
    quoted_python = f'"{sys.executable}"'
    assert viewer_class is None
    assert "Unable to start the optional navigate Volume Viewer" in terminal_message
    assert "tkinterdnd2" in terminal_message
    assert "activate" in terminal_message.lower()
    assert f'{quoted_python} -m pip install -e ".[opengl]"' in terminal_message
    assert (
        f'{quoted_python} -m pip install "navigate-micro[opengl]"' in terminal_message
    )
    assert "navigate --viewer" in terminal_message
    assert "ModuleNotFoundError: No module named 'tkinterdnd2'" in terminal_message
    assert "Unable to import the optional Volume Viewer" in caplog.text
