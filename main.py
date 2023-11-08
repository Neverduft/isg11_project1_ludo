import random


class Token:
    def __init__(self, color):
        self.color = color
        self.position = -1  # -1 means it's not on the board yet, -2 is in-home
        self.moved_squares = 0
        self.in_home_position = -1


class Player:
    def __init__(self, color, starting_position):
        self.color = color
        self.tokens = [Token(color) for _ in range(4)]
        self.starting_position = starting_position

    def has_won(self):
        # Winning condition is if all tokens are in-home
        return all(token.position == -2 for token in self.tokens)


class LudoGame:
    BOARD_LENGTH = 40
    HOME_LENGTH = 4 - 1

    def __init__(self):
        self.players = {
            "red": Player("red", 0),
            "green": Player("green", 10),
            "yellow": Player("yellow", 20),
            "blue": Player("blue", 30),
        }

        self.turn = "red"  # Starting player

    def roll_dice(self):
        return random.randint(1, 6)

    def next_turn(self):
        colors = list(self.players.keys())
        current_index = colors.index(self.turn)
        self.turn = colors[(current_index + 1) % 4]

    def move_token(self, player_color, token_index, dice_value):
        player = self.players[player_color]
        token = player.tokens[token_index]
        candidate_position = (token.position + dice_value) % self.BOARD_LENGTH
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
            # Checking if there's any token of the same color on the potential new position
            if any(t.position == candidate_position for t in player.tokens):
                print(
                    f"Illegal move! {player_color} already has a token at position {candidate_position}."
                )
                return False

            token.position = candidate_position
            token.moved_squares += dice_value
            print(f"{player_color} moved a token to position {token.position}")

        # Move into/inside of home
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

            if candidate_home_position in occupied_home_positions:
                print(
                    f"Illegal move! {player_color} cannot move to home position {candidate_home_position} as it's occupied."
                )
                return False

            if any(
                occupied_position < candidate_home_position
                for occupied_position in occupied_home_positions
            ):
                print(f"Illegal move! {player_color} cannot skip over a token in home.")
                return False

            if token.in_home_position == -1:
                print(f"{player_color} moved a token inside of home.")
            else:
                print(f"{player_color} moved a token into home.")

            token.position = -2
            token.moved_squares += dice_value
            token.in_home_position = candidate_home_position

        else:
            # If none of the above, the move is illegal
            print(f"Illegal move attempted by {player_color}.")
            return False

        if token.position >= 0:
            for other_color, other_player in self.players.items():
                if other_color != player_color:
                    for other_token in other_player.tokens:
                        if other_token.position == candidate_position:
                            other_token.position = -1
                            other_token.moved_squares = 0
                            print(
                                f"{player_color}'s token captured {other_color}'s token!"
                            )

        return True

    # TODO check enforcement of spawn
    # TODO Comments
    def get_legal_moves(self, player_color, dice_value):
        player = self.players[player_color]
        legal_moves = []

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
                legal_moves.append((idx, "spawn"))
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
                                    (idx, "capture_move", candidate_position)
                                )
                                capturing = True

                if not capturing:
                    legal_moves.append((idx, "move_to_position", candidate_position))

            # Check for move into/inside of home
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
                        legal_moves.append((idx, "move_inside_home"))
                    else:
                        legal_moves.append((idx, "move_to_home"))

        return legal_moves

    def display_board(self):
        # print(" TODO ?")
        return

    def play_game(self):
        def game_over():
            # Checks if any player has won
            return any(player.has_won() for player in self.players.values())

        def get_player_move(player_color):
            dice_roll = self.roll_dice()
            print(f"{player_color} rolled a {dice_roll}")

            legal_moves = self.get_legal_moves(player_color, dice_roll)

            # Just take the first legal move for now, will be updated with strategies TODO
            return legal_moves[0] if legal_moves else None, dice_roll

        print("Game start!")
        self.display_board()

        while not game_over():
            print(f"{self.turn}'s turn.")
            move, dice_roll = get_player_move(self.turn)

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
                self.next_turn()


# Example usage:
game = LudoGame()
game.play_game()
