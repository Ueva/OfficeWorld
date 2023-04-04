import networkx as nx

from officeworld.generator import CellType

valid_state_types = {CellType.ROOM, CellType.HALL, CellType.ELEVATOR}


def generate_office_graph(office, layout=True):
    stg = nx.DiGraph()

    num_floors = len(office)
    floor_height = len(office[0])
    floor_width = len(office[0][0])

    print(num_floors)

    for floor in range(num_floors):
        for y in range(floor_height):
            for x in range(floor_width):
                if office[floor][y][x] in valid_state_types:
                    state = (floor, x, y)

                    # Add node if it doesn't exist.
                    if state not in stg.nodes():
                        stg.add_node(state)

                    # Add edges between this node and its neighbours.
                    if office[floor][y + 1][x] in valid_state_types:
                        stg.add_edge(state, (floor, x, y + 1))
                    if office[floor][y - 1][x] in valid_state_types:
                        stg.add_edge(state, (floor, x, y - 1))
                    if office[floor][y][x + 1] in valid_state_types:
                        stg.add_edge(state, (floor, x + 1, y))
                    if office[floor][y][x - 1] in valid_state_types:
                        stg.add_edge(state, (floor, x - 1, y))

                    # Add edges between elevators on different floors.
                    if office[floor][y][x] == CellType.ELEVATOR:
                        if floor < num_floors - 1:  # Up elevator.
                            stg.add_edge(state, (floor + 1, x, y))
                        if floor > 0:  # Down elevator.
                            stg.add_edge(state, (floor - 1, x, y))

                    # Add self-loops to states next to walls.
                    if office[floor][y + 1][x] == CellType.WALL:
                        stg.add_edge(state, state)
                    if office[floor][y - 1][x] == CellType.WALL:
                        stg.add_edge(state, state)
                    if office[floor][y][x + 1] == CellType.WALL:
                        stg.add_edge(state, state)
                    if office[floor][y][x - 1] == CellType.WALL:
                        stg.add_edge(state, state)

    if layout:
        _office_layout(stg, floor_height, floor_width)

    return stg


def _office_layout(stg, floor_height, floor_width, spacing=24.0):
    default_pos = {node: {"viz": {"position": {"x": 1.0, "y": 1.0, "z": 1.0}}} for node in stg.nodes}
    nx.set_node_attributes(stg, default_pos)

    for node, _ in stg.nodes(data=True):
        (floor, x, y) = node

        stg.nodes[node]["viz"]["position"]["x"] = x * spacing
        stg.nodes[node]["viz"]["position"]["y"] = -y * spacing - ((floor * floor_height) + 3) * spacing


if __name__ == "__main__":
    from officeworld.generator import OfficeGenerator

    office_gen = OfficeGenerator(num_floors=5, elevator_location=(7, 7))
    office_building = office_gen.generate_office_building()
    stg = generate_office_graph(office_building)

    nx.write_gexf(stg, "Office_STG.gexf")
