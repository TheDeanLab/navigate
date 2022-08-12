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
                    xml += f" {k}=\"{v}\""
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
        if text != '':
            d['text'] = text
    except AttributeError:
        # root.text is None
        pass
    prev_tag = ''
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
