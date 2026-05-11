import time
import xml.etree.ElementTree as ET
from typing import Dict, Any, Callable, Tuple
from multilevelgraphs import MultilevelGraph, __version__, Supernode, Superedge


def _default_node_label_func(supernode: Supernode) -> str:
    return str(supernode['label']) if 'label' in supernode.attr else str(supernode.key)


def _default_node_color_func(supernode: Supernode) -> Tuple[str, str, str, str]:
    if 'color' in supernode.attr and isinstance(supernode['color'], Tuple) and len(supernode['color']) == 3 and \
            all((isinstance(c, int) and 0 <= c <= 255) for c in supernode['color']):
        return str(supernode['color'][0]), str(supernode['color'][1]), str(supernode['color'][2]), "1.0"
    elif supernode.supernode:
        hashcode = hash(supernode.supernode.key)
    else:
        hashcode = hash(supernode.key)
    return str((hashcode & 0xFF0000) >> 16), str((hashcode & 0x00FF00) >> 8), str(hashcode & 0x0000FF), "1.0"


def _default_node_size_func(supernode: Supernode) -> str:
    if 'size' in supernode.attr:
        return str(supernode['size'])
    else:
        return str(supernode.size() * 10)


def _default_edge_color_func(edge: Superedge) -> Tuple[str, str, str, str]:
    if 'color' in edge.attr and isinstance(edge['color'], Tuple) and len(edge['color']) == 3 and \
            all((isinstance(c, int) and 0 <= c <= 255) for c in edge['color']):
        return str(edge['color'][0]), str(edge['color'][1]), str(edge['color'][2]), "1.0"
    elif edge.tail.supernode and edge.head.supernode and edge.tail.supernode == edge.head.supernode:
        hashcode = hash(edge.tail.supernode.key)
        return str((hashcode & 0xFF0000) >> 16), str((hashcode & 0x00FF00) >> 8), str(hashcode & 0x0000FF), "1.0"
    else:
        return "0", "0", "0", "1.0"


def _default_edge_thickness_func(edge: Superedge) -> str:
    if 'thickness' in edge.attr:
        return str(edge['thickness'])
    else:
        return str(edge.size())


def write_gexf(ml_graph: MultilevelGraph, file_path: str, description: str = None):
    """
    Write a GEXF file for the given MultilevelGraph in the specified file path.
    The produced GEXF file will contain just the core information, in order to retain the graph structure and
    information including nodes and edges attributes.

    For visualization purposes, use :meth:`write_gexf_for_viz` instead.

    :param ml_graph: the MultilevelGraph to write
    :param file_path: the path of the file to write
    :param description: a description of the graph to add in the metadata of the GEXF file
    """
    writer = GEXFWriter(ml_graph, description=description)
    for supernode in ml_graph.get_graph(ml_graph.height(), deepcopy=False).nodes():
        _add_node_and_children(writer, supernode)

    for key, edge in [key_edge for i in range(ml_graph.height())
                      for key_edge in ml_graph.get_graph(i, deepcopy=False).E.items()]:
        superedge_attr = edge.attr
        if edge.level:
            superedge_attr |= {'level': edge.level}
        writer.add_edge(str(key), str(edge.tail.key), str(edge.head.key), attributes=superedge_attr)

    writer.write(file_path)


