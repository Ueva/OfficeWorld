import random

import networkx as nx

from enum import Enum

from officeworld.utils import office_layout
from officeworld.generator.cell_type import CellType
from officeworld.generator.office_building import OfficeBuilding


class OfficeGenerator(object):
    def __init__(
        self,
        floor_width=50,
        floor_height=40,
        num_floors=1,
        hall_width=2,
        min_room_area=50,
        min_room_length=4,
        max_hall_rate=0.15,
        extra_door_prob=0.2,
        elevator_location=None,
        start_floor=-1,
        goal_floor=-1,
    ):
        """
        Initialises an Office generator.

        Args:
            floor_width (int, optional): The width of each office floor. Defaults to 50.
            floor_height (int, optional): The height of each office floor. Defaults to 40.
            num_floors (int, optional): How many floors the office should have. Defaults to 1.
            hall_width (int, optional): How wide each corridor should be. Defaults to 2.
            min_room_area (int, optional): The generator will not try to subdivide rooms with less area than this. Defaults to 50.
            min_room_length (int, optional): The generator will not try to subdivide rooms with an edge length less than this. Defaults to 4.
            max_hall_rate (float, optional): The proportion of a floor the generator will aim to cover in corridors. Defaults to 0.15.
            extra_door_prob (float, optional): How likely another door will be added to a room after one has already been placed. Defaults to 0.2.
            elevator_location (_type_, optional): The at which the elevator shaft will be placed. Defaults to None.
            start_floor (_type_, optional): Which floor the start room will be on. Defaults to None.
            goal_floor (_type_, optional): Which floor the goal room will be on. Defaults to None.
        """
        # Initialise Floor Parameters.
        self.floor_width = floor_width
        self.floor_height = floor_height
        self.num_floors = num_floors
        self.hall_width = hall_width
        self.total_floor_area = floor_width * floor_height

        # Initialise other Office Generation constraints.
        self.min_room_area = min_room_area
        self.max_hall_rate = max_hall_rate
        self.min_room_length = min_room_length
        self.extra_door_prob = extra_door_prob

        if elevator_location is None:
            self.elevator_location = None
        else:
            self.elevator_location = elevator_location

        # Initialise start and goal parameters.
        self.start_floor = start_floor
        self.goal_floor = goal_floor

        # Initialise Office.
        self.office_floors = [self._create_empty_office_floor() for _ in range(num_floors)]
        self.office_halls = [None] * num_floors
        self.office_rooms = [None] * num_floors

    def generate_office_building(self, verbose: bool = False) -> "OfficeBuilding":
        rej_elevator = 0
        rej_connected = 0

        for i in range(self.num_floors):
            while True:
                # Generate a new office floor.
                if self.elevator_location is None:
                    layout, halls, rooms = self.generate_office_floor(i == self.start_floor, i == self.goal_floor)
                    self.office_floors[i] = layout
                    self.office_halls[i] = halls
                    self.office_rooms[i] = rooms
                else:
                    y, x = self.elevator_location
                    while self.office_floors[i][y][x] != CellType.HALL:
                        layout, halls, rooms = self.generate_office_floor(i == self.start_floor, i == self.goal_floor)
                        self.office_floors[i] = layout
                        self.office_halls[i] = halls
                        self.office_rooms[i] = rooms

                        if self.office_floors[i][y][x] != CellType.HALL:
                            # print("Rejected: Cannot Place Elevator in Wall.")
                            rej_elevator += 1
                    self.office_floors[i][y][x] = CellType.ELEVATOR

                # Check that the new office floor is valid (i.e., that the state transition graph is connected).
                if nx.is_weakly_connected(self.generate_office_graph([self.office_floors[i]], layout=False)):
                    break
                else:
                    # print("Rejected: State-transition graph is not connected.")
                    rej_connected += 1

        if verbose:
            print(f"Successfully generated office building with {self.num_floors} floors!")
            print(
                f"Rejected {rej_elevator + rej_connected} floors.\n\tCouldn't place elevator {rej_elevator} times.\n\tOffice not connected {rej_connected} times."
            )

        return OfficeBuilding(
            self.office_floors,
            self.office_halls,
            self.office_rooms,
            self.start_floor,
            self.goal_floor,
            self.start_floor != -1,
            self.goal_floor != -1,
        )

    def generate_office_floor(self, contains_start: bool = False, contains_goal: bool = False):
        # Fill entire map with wall.
        office_floor = self._create_empty_office_floor()

        splittable_chunks = [(1, 1, self.floor_width - 2, self.floor_height - 2)]
        unsplittable_chunks = []
        halls = []
        rooms = []
        hall_rate = 0.0

        # Hallway Phase.
        # While there are still splittable chunks left, take the first one and split it.
        while len(splittable_chunks) > 0:
            splittable_chunks.sort(key=lambda x: x[2] * x[3], reverse=True)
            chunk = splittable_chunks.pop(0)
            office_floor = self._carve_area(chunk, CellType.WALL, office_floor)

            # If we don't yet have enough hallways, and the area is big enough, create a new
            # hallway along dividing the longest axis and add the chunks left on either side back to the queue.
            # print(hall_rate)
            if hall_rate < self.max_hall_rate:
                # If chunk is large enough to be split by a hall, split it.

                if (
                    max(chunk[2], chunk[3]) > 2 * (self.min_room_length + 1) + self.hall_width
                    and chunk[2] * chunk[3] > self.min_room_area
                ):
                    hall, chunks = self._create_hall(chunk)
                    halls.append(hall)
                    hall_rate += hall[2] * hall[3] / self.total_floor_area
                    splittable_chunks.extend(chunks)
                    office_floor = self._carve_area(hall, CellType.HALL, office_floor)

                    for _chunk in splittable_chunks:
                        office_floor = self._carve_area(_chunk, CellType.ROOM, office_floor)

                # Otherwise, place the chunk in the list of unsplittable chunks.
                else:
                    unsplittable_chunks.append(chunk)
                    office_floor = self._carve_area(chunk, CellType.ROOM, office_floor)
            else:
                unsplittable_chunks.append(chunk)
                office_floor = self._carve_area(chunk, CellType.ROOM, office_floor)
                break

        # Finish connecting all halls to each other.
        office_floor = self._connect_halls(office_floor)

        # Room Phase.
        splittable_chunks = splittable_chunks + unsplittable_chunks
        while len(splittable_chunks) > 0:
            splittable_chunks.sort(key=lambda x: x[2] * x[3], reverse=True)
            chunk = splittable_chunks.pop(0)
            office_floor = self._carve_area(chunk, CellType.WALL, office_floor)

            # Get valid directions for splitting this chunk.
            valid_split_directions = self._get_valid_split_directions(chunk)

            # If there is a valid direction to split the chunk, choose one at random, split it
            # and add the two resulting chunks to the queue.
            if len(valid_split_directions) > 0:
                chunks = self._create_rooms(chunk, random.choice(valid_split_directions))
                splittable_chunks.extend(chunks)

                for _chunk in splittable_chunks + rooms:
                    office_floor = self._carve_area(_chunk, CellType.ROOM, office_floor)

            # If there are no valid directions to split the chunk,
            # add it to the list of final rooms.
            else:
                rooms.append(chunk)
                office_floor = self._carve_area(chunk, CellType.ROOM, office_floor)

        # Doors Phase
        unconnected_rooms = rooms
        connected_rooms = []

        # Loop through every unconnected room.
        while len(unconnected_rooms) > 0:
            room = unconnected_rooms.pop(0)
            room_connected = False

            # Get the room's walls.
            left, top, width, height = room
            top_wall = [(x, top - 1) for x in range(left, left + width)]
            bottom_wall = [(x, top + height) for x in range(left, left + width)]
            left_wall = [(left - 1, y) for y in range(top, top + height)]
            right_wall = [(left + width, y) for y in range(top, top + height)]
            walls = top_wall + bottom_wall + left_wall + right_wall
            random.shuffle(walls)

            # Walk around the room's walls.
            # If it is next to a hallway, make a door leading to it.
            for wall in walls:
                x, y = wall

                # Check if there's a hallway above this room.
                if y - 1 >= 0 and office_floor[y - 1][x] == CellType.HALL and wall in top_wall:
                    office_floor[y][x] = CellType.ROOM
                    connected_rooms.append(room)
                    room_connected = True
                    break
                # Check if there's a hallway below this room.
                elif y + 1 < len(office_floor) and office_floor[y + 1][x] == CellType.HALL and wall in bottom_wall:
                    office_floor[y][x] = CellType.ROOM
                    connected_rooms.append(room)
                    room_connected = True
                    break
                # Check if there's a hallway to the left of this room.
                elif x - 1 >= 0 and office_floor[y][x - 1] == CellType.HALL and wall in left_wall:
                    office_floor[y][x] = CellType.ROOM
                    connected_rooms.append(room)
                    room_connected = True
                    break
                # Check if there's a hallway to the right of this room.
                elif x + 1 < len(office_floor[0]) and office_floor[y][x + 1] == CellType.HALL and wall in right_wall:
                    office_floor[y][x] = CellType.ROOM
                    connected_rooms.append(room)
                    room_connected = True
                    break

            if room_connected:
                continue

            # Walk around the room's walls.
            # If it is next to a connected room, make a door leading to it.
            for wall in walls:
                x, y = wall

                # Check if there's a connected room above this room.
                if y - 1 >= 0 and office_floor[y - 1][x] == CellType.ROOM and wall in top_wall:
                    neigh_room, _ = self._get_room_at_point(
                        x, y - 1, connected_rooms + unconnected_rooms, halls, office_floor
                    )
                    if neigh_room is not None and neigh_room in connected_rooms:
                        office_floor[y][x] = CellType.ROOM
                        connected_rooms.append(room)
                        room_connected = True
                        break
                # Check if there's a connected room below this room.
                elif y + 1 < len(office_floor) and office_floor[y + 1][x] == CellType.ROOM and wall in bottom_wall:
                    neigh_room, _ = self._get_room_at_point(
                        x, y + 1, connected_rooms + unconnected_rooms, halls, office_floor
                    )
                    if neigh_room is not None and neigh_room in connected_rooms:
                        office_floor[y][x] = CellType.ROOM
                        connected_rooms.append(room)
                        room_connected = True
                        break
                # Check if there's a connected room to the left of this room.
                elif x - 1 >= 0 and office_floor[y][x - 1] == CellType.ROOM and wall in left_wall:
                    neigh_room, _ = self._get_room_at_point(
                        x - 1, y, connected_rooms + unconnected_rooms, halls, office_floor
                    )
                    if neigh_room is not None and neigh_room in connected_rooms:
                        office_floor[y][x] = CellType.ROOM
                        connected_rooms.append(room)
                        room_connected = True
                        break
                # Check if there's a connected room to the right of this room.
                elif x + 1 < len(office_floor[0]) and office_floor[y][x + 1] == CellType.ROOM and wall in right_wall:
                    neigh_room, _ = self._get_room_at_point(
                        x + 1, y, connected_rooms + unconnected_rooms, halls, office_floor
                    )
                    if neigh_room is not None and neigh_room in connected_rooms:
                        office_floor[y][x] = CellType.ROOM
                        connected_rooms.append(room)
                        room_connected = True
                        break

            # Else, return the room to the list of unconnected rooms.
            if not room_connected:
                unconnected_rooms.append(room)

        # Choose random starting room.
        if contains_start:
            starting_room = random.choice(connected_rooms)
            self._carve_area(starting_room, CellType.START, office_floor)

        # Choose random goal room.
        if contains_goal:
            goal_room = random.choice(connected_rooms)
            self._carve_area(goal_room, CellType.GOAL, office_floor)

        return office_floor, halls, connected_rooms

    def _create_empty_office_floor(self):
        office = []
        for y in range(self.floor_height):
            office.append([])
            for x in range(self.floor_width):
                office[y].append(CellType.WALL)
        return office

    def _create_hall(self, chunk):
        left, top, width, height = chunk

        # Choose to split along the lonest axis.
        hall_dir = "V" if width > height else "H"

        # Choose a splitting point, ensuring the remaining chunks
        # are large enough to become rooms (or be split again).
        if hall_dir == "V":
            splitting_point = random.randint(
                self.min_room_length + 1, (width - 1) - self.min_room_length - self.hall_width - 1
            )
            hall = (left + splitting_point, top, self.hall_width, height)
            l_chunk = (left, top, splitting_point - 1, height)
            r_chunk = (
                left + splitting_point + self.hall_width + 1,
                top,
                width - splitting_point - self.hall_width - 1,
                height,
            )
            return hall, [l_chunk, r_chunk]

        elif hall_dir == "H":
            splitting_point = random.randint(
                self.min_room_length + 1, (height) - self.min_room_length - self.hall_width - 1
            )
            hall = (left, top + splitting_point, width, self.hall_width)
            u_chunk = (left, top, width, splitting_point - 1)
            d_chunk = (
                left,
                top + splitting_point + self.hall_width + 1,
                width,
                height - splitting_point - self.hall_width - 1,
            )
            return hall, [u_chunk, d_chunk]

    def _create_rooms(self, chunk, direction):
        left, top, width, height = chunk

        # Split Vertically.
        if direction == "V":
            splitting_point = random.randint(self.min_room_length - 1, (width - 1) - self.min_room_length - 1)
            l_chunk = (left, top, splitting_point, height)
            r_chunk = (left + splitting_point + 1, top, width - splitting_point - 1, height)
            return [l_chunk, r_chunk]

        # Split Horizontally.
        elif direction == "H":
            splitting_point = random.randint(self.min_room_length - 1, (height) - self.min_room_length - 1)
            u_chunk = (left, top, width, splitting_point)
            d_chunk = (left, top + splitting_point + 1, width, height - splitting_point - 1)
            return [u_chunk, d_chunk]

    def _carve_area(self, chunk, type, office_floor):
        left, top, width, height = chunk
        for y in range(top, top + height):
            for x in range(left, left + width):
                office_floor[y][x] = type
        return office_floor

    def _connect_halls(self, office_floor):
        for y in range(len(office_floor) - 2):
            for x in range(len(office_floor[0]) - 2):
                if office_floor[y][x - 1] == CellType.HALL and office_floor[y][x + 1] == CellType.HALL:
                    office_floor[y][x] = CellType.HALL
                elif office_floor[y - 1][x] == CellType.HALL and office_floor[y + 1][x] == CellType.HALL:
                    office_floor[y][x] = CellType.HALL
        return office_floor

    def _get_valid_split_directions(self, chunk):
        valid_split_directions = []
        if chunk[2] >= 2 * self.min_room_length + 1:
            valid_split_directions.append("V")

        if chunk[3] >= 2 * self.min_room_length + 1:
            valid_split_directions.append("H")

        return valid_split_directions

    def _is_point_in_room(self, x, y, room):
        left, top, width, height = room
        if (left <= x and x < left + width) and (top <= y and y < top + height):
            return True
        else:
            return False

    def _get_room_at_point(self, x, y, rooms, halls, office):
        if office[y][x] == CellType.WALL:
            return None, CellType.WALL
        else:
            for room in rooms:
                if self._is_point_in_room(x, y, room):
                    return room, CellType.ROOM
            for hall in halls:
                if self._is_point_in_room(x, y, hall):
                    return hall, CellType.HALL

        return None, office[y][x]

    def generate_office_graph(self, office=None, layout=True):
        if office is None:
            office_floors = self.office_floors
        else:
            if isinstance(office, OfficeBuilding):
                office_floors = office.layout
            else:
                office_floors = office

        valid_state_types = {CellType.ROOM, CellType.HALL, CellType.ELEVATOR, CellType.START, CellType.GOAL}

        stg = nx.DiGraph()

        num_floors = len(office_floors)
        floor_height = len(office_floors[0])
        floor_width = len(office_floors[0][0])

        for floor in range(num_floors):
            for y in range(floor_height):
                for x in range(floor_width):
                    if office_floors[floor][y][x] in valid_state_types - {CellType.GOAL}:
                        state = (floor, y, x)

                        # Add node if it doesn't exist.
                        if state not in stg.nodes():
                            stg.add_node(state)

                        # Add edges between this node and its neighbours.
                        if office_floors[floor][y + 1][x] in valid_state_types:
                            stg.add_edge(state, (floor, y + 1, x))
                        if office_floors[floor][y - 1][x] in valid_state_types:
                            stg.add_edge(state, (floor, y - 1, x))
                        if office_floors[floor][y][x + 1] in valid_state_types:
                            stg.add_edge(state, (floor, y, x + 1))
                        if office_floors[floor][y][x - 1] in valid_state_types:
                            stg.add_edge(state, (floor, y, x - 1))

                        # Add edges between elevators on different floors.
                        if office_floors[floor][y][x] == CellType.ELEVATOR:
                            if floor < num_floors - 1:  # Up elevator.
                                stg.add_edge(state, (floor + 1, y, x))
                            if floor > 0:  # Down elevator.
                                stg.add_edge(state, (floor - 1, y, x))

                        # Add self-loops to states next to walls.
                        if office_floors[floor][y + 1][x] == CellType.WALL:
                            stg.add_edge(state, state)
                        if office_floors[floor][y - 1][x] == CellType.WALL:
                            stg.add_edge(state, state)
                        if office_floors[floor][y][x + 1] == CellType.WALL:
                            stg.add_edge(state, state)
                        if office_floors[floor][y][x - 1] == CellType.WALL:
                            stg.add_edge(state, state)

        if layout:
            office_layout(stg, floor_height, floor_width)

        return stg
