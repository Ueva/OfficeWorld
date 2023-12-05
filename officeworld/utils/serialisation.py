import json

from officeworld.generator import CellType

PUBLIC_ENUMS = {"CellType": CellType}


# Source: https://stackoverflow.com/questions/24481852/serialising-an-enum-member-to-json/24482806#24482806
class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) in PUBLIC_ENUMS.values():
            return {"__enum__": str(obj)}
        return json.JSONEncoder.default(self, obj)


def as_enum(d):
    if "__enum__" in d:
        name, member = d["__enum__"].split(".")
        return getattr(PUBLIC_ENUMS[name], member)
    else:
        return d
