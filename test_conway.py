import pytest
from conway import Grid, ConwaysGameOfLife, Point, CellColours, Symbols, color_cell_row, show_cells, get_cells_from_file


def test_correct_grid_is_constructed_when_given_a_string_as_input():
    cells = """
    *-*-*
    -**
    *--
    -
    -**
    """
    expected = [
        ['*', '-', '*', '-', '*'],
        ['-', '*', '*', '-', '-'],
        ['*', '-', '-', '-', '-'],
        ['-', '-', '-', '-', '-'],
        ['-', '*', '*', '-', '-'],
    ]

    cell_grid = Grid(cell_pattern=cells)
    assert cell_grid.cells == expected


def test_alive_neighbours_for_each_cell_in_a_grid_are_counted_properly():
    cells = """
    *-*
    -**
    *--
    """
    grid = Grid(cell_pattern=cells)
    game = ConwaysGameOfLife(grid)
    actual_count = []
    expected_count = [1, 4, 2, 3, 4, 2, 1, 3, 2]

    for y in range(grid.rows):
        for x in range(grid.cols):
            actual_count.append(game.count_neighbours(game.grid.cells, Point(x, y)))

    for expected_count, actual_count in zip(actual_count, expected_count):
        assert expected_count == actual_count


def test_cell_iterations_are_generated_using_conways_rules():
    original = """
    -------
    -------
    --***--
    ---*---
    --***--
    -------
    -------
    """
    iteration_0 = [
        ['-', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '*', '*', '*', '-', '-'],
        ['-', '-', '-', '*', '-', '-', '-'],
        ['-', '-', '*', '*', '*', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-'],
    ]
    iteration_1 = [
        ['-', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '-', '*', '-', '-', '-'],
        ['-', '-', '*', '*', '*', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '*', '*', '*', '-', '-'],
        ['-', '-', '-', '*', '-', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-'],
    ]
    iteration_2 = [
        ['-', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '*', '*', '*', '-', '-'],
        ['-', '-', '*', '*', '*', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '*', '*', '*', '-', '-'],
        ['-', '-', '*', '*', '*', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-'],
    ]
    iteration_3 = [
        ['-', '-', '-', '*', '-', '-', '-'],
        ['-', '-', '*', '-', '*', '-', '-'],
        ['-', '-', '*', '-', '*', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '*', '-', '*', '-', '-'],
        ['-', '-', '*', '-', '*', '-', '-'],
        ['-', '-', '-', '*', '-', '-', '-'],
    ]
    expected = [iteration_0, iteration_1, iteration_2, iteration_3]
    cell_grid = Grid(cell_pattern=original)
    game = ConwaysGameOfLife(cells=cell_grid)

    for expected_iteration, actual_iteration in zip(expected, game.run_conways_game(iterations=4)):
        assert expected_iteration == actual_iteration


def test_cells_that_do_not_change_stay_the_same():
    iter_count = 3
    original = """
    ---------------
    ---**-----**---
    ---**-----**---
    ---------------
    -------**------
    -------**------
    ---------------
    """
    iterations = [
        [
        ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '-', '*', '*', '-', '-', '-', '-', '-', '*', '*', '-', '-', '-'],
        ['-', '-', '-', '*', '*', '-', '-', '-', '-', '-', '*', '*', '-', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-', '*', '*', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-', '*', '*', '-', '-', '-', '-', '-', '-'],
        ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-']] for _ in range(iter_count)
        ]

    grid = Grid(cell_pattern=original)
    game = ConwaysGameOfLife(grid)
    for expected, actual in zip(iterations, game.run_conways_game(iterations=iter_count)):
        assert expected == actual


def test_cells_are_coloured_correctly_with_alternative_symbols():
    cells = """
    *-*
    -**
    """
    symbols = Symbols('~', '^')
    colours = CellColours('dead_colour', 'alive_colour')
    grid = Grid(cell_pattern=cells)
    game = ConwaysGameOfLife(grid)
    grid_as_list = game.grid.cells
    row = grid_as_list[0]
    expected = '[alive_colour]^[/alive_colour][dead_colour]~[/dead_colour][alive_colour]^[/alive_colour]\n'

    assert expected == color_cell_row(symbols, colours=colours, cell_row=row)


def test_cells_are_displayed_correctly_in_basic_mode():
    cells = """
    *--
    -**
    **-
    """
    expected = """
    [green4]+[/green4][grey27]&[/grey27][grey27]&[/grey27]
    [grey27]&[/grey27][green4]+[/green4][green4]+[/green4]
    [green4]+[/green4][green4]+[/green4][grey27]&[/grey27]
    """.strip().replace(' ', '')
    mode = 'basic'
    grid = Grid(cells)
    symbols = Symbols('&', '+')
    colours = CellColours('grey27', 'green4')

    assert expected == show_cells(symbols=symbols, colours=colours, mode=mode, grid=grid.cells)


def test_grid_is_read_from_a_text_file_correctly(tmpdir):
    data = '---\n** *\n***\n'
    expected = [['-', '-', '-', '-'], ['*', '*', '-', '*'], ['*', '*', '*', '-']]
    file = tmpdir.join('test_grid.txt')
    file.write(data)
    file_location = str(file)
    
    cells = get_cells_from_file(file_location)
    grid = Grid(cell_pattern=cells)
    assert grid.cells == expected
