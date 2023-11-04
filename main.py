import random


class Token:
    def __init__(self, color):
        self.color = color
        self.position = -1  # -1 means it's not on the board yet, -2 means in-home
        self.moved_squares = 0  # Track the number of squares the token has moved
        self.in_home_position = -1  # Token's position inside the home column


class Player:
    def __init__(self, color, starting_position):
        self.color = color
        self.tokens = [Token(color) for _ in range(4)]
        self.starting_position = starting_position


class LudoGame:
    def __init__(self):
        self.players = {
            "red": Player("red", 0),
            "green": Player("green", 13),
            "yellow": Player("yellow", 26),
            "blue": Player("blue", 39),
        }

        self.turn = "red"  # Starting player

    def roll_dice(self):
        return random.randint(1, 6)

    # TODO : Implement take turn method and additional turns after rolling 6
    def next_turn(self):
        colors = list(self.players.keys())
        current_index = colors.index(self.turn)
        self.turn = colors[(current_index + 1) % 4]

    def move_token(self, player_color, token_index, dice_value):
        player = self.players[player_color]
        token = player.tokens[token_index]

        print(f"{player_color} rolled a {dice_value}")

        # Logging previous position for the token
        previous_position = token.position

        # Spawning a token if a 6 is rolled
        if (
            dice_value == 6
            and any(t.position == -1 for t in player.tokens)
            and not any(t.position == player.starting_position for t in player.tokens)
        ):
            token.position = player.starting_position
            token.moved_squares = 0
            print(f"{player_color} spawned a token at position {token.position}")
            return

        # Handle moving into home positions
        elif 51 < (token.moved_squares + dice_value) <= 55:
            potential_home_position = dice_value
            occupied_home_positions = [t.in_home_position for t in player.tokens]

            if potential_home_position in occupied_home_positions:
                print(
                    f"Illegal move! {player_color} cannot move to home position {potential_home_position} as it's occupied."
                )
                return

            if not all(
                earlier_pos not in occupied_home_positions
                for earlier_pos in range(1, potential_home_position)
            ):
                print(f"Illegal move! {player_color} cannot skip over a token in home.")
                return

            token.position = -2
            token.moved_squares += dice_value
            token.in_home_position = potential_home_position
            print(
                f"{player_color} moved a token to home position {token.in_home_position}"
            )
            return

        # Regular movement
        elif token.position != -1:
            potential_new_position = (token.position + dice_value) % 52

            # Checking if there's any token of the same color on the potential new position
            if any(t.position == potential_new_position for t in player.tokens):
                print(
                    f"Illegal move! {player_color} already has a token at position {potential_new_position}."
                )
                return

            token.position = potential_new_position
            token.moved_squares += dice_value
            print(
                f"{player_color} moved a token from {previous_position} to {token.position}"
            )

        # Logic for capturing other player's token
        for other_color, other_player in self.players.items():
            if other_color != player_color:
                for other_token in other_player.tokens:
                    if other_token.position == token.position:
                        other_token.position = -1
                        other_token.moved_squares = 0
                        other_token.in_home_position = -1
                        print(f"{player_color}'s token captured {other_color}'s token!")

    # TODO : Only return 1 legal spawn move even if multiple tokens in base
    def get_legal_moves(self, player_color, dice_value):
        player = self.players[player_color]
        legal_moves = []

        for idx, token in enumerate(player.tokens):
            # Spawning a token if a 6 is rolled
            if (
                dice_value == 6
                and token.position == -1
                and not any(
                    t.position == player.starting_position for t in player.tokens
                )
            ):
                legal_moves.append((idx, "spawn"))

            # Handle moving within home positions
            if 0 <= token.in_home_position + dice_value <= 3 and token.position == -2:
                potential_home_position = token.in_home_position + dice_value
                occupied_home_positions = [t.in_home_position for t in player.tokens]
                if potential_home_position not in occupied_home_positions:
                    legal_moves.append(
                        (idx, "move_within_home", potential_home_position)
                    )

            # Handle moving into home positions from the board
            elif 51 < (token.moved_squares + dice_value) <= 55:
                potential_home_position = dice_value
                occupied_home_positions = [t.in_home_position for t in player.tokens]
                if potential_home_position not in occupied_home_positions and all(
                    earlier_pos not in occupied_home_positions
                    for earlier_pos in range(1, potential_home_position)
                ):
                    legal_moves.append((idx, "move_to_home"))

            # Regular movement
            elif token.position != -1:
                potential_new_position = (token.position + dice_value) % 52
                if not any(t.position == potential_new_position for t in player.tokens):
                    # Check for capture
                    capture = False
                    for other_color, other_player in self.players.items():
                        if other_color != player_color:
                            for other_token in other_player.tokens:
                                if other_token.position == potential_new_position:
                                    capture = True
                                    break
                    if capture:
                        legal_moves.append(
                            (idx, "capture_move", potential_new_position)
                        )
                    else:
                        legal_moves.append(
                            (idx, "move_to_position", potential_new_position)
                        )

        return legal_moves

    def display_board(self):
        board_representation = ["-"] * 52
        for color, player in self.players.items():
            for token in player.tokens:
                if token.position != -1 and token.position != "completed":
                    board_representation[token.position] = color[0]
        print(" ".join(board_representation))


# Example usage:
game = LudoGame()
dice_value = game.roll_dice()
game.move_token("red", 0, dice_value)
game.display_board()
game.next_turn()
