import glob

import xml.etree.ElementTree as ET

def test_xml_parse_write():
    from aslm.tools import xml_tools

    for fn in glob.glob('./xml_examples/*.xml'):
        with open(fn, 'r') as fp:
            example = fp.read()
        root = ET.fromstring(example)
        parsed = xml_tools.parse_xml(root)
        xml_string = xml_tools.dict_to_xml(parsed, root.tag)

        example_str = "".join(example.split("\n")[2:]).replace(" ", "").replace("\t", "")
        xml_str = xml_string.strip().replace(" ", "").replace("\n", "").replace("\t", "")
        
        assert(example_str == xml_str)
