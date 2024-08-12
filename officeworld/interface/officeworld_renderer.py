import pygame

from typing import List

from officeworld.generator.cell_type import CellType

WIDTH = 640
HEIGHT = 360
SCALE_FACTOR = 0.9

COLOURS = {
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

ORANGE = (255, 165, 0)


class OfficeWorldRenderer(object):
    def __init__(self, layout: List[List[List["CellType"]]], num_floors: int, floor_height: int, floor_width: int):
        # Office dimension variables.
        self.layout = layout
        self.num_floors = num_floors
        self.floor_height = floor_height
        self.floor_width = floor_width

        # Display variables.
        self.block_size = min(WIDTH // floor_width, HEIGHT // floor_height)
        self.offset_y = HEIGHT // 2 - self.block_size * floor_height // 2
        self.offset_x = WIDTH // 2 - self.block_size * floor_width // 2

        # Initialise pygame and display window.
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font = pygame.font.SysFont("Courier New", 16)
        self.clock = pygame.time.Clock()

    def update(self, state):
        floor, y, x = state

        # Tick clock and process events.
        self.clock.tick(165)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()

        # Draw the agent's current floor.
        self.screen.fill(COLOURS[CellType.BACKGROUND])
        for y_ in range(self.floor_height):
            for x_ in range(self.floor_width):
                pygame.draw.rect(
                    self.screen,
                    COLOURS[self.layout[floor][y_][x_]],
                    (
                        self.offset_x + x_ * self.block_size,
                        self.offset_y + y_ * self.block_size,
                        self.block_size,
                        self.block_size,
                    ),
                )

        # Draw the agent's current position orange.
        pygame.draw.rect(
            self.screen,
            ORANGE,
            (
                self.offset_x + x * self.block_size,
                self.offset_y + y * self.block_size,
                self.block_size,
                self.block_size,
            ),
        )

        # Show FPS.
        self.screen.blit(
            self.font.render(
                f"{int(self.clock.get_fps())}fps   Floor {floor + 1} of {self.num_floors}", 1, pygame.Color("WHITE")
            ),
            (0, 0),
        )

        pygame.display.update()

    def close(self):
        pygame.quit()
