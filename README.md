# Port Security Simulation

## Overview

This project simulates a port security scenario using the Mesa agent-based modeling framework and Pygame for visualization. It models the behavior of ships navigating a port environment, including inspections by security agents and handling suspicious vessels.

## Features

- Ships can dock, move to finish positions, or be inspected by security agents.
- Suspicious ships undergo inspections before being allowed to dock.
- Barriers restrict ship movements, guiding them through entry points.
- Visualization using Pygame with icons for ships, docks and security agents.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/niklasrosseck/ABM.git
```

2. Install dependencies:

```bash
pip install mesa pygame
```

3. Ensure the following image files are in the `Images/` directory:
   - `ship.png`: Ship icon
   - `security.png`: Security icon
   - `Dock.png`: Dock icon

## Usage

Run the simulation using the following command:

```bash
python security.py
```

The simulation window will open, showing the port environment. Ships will attempt to dock, undergo inspections, and move to finish positions.

## Code Structure

- `Ship`: Represents a ship agent that can move, dock, and be inspected.
- `PortSecurityModel`: Manages the environment, ship creation, and behavior.
- `run_pygame`: Handles the Pygame visualization loop.

## Controls

- Close the simulation window to end the simulation.

## Future Improvements

- Add more dynamic behaviors for ships.
- Implement threat assessment based on inspection outcomes.
- Integrate dynamic barriers and patrolling security agents.

## License

This project is open-source and available under the MIT License.
