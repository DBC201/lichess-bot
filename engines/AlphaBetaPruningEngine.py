import time

import chess

from lib import model
from lib.conversation import Conversation
from lib.engine_wrapper import MinimalEngine, MOVE
from chess.engine import PlayResult
import random

# https://github.com/DBC201/chess-ai/blob/master/public/ai.js


class Node:
    def __init__(self, board: chess.Board, piece_score):
        self.game = chess.Board(board.fen())

        self.piece_score = piece_score
        self.eval_score = None

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

    def get_score(self):
        if self.game.is_checkmate():
            self.eval_score = 1000 if self.game.turn == chess.BLACK else -1000
            return self.eval_score

        if self.game.is_stalemate():
            self.eval_score = 0
            return self.eval_score

        if self.eval_score is not None:
            return self.eval_score
        else:
            return self.piece_score

    def get_ordered_moves(self):
        moves = self.game.legal_moves

        has_capture = False

        ordered_moves = []

        for move in moves:
            if self.game.is_capture(move):
                if len(self.game.move_stack) > 0 and self.game.peek().to_square == move.to_square:
                    prev_move = self.game.pop()
                    if self.game.is_capture(prev_move):
                        has_capture = True
                    self.game.push(prev_move)

                piece = self.game.piece_at(move.to_square)
                if piece is None: # en passant
                    ordered_moves.append((move, 1))
                else:
                    ordered_moves.append((move, self.piece_values[piece.piece_type]))
            else:
                ordered_moves.append((move, 0))

        return ordered_moves, has_capture

    def eval(self):
        if self.game.is_checkmate():
            self.eval_score = -1000 if self.game.turn == chess.WHITE else 1000
            return

        if self.game.is_stalemate():
            self.eval_score = 0
            return

        pieces = self.game.piece_map()
        self.eval_score = 0
        for square, piece in pieces.items():
            if piece.color == chess.WHITE:
                self.eval_score += self.piece_values[piece.piece_type]
            else:
                self.eval_score -= self.piece_values[piece.piece_type]


class AlphaBetaPruningEngine(MinimalEngine):
    cache = None
    time_spent = 0
    max_depth = 3

    def alpha_beta_pruning(self, root: Node, alpha: int, beta: int, multiple_moves_flag: bool) -> None:
        ordered_moves, has_capture = root.get_ordered_moves()

        if root.game.is_game_over():
            return
        elif root.depth >= self.max_depth and not has_capture:
            return

        if root.game.turn == chess.WHITE:
            max_score = -1000
            for move, score_change in ordered_moves:
                child = Node(root.game, root.get_score() + score_change)
                child.add_parent(root)
                child.game.push(move)
                self.alpha_beta_pruning(child, alpha, beta, multiple_moves_flag)

                max_score = max(max_score, child.get_score())

                alpha = max(alpha, max_score)

                if multiple_moves_flag and beta < alpha:
                    break
                elif not multiple_moves_flag and beta <= alpha:
                    break
            root.eval_score = max_score
        else:
            min_score = 1000
            for move, score_change in ordered_moves:
                child = Node(root.game, root.get_score() - score_change)
                child.add_parent(root)
                child.game.push(move)
                self.alpha_beta_pruning(child, alpha, beta, multiple_moves_flag)

                min_score = min(min_score, child.get_score())

                beta = min(beta, min_score)

                if multiple_moves_flag and beta < alpha:
                    break
                elif not multiple_moves_flag and beta <= alpha:
                    break
            root.eval_score = min_score

    def search(self, board: chess.Board, time_limit: chess.engine.Limit, ponder: bool, draw_offered: bool,
               root_moves: MOVE, conversation: Conversation, game: model.Game) -> PlayResult:
        root = None

        is_opening = board.ply() < 20

        if is_opening and self.max_depth > 2:
            conversation.send_message("player", "I am in the opening phase. I will search two moves ahead.")
            conversation.send_message("spectator", "I am in the opening phase. I will search two moves ahead.")
            self.max_depth = 2

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
        elif time_left > 10 and not is_opening:
            if self.max_depth != 3:
                conversation.send_message("player", "I have enough time. I will search three moves ahead.")
                conversation.send_message("spectator", "I have enough time. I will search three moves ahead.")
                self.max_depth = 3

        if self.cache is None:
            root = Node(board, None)
            root.eval()
            self.alpha_beta_pruning(root, -1001, 1001, is_opening)
        else:
            root = self.cache

        next_child = None

        if is_opening:
            possible_children = [child for child in root.children if child.get_score() == root.get_score()]
            next_child = random.choice(possible_children)
        else:
            for child in root.children:
                if child.get_score() == root.get_score():
                    next_child = child
                    break

        if (root.get_score() == 1000 or root.get_score() == -1000) and len(next_child.children) > 0:
            for child in next_child.children:
                if child.get_score() == root.get_score():
                    self.cache = child
                    break
            conversation.send_message("player", next_child.game.peek().uci() + "results in a checkmate.")
            conversation.send_message("spectator", next_child.game.peek().uci() + "results in a checkmate.")
        else:
            self.cache = None

        end_time = time.time()

        self.time_spent += end_time - start_time - increment

        return PlayResult(next_child.game.peek(), None)