def write_gexf_for_viz(ml_graph: MultilevelGraph, file_path: str, description: str = None,
                       node_label_func: Callable[[Supernode], str] = _default_node_label_func,
                       node_color_func: Callable[[Supernode], Tuple[str, str, str, str]] = _default_node_color_func,
                       node_size_func: Callable[[Supernode], str] = _default_node_size_func,
                       edge_color_func: Callable[[Superedge], Tuple[str, str, str, str]] = _default_edge_color_func,
                       edge_thickness_func: Callable[[Superedge], str] = _default_edge_thickness_func):
    """
    Write a GEXF file for the given MultilevelGraph in the specified file path.
    The produced GEXF file will contain all the information for visualization such as visual attributes and
    extra edges between children and supernodes.

    More specifically, all the extra edges between children and supernodes will have their color set to the child color
    and will be made semi-transparent in the visualization to distinguish them from the edges between supernodes of the
    same level.
    Furthermore, an extra boolean edge attribute `same_level` will be added to distinguish between original and added
    edges, having the value `1` (true) and `0` (false) respectively.

    The visualization attributes can be customized by passing the appropriate functions as parameters.

    :param ml_graph: the MultilevelGraph to write
    :param file_path: the path of the file to write
    :param description: a description of the graph to add in the metadata of the GEXF file
    :param node_label_func: a function that takes a Supernode and returns the label for the node. The default function
        returns the key of the supernode if a 'label' custom attribute is not present.
    :param node_color_func: a function that takes a Supernode and returns the color for the node. The default function
        returns a color based on the hash of the supernode key if a 'color' custom attribute is not present.
    :param node_size_func: a function that takes a Supernode and returns the size for the node. The default function
        returns the size of the supernode multiplied by 10 if a 'size' custom attribute is not present.
    :param edge_color_func: a function that takes a Superedge and returns the color for the edge. The default function
        returns a color based on the hash of the supernode key if a 'color' custom attribute is not present.
    :param edge_thickness_func: a function that takes a Superedge and returns the thickness for the edge. The default
        function returns the size of the edge if a 'thickness' custom attribute is not present.
    """
    writer = GEXFWriter(ml_graph, description=description)
    for supernode in ml_graph.get_graph(ml_graph.height(), deepcopy=False).nodes():
        _add_node_and_children(writer, supernode, node_label_func, node_color_func, node_size_func)

    writer.add_edge_attribute('same_level', bool)
    for key, edge in [key_edge for i in range(ml_graph.height()+1)
                      for key_edge in ml_graph.get_graph(i, deepcopy=False).E.items()]:
        superedge_attr = edge.attr
        if edge.level is not None:
            superedge_attr |= {'level': edge.level}
        writer.add_edge(str(key), str(edge.tail.key), str(edge.head.key),
                        color=edge_color_func(edge),
                        thickness=edge_thickness_func(edge),
                        attributes=superedge_attr | {'same_level': "1"})
    writer.write(file_path)


def _add_node_and_children(writer: 'GEXFWriter', supernode: Supernode,
                           node_label_func: Callable[[Supernode], str] = None,
                           node_color_func: Callable[[Supernode], Tuple[str, str, str, str]] = None,
                           node_size_func: Callable[[Supernode], str] = None,
                           supernode_element: ET.Element = None):

    # Gather supernode attributes
    supernode_attr = supernode.attr
    if supernode.level is not None:
        supernode_attr |= {'level': supernode.level}
    if supernode.supernode is not None:
        supernode_attr |= {'supernode': supernode.supernode}
    if supernode.component_sets is not None:
        supernode_attr |= {'component_sets': supernode.component_sets}

    # Add supernode
    node_element = writer.add_node(node_id=str(supernode.key),
                                   label=node_label_func(supernode) if node_label_func is not None else None,
                                   color=node_color_func(supernode) if node_color_func is not None else None,
                                   size=node_size_func(supernode) if node_size_func is not None else None,
                                   parent=supernode_element,
                                   attributes=supernode_attr)

    # Add children and edges between children and their supernode
    for child in supernode.dec.nodes():
        _add_node_and_children(writer, child, node_label_func, node_color_func, node_size_func, node_element)

        # If the GEXF is for visualization, add an extra edge between the child and the supernode
        if node_label_func is not None:
            # Edges between children and supernode have their color set to the child color and are made semi-transparent
            # in the visualization to distinguish them from the edges between supernodes of the same level
            edge_color = node_color_func(child)
            edge_color = (edge_color[0], edge_color[1], edge_color[2], "0.3")
            writer.add_edge(edge_id="(" + child.key + ", " + supernode.key + ")",
                            source_id=str(child.key),
                            target_id=str(supernode.key),
                            color=edge_color,
                            attributes={'same_level': "0"})


class GEXF:
    versions = {
        "1.3": {
            "NS_GEXF": 'http://gexf.net/1.3',
            "NS_VIZ": "http://www.gexf.net/1.3/viz",
            "NS_XSI": 'http://www.w3.org/2001/XMLSchema-instance',
            "SCHEMALOCATION": " ".join([
                'http://gexf.net/1.3,'
                'http://gexf.net/1.3/gexf.xsd']),
            "VERSION": "1.3",
        }
    }

    types: Dict[type, str] = dict([
        (int, "integer"),
        (float, "float"),
        (bool, "boolean"),
        (str, "string")
    ])


