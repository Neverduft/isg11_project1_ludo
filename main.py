import random


## Game Objects
class Token:
    def __init__(self, color):
        self.color = color
        self.position = -1  # -1 means it's not on the board yet, -2 is in-home
        self.moved_squares = 0
        self.in_home_position = -1  # -1 means not in-home


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
    def select_move(self, legal_moves, dice_roll):
        raise NotImplementedError("This method should be overridden by subclasses")


# Just take the first legal move for now, will be updated with new strategies TODO
class FirstLegalMoveStrategy(MoveStrategy):
    def select_move(self, legal_moves, dice_roll):
        return legal_moves[0] if legal_moves else None


## Game
class LudoGame:
    BOARD_LENGTH = 40
    HOME_LENGTH = 4 - 1

    def __init__(self):
        self.players = {
            "red": Player("red", 0, FirstLegalMoveStrategy()),
            "green": Player("green", 10, FirstLegalMoveStrategy()),
            "yellow": Player("yellow", 20, FirstLegalMoveStrategy()),
            "blue": Player("blue", 30, FirstLegalMoveStrategy()),
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
                        if other_token.position == candidate_position:
                            other_token.position = -1
                            other_token.moved_squares = 0
                            print(
                                f"{player_color}'s token captured {other_color}'s token!"
                            )

        return True

    def get_legal_moves(self, player_color, dice_value):
        player = self.players[player_color]
        legal_moves = []
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
                legal_moves.append((idx, "spawn"))
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
                                    (idx, "capture_move", candidate_position)
                                )
                                capturing = True

                if not capturing:
                    legal_moves.append((idx, "move_to_position", candidate_position))

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
                        legal_moves.append((idx, "move_inside_home"))
                    else:
                        legal_moves.append((idx, "move_to_home"))

        # If a spawn move is found, clear all other moves
        if spawn_found:
            legal_moves = [(idx, "spawn")]

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

    def play_game(self):
        # Check if any player has won
        def game_over():
            return any(player.has_won() for player in self.players.values())

        # Get move for current player
        def get_player_move(player_color, dice_roll):
            player = self.players[player_color]
            print(f"{player_color} rolled a {dice_roll}")

            legal_moves = self.get_legal_moves(player_color, dice_roll)
            selected_move = player.strategy.select_move(legal_moves, dice_roll)

            return selected_move

        print("Game start!")
        self.display_board()

        # Main game loop
        while not game_over():
            print(f"==> {self.turn}'s turn.")
            dice_roll = self.roll_dice()
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
                print(f"No legal moves for {self.turn}, next player's turn.\n\n")
                self.next_turn()


# Start game:
game = LudoGame()
game.play_game()
