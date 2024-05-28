from typing import Optional, Set, Dict, Any, Iterable, FrozenSet
import networkx as nx


class DecGraph:
    V: Dict[Any, 'Supernode']
    E: Dict[Any, 'Superedge']
    _graph: nx.DiGraph

    def __init__(self, dict_V: Dict[Any, 'Supernode'] = None, dict_E: Dict[Any, 'Superedge'] = None):
        self._graph = nx.DiGraph()
        self.V = dict_V if dict_V is not None else dict()
        self.E = dict_E if dict_E is not None else dict()
        self._graph.add_nodes_from(self.V.keys())
        self._graph.add_edges_from(self.E.keys())

    def nodes(self) -> Set['Supernode']:
        """
        Returns the set of supernodes in the decontractible graph.

        :return: the set of supernodes in the decontractible graph
        """
        return set(self.V.values())

    def edges(self) -> Set['Superedge']:
        """
        Returns the set of superedges in the decontractible graph.

        :return: the set of superedges in the decontractible graph
        """
        return set(self.E.values())

    def nodes_keys(self) -> Set:
        """
        Returns the set of keys of supernodes in the decontractible graph.

        :return: the set of keys of supernodes in the decontractible graph
        """
        return set(self.V.keys())

    def edges_keys(self) -> Set:
        """
        Returns the set of keys of superedges in the decontractible graph.

        :return: the set of keys of superedges in the decontractible graph
        """
        return set(self.E.keys())

    def forward_star(self, node: 'Supernode') -> Set['Supernode']:
        """
        Returns the forward star of a supernode in the decontractible graph, which is the set of supernodes m
        such that there is an edge from the given supernode to m in the decontractible graph.

        :param node: the supernode to get the forward star
        :return: the forward star of the supernode
        """
        return {self.V[key] for key in self.graph().successors(node.key)}

    def reverse_star(self, node: 'Supernode') -> Set['Supernode']:
        """
        Returns the reverse star of a supernode in the decontractible graph, which is the set of supernodes m
        such that there is an edge from m to the given supernode in the decontractible graph.

        :param node: the supernode to get the reverse star
        :return: the reverse star of the supernode
        """
        return {self.V[key] for key in self.graph().predecessors(node.key)}

    def out_edges(self, node: 'Supernode') -> Set['Superedge']:
        """
        Returns the set of superedges that have the given supernode as tail in the decontractible graph.

        :param node: the supernode to get the out edges
        :return: the set of superedges that have the given supernode as tail
        """
        return {self.E[(node.key, head.key)] for head in self.forward_star(node)}

    def in_edges(self, node: 'Supernode') -> Set['Superedge']:
        """
        Returns the set of superedges that have the given supernode as head in the decontractible graph.

        :param node: the supernode to get the in edges
        :return: the set of superedges that have the given supernode as head
        """
        return {self.E[(tail.key, node.key)] for tail in self.reverse_star(node)}

    def graph(self, ref: bool = False, attr: bool = False) -> nx.DiGraph:
        """
        Returns this decontractible graph as a simple directed graph with simple nodes and edges.
        If ref is True, the returned graph is a reference to this decontractible graph structure and
        changes in the returned graph will affect the orginal decontractible graph structure.
        If attr is True, nodes in the returned graph will carry the same attributes as the original decontractible
        graph supernodes.
        Note that setting ref to True will always return a graph with no attributes in the nodes, regardless of the
        value of the attr parameter.

        :param ref: If True, the returned graph is a view of the decontractible graph.
        :param attr: If True, the returned graph nodes have the same attributes as in the original
        decontractible graph.
        :return: the corresponding NetworkX directed graph
        """
        if ref:
            return self._graph
        elif attr:
            graph = nx.DiGraph()
            for n in self.nodes():
                graph.add_node(n.key, **n.attr)
            for e in self.edges():
                graph.add_edge(e.tail.key, e.head.key, **e.attr)
            return graph
        else:
            return nx.DiGraph(self._graph)

    def add_node(self, supernode: 'Supernode'):
        """
        Adds a supernode to the decontractible graph.
        If the supernode has a key that is already in the graph, it will not be added again.

        :param supernode: the supernode to be added
        """
        self.V[supernode.key] = supernode
        self._graph.add_node(supernode.key)

    def add_edge(self, superedge: 'Superedge'):
        """
        Adds a superedge to the decontractible graph.
        If the superedge has a tail and head the key of which are already in the graph as an edge,
        it will not be added again.
        If the supernodes of the superedge to be added are not included in the decontractible graph, rises a ValueError.

        :param superedge: the superedge to be added
        """
        if superedge.tail not in self.V.values() or superedge.head not in self.V.values():
            raise ValueError('The supernodes of the superedge to be added must be included in the decontractible graph.')
        if (superedge.tail.key, superedge.head.key) not in self.E:
            self.E[(superedge.tail.key, superedge.head.key)] = superedge
            self._graph.add_edge(superedge.tail.key, superedge.head.key)

    def remove_node(self, supernode: 'Supernode'):
        """
        Removes a supernode from the decontractible graph.
        All edges that have the supernode as tail or head in this decontractible graph will be removed as well.
        If the supernode has a key which is not in the graph, rise a KeyError.

        :param supernode: the supernode to be removed
        """
        for edge in self.in_edges(supernode):
            self.remove_edge(edge)
        for edge in self.out_edges(supernode):
            self.remove_edge(edge)

        self.V.pop(supernode.key)
        self._graph.remove_node(supernode.key)

    def remove_edge(self, superedge: 'Superedge'):
        """
        Removes a superedge from the decontractible graph.
        If the superedge has a tail and head the key of which are not in the graph as an edge,
        rise a KeyError.

        :param superedge: the superedge to be removed
        """
        self.E.pop((superedge.tail.key, superedge.head.key))
        self._graph.remove_edge(superedge.tail.key, superedge.head.key)

    def height(self) -> int:
        """
        Returns the height of the decontractible graph, as the maximum height among supernodes in this graph,
        where the height of a supernode is the height of the decontractible graph represented by the supernode.

        :return: the height of the decontractible graph
        """
        if not self.nodes():
            return -1
        else:
            return max(node.height() for node in self.nodes())

    def order(self) -> int:
        """
        Returns the order of the decontractible graph, as the number of supernodes in this graph.

        :return: the order of the decontractible graph
        """
        return len(self.nodes())

    def complete_decontraction(self) -> 'DecGraph':
        """
        Returns the complete decontraction of this decontractible graph.
        The complete decontraction of a decontractible graph is the decontractible graph obtained by expanding
        all supernodes and superedges into the supernodes and superedges they represent.

        If all supernodes and superedges in this decontractible graph have an empty decontraction, an empty
        decontractible graph is returned. Otherwise, if at least one supernode or superedge has a non-empty
        decontraction, the complete decontraction will contain all supernodes and superedges in those non-empty
        decontractions.

        :return: the complete decontraction of this decontractible graph
        """
        complete_decontraction = DecGraph()

        for node in self.nodes():
            for n in node.dec.nodes():
                complete_decontraction.add_node(n)
            for e in node.dec.edges():
                complete_decontraction.add_edge(e)

        for edge in self.edges():
            for e in edge.dec:
                complete_decontraction.add_edge(e)

        return complete_decontraction

    def induced_subgraph(self, nodes: Iterable['Supernode']) -> 'DecGraph':
        """
        Returns the induced decontractible subgraph of this decontractible graph by the given set of supernodes.
        The induced subgraph of a graph on a subset of nodes N is the graph with nodes N and edges from G which have
        both ends in N.
        If the set of supernodes keys is not entirely included in the decontractible graph, only the supernodes
        that are included in the decontractible graph will be considered.

        :param self: the decontractible graph
        :param nodes: the set of supernodes to induce the subgraph
        :return: the induced subgraph
        """
        return self.induced_subgraph_from_keys(set(map(lambda n: n.key, nodes)))

    def induced_subgraph_from_keys(self, nodes_keys: Set) -> 'DecGraph':
        """
        Returns the induced decontractible subgraph of this decontractible graph by the given set of supernodes
        keys.
        The induced subgraph of a graph on a subset of nodes N is the graph with nodes N and edges from G which have
        both ends in N.
        If the set of supernodes keys is not entirely included in the decontractible graph, only the supernodes
        keys that are included in this decontractible graph will be considered.

        :param self: the decontractible graph
        :param nodes_keys: the set of supernodes keys to induce the subgraph
        :return: the induced subgraph
        """
        induced_subgraph = nx.induced_subgraph(self._graph, self.nodes_keys() & nodes_keys)
        return DecGraph(dict_V={key: self.V[key] for key in induced_subgraph.nodes()},
                        dict_E={key: self.E[key] for key in induced_subgraph.edges()})

    def __len__(self):
        return self.order()

    def __eq__(self, other: 'DecGraph'):
        """
        Returns True if the decontractible graph is equal to the other decontractible graph.
        A decontractible graph is considered equal to another if there is a bijection between their supernodes and
        superedge where each supernode and superedge have the same key and an equal decontraction.

        :param other: the other decontractible graph to compare
        :return: True if this decontractible graph is equal to the other
        """
        other_nodes = other.nodes()
        self_nodes = self.nodes()
        if len(other_nodes) != len(self_nodes):
            return False
        for other_node in other_nodes:
            if other_node not in self_nodes:
                return False
            self_node = self.V[other_node.key]
            if self_node.dec != other_node.dec:
                return False

        other_edges = other.edges()
        self_edges = self.edges()
        if len(other_edges) != len(self_edges):
            return False
        for other_edge in other_edges:
            if other_edge not in self_edges:
                return False
            self_edge = self.E[(other_edge.tail.key, other_edge.head.key)]
            if self_edge.dec != other_edge.dec:
                return False

        return True


