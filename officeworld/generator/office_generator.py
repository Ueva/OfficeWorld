import random

from enum import Enum

CellType = Enum("CellType", ["WALL", "HALL", "ROOM", "UPSTAIR", "DOWNSTAIR", "BACKGROUND"])


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
    ):
        # Initialise Floor Parameters.
        self.floor_width = floor_width
        self.floor_height = floor_height
        self.num_floors = num_floors
        self.hall_width = hall_width
        self.total_floor_area = floor_width * floor_height

        # Initialise other OfficeGen constraints.
        self.min_room_area = min_room_area
        self.max_hall_rate = max_hall_rate
        self.min_room_length = min_room_length
        self.extra_door_prob = extra_door_prob

        # Initialise Office.
        self.office = [self._get_empty_office_floor() for _ in range(num_floors)]

    def generate_office_building(self):
        for i in range(len(self.office)):
            self.office[i] = self.generate_office_floor()

        return self.office

    def generate_office_floor(self):
        # Fill entire map with wall.
        office = []
        for y in range(self.floor_height):
            office.append([])
            for x in range(self.floor_width):
                office[y].append(CellType.WALL)

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
            office = self._carve_area(chunk, CellType.WALL, office)

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
                    office = self._carve_area(hall, CellType.HALL, office)

                    for _chunk in splittable_chunks:
                        office = self._carve_area(_chunk, CellType.ROOM, office)

                # Otherwise, place the chunk in the list of unsplittable chunks.
                else:
                    unsplittable_chunks.append(chunk)
                    office = self._carve_area(chunk, CellType.ROOM, office)
            else:
                unsplittable_chunks.append(chunk)
                office = self._carve_area(chunk, CellType.ROOM, office)
                break

        # Finish connecting all halls to each other.
        office = self._connect_halls(office)

        # Room Phase.
        splittable_chunks = splittable_chunks + unsplittable_chunks
        while len(splittable_chunks) > 0:
            splittable_chunks.sort(key=lambda x: x[2] * x[3], reverse=True)
            chunk = splittable_chunks.pop(0)
            office = self._carve_area(chunk, CellType.WALL, office)

            # Get valid directions for splitting this chunk.
            valid_split_directions = self._get_valid_split_directions(chunk)

            # If there is a valid direction to split the chunk, choose one at random, split it
            # and add the two resulting chunks to the queue.
            if len(valid_split_directions) > 0:
                chunks = self._create_rooms(chunk, random.choice(valid_split_directions))
                splittable_chunks.extend(chunks)

                for _chunk in splittable_chunks + rooms:
                    office = self._carve_area(_chunk, CellType.ROOM, office)

            # If there are no valid directions to split the chunk,
            # add it to the list of final rooms.
            else:
                rooms.append(chunk)
                office = self._carve_area(chunk, CellType.ROOM, office)

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
                if y - 1 >= 0 and office[y - 1][x] == CellType.HALL and wall in top_wall:
                    office[y][x] = CellType.ROOM
                    connected_rooms.append(room)
                    room_connected = True
                    break
                # Check if there's a hallway below this room.
                elif y + 1 < len(office) and office[y + 1][x] == CellType.HALL and wall in bottom_wall:
                    office[y][x] = CellType.ROOM
                    connected_rooms.append(room)
                    room_connected = True
                    break
                # Check if there's a hallway to the left of this room.
                elif x - 1 >= 0 and office[y][x - 1] == CellType.HALL and wall in left_wall:
                    office[y][x] = CellType.ROOM
                    connected_rooms.append(room)
                    room_connected = True
                    break
                elif x + 1 < len(office[0]) and office[y][x + 1] == CellType.HALL and wall in right_wall:
                    office[y][x] = CellType.ROOM
                    connected_rooms.append(room)
                    room_connected = True
                    break

            if room_connected:
                continue

            # Walk around the room's walls.
            # If it is next to a connected room, make a door leading to it.
            for wall in walls:
                x, y = wall

                # Check if there's a hallway above this room.
                if y - 1 >= 0 and office[y - 1][x] == CellType.ROOM and wall in top_wall:
                    neigh_room, _ = self._get_room_at_point(
                        x, y - 1, connected_rooms + unconnected_rooms, halls, office
                    )
                    if neigh_room in connected_rooms:
                        office[y][x] = CellType.ROOM
                        connected_rooms.append(room)
                        room_connected = True
                        break
                # Check if there's a hallway below this room.
                elif y + 1 < len(office) and office[y + 1][x] == CellType.ROOM and wall in bottom_wall:
                    neigh_room, _ = self._get_room_at_point(
                        x, y + 1, connected_rooms + unconnected_rooms, halls, office
                    )
                    if neigh_room in connected_rooms:
                        office[y][x] = CellType.ROOM
                        connected_rooms.append(room)
                        room_connected = True
                        break
                # Check if there's a hallway to the left of this room.
                elif x - 1 >= 0 and office[y][x - 1] == CellType.ROOM and wall in left_wall:
                    neigh_room, _ = self._get_room_at_point(
                        x - 1, y, connected_rooms + unconnected_rooms, halls, office
                    )
                    if neigh_room in connected_rooms:
                        office[y][x] = CellType.ROOM
                        connected_rooms.append(room)
                        room_connected = True
                        break
                elif x + 1 < len(office[0]) and office[y][x + 1] == CellType.ROOM and wall in right_wall:
                    neigh_room, _ = self._get_room_at_point(
                        x + 1, y, connected_rooms + unconnected_rooms, halls, office
                    )
                    if neigh_room in connected_rooms:
                        office[y][x] = CellType.ROOM
                        connected_rooms.append(room)
                        room_connected = True
                        break

            # Else, return the room to the list of unconnected rooms.
            if not room_connected:
                unconnected_rooms.append(room)

        return office

    def _get_empty_office_floor(self):
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

    def _carve_area(self, chunk, type, office):
        left, top, width, height = chunk
        for y in range(top, top + height):
            for x in range(left, left + width):
                office[y][x] = type
        return office

    def _connect_halls(self, office):
        for y in range(len(office) - 2):
            for x in range(len(office[0]) - 2):
                if office[y][x - 1] == CellType.HALL and office[y][x + 1] == CellType.HALL:
                    office[y][x] = CellType.HALL
                elif office[y - 1][x] == CellType.HALL and office[y + 1][x] == CellType.HALL:
                    office[y][x] = CellType.HALL
        return office

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
        raise ValueError(f"Point ({x},{y}) outside bounds of office of sized ({len(office[0])},{len(office)}).")
