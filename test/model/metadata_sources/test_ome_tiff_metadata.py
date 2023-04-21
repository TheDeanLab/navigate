import urllib.request
import os
import platform

from aslm.tools.file_functions import delete_folder


def test_ome_metadata_valid(dummy_model):
    from aslm.model.metadata_sources.ome_tiff_metadata import OMETIFFMetadata

    # First, download OME-XML validation tools
    urllib.request.urlretrieve(
        "https://downloads.openmicroscopy.org/bio-formats/6.0.1/artifacts/bftools.zip",
        "bftools.zip",
    )

    # Unzip
    output = os.popen("tar -xzvf bftools.zip").read()

    # Create metadata
    md = OMETIFFMetadata()

    md.configuration = dummy_model.configuration

    # Write metadata to file
    md.write_xml("test.xml")

    # Validate the XML
    if platform.system() == "Windows":
        output = os.popen("bftools\\xmlvalid.bat test.xml").read()
    else:
        output = os.popen("./bftools/xmlvalid test.xml").read()

    print(output)

    # Delete bftools
    delete_folder("./bftools")
    os.remove("bftools.zip")

    # Delete XML
    os.remove("test.xml")

    assert "No validation errors found." in output
