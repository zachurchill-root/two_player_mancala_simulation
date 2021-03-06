import json

import pytest

from mancala.mancala import Player, PlayerRow, get_new_board
from mancala.serialize import to_serializable
from mancala.simulation import SimulationLoop
from mancala.strategy import (
    AlwaysMaximumPlayerStrategy,
    AlwaysMinimumPlayerStrategy,
    ExampleRandomPlayerStrategy,
)


def test_simulation_loop_provides_player_strategy_properties():
    player_one = ExampleRandomPlayerStrategy()
    player_two = ExampleRandomPlayerStrategy()
    loop = SimulationLoop(player_one=player_one, player_two=player_two)
    assert loop.player_one_strategy == player_one
    assert loop.player_two_strategy == player_two


def test_simulation_loops_provides_player_strategies_in_dict_format():
    player_one = ExampleRandomPlayerStrategy()
    player_two = ExampleRandomPlayerStrategy()
    loop = SimulationLoop(player_one=player_one, player_two=player_two)
    assert {Player.ONE, Player.TWO} == loop.player_strategies.keys()
    assert player_one == loop.player_strategies[Player.ONE]
    assert player_two == loop.player_strategies[Player.TWO]


@pytest.mark.parametrize("player", Player)
def test_simulation_loop_provides_option_to_choose_starting_player(player):
    loop = SimulationLoop(
        player_one=ExampleRandomPlayerStrategy(),
        player_two=ExampleRandomPlayerStrategy(),
        starting_player=player,
    )
    assert loop.starting_player == player


def test_simulation_loop_sets_up_starting_player_if_not_provided():
    loop = SimulationLoop(
        player_one=ExampleRandomPlayerStrategy(),
        player_two=ExampleRandomPlayerStrategy(),
    )
    assert loop.starting_player is not None
    assert loop.starting_player in {Player.ONE, Player.TWO}


def test_simulation_loop_starts_off_with_no_run_and_winning_player():
    loop = SimulationLoop(
        player_one=ExampleRandomPlayerStrategy(),
        player_two=ExampleRandomPlayerStrategy(),
    )
    assert loop.has_run is False
    assert loop.winning_player is None


def test_simulation_loop_starts_with_new_board():
    loop = SimulationLoop(
        player_one=ExampleRandomPlayerStrategy(),
        player_two=ExampleRandomPlayerStrategy(),
    )
    assert len(loop.boards) == 1
    assert loop.boards[0] == get_new_board()


def test_simulation_loop_starts_with_no_turns():
    loop = SimulationLoop(
        player_one=ExampleRandomPlayerStrategy(),
        player_two=ExampleRandomPlayerStrategy(),
    )
    assert len(loop.turns) == 0


# The Minimum strategy always beats the Maximum strategy
@pytest.mark.parametrize(
    "p1,p2,expected_winner",
    [
        (AlwaysMaximumPlayerStrategy(), AlwaysMinimumPlayerStrategy(), Player.TWO),
        (AlwaysMinimumPlayerStrategy(), AlwaysMaximumPlayerStrategy(), Player.ONE),
    ],
)
def test_simulation_loop_stops_when_goal_is_over_24(p1, p2, expected_winner):
    loop = SimulationLoop(player_one=p1, player_two=p2)
    assert loop.has_run is False
    assert loop.winning_player is None

    loop.run()
    assert loop.has_run is True
    assert len(loop.turns) > 1
    assert len(loop.boards) > 1

    assert loop.winning_player is not None
    assert loop.winning_player == expected_winner
    assert loop.boards[-1][loop.winning_player].goal >= 24


def test_simulation_loop_stops_if_there_is_a_tie():
    loop = SimulationLoop(
        player_one=AlwaysMinimumPlayerStrategy(),
        player_two=AlwaysMinimumPlayerStrategy(),
    )
    assert loop.has_run is False
    assert loop.winning_player is None

    loop.run()
    assert loop.has_run is True
    assert len(loop.turns) > 1
    assert len(loop.boards) > 1
    assert loop.winning_player is None

    last_board = loop.boards[-1]
    assert last_board[Player.ONE].goal == 24
    assert last_board[Player.TWO].goal == 24


def test_simulation_loop_serialization():
    p1 = AlwaysMinimumPlayerStrategy()
    p2 = AlwaysMaximumPlayerStrategy()
    loop = SimulationLoop(player_one=p1, player_two=p2)
    expected_serialization_keys = {
        "player_strategies",
        "starting_player",
        "winning_player",
        "turns",
        "boards",
    }

    # Pre-run
    prerun_serialization = json.loads(loop.serialize())
    assert prerun_serialization.keys() == expected_serialization_keys
    assert prerun_serialization["player_strategies"].keys() == {"one", "two"}
    assert prerun_serialization["player_strategies"]["one"] == p1.strategy_name
    assert prerun_serialization["player_strategies"]["two"] == p2.strategy_name
    assert prerun_serialization["starting_player"] in ["one", "two"]
    assert prerun_serialization["winning_player"] is None
    assert len(prerun_serialization["turns"]) == 0
    assert len(prerun_serialization["boards"]) == 1
    assert prerun_serialization["boards"][0] == {
        "one": {
            "bins": [4, 4, 4, 4, 4, 4],
            "goal": 0,
        },
        "two": {
            "bins": [4, 4, 4, 4, 4, 4],
            "goal": 0,
        },
    }

    # Post-run
    loop.run()
    postrun_serialization = json.loads(loop.serialize())
    assert postrun_serialization.keys() == expected_serialization_keys
    assert postrun_serialization["player_strategies"].keys() == {"one", "two"}
    assert postrun_serialization["player_strategies"]["one"] == p1.strategy_name
    assert postrun_serialization["player_strategies"]["two"] == p2.strategy_name
    assert postrun_serialization["starting_player"] in ["one", "two"]
    assert (
        postrun_serialization["winning_player"] == "one"
    )  # minimum strategy always wins
    assert len(postrun_serialization["turns"]) > 0
    assert postrun_serialization["turns"] == [
        to_serializable(turn) for turn in loop.turns
    ]
    assert len(postrun_serialization["boards"]) > 1
    assert postrun_serialization["boards"] == [
        to_serializable(board) for board in loop.boards
    ]