class Supernode:
    __slots__ = ('key', 'level', 'dec', 'component_sets', 'supernode', 'attr')

    def __init__(self, key,
                 level: int = None,
                 dec: DecGraph = None,
                 component_sets: FrozenSet = None,
                 supernode: Optional['Supernode'] = None,
                 **attr):
        """
        Initializes a supernode.

        :param key: an immutable value representing the key label of the supernode. It is used to identify the
        supernode in the decontractible graph and should be unique in the decontractible graph where the
        supernode resides.
        :param level: the level this supernode belongs to in a multilevel graph, if any
        :param dec: the decontractible graph represented by this supernode
        :param supernode: the supernode that this supernode into
        :param attr: a dictionary of attributes to be added to the supernode
        """
        self.key = key
        self.level = level
        self.dec = dec if dec is not None else DecGraph()
        self.component_sets = component_sets if component_sets is not None else frozenset()
        self.supernode = supernode
        self.attr = attr

    def is_in_multi_level_graph(self) -> bool:
        """
        Returns True if this supernode belongs to a multilevel graph, False otherwise.

        :return: True if this supernode belongs to a multilevel graph, False otherwise
        """
        return self.level is not None

    def add_node(self, supernode: 'Supernode'):
        """
        Adds a supernode to the decontractible graph represented by this supernode.
        If the supernode has a key that is already in the graph, it will not be added again.
        If this supernode belongs to a multilevel graph, the level of the supernode to be added must be one less than
        the level of this supernode.

        :param supernode: the supernode to be added
        """
        if self.level is not None and supernode.level != self.level-1:
            raise ValueError('The level of the supernode to be added must be one less than the level of this supernode.')
        self.dec.add_node(supernode)

    def add_edge(self, edge_for_adding: 'Superedge'):
        """
        Adds a superedge to the decontractible graph represented by this supernode.
            If the superedge has a tail and head the key of which are already in the graph as an edge,
            it will not be added again.

        :param edge_for_adding: the edge to be added
        """
        self.dec.add_edge(edge_for_adding)

    def remove_node(self, supernode: 'Supernode'):
        """
        Removes a supernode from the decontractible graph represented by this supernode.
            If the supernode has a key which is not in the graph, rise a KeyError.

        :param supernode: the supernode to be removed
        """
        self.dec.remove_node(supernode)

    def remove_edge(self, edge_for_removal: 'Superedge'):
        """
        Removes a superedge from the decontractible graph represented by this supernode.
            If the superedge has a tail and head the key of which are not in the graph as an edge,
            rise a KeyError.

        :param edge_for_removal: the superedge to be removed
        """
        self.dec.remove_edge(edge_for_removal)

    def height(self) -> int:
        """
        Returns the height of this supernode as the height of the decontractible graph represented by
        this supernode. This is equivalent to the height of the hierarchy tree of supernodes contracted into
        this supernode.
        If this node belongs to a multilevel graph, the height of the supernode is the level where the
        supernode is located in the multilevel graph.

        :return: the height of the decontractible graph
        """
        return self.dec.height() + 1

    def __eq__(self, other):
        if not isinstance(other, Supernode):
            return False
        return self.key == other.key

    def __hash__(self):
        return hash((self.key, self.level))

    def __str__(self):
        return "(Key: " + str(self.key) + ", " + \
                ("(Level: " + str(self.level) + "), " if self.level is not None else "") + \
                str(self.attr) + ")"

    def __getitem__(self, key: str) -> Any:
        return self.attr[key]

    def __setitem__(self, key: str, value: Any):
        self.attr[key] = value

    def __delitem__(self, key: str):
        del self.attr[key]

    def update(self, **attr):
        """
        Update the supernode attributes with the given attributes.

        :param attr: the attributes to be added to the supernode
        """
        self.attr.update(attr)


