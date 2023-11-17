from copy import deepcopy
from enum import Enum
import json
import math
import random
import os
import time


def cls():
    os.system("cls" if os.name == "nt" else "clear")


## Game Objects
class Token:
    def __init__(self, color):
        self.color = color
        self.position = -1  # -1 means it's not on the board yet, -2 is in-home
        self.moved_squares = 0
        self.in_home_position = -1  # -1 means not in-home


class Moves(Enum):
    spawn = 1
    move_to_position = 2
    move_to_home = 3
    move_inside_home = 4
    capture_move = 5


class Player:
    def __init__(self, color, starting_position, strategy):
        self.color = color
        self.tokens = [Token(color) for _ in range(4)]
        self.starting_position = starting_position
        self.strategy = strategy

    # Winning condition is if all tokens are in-home
    def has_won(self):
        return all(token.position == -2 for token in self.tokens)


## Strategies
class MoveStrategy:
    def select_move(
        self,
        legal_moves: list[tuple[int, Moves]],
        dice_roll: int,
        player_color: str,
        all_players: list[Player],
    ) -> Moves:
        raise NotImplementedError("This method should be overridden by subclasses")

    def find_move(
        self, target: Moves, moves: list[tuple[int, Moves]]
    ) -> tuple[int, Moves] | None:
        for move in moves:
            if target.value == move[1].value:
                return move
        return None

    def calculate_risk(self, player_token, opponents: list[Player]) -> list:
        risk_level = 0

        if player_token.position >= 0:  # Only tokens on the board are at risk
            for opponent in opponents:
                # Increase risk if we are on the spawn point of an opponent
                if opponent.starting_position == player_token.position:
                    risk_level += 3
                for opp_token in opponent.tokens:
                    if opp_token.position >= 0:
                        opponent_distance_to_home = (
                            opponent.starting_position - opp_token.position
                        ) % LudoGame.BOARD_LENGTH
                        # WORKAROUND: starting position modulo
                        if opponent_distance_to_home == 0:
                            opponent_distance_to_home = 40
                        distance_to_token = (
                            player_token.position - opp_token.position
                        ) % LudoGame.BOARD_LENGTH
                        # Check if opponents home is between the enemies token and our token
                        if opponent_distance_to_home < distance_to_token:
                            continue
                        # A token is at risk if an opponent token is within 6 steps behind it
                        if 0 < distance_to_token <= 6:
                            risk_level += 1
        return risk_level


# Just take the first legal move for now, will be updated with new strategies TODO
class FirstLegalMoveStrategy(MoveStrategy):
    def select_move(
        self,
        legal_moves: list[tuple[int, Moves]],
        dice_roll: int,
        player_color: str,
        all_players: list[Player],
    ):
        return legal_moves[0] if legal_moves else None


class AggressiveStrategy(MoveStrategy):
    def select_move(
        self,
        legal_moves: list[tuple[int, Moves]],
        dice_roll: int,
        player_color: str,
        all_players: list[Player],
    ):
        if len(legal_moves) == 1:  # e.g. only "spawn" move
            return legal_moves[0]

        capture_move = self.find_move(Moves.capture_move, legal_moves)
        if capture_move is not None:
            return capture_move

        move_weights: dict[tuple[int, Moves], float] = {}
        other_players: list[Player] = []
        for player in all_players:
            if player.color == player_color:
                self_player = player
            else:
                other_players.append(player)
        for move in legal_moves:
            if move[1] == Moves.move_to_position:
                self_token = self_player.tokens[move[0]]

                distances_to_enemy: list[int] = []
                for player in other_players:
                    for other_token in player.tokens:
                        temp_token_after_turn = deepcopy(self_token)
                        temp_token_after_turn.position += dice_roll
                        temp_token_after_turn.moved_squares += dice_roll
                        distance = LudoGame.get_reachable_distance_between(
                            temp_token_after_turn, other_token
                        )
                        if distance == -2:  # token2 not on board
                            continue
                        elif distance == -1:  # token2 not reachable
                            if (
                                LudoGame.get_reachable_distance_between(
                                    self_token, other_token
                                )
                                != -1
                            ):  # but was reachable before
                                distances_to_enemy.append(distance)  # append the -1
                        else:
                            distances_to_enemy.append(distance)

                # Calculate move weight
                move_weights[move] = 0
                for distance in distances_to_enemy:
                    if distance == -1:  # went out of reach
                        move_weights[move] -= 10
                    else:
                        min_turn_amount = math.ceil(distance / 6)
                        move_weights[move] += 10 / min_turn_amount
                if distances_to_enemy:
                    move_weights[move] /= len(distances_to_enemy)

        if move_weights:
            print("RED move weights:")
            print(
                [
                    f"{move[1].name}[{move[0]}]: {weight}"
                    for (move, weight) in move_weights.items()
                ]
            )
            return max(move_weights, key=move_weights.get)  # the move with max weight

        # Fallback
        ranked_moves = [
            self.find_move(Moves.move_to_home, legal_moves),
            self.find_move(Moves.move_inside_home, legal_moves),
        ]
        return next((move for move in ranked_moves if move is not None), None)

