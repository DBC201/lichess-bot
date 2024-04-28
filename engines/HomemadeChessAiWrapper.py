import time

import chess

from lib import model
from lib.conversation import Conversation
from lib.engine_wrapper import MinimalEngine, MOVE
from chess.engine import PlayResult

from engines.ChessAi import ChessAi


class HomemadeChessAiWrapper(MinimalEngine):
    time_spent = 0
    chess_ai = ChessAi(3)

    def search(self, board: chess.Board, time_limit: chess.engine.Limit, ponder: bool, draw_offered: bool,
               root_moves: MOVE, conversation: Conversation, game: model.Game) -> PlayResult:
        start_time = time.time()

        increment = game.clock_increment.total_seconds()

        time_left = game.clock_initial.total_seconds() - self.time_spent

        if time_left < 5:
            if self.chess_ai.max_depth != 1:
                conversation.send_message("player", "I am about to run out of time. I will only search one move ahead.")
                conversation.send_message("spectator", "I am about to run out of time. I will only search one move ahead.")
                self.chess_ai.max_depth = 1
        elif time_left <= 10:
            if self.chess_ai.max_depth != 2:
                conversation.send_message("player", "I am running low on time. I will only search two moves ahead.")
                conversation.send_message("spectator", "I am running low on time. I will only search two moves ahead.")
                self.chess_ai.max_depth = 2
        else:
            if self.chess_ai.max_depth != 3:
                conversation.send_message("player", "I have enough time. I will search three moves ahead.")
                conversation.send_message("spectator", "I have enough time. I will search three moves ahead.")
                self.chess_ai.max_depth = 3

        next_move = self.chess_ai.get_move(board)

        end_time = time.time()

        self.time_spent += end_time - start_time - increment

        return PlayResult(next_move, None)
