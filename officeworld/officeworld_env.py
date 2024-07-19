import random

import networkx as nx
import numpy as np
from simpleoptions import TransitionMatrixBaseEnvironment

from officeworld.generator import OfficeGenerator, CellType

# TODO: ADD SUPPORT FOR UPSTAIR AND DOWNSTAIR TILES.
# TODO: ADD SUPPORT FOR MUDDY TILES (LARGER PENALTY).
# TODO: ADD SUPPORT FOR CROWDED TILES (STOCHASTIC MOVEMENT).
# TODO: REWRITE SR FUNCTIONALITY BASED ON TRANSITIONMATRIXBASEENVIRONMENT.


class OfficeWorldEnvironment(TransitionMatrixBaseEnvironment):
    def __init__(self, office=None, officegen_kwargs=None):

        if officegen_kwargs is None and office is None:
            raise ValueError("You must provide either an existing office or the arguments to generate one.")

        if office is not None:
            self.office = office
        else:
            generator = OfficeGenerator(**officegen_kwargs)
            self.office = generator.generate_office_building()

        self.num_floors = len(self.office)
        self.floor_height = len(self.office[0])
        self.floor_width = len(self.office[0][0])

        self.stg = OfficeGenerator().generate_office_graph(self.office, layout=False)

        self.actions = [0, 1, 2, 3, 4, 5]  # North, South, East, West, Ascend, Descend
        self.num_actions = len(self.actions)
        self.state_space = set(self.stg.nodes)
        self.num_states = len(self.state_space)
        self.initial_states = self._initialise_initial_states()
        self.terminal_states = self._initialise_terminal_states()
        self.successor_representation = None
        self._cached_sr_gamma = None

        super().__init__(deterministic=True)

    def _initialise_initial_states(self):
        initial_states = []
        for i in range(self.num_floors):
            for y in range(self.floor_height):
                for x in range(self.floor_width):
                    if self.office[i][y][x] == CellType.START:
                        initial_states.append((i, x, y))

        return initial_states

    def _initialise_terminal_states(self):
        terminal_states = set()
        for i in range(self.num_floors):
            for y in range(self.floor_height):
                for x in range(self.floor_width):
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

    def step(self, action, state=None):
        if state is None:
            next_state, reward, terminal, info = super().step(action, state=self.current_state)
        else:
            next_state, reward, terminal, info = super().step(action, state=state)

        self.current_state = next_state

        return next_state, reward, terminal, info

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
        # is an elevator or not. Also, if there is only one floor, the agent cannot go up or down.
        floor, x, y = state
        if self.office[floor][y][x] == CellType.ELEVATOR and self.num_floors > 1:
            # If on ground floor, agent can only go up.
            if floor == 0:
                return [0, 1, 2, 3, 4]
            # If on top floor, agent can only go down.
            elif floor == len(self.office) - 1:
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
            floor_0, x_0, y_0 = state
        else:
            floor_0, x_0, y_0 = self.current_state

        if actions is None:
            actions = self.get_available_actions(state=(floor_0, x_0, y_0))

        successors = []
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

            if self.is_state_terminal((floor, x, y)):
                reward = 1.0 + -0.0001
            else:
                reward = -0.0001

            successors.append((((floor, x, y), reward), 1.0 / len(actions)))

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
        floor, x, y = state
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
        if directed:
            return self.stg
        else:
            return self.stg.to_undirected()
