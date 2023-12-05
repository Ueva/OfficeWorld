import networkx as nx

from office_generator import CellType

if __name__ == "__main__":
    from officeworld.generator import OfficeGenerator

    office_gen = OfficeGenerator(num_floors=500, elevator_location=(7, 7))
    office_building = office_gen.generate_office_building()
    stg = office_gen.generate_office_graph(office_building)
    nx.write_gexf(stg, "Office_STG.gexf")
