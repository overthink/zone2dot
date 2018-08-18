import sys
import json

from collections import defaultdict
from collections import namedtuple
from operator import attrgetter

def dot_esc(str):
    """Escape str for use in DOT"""
    return str.replace('"', '\\"')

def dot_node(id_, label=None):
    """Return a string representing a node in DOT."""
    result = '"{}"'.format(dot_esc(id_))
    if label:
        result += ' [label="{}"]'.format(dot_esc(label))
    return result

def dot_edge(from_id, to_id, label=None):
    """Return a string representing a directed edge in DOT."""
    result = '"{}" -> "{}"'.format(dot_esc(from_id), dot_esc(to_id))
    if label is not None:
        result += ' label="{}"'.format(dot_esc(label))
    return result

class Alias(object):
    """Reprsents the alias data in a Route53 Record."""
    def __init__(self, name, type_):
        self.name = name
        self.type = type_

class Record(object):
    """Represents a Route53 "record set", which I just call a record."""

    def __init__(self, data):
        self.data = data
        self.name = data.get("Name")
        self.type = data.get("Type")
        self.label = "{} ({})".format(self.name, self.type)
        self.set_id = data.get("SetIdentifier", "")
        self.id = ":".join([self.name, self.type, self.set_id])

        self.alias = None
        alias_data = data.get("AliasTarget")
        if alias_data:
            self.alias = Alias( alias_data.get("DNSName"), self.type)

        self.resources = []
        for resource in data.get("ResourceRecords", []):
            self.resources.append(resource.get("Value"))

        self.routing_desc = None
        weight = data.get("Weight")
        region = data.get("Region")
        desc = [] # pretty sure it is invalid to have both weight and latency, but let's see
        if weight is not None:
            desc.append("w:{}".format(weight))
        if region is not None:
            desc.append("lat:{}".format(region))
        if desc:
            self.routing_desc = ", ".join(desc)

class Edge(object):
    """A directed edge."""
    def __init__(self, src_id, dst_id, label=None):
        self.src_id = src_id
        self.dst_id = dst_id
        self.label = label

    def dot(self, prefix=""):
        return prefix + dot_edge(self.src_id, self.dst_id, self.label)

class Node(object):
    def __init__(self, id_, label, routing_desc=None):
        """routing_desc describes how traffic is routed to this node, e.g. the
        weight or region or geo of this node. It ends up used as an edge label
        for directed edges ending at this node."""
        self.id = id_
        self.label = label
        self.routing_desc = routing_desc
        self.children = []
        self.edges = []

    def add_edge(self, dst_node, label):
        # TODO
        pass

    def dot(self, prefix=""):
        result = []
        result.append(prefix + dot_node(self.id, self.label))
        # edges out from this node
        for child in self.children:
            result.append(prefix + dot_edge(self.id, child.id, child.routing_desc))
        return "\n".join(result)

class Graph(object):
    """More of a forest than a graph. Builds up a graph from the records given.
    Can output DOT."""

    def _get_or_create_node(self, name, type_, routing_desc=None):
        """Get or create a node with the given data."""
        node_id = ":".join([name, type_])
        node = self.node_by_id.get(node_id)
        if node is not None:
            node.routing_desc = routing_desc
            return node
        node = Node(node_id, "{} ({})".format(name, type_), routing_desc)
        self.node_by_id[node_id] = node
        return node

    def _build_graph(self):
        for rec in self.records:
            # Each record is an edge in the graph, so extract the src and dst
            # nodes, make an edge between them, and store it on the src node
            src = self._get_or_create_node(rec.name, rec.type)
            if rec.alias:
                dst = self._get_or_create_node(rec.alias.name, rec.type, rec.routing_desc)
                src.children.append(dst)
            else:
                for res in rec.resources:
                    src.children.append(Node(res, res))

    def __init__(self, records):
        """records is a list of ResourceRecordSets form the aws route53 api
        parsed into python dicts."""
        self.records = records
        self.node_by_id = {}
        self._build_graph()

    def dot(self):
        """Return graph as a big string in DOT syntax."""
        result = []
        result.append("digraph {")
        result.append("  node [shape=rectangle]")
        for node in sorted(self.node_by_id.values(), key=attrgetter('id')):
            result.append(node.dot(prefix="  "))
        result.append("}")
        return "\n".join(result)

def load_records(filename):
    """Returns a list of Record objects parsed from filename."""
    with open(filename) as f:
        records = json.load(f).get("ResourceRecordSets")
    return [Record(r) for r in records]

def main():
    if len(sys.argv) < 2:
        print "Usage: {}: <zonefile>".format(sys.argv[0])
        sys.exit(1)

    records = load_records(sys.argv[1])
    g = Graph(records)
    print g.dot()

if __name__ == "__main__":
    main()

