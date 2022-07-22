def dict_to_xml(d, root='object'):
    """Parse a Python dictionary to XML.
    
    Parameters
    ----------
    d: dict
        Dictionary to parse to XML.
    root : str
        Root key of dictionary
    """

    xml = f"<{root}"
    if isinstance(d, dict):
        next_xml = ""
        print(d.keys(), root)
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
