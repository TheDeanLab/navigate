def dict_to_xml(d, root=None):
    """Parse a Python dictionary to XML.
    
    Parameters
    ----------
    d: dict
        Dictionary to parse to XML.
    root : str
        Root key of dictionary
    """

    if root is None:
        root = list(d.keys())[0]

    xml = f"<{root}"
    if isinstance(d, dict):
        next_xml = ""
        for k, v in d.items():
            if isinstance(v, dict):
                # Not a leaf node
                next_xml = dict_to_xml(v, k)
            else:
                xml += f" {k}=\"{v}\""
        xml += ">"
        xml += next_xml
    xml += f"</{root}>"

    return xml

def parse_xml(root):
    """
    Parse an XML ElementTree.

    Parameters
    ----------
    root : xml.etree.ElementTree.Element
        root Element of XML ElementTree
    """
    d = {}
    for k, v in root.attrib.items():
        d[k] = v
    text = root.text.strip()
    if text != '':
        d['text'] = text
    prev_tag = ''
    count = 0
    for child in root:
        tag = child.tag + str(count)
        if tag == prev_tag:
            count += 1
            tag = child.tag + str(count)
        prev_tag = tag
        d[tag] = parse_xml(child)
    return d
