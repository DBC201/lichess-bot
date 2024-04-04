import time

import chess

from lib import model
from lib.conversation import Conversation
from lib.engine_wrapper import MinimalEngine, MOVE
from chess.engine import PlayResult
import random

# https://github.com/DBC201/chess-ai/blob/master/public/ai.js


class Node:
    def __init__(self, board: chess.Board):
        self.game = chess.Board(board.fen())
        self.score = None
        self.parent = None
        self.children = []
        self.depth = 0

        self.piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 1000
        }

    def add_parent(self, parent):
        self.parent = parent
        parent.children.append(self)
        self.depth = parent.depth + 1

    def update_score(self):
        if self.game.is_checkmate():
            self.score = -1000 if self.game.turn == chess.WHITE else 1000
            return

        if self.game.is_stalemate():
            self.score = 0
            return

        pieces = self.game.piece_map()
        self.score = 0
        for square, piece in pieces.items():
            if piece.color == chess.WHITE:
                self.score += self.piece_values[piece.piece_type]
            else:
                self.score -= self.piece_values[piece.piece_type]

    def get_score(self):
        if self.score is None:
            self.update_score()
        return self.score


class AlphaBetaPruningEngine(MinimalEngine):
    cache = None
    time_spent = 0
    max_depth = 3

    def alpha_beta_pruning(self, root: Node, alpha: int, beta: int) -> None:
        if root.depth >= self.max_depth or root.game.is_game_over():
            return

        if root.game.turn == chess.WHITE:
            max_score = -1000
            for move in root.game.legal_moves:
                child = Node(root.game)
                child.add_parent(root)
                child.game.push(move)
                self.alpha_beta_pruning(child, alpha, beta)
                max_score = max(max_score, child.get_score())
                alpha = max(alpha, max_score)
                if beta < alpha:
                    break
            root.score = max_score
        else:
            min_score = 1000
            for move in root.game.legal_moves:
                child = Node(root.game)
                child.add_parent(root)
                child.game.push(move)
                self.alpha_beta_pruning(child, alpha, beta)
                min_score = min(min_score, child.get_score())
                beta = min(beta, min_score)
                if beta < alpha:
                    break
            root.score = min_score

    def search(self, board: chess.Board, time_limit: chess.engine.Limit, ponder: bool, draw_offered: bool,
               root_moves: MOVE, conversation: Conversation, game: model.Game) -> PlayResult:
        root = None

        start_time = time.time()

        increment = game.clock_increment.total_seconds()

        time_left = game.clock_initial.total_seconds() - self.time_spent

        if time_left < 5:
            if self.max_depth != 1:
                conversation.send_message("player", "I am about to run out of time. I will only search one move ahead.")
                conversation.send_message("spectator", "I am about to run out of time. I will only search one move ahead.")
                self.max_depth = 1
        elif time_left <= 10:
            if self.max_depth != 2:
                conversation.send_message("player", "I am running low on time. I will only search two moves ahead.")
                conversation.send_message("spectator", "I am running low on time. I will only search two moves ahead.")
                self.max_depth = 2
        elif time_left > 10:
            if self.max_depth != 3:
                conversation.send_message("player", "I have enough time. I will search three moves ahead.")
                conversation.send_message("spectator", "I have enough time. I will search three moves ahead.")
                self.max_depth = 3

        if self.cache is None:
            root = Node(board)
            self.alpha_beta_pruning(root, -1000, 1000)
        else:
            root = self.cache

        possible_children = [child for child in root.children if child.get_score() == root.get_score()]

        next_child = random.choice(possible_children)

        if (root.score == 1000 or root.score == -1000) and len(next_child.children) > 0:
            possible_children = [child for child in next_child.children if child.get_score() == next_child.get_score()]
            self.cache = random.choice(possible_children)
            conversation.send_message("player", next_child.game.peek().uci() + "results in a checkmate.")
            conversation.send_message("spectator", next_child.game.peek().uci() + "results in a checkmate.")
        else:
            self.cache = None

        end_time = time.time()

        self.time_spent += end_time - start_time - increment

        return PlayResult(next_child.game.peek(), None)
