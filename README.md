# isg11_project1_ludo

## Installation
Have Python installed and run `pip install requirements -r`.

## Main game
The main file contains the game data structure, strategies and simulation loop.
To start the simulation enter the amount of games to be simulated at the bottom of the file (current default at 1000) and launch `main.py`.
To start a single game with visualization in the console, set `ENABLE_CONSOLE` to true and start `main.py`, afterwards every ENTER press will perform one action.

## Agent strategies
The gameplay strategies to be used by the agents can be chosen within the `LudoGame` class under `self.players`.

## Plot graphs
After running the evaluation, the results will be saved in a JSON file.
To plot these results launch `simulation_plot_lib.py`, multiple graphs will be shown one after another.

## Note
In the visualization the board is displayed in a flattened manner, it basically represents the real game board in a simple way.