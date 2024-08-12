from typing import List, Tuple

from officeworld.generator.cell_type import CellType


class OfficeBuilding(object):
    def __init__(
        self,
        layout: List[List[List["CellType"]]],
        halls: List[List[Tuple[int, int, int, int]]],
        rooms: List[List[Tuple[int, int, int, int]]],
        start_floor: int = -1,
        goal_floor: int = -1,
        contains_start: bool = False,
        contains_goal: bool = False,
    ):
        """
        A data class representing an officeworld office building.

        Args:
            layout (List[List[List[&quot;CellType&quot;]]]): A nested list of cells representing the layout of the office. Has the structure layout[floor][row][col].
            halls (List[List[Tuple[int, int, int, int]]]): A nested list of tuples representing the hallways. Has the structure halls[floor] = [(left, top, width, height)]
            rooms (List[List[Tuple[int, int, int, int]]]): A nested list of tuples representing the rooms. Has the structure rooms[floor] = [(left, top, width, height)]
            start_floor (int, optional): Which floor the agent should start on (zero-based). Defaults to -1, in which case no start floor is set.
            goal_floor (int, optional): Which floor the goal should be on (zero-based). Defaults to -1, in which case no goal floor is set.
            contains_start (bool, optional): Whether the office contains any specified start cells. Defaults to False.
            contains_start (bool, optional): Whether the office contains any specified goal cells. Defaults to False.
        """
        self.layout = layout
        self.halls = halls
        self.rooms = rooms
        self.start_floor = start_floor
        self.goal_floor = goal_floor
        self.contains_start = contains_start
        self.contains_goal = contains_goal
