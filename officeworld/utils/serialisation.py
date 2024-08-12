import json

from enum import Enum

from officeworld.generator.cell_type import CellType
from officeworld.generator.office_building import OfficeBuilding

PUBLIC_ENUMS = {"CellType": CellType}


# Source: https://stackoverflow.com/questions/24481852/serialising-an-enum-member-to-json/24482806#24482806
class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) in PUBLIC_ENUMS.values():
            return {"__enum__": str(obj)}
        return json.JSONEncoder.default(self, obj)

    @staticmethod
    def decoder(obj):
        if "__enum__" in obj:
            name, member = obj["__enum__"].split(".")
            return getattr(PUBLIC_ENUMS[name], member)
        else:
            return obj


class OfficeBuildingJSONHandler:
    class Encoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, OfficeBuilding):
                return {
                    "__type__": "OfficeBuilding",
                    "layout": obj.layout,
                    "halls": obj.halls,
                    "rooms": obj.rooms,
                }
            elif isinstance(obj, Enum):
                return {"__enum__": str(obj)}
            else:
                return super().default(obj)

    @staticmethod
    def decoder(obj):
        if "__type__" in obj and obj["__type__"] == "OfficeBuilding":
            layout = obj["layout"]
            decoded_layout = [
                [
                    [
                        (
                            getattr(CellType, cell["__enum__"].split(".")[1])
                            if isinstance(cell, dict) and "__enum__" in cell
                            else cell
                        )
                        for cell in row
                    ]
                    for row in floor
                ]
                for floor in layout
            ]
            decoded_halls = [[tuple(hall) for hall in floor] for floor in obj["halls"]]
            decoded_rooms = [[tuple(room) for room in floor] for floor in obj["rooms"]]
            return OfficeBuilding(
                decoded_layout,
                decoded_halls,
                decoded_rooms,
            )
        elif "__enum__" in obj:
            name, member = obj["__enum__"].split(".")
            return getattr(PUBLIC_ENUMS[name], member)
        else:
            return obj

    @staticmethod
    def save_to_json(obj, file_path) -> "OfficeBuilding":
        with open(file_path, "w") as f:
            json.dump(obj, f, cls=OfficeBuildingJSONHandler.Encoder)

    @staticmethod
    def load_from_json(file_path) -> "OfficeBuilding":
        with open(file_path, "r") as f:
            return json.load(f, object_hook=OfficeBuildingJSONHandler.decoder)
