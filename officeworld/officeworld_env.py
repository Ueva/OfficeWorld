import random

import networkx as nx
import numpy as np

from typing import Dict

from simpleoptions import TransitionMatrixBaseEnvironment

from officeworld.generator.office_generator import OfficeGenerator
from officeworld.generator.office_building import OfficeBuilding
from officeworld.generator.cell_type import CellType
from officeworld.interface.officeworld_renderer import OfficeWorldRenderer
from officeworld.utils.graph_utils import office_layout

# TODO: ADD SUPPORT FOR UPSTAIR AND DOWNSTAIR TILES.
# TODO: ADD SUPPORT FOR MUDDY TILES (LARGER PENALTY).
# TODO: ADD SUPPORT FOR CROWDED TILES (STOCHASTIC MOVEMENT).
# TODO: REWRITE SR FUNCTIONALITY BASED ON TRANSITIONMATRIXBASEENVIRONMENT.


class OfficeWorldEnvironment(TransitionMatrixBaseEnvironment):
    def __init__(
        self,
        office: "OfficeBuilding" = None,
        officegen_kwargs: Dict = None,
        movement_penalty: float = -0.0001,
        goal_reward: float = 1.0,
        explorable: bool = False,
    ):
        """
        A gym-like environment for interacting with an OfficeWorld office building.

        Args:
            office (OfficeBuilding, optional): The office to base the environment on. Defaults to None, in which a new office is generated.
            officegen_kwargs (Dict, optional): Keword arguments to provide to OfficeGenerator, to generate a new office. Defaults to None, in which a provided office is used.
            movement_penalty (float, optional): The penalty for each action taken. Defaults to -0.001.
            goal_reward (float, optional): The reward for reaching the goal. Defaults to 1.0.
            explorable (bool, optional): Whether the environment should be explorable, in which case terminal states are ignored. Defaults to False.

        Raises:
            ValueError: Raised if both office and officegen_kwargs are None. You must either provide a pre-generated office, or tell this class how to generate one.
        """

        if officegen_kwargs is None and office is None:
            raise ValueError("You must provide either an existing office or the arguments to generate one.")

        if office is not None:
            self._office_gen = OfficeGenerator()
            self.office = office
        else:
            self._office_gen = OfficeGenerator(**officegen_kwargs)
            self.office = self._office_gen.generate_office_building()

        # Extract office building dimensions.
        self.num_floors = len(self.office.layout)
        self.floor_height = len(self.office.layout[0])
        self.floor_width = len(self.office.layout[0][0])

        # Define the action-space.
        self.actions = [0, 1, 2, 3, 4, 5]  # North, South, East, West, Ascend, Descend.
        self.num_actions = len(self.actions)

        # If the office doesn't contain a start, we need to choose one.
        if not self.office.contains_start:
            start_room = None
            while start_room is None:
                # If a start floor is specified, we can choose a random start room on that floor.
                if self.office.start_floor != -1:
                    start_floor = self.office.start_floor
                # Otherwise, we choose a random start floor.
                else:
                    start_floor = random.randint(0, self.num_floors - 1)

                # Pick a random room on the start floor and set it as the start.
                start_room = random.choice(self.office.rooms[start_floor])

                # Check that the room is empty (i.e., that its cells are "ROOM" cells). We only need to check the top-left cell.
                # We don't want to overwrite a room that has already been set as a goal.
                left, top, _, _ = start_room
                if self.office.layout[start_floor][top][left] != CellType.ROOM:
                    start_room = None

            self._office_gen._carve_area(start_room, CellType.START, self.office.layout[start_floor])

        # If the office doesn't contain a goal, we need to choose one.
        if not self.office.contains_goal and not explorable:
            goal_room = None
            while goal_room is None:
                # If a goal floor is specified, we can choose a random goal room on that floor.
                if self.office.goal_floor != -1:
                    goal_floor = self.office.goal_floor
                # Otherwise, we choose a random goal floor.
                else:
                    goal_floor = random.randint(0, self.num_floors - 1)

                # Pick a random room on the goal floor and set it as the goal.
                goal_room = random.choice(self.office.rooms[goal_floor])

                # Check that the room is empty (i.e., that its cells are "ROOM" cells). We only need to check the top-left cell.
                # We don't want to overwrite a room that has already been set as a start.
                left, top, _, _ = goal_room
                if self.office.layout[goal_floor][top][left] != CellType.ROOM:
                    goal_room = None

            self._office_gen._carve_area(goal_room, CellType.GOAL, self.office.layout[goal_floor])

        # Define rewards and penalties.
        self.movement_penalty = movement_penalty
        self.goal_reward = goal_reward

        # Define the state-transition graph and the state-space.
        self.explorable = explorable
        self.initial_states = self._initialise_initial_states()
        self.terminal_states = self._initialise_terminal_states()
        self.stg = self.generate_interaction_graph(directed=True)
        self.state_space = set(self.stg.nodes)
        self.num_states = len(self.state_space)

        # Successor representation variables.
        self.successor_representation = None
        self._cached_sr_gamma = None

        # Renderer variables.
        self.renderer = None

        super().__init__(deterministic=True)

    def _initialise_initial_states(self):
        initial_states = []
        for i in range(self.num_floors):
            for y in range(self.floor_height):
                for x in range(self.floor_width):
                    if self.office.layout[i][y][x] == CellType.START:
                        initial_states.append((i, y, x))

        return initial_states

    def _initialise_terminal_states(self):
        terminal_states = set()
        if not self.explorable:
            for i in range(self.num_floors):
                for y in range(self.floor_height):
                    for x in range(self.floor_width):
                        if self.office.layout[i][y][x] == CellType.GOAL:
                            terminal_states.add((i, y, x))

        return terminal_states

    def reset(self, state=None):
        if state is not None:
            current_state = state
        else:
            current_state = random.choice(self.initial_states)

        self.current_state = current_state

        return current_state

    def step(self, action, state=None):
        if state is None:
            next_state, reward, terminal, info = super().step(action, state=self.current_state)
        else:
            next_state, reward, terminal, info = super().step(action, state=state)

        self.current_state = next_state

        return next_state, reward, terminal, info

    def render(self, mode="human"):
        if self.renderer is None:
            self.renderer = OfficeWorldRenderer(
                self.office.layout, self.num_floors, self.floor_height, self.floor_width
            )

        self.renderer.update(self.current_state)

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None

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
        # is an elevator or not. Also, if there is only one floor, the agent cannot go up or down.
        floor, y, x = state
        if self.office.layout[floor][y][x] == CellType.ELEVATOR and self.num_floors > 1:
            # If on ground floor, agent can only go up.
            if floor == 0:
                return [0, 1, 2, 3, 4]
            # If on top floor, agent can only go down.
            elif floor == len(self.office.layout) - 1:
                return [0, 1, 2, 3, 5]
            # Else, the agent can go up and down.
            else:
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
            floor_0, y_0, x_0 = state
        else:
            floor_0, y_0, x_0 = self.current_state

        if actions is None:
            actions = self.get_available_actions(state=(floor_0, y_0, x_0))

        successors = []
        for action in actions:
            if action == 0:  # North.
                floor, y, x = floor_0, y_0 + 1, x_0
            elif action == 1:  # South.
                floor, y, x = floor_0, y_0 - 1, x_0
            elif action == 2:  # East.
                floor, y, x = floor_0, y_0, x_0 + 1
            elif action == 3:  # West.
                floor, y, x = floor_0, y_0, x_0 - 1
            elif action == 4:  # Up.
                floor, y, x = floor_0 + 1, y_0, x_0
            elif action == 5:  # Down.
                floor, y, x = floor_0 - 1, y_0, x_0

            if self.office.layout[floor][y][x] == CellType.WALL:
                floor, y, x = floor_0, y_0, x_0

            if self.is_state_terminal((floor, y, x)):
                reward = self.goal_reward + self.movement_penalty
            else:
                reward = self.movement_penalty

            successors.append((((floor, y, x), reward), 1.0 / len(actions)))

        return successors

    def get_successor_representation(self, gamma, state=None):
        if self.successor_representation is None or self._cached_sr_gamma != gamma:
            # TODO: Rewrite to use TransitionMatrixBaseEnvironment's transition matrix.
            # First, we build up the transition matrix (assuming a random policy).
            transition_matrix = self.build_transition_matrix()
            # Then, we use the Von Neumann expansion to compute the Successor Representation.
            sr = np.linalg.inv(np.identity(len(transition_matrix)) - gamma * transition_matrix)

            self.successor_representation = sr
            self._cached_sr_gamma = gamma

        if state is None:
            return self.successor_representation
        else:
            return self.successor_representation[state]

    def build_transition_matrix(self):
        transition_matrix = np.zeros((len(self.state_space), len(self.state_space)))
        self.mask = self.get_state_mask()
        for state in self.state_space:
            for a in self.get_available_actions(state):
                self.reset(state)
                next_state, _, _, _ = self.step(a)
                s = self.encode(state)
                next_state = self.encode(next_state)
                transition_matrix[self.mask.index(s)][self.mask.index(next_state)] += 1.0 / self.num_actions
        return transition_matrix

    def state_to_index(self, state):
        encoding = self.encode(state)
        return self.mask.index(encoding)

    def index_to_state(self, index):
        encoding = self.mask[index]
        return self.decode(encoding)

    def get_state_mask(self):
        atomic_states = [self.encode(s) for s in self.state_space]
        return sorted(atomic_states)

    def encode(self, state):
        floor, y, x = state
        # num_floors, width, height
        i = floor
        i *= self.floor_width
        i += x
        i *= self.floor_height
        i += y
        return i

    def decode(self, i):
        out = []
        out.append(i % self.floor_height)
        i = i // self.floor_height
        out.append(i % self.floor_width)
        i = i // self.floor_width
        out.append(i)
        return reversed(out)

    def generate_interaction_graph(self, directed=True):
        stg = super().generate_interaction_graph(directed=directed)
        office_layout(stg, self.floor_height, self.floor_width)
        return stg