# TODO Seems to not put tokens into base?
class DefensiveStrategy(MoveStrategy):
    def select_move(
        self,
        legal_moves: list[tuple[int, Moves]],
        dice_roll: int,
        player_color: str,
        all_players: list[Player],
    ):
        if len(legal_moves) == 1:  # e.g. only "spawn" move
            return legal_moves[0]

        other_players: list[Player] = []
        for player in all_players:
            if player.color == player_color:
                self_player = player
            else:
                other_players.append(player)

        best_move: tuple[int, Moves] | None = None
        for move in legal_moves:
            if move[1] == Moves.move_to_position or move[1] == Moves.capture_move:
                self_token = self_player.tokens[move[0]]
                if not best_move:
                    best_move = move
                else:
                    best_token = self_player.tokens[best_move[0]]
                    if self_token.moved_squares < best_token.moved_squares:
                        best_move = move
        if best_move:
            return best_move

        # Fallback
        ranked_moves = [
            self.find_move(Moves.move_to_home, legal_moves),
            self.find_move(Moves.move_inside_home, legal_moves),
        ]
        return next((move for move in ranked_moves if move is not None), None)


class SmartStrategy(MoveStrategy):
    def select_move(
        self,
        legal_moves: list[tuple[int, Moves]],
        dice_roll: int,
        player_color: str,
        all_players: list[Player],
    ):
        current_player = next(
            player for player in all_players if player.color == player_color
        )
        opponents = [player for player in all_players if player.color != player_color]

        # Assess the current risk for each token
        current_risks = [
            self.calculate_risk(token, opponents) for token in current_player.tokens
        ]

        print("RISKS:", current_risks)
        print("MOVES:", legal_moves)

        best_move = None
        best_risk_reduction = 0

        for move in legal_moves:
            token = current_player.tokens[move[0]]
            # Calculate token's position after the move
            new_position = (
                (token.position + dice_roll) % LudoGame.BOARD_LENGTH
                if move[1] == Moves.move_to_position or move[1] == Moves.capture_move
                else -2
            )
            # Make a hypothetical token for risk assessment
            hypo_token = Token(token.color)
            hypo_token.position = new_position

            # Calculate the risk after the move
            new_risk = self.calculate_risk(hypo_token, opponents)

            # TODO Use linear scaling risk reduction based on how far the token has already moved (tokens further on board are more important)

            if new_position == -2:
                risk_reduction = 1  # Priotitise getting token into home
            else:
                risk_reduction = current_risks[move[0]] - new_risk

            # If the move reduces risk and is better than previous best, select it
            if risk_reduction > best_risk_reduction:
                best_move = move
                best_risk_reduction = risk_reduction

            # If risk stays same but we can capture, select it
            elif (
                risk_reduction == best_risk_reduction and move[1] == Moves.capture_move
            ):
                best_move = move
                best_risk_reduction = risk_reduction

            # If risk stays same for the move, select it
            elif (
                risk_reduction == best_risk_reduction
                and move[1] == Moves.move_to_position
            ):
                if best_move and best_move[1] == Moves.capture_move:
                    continue
                best_move = move
                best_risk_reduction = risk_reduction

        # If we found a move that reduces risk, return it
        if best_move:
            return best_move

        # If no risk reducing move is found, use fallback priorities // could be improved ?
        rankedMoves = [
            self.find_move(Moves.move_to_home, legal_moves),
            self.find_move(Moves.capture_move, legal_moves),
            self.find_move(Moves.move_inside_home, legal_moves),
            self.find_move(Moves.move_to_position, legal_moves),
            self.find_move(Moves.spawn, legal_moves),
        ]
        return next((move for move in rankedMoves if move is not None), None)