class GEXFWriter:
    def __init__(self, ml_graph: MultilevelGraph,
                 version: str = "1.3",
                 encoding: str = "utf-8",
                 prettyprint: bool = True,
                 description: str = None):
        """
        Create a GEXFWriter object to write a GEXF file for a multilevel graph.

        :param ml_graph: the multilevel graph to write
        :param version: the version of the GEXF file to write
        :param encoding: the encoding of the GEXF file to write
        :param prettyprint: if True, the GEXF file will be written with indentation and newlines for better readability
        :param description: a description of the graph to add in the meta element
        """
        self.gexf = ET.Element('gexf',
                               {'xmlns': GEXF.versions[version]["NS_GEXF"],
                                'xmlns:viz': GEXF.versions[version]["NS_VIZ"],
                                'xmlns:xsi': GEXF.versions[version]["NS_XSI"],
                                'xsi:schemaLocation': GEXF.versions[version]["SCHEMALOCATION"],
                                'version': GEXF.versions[version]["VERSION"]})
        self.encoding = encoding
        self.prettyprint = prettyprint
        self.graph = ET.SubElement(self.gexf, 'graph', {'mode': 'static', 'defaultedgetype': 'directed'})
        self.graph.set('height', str(ml_graph.height()))
        self.graph.set('schemes', str(ml_graph.get_contraction_schemes()))
        self.node_attributes = ET.SubElement(self.graph, 'attributes', {'class': 'node'})
        self.edge_attributes = ET.SubElement(self.graph, 'attributes', {'class': 'edge'})
        self.nodes = ET.SubElement(self.graph, 'nodes')
        self.edges = ET.SubElement(self.graph, 'edges')
        self.nodes_attr_set = set()
        self.edges_attr_set = set()

        # Make meta element a non-graph element
        # Also add lastmodifieddate as attribute, not tag
        meta_element = ET.Element("meta")
        ET.SubElement(meta_element, "creator").text = f"MultiLevelGraphs {__version__}"
        meta_element.set("lastmodifieddate", time.strftime("%d-%m-%Y"))
        if description:
            ET.SubElement(meta_element, "description").text = description
        self.gexf.append(meta_element)

    def add_node_attribute(self, attr_name: str, attr_type: type):
        if attr_name not in self.nodes_attr_set:
            ET.SubElement(self.node_attributes, 'attribute',
                          {'id': attr_name,
                           'title': attr_name.title(),
                           'type': GEXF.types.setdefault(attr_type, 'string')})
            self.nodes_attr_set.add(attr_name)

    def add_edge_attribute(self, attr_name: str, attr_type: type):
        if attr_name not in self.edges_attr_set:
            ET.SubElement(self.edge_attributes, 'attribute',
                          {'id': attr_name,
                           'title': attr_name.title(),
                           'type': GEXF.types.setdefault(attr_type, 'string')})
            self.edges_attr_set.add(attr_name)

    def add_node(self, node_id: str,
                 label: str = None,
                 color: Tuple[str, str, str, str] = None,
                 size: str = None,
                 parent: ET.Element = None,
                 attributes: Dict[str, Any] = None) -> ET.Element:

        # Create node element
        if label:
            node = ET.Element('node', {'id': node_id, 'label': label})
        else:
            node = ET.Element('node', {'id': node_id})

        # Add custom attributes
        if attributes:
            attvalues = ET.SubElement(node, 'attvalues')
            for attr_name, value in attributes.items():
                self.add_node_attribute(attr_name, type(value))
                ET.SubElement(attvalues, 'attvalue', {'for': attr_name, 'value': str(value)})

        # Add visualization attributes
        if color:
            ET.SubElement(node, 'viz:color', {'r': color[0], 'g': color[1], 'b': color[2], 'a': color[3]})
        if size:
            ET.SubElement(node, 'viz:size', {'value': size})

        # Add node to the graph or to the parent node nodes
        if parent is not None:
            if parent.find('nodes') is None:
                ET.SubElement(parent, 'nodes')
            parent.find('nodes').append(node)
        else:
            self.nodes.append(node)

        return node

    def add_edge(self, edge_id: str, source_id: str, target_id: str,
                 color: Tuple[str, str, str, str] = None,
                 thickness: str = None,
                 attributes: Dict[str, Any] = None):

        # Create edge element
        edge = ET.SubElement(self.edges, 'edge', {'id': edge_id, 'source': source_id, 'target': target_id})

        # Add visualization attributes
        if attributes:
            attvalues = ET.SubElement(edge, 'attvalues')
            for attr_id, value in attributes.items():
                self.add_edge_attribute(attr_id, type(value))
                ET.SubElement(attvalues, 'attvalue', {'for': attr_id, 'value': str(value)})

        # Add visualization attributes
        if color:
            ET.SubElement(edge, 'viz:color', {'r': color[0], 'g': color[1], 'b': color[2], 'a': color[3]})
        if thickness:
            ET.SubElement(edge, 'viz:thickness', {'value': thickness})

    def write(self, file_path):
        if self.prettyprint:
            self._indent(self.gexf)
        tree = ET.ElementTree(self.gexf)
        tree.write(file_path, encoding=self.encoding, xml_declaration=True)

    def _indent(self, elem, level=0):
        # in-place prettyprint formatter
        i = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i