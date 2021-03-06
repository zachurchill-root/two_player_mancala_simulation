import copy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

from mancala.config import NUMBER_OF_BINS, NUMBER_OF_STARTING_PIECES


class Player(Enum):
    ONE = 0
    TWO = 1


def _ensure_bin_selection_is_correct(selected_bin: int) -> None:
    upper_bound = NUMBER_OF_BINS - 1
    if selected_bin < 0 or selected_bin > upper_bound:
        raise ValueError(f"bin must be between 0 and {upper_bound}, inclusive")


@dataclass
class Turn:
    player: Player
    selected_bin: int

    def __post_init__(self):
        _ensure_bin_selection_is_correct(self.selected_bin)


class PlayerRow:
    def __init__(self, bins: List[int], goal: int):
        if len(bins) != NUMBER_OF_BINS:
            raise ValueError(f"bins must be of length {NUMBER_OF_BINS}")
        if not all(b >= 0 for b in bins):
            raise ValueError("All bins must have a non-negative amount of pieces")
        if goal < 0:
            raise ValueError("goal must have a non-negative amount of pieces")

        self._bins = bins
        self._goal = goal

    def __repr__(self) -> str:
        return "[ {:>2} | {} ]".format(
            self.goal, ", ".join(["{:>2}".format(b) for b in self.bins])
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PlayerRow):
            return False
        return (
            all([b == other_b for b, other_b in zip(self.bins, other.bins)])
            and self.goal == other.goal
        )

    @property
    def bins(self) -> List[int]:
        return self._bins

    @property
    def goal(self) -> int:
        return self._goal

    @classmethod
    def get_new_player_row(cls) -> "PlayerRow":
        return cls(
            bins=[NUMBER_OF_STARTING_PIECES for _ in range(NUMBER_OF_BINS)],
            goal=0,
        )

    def add_pieces_to_goal(self, pieces: int = 1) -> None:
        if pieces <= 0:
            raise ValueError("pieces should be positive")
        self._goal += pieces

    def add_piece_in_bin(self, bin: int) -> None:
        _ensure_bin_selection_is_correct(bin)
        self._bins[bin] += 1


class Board(Dict[Player, PlayerRow]):
    pass


def get_new_board() -> Board:
    return Board(
        {
            Player.ONE: PlayerRow.get_new_player_row(),
            Player.TWO: PlayerRow.get_new_player_row(),
        }
    )


def take_turn(board: Board, turn: Turn) -> Board:
    new_board = copy.deepcopy(board)
    opponent = Player.ONE if turn.player == Player.TWO else Player.TWO

    # 'Pick up' the pieces
    pieces = new_board[turn.player].bins[turn.selected_bin]
    new_board[turn.player].bins[turn.selected_bin] -= pieces

    bin_indexes_to_increment = range(
        max(0, turn.selected_bin - pieces), turn.selected_bin
    )
    pieces -= len(bin_indexes_to_increment)
    for bin_index in bin_indexes_to_increment:
        new_board[turn.player].add_piece_in_bin(bin_index)

    # If there are no pieces, then stop; otherwise, add 1 piece to the goal
    if pieces == 0:
        last_piece_landed_in = list(bin_indexes_to_increment)[0]
        landed_in_previously_empty_bin = (
            new_board[turn.player].bins[last_piece_landed_in] == 1
        )
        opponent_has_pieces_in_same_bin = (
            new_board[opponent].bins[last_piece_landed_in] > 0
        )
        if landed_in_previously_empty_bin and opponent_has_pieces_in_same_bin:
            new_board[turn.player].bins[last_piece_landed_in] -= 1
            stolen_pieces = new_board[opponent].bins[last_piece_landed_in]
            new_board[opponent].bins[last_piece_landed_in] -= stolen_pieces
            new_board[turn.player].add_pieces_to_goal(stolen_pieces + 1)
        return new_board
    new_board[turn.player].add_pieces_to_goal(1)
    pieces -= 1

    # If there are no pieces, then stop; otherwise, continue to opponent's row
    if pieces == 0:
        return new_board

    last_bin_index = len(new_board[opponent].bins) - 1
    bin_indexes_to_increment = range(
        last_bin_index, max(-1, last_bin_index - pieces), -1
    )
    pieces -= len(bin_indexes_to_increment)
    for bin_index in bin_indexes_to_increment:
        new_board[opponent].add_piece_in_bin(bin_index)

    # Potentially reach back around to the player's row, but this time
    # we're starting at the bin furthest from the goal
    if pieces == 0:
        return new_board
    last_bin_index = len(new_board[turn.player].bins) - 1
    bin_indexes_to_increment = range(
        last_bin_index, max(-1, last_bin_index - pieces), -1
    )
    pieces -= len(bin_indexes_to_increment)
    for bin_index in bin_indexes_to_increment:
        new_board[turn.player].add_piece_in_bin(bin_index)

    if pieces == 0:
        last_piece_landed_in = list(bin_indexes_to_increment)[-1]
        landed_in_previously_empty_bin = (
            new_board[turn.player].bins[last_piece_landed_in] == 1
        )
        opponent_has_pieces_in_same_bin = (
            new_board[opponent].bins[last_piece_landed_in] > 0
        )
        if landed_in_previously_empty_bin and opponent_has_pieces_in_same_bin:
            new_board[turn.player].bins[last_piece_landed_in] -= 1
            stolen_pieces = new_board[opponent].bins[last_piece_landed_in]
            new_board[opponent].bins[last_piece_landed_in] -= stolen_pieces
            new_board[turn.player].add_pieces_to_goal(stolen_pieces + 1)
        return new_board
    new_board[turn.player].add_pieces_to_goal(1)
    pieces -= 1

    # If there are no pieces, then stop; otherwise, continue to opponent's row
    if pieces == 0:
        return new_board

    last_bin_index = len(new_board[opponent].bins) - 1
    bin_indexes_to_increment = range(
        last_bin_index, max(-1, last_bin_index - pieces), -1
    )
    pieces -= len(bin_indexes_to_increment)
    for bin_index in bin_indexes_to_increment:
        new_board[opponent].add_piece_in_bin(bin_index)

    return new_board


def who_gets_next_turn(prior_board: Board, turn: Turn, new_board: Board) -> Player:
    opponent = Player.ONE if turn.player == Player.TWO else Player.TWO

    prior_player_bins = prior_board[turn.player].bins
    prior_player_goal = prior_board[turn.player].goal
    new_player_bins = new_board[turn.player].bins
    new_player_goal = new_board[turn.player].goal

    single_wrap_conditions = (
        new_player_goal == prior_player_goal + 1
        and prior_board[opponent].bins == new_board[opponent].bins
    )

    double_wrap_conditions = (
        new_player_goal == prior_player_goal + 2
        and new_player_bins[turn.selected_bin] == 1
        and all(
            [
                new_player_bins[i] == prior_player_bins[i] + 2
                for i in range(turn.selected_bin)
            ]
        )
    )

    if single_wrap_conditions or double_wrap_conditions:
        return turn.player
    else:
        return opponent
