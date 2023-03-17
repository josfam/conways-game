from collections import deque, namedtuple, Counter
from copy import copy, deepcopy
from rich import print as rprint
from rich.table import Table, box
from typing import Generator, List, Union, Dict
import argparse
import default_grids
import os
import random
import sys
import time

Point = namedtuple('Point', ['x', 'y'])
Symbols = namedtuple('Symbols', ['dead', 'alive'])
CellColours = namedtuple('CellColours', ['dead', 'alive'])

ALIVE = '*'
DEAD = '-'
COLOURS = CellColours('grey39', 'grey100')  # default colors for dead and alive cells
GRID_SIZE = 20
GRIDS = default_grids.cells
ITERATION_HISTORY_SIZE = 15  # how many previous iterations are remembered
MAX_ITERATIONS = 2000
MAX_COPIES_IN_HISTORY = 4  # the game ends if an iteration has occured `MAX_COPIES_IN_HISTORY` times in history
PAUSE_DURATION = 0.2

SYMBOLS = Symbols('-', '\u25a0')  # represents ('-', '■')

ALT_COLOURS = {
    'black-white': CellColours('black', 'bright_white'),
    'white-black': CellColours('bright_white', 'black'),
    'grey-green': CellColours('grey27', 'green4'),
    'grey-orange': CellColours('grey23', 'dark_orange'),
}


class Grid:
    """Represents a grid that is populated by dead and alive cells"""

    def __init__(self, cell_pattern: Union[str, None] = None) -> None:
        self._cells = self.cells_to_grid(cell_pattern)
        self._cols: int = len(self._cells[0])
        self._rows: int = len(self._cells)

    @property
    def rows(self) -> int:
        """Returns the number of rows in the grid"""
        return self._rows

    @property
    def cols(self) -> int:
        """Returns the number of columns in the grid"""
        return self._cols

    @property
    def cells(self):
        """Returns the structure representing all the cells in the grid"""
        return self._cells

    def cells_to_grid(self, cell_pattern: Union[str, None]) -> List[List[str]]:
        """Returns a grid, extracted from the inputted string representation. If no string representation
        is provided, a grid of randomly placed dead and alive cells is returned
        """
        if cell_pattern:
            cell_pattern = cell_pattern.replace(' ', '')  # remove any empty spaces
            raw_cells = list(list(line) for line in cell_pattern.splitlines())
            compact_cells = list(filter(lambda x: not x == [], raw_cells))  # remove any empty lists
            return self.pad_cells(compact_cells)
        else:
            return self.random_arrangement()

    def random_arrangement(self) -> List[List[str]]:
        """Returns a random arrangement of dead and alive cells"""
        cells = []
        for _ in range(GRID_SIZE):
            cells.append(random.choices(['-', '*'], k=GRID_SIZE))

        return cells

    def pad_cells(self, cells: List[List[str]]) -> List[List[str]]:
        """Returns a padded version of the cells provided, where each row of cells is the same length as the
        longest row. Shorter rows are padded with dead cells.
        """
        cells = copy(cells)
        longest_row = len(max(cells, key=len))

        for row in cells:
            if not len(row) == longest_row:
                row.extend('-' * (longest_row - len(row)))

        return cells


