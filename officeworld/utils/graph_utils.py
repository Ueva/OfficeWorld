import networkx as nx


# Takes an office graph as input, returns a nicely laid-out version of it (using graph viz position attributes).
def office_layout(stg, floor_height, floor_width, spacing=24.0):
    default_pos = {node: {"viz": {"position": {"x": 1.0, "y": 1.0, "z": 1.0}}} for node in stg.nodes}
    nx.set_node_attributes(stg, default_pos)

    for node, _ in stg.nodes(data=True):
        (floor, x, y) = node

        stg.nodes[node]["viz"]["position"]["x"] = x * spacing
        stg.nodes[node]["viz"]["position"]["y"] = -y * spacing - ((floor * floor_height) + 3) * spacing
