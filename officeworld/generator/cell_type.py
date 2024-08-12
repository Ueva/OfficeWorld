from enum import Enum

CellType = Enum("CellType", ["WALL", "HALL", "ROOM", "UPSTAIR", "DOWNSTAIR", "ELEVATOR", "BACKGROUND", "START", "GOAL"])