class ConwaysGameOfLife:
    """Represents a game of Conway's game of life based on the following rules:
    - Living cells with 2 or 3 neighbours stay ALIVE in the next step of the simulation
    - Dead cells with exactly 3 neighbours become ALIVE in the next ste of the simulation
    - Any other cell dies or stays dead in the next step of the simulation
    """

    def __init__(self, cells: Grid) -> None:
        self._grid = cells
        self._iteration_history: deque = deque(maxlen=ITERATION_HISTORY_SIZE)
        self._total_iterations = 0
        self._repeated_pattern_halted_the_game = False

    @property
    def grid(self):
        """Returns the cell grid"""
        return self._grid

    @property
    def iteration_history(self):
        """Returns the most recent iterations"""
        return self._iteration_history

    @property
    def total_iterations(self):
        """Returns how many iterations of the original generations were made before the game stopped"""
        return self._total_iterations

    @property
    def repeated_pattern_halted_the_game(self):
        """Returns True if the game was halted because there was a repeated pattern. Returns False otherwise"""
        return self._repeated_pattern_halted_the_game

    def count_neighbours(self, grid: List[List[str]], location: Point) -> int:
        """Returns how many living neighbours surround the given location in the grid"""
        grid = copy(grid)
        alive_neighbours = 0
        here = location

        # top, right, bottom, left, top-left, top-right, bottom-right, and bottom-left points
        neighbours = [
            Point(here.x, here.y - 1),
            Point(here.x + 1, here.y),
            Point(here.x, here.y + 1),
            Point(here.x - 1, here.y),
            Point(here.x - 1, here.y - 1),
            Point(here.x + 1, here.y - 1),
            Point(here.x + 1, here.y + 1),
            Point(here.x - 1, here.y + 1),
        ]

        for neighbour in neighbours:
            if self.valid_loc(grid, neighbour) and grid[neighbour.y][neighbour.x] == ALIVE:
                alive_neighbours += 1

        return alive_neighbours

    def valid_loc(self, grid: List[List[str]], location: Point) -> bool:
        """Returns True if the given location exists within the grid.
        Returns False otherwise
        """
        if not 0 <= location.x < len(grid[0]):
            return False
        if not 0 <= location.y < len(grid):
            return False
        return True

    def get_next_iteration(self, grid: List[List[str]]):
        """Returns the next iteration of the provided grid, using the rules of Conway's game of life"""
        prev_iter = copy(grid)
        next_iter = deepcopy(prev_iter)

        for y in range(self.grid.rows):
            for x in range(self.grid.cols):
                living_neighbours = self.count_neighbours(prev_iter, Point(x, y))

                if prev_iter[y][x] == ALIVE and living_neighbours in [2, 3]:
                    next_iter[y][x] = ALIVE
                elif prev_iter[y][x] == DEAD and living_neighbours == 3:
                    next_iter[y][x] = ALIVE
                else:
                    next_iter[y][x] = DEAD

        return next_iter

    def run_conways_game(self, iterations: int = MAX_ITERATIONS) -> Generator[List[List[str]], None, None]:
        """Runs Conway's game of life, `iteration` times.

        If `iterations` is not provided, the game will run for a maximum of `MAX_ITERATIONS` iterations
        (unless a repeating pattern is detected, in which case the game will automatically stop).
        """
        current_gen = self.grid.cells
        
        # keep the original generation in history to take into account patterns that do not evolve
        self.iteration_history.append(current_gen)

        yield current_gen  # the first generation will be shown, but does not count as an iteration

        for _ in range(iterations):
            next_iteration = self.get_next_iteration(current_gen)

            current_gen = next_iteration

            if self.iteration_history.count(next_iteration) == MAX_COPIES_IN_HISTORY:
                self._repeated_pattern_halted_the_game = True
                break
            else:
                self._total_iterations += 1
                yield next_iteration
                

            self._iteration_history.append(next_iteration)


def show_cells(
    symbols: Symbols = SYMBOLS, colours: CellColours = COLOURS, grid: List[List[str]] = [], mode=None
) -> Union[Table, str]:
    """Returns the provided grid with the dead and alive cells coloured with the provided `colours`, and replaced
    with the provided(alternative) `symbols`.

    A `rich` Table is returned by default, unless a `mode` is provided (in which case a string is returned)
    """
    rows = []
    for index, _ in enumerate(grid):
        if not index == len(grid) - 1:
            rows.append(color_cell_row(symbols, colours, grid[index]))
        else:
            rows.append(color_cell_row(symbols, colours, grid[index]).strip())  # no newline after the last row
    if not mode:  # return a table by default
        table = Table(show_header=False, show_lines=False, box=box.ROUNDED)
        table.add_column
        table.add_row(''.join(rows))
        return table
    else:
        return ''.join(rows)


def color_cell_row(symbols: Symbols, colours: CellColours = COLOURS, cell_row: List[str] = []) -> str:
    """Returns a string in which the alive and dead cells in the provided cell row are colored, and replaced with
    alternative symbols
    """
    alive_coloring = f'[{colours.alive}]{symbols.alive}[/{colours.alive}]'
    dead_coloring = f'[{colours.dead}]{symbols.dead}[/{colours.dead}]'
    colored_row = tuple(map(lambda x: alive_coloring if x == '*' else dead_coloring, cell_row))
    return ''.join(colored_row) + '\n'


