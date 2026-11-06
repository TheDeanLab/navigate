import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

from test.model.metadata_sources.bioformats import _get_bftools_archive


@pytest.mark.integration
def test_ome_metadata_valid(dummy_model, pytestconfig, tmp_path):
    from navigate.model.metadata_sources.ome_tiff_metadata import OMETIFFMetadata

    archive = _get_bftools_archive(Path(pytestconfig.cache.mkdir("bioformats")))
    with ZipFile(archive) as bundle:
        bundle.extractall(tmp_path)

    md = OMETIFFMetadata()
    md.configuration = dummy_model.configuration
    xml_path = tmp_path / "test.xml"
    md.write_xml(str(xml_path))

    result = subprocess.run(
        [
            "java",
            "-Xmx512m",
            "-cp",
            str(tmp_path / "bftools" / "bioformats_package.jar"),
            "loci.formats.tools.XMLValidate",
            str(xml_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    assert "No validation errors found." in result.stdout, result.stdout + result.stderr
