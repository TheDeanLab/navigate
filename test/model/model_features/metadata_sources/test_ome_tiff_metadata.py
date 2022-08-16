import pytest


@pytest.mark.skip(reason="Error parsing schema on Windows, despite schema being present and accurate.")
def test_ome_metadata_valid():
    import urllib.request
    import os
    import platform
    from aslm.model.dummy_model import get_dummy_model
    from aslm.model.model_features.metadata_sources.ome_tiff_metadata import OMETIFFMetadata

    # First, download OME-XML validation tools
    urllib.request.urlretrieve("https://downloads.openmicroscopy.org/bio-formats/6.0.1/artifacts/bftools.zip",
                               "bftools.zip")

    # Unzip
    output = os.popen('tar -xzvf bftools.zip').read()

    # Create metadata
    model = get_dummy_model()

    md = OMETIFFMetadata()

    md.configuration = model.configuration
    md.experiment = model.experiment

    # Write metadata to file
    md.write_xml('test.xml')

    # Validate the XML
    if platform.system() == 'Windows':
        output = os.popen('bftools\\xmlvalid.bat test.xml').read()
    else:
        output = os.popen('./bftools/xmlvalid test.xml').read()

    print(output)

    assert('No validation errors found.' in output)

    # Delete bftools
    os.rmdir('./bftools')
    os.remove('bftools.zip')

    # Delete XML
    os.remove('test.xml')

