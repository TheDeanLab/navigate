import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_main_import_does_not_require_opengl_dependencies():
    repository_root = Path(__file__).resolve().parents[1]
    source_root = repository_root / "src"
    script = textwrap.dedent(
        """
        import builtins

        original_import = builtins.__import__
        blocked = {"oblisq", "OpenGL", "glfw", "glm", "tkinterdnd2"}

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
