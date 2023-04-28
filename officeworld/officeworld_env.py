import random

import networkx as nx

from simpleoptions import BaseEnvironment

from officeworld.generator import OfficeGenerator, CellType


class OfficeWorldEnvironment(BaseEnvironment):
    def __init__(self, office=None, officegen_kwargs=None):
        super().__init__()

        if office is not None:
            self.office = office
        else:
            generator = OfficeGenerator(**officegen_kwargs)
            self.office = generator.generate_office_building()

        self.stg = OfficeGenerator().generate_office_graph(self.office, layout=False)

        self.state_space = set(self.stg.nodes)
        self.initial_states = self._initialise_initial_states()
        self.terminal_states = self._initialise_terminal_states()

    def _initialise_initial_states(self):
        initial_states = []

        num_floors = len(self.office)
        floor_height = len(self.office[0])
        floor_width = len(self.office[0][0])

        for i in range(num_floors):
            for y in range(floor_height):
                for x in range(floor_width):
                    if self.office[i][y][x] == CellType.START:
                        initial_states.append((i, x, y))

        return initial_states

    def _initialise_terminal_states(self):
        terminal_states = set()

        num_floors = len(self.office)
        floor_height = len(self.office[0])
        floor_width = len(self.office[0][0])

        for i in range(num_floors):
            for y in range(floor_height):
                for x in range(floor_width):
                    if self.office[i][y][x] == CellType.GOAL:
                        terminal_states.add((i, x, y))

        return terminal_states

    def reset(self, state=None):
        if state is not None:
            current_state = state
        else:
            current_state = random.choice(self.initial_states)

        self.current_state = current_state

        return current_state

    def step(self, action):
        floor, x, y = self.current_state

        # Go North.
        if action == 0:
            y += 1
        # Go South.
        elif action == 1:
            y -= 1
        # Go East:
        elif action == 2:
            x += 1
        # Go West.
        elif action == 3:
            x -= 1
        # Go Up.
        elif action == 4:
            floor += 1
        # Go Down.
        elif action == 5:
            floor -= 1

        # Keep the agent in the same state if they have moved into a wall.
        if self.office[floor][y][x] == CellType.WALL:
            floor, x, y = self.current_state

        # Compute reward: -0.0001 per decision stage, +1.0 for reaching the goal.
        terminal = False
        reward = -0.0001
        if self.office[floor][y][x] == CellType.GOAL:
            terminal = True
            reward += 1.0

        return (floor, x, y), reward, terminal, {}

    def render(self, mode="human"):
        pass

    def close(self):
        pass

    def get_state_space(self):
        return self.state_space

    def get_action_space(self):
        return {0, 1, 2, 3, 4, 5}

    def get_available_actions(self, state=None):
        if state is None:
            state = self.current_state

        # If the state is terminal, no actions are available.
        if self.is_state_terminal(state):
            return []

        # Otherwise, the available actions depend on whether the state
        # is an elevator or not.
        # TODO: ADD SUPPORT FOR UPSTAIR AND DOWNSTAIR TILES WHEN THEY ARE ADDED.
        floor, x, y = state
        if self.office[floor][y][x] == CellType.ELEVATOR:
            return [0, 1, 2, 3, 4, 5]
        else:
            return [0, 1, 2, 3]

    def is_state_terminal(self, state=None):
        if state is None:
            state = self.current_state

        return state in self.terminal_states

    def get_initial_states(self):
        return self.initial_states

    def get_successors(self, state=None, actions=None):
        if state is not None:
            floor_0, x_0, y_0 = state
        else:
            floor_0, x_0, y_0 = self.current_state

        successors = set()
        for action in actions:
            if action == 0:  # North.
                floor, x, y = floor_0, x_0, y_0 + 1
            elif action == 1:  # South.
                floor, x, y = floor_0, x_0, y_0 - 1
            elif action == 2:  # East.
                floor, x, y = floor_0, x_0 + 1, y_0
            elif action == 3:  # West.
                floor, x, y = floor_0, x_0 - 1, y_0
            elif action == 4:  # Up.
                floor, x, y = floor_0 + 1, x_0, y_0
            elif action == 5:  # Down.
                floor, x, y = floor_0 - 1, x_0, y_0

            if self.office[floor][y][x] == CellType.WALL:
                floor, x, y = floor_0, x_0, y_0

            successors.add((floor, x, y))

        return list(successors)

    def get_successor_representation(self, gamma, state=None):
        pass

    def generate_interaction_graph(self, directed=True):
        if directed:
            return self.stg
        else:
            return self.stg.to_undirected()
