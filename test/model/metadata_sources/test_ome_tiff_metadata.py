import platform
import subprocess
from pathlib import Path

import pytest

from test.model.metadata_sources.bioformats import _get_bftools_archive


@pytest.mark.integration
def test_ome_metadata_valid(dummy_model, pytestconfig, tmp_path):
    from navigate.model.metadata_sources.ome_tiff_metadata import OMETIFFMetadata

    archive = _get_bftools_archive(Path(pytestconfig.cache.mkdir("bioformats")))
    subprocess.run(["tar", "-xf", str(archive)], cwd=tmp_path, check=True, timeout=60)

    md = OMETIFFMetadata()
    md.configuration = dummy_model.configuration
    xml_path = tmp_path / "test.xml"
    md.write_xml(str(xml_path))

    launcher = "xmlvalid.bat" if platform.system() == "Windows" else "xmlvalid"
    result = subprocess.run(
        [str(tmp_path / "bftools" / launcher), str(xml_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    assert "No validation errors found." in result.stdout, result.stdout + result.stderr
