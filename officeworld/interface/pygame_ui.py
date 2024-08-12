import json
import pygame

from officeworld.generator.cell_type import CellType
from officeworld.generator.office_generator import OfficeGenerator
from officeworld.utils.serialisation import OfficeBuildingJSONHandler

Colors = {
    CellType.WALL: (50, 15, 15),
    CellType.HALL: (175, 175, 175),
    CellType.ROOM: (175, 125, 85),
    CellType.UPSTAIR: (0, 128, 0),
    CellType.DOWNSTAIR: (128, 0, 0),
    CellType.ELEVATOR: (0, 0, 128),
    CellType.BACKGROUND: (80, 60, 40),
    CellType.START: (0, 255, 0),
    CellType.GOAL: (255, 0, 0),
}

# Initialise Office Generator.
# office_gen = OfficeGenerator(num_floors=1, elevator_location=(25, 20), start_floor=1, goal_floor=2)
office_gen = OfficeGenerator(
    floor_width=50,
    floor_height=40,
    min_room_area=12,
    min_room_length=4,
    max_hall_rate=0.2,
    num_floors=1,
    elevator_location=(20, 25),
)
# office_gen = OfficeGenerator(start_floor=0, goal_floor=0)
# office = office_gen.generate_office_floor()

# Display Variables.
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 360
SCALE_FACTOR = 0.9
BLOCK_SIZE = int(
    min(
        SCALE_FACTOR * (SCREEN_WIDTH / office_gen.floor_width),
        SCALE_FACTOR * (SCREEN_HEIGHT / office_gen.floor_height),
    )
)
OFFSET_X = SCREEN_WIDTH / 2 - BLOCK_SIZE * office_gen.floor_width / 2
OFFSET_Y = SCREEN_HEIGHT / 2 - BLOCK_SIZE * office_gen.floor_height / 2

# Initialise pygame.
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Courier New", 16)


def regen_office():
    office = office_gen.generate_office_building()

    OfficeBuildingJSONHandler.save_to_json(office, "office.json")
    office = OfficeBuildingJSONHandler.load_from_json("office.json")

    print(office_gen.generate_office_graph(layout=False).number_of_nodes())

    return office


office = regen_office()
num_floors = len(office.layout)

floor = 0
running = True
while running:
    # Process Events.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                floor = min(floor + 1, num_floors - 1)
            elif event.key == pygame.K_DOWN:
                floor = max(floor - 1, 0)
            elif event.key == pygame.K_r:
                office = regen_office()
                num_floors = len(office.layout)
            elif event.key == pygame.K_HOME:
                floor = 0
            elif event.key == pygame.K_END:
                floor = num_floors - 1

    # Update Display.
    screen.fill(Colors[CellType.BACKGROUND])

    for y in range(office_gen.floor_height):
        for x in range(office_gen.floor_width):
            pygame.draw.rect(
                screen,
                Colors[office.layout[floor][y][x]],
                pygame.Rect(OFFSET_X + x * BLOCK_SIZE, OFFSET_Y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
            )

    # Show FPS.
    screen.blit(
        font.render(f"{int(clock.get_fps())}fps   Floor {floor + 1} of {num_floors}", 1, pygame.Color("WHITE")),
        (0, 0),
    )

    pygame.display.update()

    clock.tick(165)
