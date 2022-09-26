import pytest


def test_ome_metadata_valid():
    import urllib.request
    import os
    import platform
    from aslm.model.dummy_model import DummyModel
    from aslm.model.model_features.metadata_sources.ome_tiff_metadata import OMETIFFMetadata

    # First, download OME-XML validation tools
    urllib.request.urlretrieve("https://downloads.openmicroscopy.org/bio-formats/6.0.1/artifacts/bftools.zip",
                               "bftools.zip")

    # Unzip
    output = os.popen('tar -xzvf bftools.zip').read()

    # Create metadata
    model = DummyModel()

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

    # Delete bftools
    delete_folder('./bftools')
    os.remove('bftools.zip')

    # Delete XML
    os.remove('test.xml')

    assert ('No validation errors found.' in output)


def delete_folder(top):
    # https://docs.python.org/3/library/os.html#os.walk
    # Delete everything reachable from the directory named in "top",
    # assuming there are no symbolic links.
    # CAUTION:  This is dangerous!  For example, if top == '/', it
    # could delete all your disk files.
    import os
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
