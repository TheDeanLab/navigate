from pathlib import Path

from navigate.tools import file_functions


def _base_saving_settings(root_directory):
    return {
        "root_directory": str(root_directory),
        "user": "Test User",
        "tissue": "Brain",
        "celltype": "Neuron",
        "prefix": "Cell_",
    }


def test_create_save_path_with_multichannel_labels(tmp_path):
    saving_settings = _base_saving_settings(tmp_path)
    saving_settings.update(
        {
            "label_561nm": "",
            "label_488nm": "GFP",
        }
    )

    save_directory = file_functions.create_save_path(saving_settings)

    # Empty label values should keep the wavelength token only.
    assert "488nm_gfp_561nm" in save_directory
    assert saving_settings["save_directory"] == save_directory
    assert len(saving_settings["date"]) == 8


def test_save_yaml_file_restores_previous_content_on_failure(tmp_path, monkeypatch):
    target_file = tmp_path / "experiment.yml"
    original_content = '{"existing": true}'
    target_file.write_text(original_content)

    def raise_dumps(*args, **kwargs):
        raise RuntimeError("forced serialization failure")

    monkeypatch.setattr(file_functions.json, "dumps", raise_dumps)

    result = file_functions.save_yaml_file(str(tmp_path), {"new": "value"})

    assert result is False
    assert target_file.read_text() == original_content


def test_write_to_yaml_handles_nested_dicts_and_lists(tmp_path):
    output = tmp_path / "out.yml"
    content = {
        "b": 2,
        "a": {"z": 1, "y": 0},
        "simple_list": [1, 2],
        "complex_list": [{"k": "v"}],
        "": "ignore_me",
    }

    file_functions.write_to_yaml(content, str(output))
    text = output.read_text()

    assert "a:\n" in text
    assert "  y: 0\n" in text
    assert "  z: 1\n" in text
    assert "simple_list: [1, 2]\n" in text
    assert "complex_list:\n" in text
    assert "    k: v\n" in text
    assert "ignore_me" not in text


def test_delete_folder_ignores_permission_and_os_errors(monkeypatch):
    calls = []
    root = str(Path("/tmp/fake_locked_root"))

    monkeypatch.setattr(
        file_functions.os,
        "walk",
        lambda top, topdown=False: [(top, ["locked_dir"], ["locked_file"])],
    )

    def fake_remove(path):
        calls.append(("remove", path))
        raise PermissionError("simulated lock")

    def fake_rmdir(path):
        calls.append(("rmdir", path))
        raise OSError("simulated lock")

    monkeypatch.setattr(file_functions.os, "remove", fake_remove)
    monkeypatch.setattr(file_functions.os, "rmdir", fake_rmdir)

    # Should swallow exceptions and finish cleanly.
    file_functions.delete_folder(root)

    assert ("remove", f"{root}/locked_file") in calls
    assert ("rmdir", f"{root}/locked_dir") in calls
    assert ("rmdir", root) in calls
