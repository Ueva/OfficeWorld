import pygame

from officeworld.generator import CellType, OfficeGenerator

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
# office_gen = OfficeGenerator(elevator_location=(7, 7))
office_gen = OfficeGenerator(start_floor=0, goal_floor=0)
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

running = True
while running:
    # Process Events.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit()

    office = office_gen.generate_office_building()[0]

    # Update Display.
    screen.fill(Colors[CellType.BACKGROUND])

    for y in range(office_gen.floor_height):
        for x in range(office_gen.floor_width):
            pygame.draw.rect(
                screen,
                Colors[office[y][x]],
                pygame.Rect(OFFSET_X + x * BLOCK_SIZE, OFFSET_Y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
            )

    # Show FPS.
    screen.blit(font.render(str(int(clock.get_fps())), 1, pygame.Color("WHITE")), (0, 0))

    pygame.display.flip()

    clock.tick()
    pygame.time.delay(200)