## Game
class LudoGame:
    BOARD_LENGTH = 40
    HOME_LENGTH = 4 - 1

    def __init__(
        self, clearConsole: bool = False, interactive: bool = False, turnTime: float = 0
    ):
        self.clearConsole = clearConsole
        self.interactive = interactive
        self.turnTime = turnTime

        self.players = {
            "red": Player("red", 0, AggressiveStrategy()),
            "green": Player("green", 10, DefensiveStrategy()),
            "yellow": Player("yellow", 20, SmartStrategy()),
            "blue": Player("blue", 30, FirstLegalMoveStrategy()),
        }

        self.turn = "red"  # Starting player

    @staticmethod
    def get_reachable_distance_between(token1: Token, token2: Token) -> int:
        if token1.position < 0 or token2.position < 0:
            return -2
        distance = (token2.position - token1.position) % LudoGame.BOARD_LENGTH
        if token1.moved_squares + distance > LudoGame.BOARD_LENGTH:
            return -1
        return distance

    def roll_dice(self):
        return random.randint(1, 6)

    def next_turn(self):
        colors = list(self.players.keys())
        current_index = colors.index(self.turn)
        self.turn = colors[(current_index + 1) % 4]

    def move_token(self, player_color, token_index, dice_value):
        player = self.players[player_color]
        token = player.tokens[token_index]
        moved_squares = token.moved_squares
        candidate_home_position = moved_squares + dice_value - self.BOARD_LENGTH

        # Check if spawning is possible and legal (no own token is on the starting position)
        if (
            dice_value == 6
            and token.position == -1
            and not any(t.position == player.starting_position for t in player.tokens)
        ):
            token.position = player.starting_position
            print(f"{player_color} spawned a token at position {token.position}")

        # Normal move on board
        elif token.position >= 0 and moved_squares + dice_value < self.BOARD_LENGTH:
            candidate_position = (token.position + dice_value) % self.BOARD_LENGTH
            # Check if there's a token of the same color on the potential new position
            if any(t.position == candidate_position for t in player.tokens):
                print(
                    f"Illegal move! {player_color} already has a token at position {candidate_position}."
                )
                return False

            token.position = candidate_position
            token.moved_squares += dice_value
            print(f"{player_color} moved a token to position {token.position}")

        # Move into/within home
        elif (
            token.position != -1
            and moved_squares + dice_value >= self.BOARD_LENGTH
            and candidate_home_position <= self.HOME_LENGTH
        ):
            occupied_home_positions = [
                t.in_home_position
                for t in player.tokens
                if t.in_home_position >= 0
                and t.in_home_position != token.in_home_position
            ]

            # Prevent moving token if there's a token of the same color on the potential new position
            if candidate_home_position in occupied_home_positions:
                print(
                    f"Illegal move! {player_color} cannot move to home position {candidate_home_position} as it's occupied."
                )
                return False

            # Prevent skipping over tokens in home
            if any(
                occupied_position < candidate_home_position
                for occupied_position in occupied_home_positions
            ):
                print(f"Illegal move! {player_color} cannot skip over a token in home.")
                return False

            if token.in_home_position == -1:
                print(f"{player_color} moved a token into home.")
            else:
                print(f"{player_color} moved a token within home.")

            token.position = -2
            token.moved_squares += dice_value
            token.in_home_position = candidate_home_position

        else:
            # If none of the above, the move is illegal
            print(f"Illegal move attempted by {player_color}.")
            return False

        # Handle capturing tokens
        if token.position >= 0:
            for other_color, other_player in self.players.items():
                if other_color != player_color:
                    for other_token in other_player.tokens:
                        if other_token.position == token.position:
                            other_token.position = -1
                            other_token.moved_squares = 0
                            print(
                                f"{player_color}'s token captured {other_color}'s token!"
                            )

        return True

    def get_legal_moves(self, player_color, dice_value) -> list[tuple[int, Moves]]:
        player = self.players[player_color]
        legal_moves: list[tuple[int, Moves]] = []
        spawn_found = False

        # Perform similar checks as in move_token to get legal moves
        for idx, token in enumerate(player.tokens):
            candidate_position = (token.position + dice_value) % self.BOARD_LENGTH
            moved_squares = token.moved_squares
            candidate_home_position = moved_squares + dice_value - self.BOARD_LENGTH

            # Check for spawning move
            if (
                dice_value == 6
                and token.position == -1
                and not any(
                    t.position == player.starting_position for t in player.tokens
                )
            ):
                legal_moves.append((idx, Moves.spawn))
                spawn_found = True
                break  # Stop looking for other moves if spawn is possible

            # Check for normal move on the board
            elif (
                token.position >= 0
                and moved_squares + dice_value < self.BOARD_LENGTH
                and not any(t.position == candidate_position for t in player.tokens)
            ):
                capturing = False
                for other_color, other_player in self.players.items():
                    if other_color != player_color:
                        for other_token in other_player.tokens:
                            if other_token.position == candidate_position:
                                legal_moves.append(
                                    (idx, Moves.capture_move, candidate_position)
                                )
                                capturing = True

                if not capturing:
                    legal_moves.append(
                        (idx, Moves.move_to_position, candidate_position)
                    )

            # Check for move into/within home
            elif (
                token.position != -1
                and moved_squares + dice_value >= self.BOARD_LENGTH
                and candidate_home_position <= self.HOME_LENGTH
            ):
                occupied_home_positions = [
                    t.in_home_position
                    for t in player.tokens
                    if t.in_home_position >= 0
                    and t.in_home_position != token.in_home_position
                ]

                if candidate_home_position not in occupied_home_positions and not any(
                    occupied_position < candidate_home_position
                    for occupied_position in occupied_home_positions
                ):
                    if token.in_home_position >= 0:
                        legal_moves.append((idx, Moves.move_inside_home))
                    else:
                        legal_moves.append((idx, Moves.move_to_home))

        # If a spawn move is found, clear all other moves
        if spawn_found:
            legal_moves = [(idx, Moves.spawn)]

        return legal_moves

    def display_board(self):
        # Create a list representing the board with empty tiles
        board = ["."] * self.BOARD_LENGTH
        home_columns = {
            "red": ["=" for i in range(self.HOME_LENGTH + 1)],
            "green": ["=" for i in range(self.HOME_LENGTH + 1)],
            "yellow": ["=" for i in range(self.HOME_LENGTH + 1)],
            "blue": ["=" for i in range(self.HOME_LENGTH + 1)],
        }

        # Place the tokens on the board
        for color, player in self.players.items():
            for token in player.tokens:
                if token.position >= 0:  # Tokens on board
                    board[token.position] = color[0].upper()
                elif token.position == -2:  # Tokens in home column
                    home_columns[color][token.in_home_position] = color[0].upper()

        # Display home columns
        print("\nHome columns:", end="  ")
        for color, column in home_columns.items():
            print(f"{color.capitalize()}: {' '.join(column)}", end="  ")

        print("")

        # Tokens in base
        print("Tokens in base:", end="  ")
        for color, player in self.players.items():
            tokens_in_base = sum(1 for t in player.tokens if t.position == -1)
            print(f"{color.capitalize()}: {tokens_in_base}", end="  ")

        print("")

        # Display the board
        print("Board:")
        for tile in board:
            print(tile, end=" ")

        print("\n\n")

    def clearAndWaitForEnter(self):
        if self.turnTime > 0:
            time.sleep(self.turnTime)
        if self.interactive:
            input("Press enter to continue...")
        if self.clearConsole:
            cls()

    def play_game(self):
        # Check if any player has won
        def game_over():
            return any(player.has_won() for player in self.players.values())

        # Get move for current player
        def get_player_move(player_color, dice_roll):
            player = self.players[player_color]

            legal_moves = self.get_legal_moves(player_color, dice_roll)
            selected_move = player.strategy.select_move(
                legal_moves, dice_roll, player_color, self.players.values()
            )

            return selected_move

        if self.clearConsole:
            cls()
        print("Game start!")
        self.display_board()
        self.clearAndWaitForEnter()

        # Main game loop
        while not game_over():
            print(f"==> {self.turn}'s turn.")
            dice_roll = self.roll_dice()
            print(f"{self.turn} rolled a {dice_roll}")

            if not any(token.position >= 0 for token in self.players[self.turn].tokens):
                if dice_roll != 6:
                    dice_roll = self.roll_dice()
                    print(f"{self.turn} rolled a {dice_roll}")
                    if dice_roll != 6:
                        dice_roll = self.roll_dice()
                        print(f"{self.turn} rolled a {dice_roll}")

            move = get_player_move(self.turn, dice_roll)

            if move:
                successful_move = self.move_token(self.turn, move[0], dice_roll)
                self.display_board()

                if game_over():
                    print(f"Game over! {self.turn} wins!")
                    break

                # Player gets another turn if they roll a six and make a legal move
                if dice_roll != 6 or not successful_move:
                    self.next_turn()
            else:
                print(f"No legal moves for {self.turn}, next player's turn.")
                self.display_board()
                self.next_turn()

            self.clearAndWaitForEnter()


# Start game:
game = LudoGame(clearConsole=False, interactive=False, turnTime=0.0)
game.play_game()

# TODO Stats class + log into json
