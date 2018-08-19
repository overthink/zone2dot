import sys
import json

from collections import namedtuple
from operator import attrgetter

Alias = namedtuple("Alias", ["name", "type_"])

class Record(object):
    """Represents a Route53 "record set", which I just call a record."""

    def __init__(self, data):
        self.data = data
        self.name = data.get("Name")
        self.type = data.get("Type")
        self.label = "{} ({})".format(self.name, self.type)

        self.alias = None
        alias_data = data.get("AliasTarget")
        if alias_data:
            self.alias = Alias(alias_data.get("DNSName"), self.type)

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

def dot_esc(str):
    """Escape str for use in DOT"""
    return str.replace('"', '\\"')

class Edge(object):
    """A directed edge."""
    def __init__(self, src_id, dst_id, label=None):
        self.src_id = src_id
        self.dst_id = dst_id
        self.label = label

    def dot(self, prefix=""):
        result = prefix + '"{}" -> "{}"'.format(
                dot_esc(self.src_id), 
                dot_esc(self.dst_id))
        if self.label is not None:
            result += ' [label="{}"]'.format(dot_esc(self.label))
        result += ";"
        return result

class Node(object):
    def __init__(self, id_, label):
        self.id = id_
        self.label = label
        self.edges = []

    def add_edge(self, dst_id, label):
        self.edges.append(Edge(self.id, dst_id, label))

    def dot(self, prefix=""):
        node_dot = prefix + '"{}"'.format(dot_esc(self.id))
        if self.label:
            node_dot += ' [label="{}"]'.format(dot_esc(self.label))
        result = [node_dot + ";"]
        # edges out from this node
        for edge in self.edges:
            result.append(edge.dot(prefix))
        return "\n".join(result)

class Graph(object):
    """More of a forest than a graph. Builds up a graph from the records given.
    Can output DOT."""

    def _get_or_create_node(self, name, type_):
        """Get or create a node with the given data."""
        node_id = ":".join([name, type_])
        node = self.node_by_id.get(node_id)
        if node is not None:
            return node
        node = Node(node_id, "{} ({})".format(name, type_))
        self.node_by_id[node_id] = node
        return node

    def _build_graph(self):
        for rec in self.records:
            if rec.type == "TXT": continue # skip TXT for now
            # Each record is an edge in the graph, so extract the src and dst
            # nodes, make an edge between them, and store it on the src node
            src = self._get_or_create_node(rec.name, rec.type)
            if rec.alias is not None:
                dst = self._get_or_create_node(rec.alias.name, rec.type)
                src.add_edge(dst.id, rec.routing_desc)
            else:
                for res in rec.resources:
                    dst = self._get_or_create_node(res, rec.type)
                    src.add_edge(dst.id, rec.routing_desc)

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
        result.append("  node [shape=rectangle];")
        result.append("  rankdir = LR;")
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