def get_cells_from_file(file: str) -> str:
    """Returns a string representing a grid of cells which is a result of parsing the provided file"""
    if os.path.exists(file):
        if not file.rpartition('.')[-1] == 'txt':
            sys.exit('Please provide a .txt file')
        lines: list = []
        with open(file, 'r', encoding='utf-8') as f:
            chars_seen = []
            while True:
                char = f.read(1)
                if not char:
                    break
                elif char == '\n':  # prepare for the next line if any
                    chars_seen.append(char)
                    lines.append(''.join(chars_seen))
                    chars_seen.clear()
                elif char in ['*', '-']:
                    chars_seen.append(char)
                elif char.isspace():  # white space will be filled with dead cells
                    chars_seen.append('-')
                else:
                    print(f"The invalid character '{char}' was found in your text file.")
                    sys.exit("Remove it, making sure you are left with only '*'s and '-'s")

            cells = ''.join(lines)
        return cells
    else:
        print(f'The file {file} does not exist.\nHere is a random preset grid:')
        cells = GRIDS[random.choice(list(GRIDS.keys()))]
        return cells

def clear_previous_generation(height: int) -> None:
    """Clears the previous `height` lines from the terminal window"""
    sys.stdout.write(f'\033[{height}A\033[K')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-b',
        '--basic',
        action='store_true',
        help='Prints the grid as basic text, and not the pretty table (which is the default)',
    )
    parser.add_argument('-p', '--pause', type=float, help='Pause duration between iterations. 0.5 is half a second')
    parser.add_argument('-i', '--iterations', type=int, help='The number of iterations of the game to run')
    parser.add_argument(
        '-s',
        '--symbols',
        type=str,
        nargs=2,
        help="Two symbols (each in single or double quotes) to use for dead and alive cells respectively.\n"
        "The defaults are '-' '■'. Include the quotes as well.",
    )
    parser.add_argument(
        '-p',
        '--preset',
        type=str,
        choices=list(GRIDS.keys()),
        help='One of the pre-defined grids from the collection',
    )
    parser.add_argument(
        '-c',
        '--colour',
        type=str,
        choices=list(ALT_COLOURS.keys()),
        help='Color combinations for dead and alive colours',
    )
    parser.add_argument('-f', '--filename', type=str, help='Path to the text file containing a predefined grid.')
    args = parser.parse_args()

    pause_time = args.pause if args.pause else PAUSE_DURATION
    iterations = args.iterations if args.iterations else MAX_ITERATIONS
    symbols = Symbols(*args.symbols) if args.symbols else SYMBOLS
    grid_source: Union[str, Dict[str, str]] = args.filename if args.filename else GRIDS
    mode = args.basic if args.basic else None
    preset_to_show = args.preset if args.preset else None
    cell_colours = args.colour if args.colour else COLOURS

    print()  # prevent script command from being cleared from the terminal

    if not isinstance(cell_colours, CellColours):
        cell_colours = ALT_COLOURS[cell_colours]
    if preset_to_show:
        cells = GRIDS[preset_to_show]
    else:
        if isinstance(grid_source, str):
            cells = get_cells_from_file(grid_source)
        else:
            grid_name = random.choice(list(GRIDS.keys()))
            print(f'Here is the {grid_name}:')
            cells = GRIDS[grid_name]

    grid = Grid(cells)
    game = ConwaysGameOfLife(grid)

    # 1 extra line for the iteration counter, 2 extra lines for the rich grid itself
    lines_to_clear = grid.rows + 1 if mode else grid._rows + 3

    last_iteration: List[List[str]] = []

    try:
        for iteration in game.run_conways_game(iterations=iterations):
            last_iteration = iteration  # keep for the final output
            rprint(show_cells(grid=iteration, symbols=symbols, mode=mode, colours=cell_colours))
            rprint(f"iteration: {game.total_iterations}")
            time.sleep(pause_time)
            clear_previous_generation(lines_to_clear)
    except KeyboardInterrupt:
        print(f'Goodbye!')
    clear_previous_generation(1)  # clear one more line leftover after the loop stops

    print('The last generation was:')
    rprint(show_cells(grid=last_iteration, symbols=symbols, mode=mode, colours=cell_colours))
    print()
    print('The first generation was:')
    rprint(show_cells(grid=game.grid.cells, symbols=symbols, mode=mode, colours=cell_colours))
    rprint(f"[That was {game.total_iterations} iterations ago]")
    
    if game.repeated_pattern_halted_the_game:
        print('Game stopped due to a repeated pattern.')
    elif iterations == game.total_iterations:
        print('Game stopped due to a limit on iterations.')
    else:
        print('Game stopped due to user interruption.')

if __name__ == '__main__':
    main()
