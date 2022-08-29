import glob

import xml.etree.ElementTree as ET

def test_xml_parse_write():
    from aslm.tools import xml_tools

    for fn in glob.glob('./xml_examples/*.xml'):
        # Open XML file
        with open(fn, 'r') as fp:
            example = fp.read()
        root = ET.fromstring(example)
        
        # Parse it
        parsed = xml_tools.parse_xml(root)
        # Convert it back to a string
        xml_string = xml_tools.dict_to_xml(parsed, root.tag)

        # get rid of <?xml and the <!-- comment
        example_str = "".join(example.split("\n")[2:]).replace(" ", "").replace("\t", "")
        xml_str = xml_string.strip().replace(" ", "").replace("\n", "").replace("\t", "")
        
        # Make sure the strings match, sans white space
        assert(example_str == xml_str)

        # Parse the string we created
        root2 = ET.fromstring(xml_string)
        parsed2 = xml_tools.parse_xml(root2)

        # Make sure it matches the dictionary parsed from the original document
        assert(parsed==parsed2)
