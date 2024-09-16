# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard library imports
import glob
import xml.etree.ElementTree as ET
import unittest

# Third party imports

# Local application imports
from navigate.tools import xml_tools


def test_xml_parse_write():

    for fn in glob.glob("./xml_examples/*.xml"):
        # Open XML file
        with open(fn, "r") as fp:
            example = fp.read()
        root = ET.fromstring(example)

        # Parse it
        parsed = xml_tools.parse_xml(root)
        # Convert it back to a string
        xml_string = xml_tools.dict_to_xml(parsed, root.tag)

        # get rid of <?xml and the <!-- comment
        example_str = (
            "".join(example.split("\n")[2:]).replace(" ", "").replace("\t", "")
        )
        xml_str = (
            xml_string.strip().replace(" ", "").replace("\n", "").replace("\t", "")
        )

        # Make sure the strings match, sans white space
        assert example_str == xml_str

        # Parse the string we created
        root2 = ET.fromstring(xml_string)
        parsed2 = xml_tools.parse_xml(root2)

        # Make sure it matches the dictionary parsed from the original document
        assert parsed == parsed2


class TestDictToXml(unittest.TestCase):
    def test_dict_to_xml_with_single_level(self):
        # Test case with a dictionary containing a single level
        d = {"name": "John", "age": 30, "city": "New York"}
        expected_xml = '<name name="John" age="30" city="New York"/>\n'
        actual_xml = xml_tools.dict_to_xml(d)
        self.assertEqual(actual_xml, expected_xml)

    def test_dict_to_xml_with_nested_dict(self):
        # Test case with a dictionary containing nested dictionaries
        d = {
            "person": {"name": "John", "age": 30, "city": "New York"},
            "address": {"street": "123 Main St", "zipcode": "10001"},
        }
        expected_xml = (
            '<root>\n  <person name="John" age="30" '
            'city="New York"/>\n  <address street="123 '
            'Main St" zipcode="10001"/>\n</root>\n'
        )
        actual_xml = xml_tools.dict_to_xml(d, tag="root")
        self.assertEqual(actual_xml, expected_xml)

    def test_dict_to_xml_with_nested_list(self):
        # Test case with a dictionary containing nested lists
        d = {
            "students": [
                {"name": "Alice", "age": 20},
                {"name": "Bob", "age": 22},
                {"name": "Charlie", "age": 21},
            ]
        }
        expected_xml = (
            '<class>\n  <students name="Alice" '
            'age="20"/>\n  <students name="Bob" '
            'age="22"/>\n  <students name="Charlie" age="21"/>\n</class>\n'
        )
        actual_xml = xml_tools.dict_to_xml(d, tag="class")
        self.assertEqual(actual_xml, expected_xml)

    def test_dict_to_xml_with_text_value(self):
        # Test case with a dictionary containing a text value
        d = {
            "person": {
                "name": "John",
                "age": 30,
                "city": "New York",
                "text": "Hello, world!",
            }
        }
        expected_xml = (
            '<root>\n  <person name="John" age="30" '
            'city="New York">Hello, world!</person>\n</root>\n'
        )
        actual_xml = xml_tools.dict_to_xml(d, tag="root")
        self.assertEqual(actual_xml, expected_xml)


if __name__ == "__main__":
    unittest.main()
