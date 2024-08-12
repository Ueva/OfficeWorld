from typing import List, Tuple

from officeworld.generator.cell_type import CellType


class OfficeBuilding(object):
    def __init__(
        self,
        layout: List[List[List["CellType"]]],
        halls: List[List[Tuple[int, int, int, int]]],
        rooms: List[List[Tuple[int, int, int, int]]],
    ):
        """
        A data class representing an officeworld office building.

        Args:
            layout (List[List[List[&quot;CellType&quot;]]]): A nested list of cells representing the layout of the office. Has the structure layout[floor][row][col].
            halls (List[List[Tuple[int, int, int, int]]]): A nested list of tuples representing the hallways. Has the structure halls[floor] = [(left, top, width, height)]
            rooms (List[List[Tuple[int, int, int, int]]]): A nested list of tuples representing the rooms. Has the structure rooms[floor] = [(left, top, width, height)]
        """
        self.layout = layout
        self.halls = halls
        self.rooms = rooms
