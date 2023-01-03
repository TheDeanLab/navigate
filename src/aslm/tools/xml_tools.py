# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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

import xml.etree.ElementTree as ET


def dict_to_xml(d, tag=None):
    """Parse a Python dictionary to XML.

    Parameters
    ----------
    d: dict
        Dictionary to parse to XML.
    tag : str
        Root key of dictionary

    Returns
    -------
    xml : str
        String of XML tags produced from dictionary.
    """

    if tag is None:
        tag = list(d.keys())[0]

    xml = f"<{tag}"
    if isinstance(d, dict):
        next_xml = ""
        text = ""
        for k, v in d.items():
            if isinstance(v, dict):
                # Not a leaf node
                next_xml += dict_to_xml(v, k)
            elif isinstance(v, list):
                for el in v:
                    next_xml += dict_to_xml(el, k)
            else:
                if k == "text":
                    text = str(v)
                else:
                    xml += f' {k}="{v}"'
        if text != "" or next_xml != "":
            xml += ">"
            xml += text
            xml += next_xml
            xml += f"</{tag}>"
        else:
            xml += "/>"

    return xml


def parse_xml(root: ET.Element) -> dict:
    """
    Parse an XML ElementTree.

    TODO: Does not account for namespacing. See OME-XML.

    Parameters
    ----------
    root : xml.etree.ElementTree.Element
        root Element of XML ElementTree

    Returns
    -------
    d : dict
        Dictionary representation of the XML file.
    """
    d = {}
    for k, v in root.attrib.items():
        d[k] = v
    try:
        text = root.text.strip()
        if text != "":
            d["text"] = text
    except AttributeError:
        # root.text is None
        pass
    prev_tag = ""
    for child in root:
        tag = child.tag
        if tag == prev_tag:
            if type(d[tag]) != list:
                # create the list
                tmp = d[tag]
                d[tag] = []
                d[tag].append(tmp)
            d[tag].append(parse_xml(child))
        else:
            d[tag] = parse_xml(child)
        prev_tag = tag
    return d
