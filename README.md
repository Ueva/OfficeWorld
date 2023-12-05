# OfficeWorld

A highly-customisable, procedurally-generated office environment for reinforcement learning agents.

## What is an Office?

An office is a building composed of multiple floors. Each floor consists of rooms connected by a series of corridors. Each floor is connected to adjacent floors by a central elevator.

We designed this environment as a scalable alternative to the traditional "gridworlds" used in the reinforcement learning literature. By varying parameters such as the floor size and the number of floors, you can easily create environments with millions of states quite easily.

## Installation

This package is not currently available via PyPI. To install OfficeWorld locally, clone this repository and run `pip install .` in its root directory. Its dependencies will be installed automatically.

## Usage

There are two steps to using OfficeWorld:

1. Generate an Office layout using the `OfficeGenerator` class.

2. Pass your generated office layout to `OfficeWorldEnvironment`, and have your agent interact with it.

You can combine these steps by passing the `officegen_kwargs` expected by `OfficeGenerator` to `OfficeWorldEnvironment`'s constructor. There are many parameters you can vary to get offices of different sizes and layouts - informative docstrings are provided.

## Future Plans

What's here is quite simple, but it does what it was designed to do. Here are some ideas for future extensions:

- Generate obstacles (e.g, desks, boxes, people) within each room. This could be done dynamically, using something like the wave function collapse algorithm.
- Generate blockages, such as crowded areas, which the agent is penalised more harshly for moving through.
- Add stairs that span a few floors, but not all floors (unlike the elevator shaft). These might have a higher cost associated with them than taking the lift.
- Outdoor areas connecting multiple office buildings.
- General code optimisations, although it would probably be best to do a lot of this within `SimpleOptions` package, which this package depends on, instead.
