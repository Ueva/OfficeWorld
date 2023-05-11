import json

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from officeworld.generator import CellType, OfficeGenerator
from officeworld.utils.serialisation import EnumEncoder, as_enum


# Initialise Office Generator.
num_floors = 1
office_gen = OfficeGenerator(num_floors=num_floors, elevator_location=(25, 20))

office_building = office_gen.generate_office_building()
with open("office.json", "w") as f:
    json.dump(office_building, f, cls=EnumEncoder)

with open("office.json", "r") as f:
    office = json.load(f, object_hook=as_enum)

image = np.zeros(shape=(office_gen.floor_height, office_gen.floor_width, 3))
for y in range(office_gen.floor_height):
    for x in range(office_gen.floor_width):
        if office_building[0][y][x] == CellType.WALL:
            image[y, x] = (0.0, 0.0, 0.0)
        elif office_building[0][y][x] == CellType.ELEVATOR:
            image[y, x] = (0.0, 0.0, 1.0)
        else:
            image[y, x] = (1.0, 1.0, 1.0)

plt.imshow(image, interpolation="nearest")
# plt.grid(which="both", axis="both", linewidth=1.2)
# plt.xticks(np.arange(-0.5, office_gen.floor_width, 1))
# plt.yticks(np.arange(-0.5, office_gen.floor_height, 1))
plt.grid(None)
plt.xticks([])
plt.yticks([])

plt.show()