class Superedge:
    __slots__ = ('tail', 'head', 'level', 'dec', 'attr')

    def __init__(self, tail: 'Supernode', head: 'Supernode', level: int = None, dec: Set['Superedge'] = None, **attr):
        self.tail = tail
        self.head = head
        self.dec = dec if dec is not None else set()
        for e in self.dec:
            if e.tail not in self.tail.dec.nodes() or e.head not in self.head.dec.nodes():
                raise ValueError('The supernodes of the superedge to be added must be included in tail and head'
                                 'decontractions respectively.')
        if level is not None and (tail.level is None or head.level is None or tail.level != head.level or level != tail.level):
            raise ValueError('The level of the superedge must be the same as the level of the tail and head supernodes.')
        self.level = level
        self.attr = attr

    def is_in_multi_level_graph(self) -> bool:
        """
        Returns True if this superedge belongs to a multilevel graph, False otherwise.

        :return: True if this superedge belongs to a multilevel graph, False otherwise
        """
        return self.level is not None

    def add_edge(self, superedge: 'Superedge'):
        """
        Adds a superedge to the superedge set represented by this superedge.
        If the superedge has a tail and head the key of which are already in the set, it will not be added again.

        :param superedge: the superedge to be added
        """
        if superedge.tail not in self.tail.dec.nodes() or superedge.head not in self.head.dec.nodes():
            raise ValueError('The supernodes of the superedge to be added must be included in tail and head'
                             'decontractions respectively.')
        if self.level is not None and superedge.level != self.level - 1:
            raise ValueError('The level of the superedge to be added must be one less than the level of this superedge.')
        self.dec.add(superedge)

    def remove_edge(self, superedge: 'Superedge'):
        """
        Removes a superedge from the superedge set represented by this superedge.
        If the superedge is not in the set, rise a KeyError.

        :param superedge: the superedge to be removed
        """
        self.dec.remove(superedge)

    def height(self) -> int:
        """
        Returns the height of this superedge as the maximum height of the superedges represented by
        this superedge. This is equivalent to the height of the hierarchy tree of superedges contracted into
        this superedge.
        If this edge belongs to a multilevel graph, the height of the superedge is the level where the
        superedge is located in the multilevel graph, and coincides with the level of the tail and
        head supernode.
        The height of a superedge having an empty set of superedges is 0.

        :return: the height of this superedge
        """
        if not self.dec:
            return 0
        return max(e.height() for e in self.dec) + 1

    def __eq__(self, other):
        if not isinstance(other, Superedge):
            return False
        return self.tail == other.tail and self.head == other.head

    def __hash__(self):
        return hash((self.tail, self.head))

    def __str__(self):
        return str(self.tail) + ' -> ' + str(self.head)

    def __getitem__(self, key: str) -> Any:
        return self.attr[key]

    def __setitem__(self, key: str, value: Any):
        self.attr[key] = value

    def __delitem__(self, key: str):
        del self.attr[key]

    def update(self, **attr):
        """
        Update the superedge attributes with the given attributes.

        :param attr: the attributes to be added to the superedge
        """
        self.attr.update(attr)
