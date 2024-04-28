# https://github.com/DBC201/chess-ai-python/blob/master/ChessAi.py
import chess
import random

CENTER_SQUARES = [chess.D4, chess.D5, chess.E4, chess.E5]

BOTTOM_EDGE_SQUARES = [chess.A1, chess.B1, chess.C1, chess.D1, chess.E1, chess.F1, chess.G1, chess.H1]
TOP_EDGE_SQUARES = [chess.A8, chess.B8, chess.C8, chess.D8, chess.E8, chess.F8, chess.G8, chess.H8]

LEFT_EDGE_SQUARES = [chess.A1, chess.A2, chess.A3, chess.A4, chess.A5, chess.A6, chess.A7, chess.A8]
RIGHT_EDGE_SQUARES = [chess.H1, chess.H2, chess.H3, chess.H4, chess.H5, chess.H6, chess.H7, chess.H8]

EDGE_SQUARES = [chess.A1, chess.A2, chess.A3, chess.A4, chess.A5, chess.A6, chess.A7, chess.A8,
                chess.H1, chess.H2, chess.H3, chess.H4, chess.H5, chess.H6, chess.H7, chess.H8,
                chess.B1, chess.C1, chess.D1, chess.E1, chess.F1, chess.G1, chess.B8, chess.C8,
                chess.D8, chess.E8, chess.F8, chess.G8]

WHITE_WIN_SCORE = 100_000
BLACK_WIN_SCORE = -100_000


def calculate_manhattan_distance(square_index1, square_index2):
    # Convert square indices to coordinates
    x1, y1 = square_index1 % 8, square_index1 // 8
    x2, y2 = square_index2 % 8, square_index2 // 8
    # Calculate Manhattan distance
    return abs(x1 - x2) + abs(y1 - y2)


def calculate_distance_to_center(square_index):
    return min(calculate_manhattan_distance(square_index, center_square_index) for center_square_index in CENTER_SQUARES)


def calculate_distance_to_edge(square_index, edge_squares):
    return min(calculate_manhattan_distance(square_index, edge_square_index) for edge_square_index in edge_squares)


class Node:
    def __init__(self, board: chess.Board, piece_score):
        self.game = chess.Board(board.fen())

        self.piece_score = piece_score
        self.eval_score = None

        self.parent = None
        self.children = []

        self.depth = 0

        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 300,
            chess.BISHOP: 300,
            chess.ROOK: 500,
            chess.QUEEN: 800,
            chess.KING: 0
        }

    def add_parent(self, parent):
        self.parent = parent
        parent.children.append(self)
        self.depth = parent.depth + 1

    def get_score(self):
        if self.game.is_checkmate():
            self.eval_score = WHITE_WIN_SCORE if self.game.turn == chess.BLACK else BLACK_WIN_SCORE
            return self.eval_score

        if self.game.is_stalemate():
            self.eval_score = 0
            return self.eval_score

        if self.eval_score is not None:
            return self.eval_score
        else:
            return self.piece_score

    def get_ordered_moves(self, shuffle=False):
        moves = list(self.game.legal_moves)

        has_capture = False
        group_by_score_change = {}

        for move in moves:
            score_change = 0
            if self.game.is_capture(move):
                if len(self.game.move_stack) > 0 and self.game.peek().to_square == move.to_square:
                    prev_move = self.game.pop()
                    if self.game.is_capture(prev_move):
                        has_capture = True
                    self.game.push(prev_move)

                piece = self.game.piece_at(move.to_square)
                if piece is None: # en passant
                    score_change += self.piece_values[chess.PAWN]
                else:
                    score_change += self.piece_values[piece.piece_type]

            pieces = self.game.piece_map()

            if len(pieces) > 28:
                piece = self.game.piece_at(move.from_square)

                old_distance_to_center = calculate_distance_to_center(move.to_square)

                new_distance_to_center = calculate_distance_to_center(move.from_square)

                if piece.piece_type == chess.PAWN or piece.piece_type == chess.KNIGHT or piece.piece_type == chess.BISHOP:
                    score_change += (new_distance_to_center - old_distance_to_center) * 10
            elif 20 < len(pieces) <= 28:
                if self.game.is_check():
                    score_change += 5

                old_attack_count = self.game.attacks(move.from_square)
                new_attack_count = self.game.attacks(move.to_square)

                score_change += (len(new_attack_count) - len(old_attack_count))

                piece = self.game.piece_at(move.from_square)

                if piece.piece_type == chess.PAWN:
                    edge_squares = TOP_EDGE_SQUARES if piece.color == chess.WHITE else BOTTOM_EDGE_SQUARES
                    old_distance_to_edge = calculate_distance_to_edge(move.to_square, edge_squares)
                    new_distance_to_edge = calculate_distance_to_edge(move.from_square, edge_squares)

                    score_change += (new_distance_to_edge - old_distance_to_edge) * 10
                elif piece.piece_type == chess.KING:
                    old_distance_to_edge = min(calculate_distance_to_edge(move.to_square, LEFT_EDGE_SQUARES),
                                               calculate_distance_to_edge(move.to_square, RIGHT_EDGE_SQUARES))
                    new_distance_to_edge = min(calculate_distance_to_edge(move.from_square, LEFT_EDGE_SQUARES),
                                                  calculate_distance_to_edge(move.from_square, RIGHT_EDGE_SQUARES))

                    score_change += (new_distance_to_edge - old_distance_to_edge) * 10
            else:
                piece = self.game.piece_at(move.from_square)

                if self.game.is_check():
                    score_change += 5

                if piece.piece_type == chess.KING:
                    old_distance_to_edge = min(calculate_distance_to_edge(move.to_square, LEFT_EDGE_SQUARES),
                                               calculate_distance_to_edge(move.to_square, RIGHT_EDGE_SQUARES),
                                               calculate_distance_to_edge(move.to_square, TOP_EDGE_SQUARES),
                                               calculate_distance_to_edge(move.to_square, BOTTOM_EDGE_SQUARES))
                    new_distance_to_edge = min(calculate_distance_to_edge(move.from_square, LEFT_EDGE_SQUARES),
                                               calculate_distance_to_edge(move.from_square, RIGHT_EDGE_SQUARES),
                                               calculate_distance_to_edge(move.from_square, TOP_EDGE_SQUARES),
                                               calculate_distance_to_edge(move.from_square, BOTTOM_EDGE_SQUARES))

                    score_change += (old_distance_to_edge - new_distance_to_edge) * 25

            if score_change in group_by_score_change:
                group_by_score_change[score_change].append(move)
            else:
                group_by_score_change[score_change] = [move]

        ordered_moves = []

        for score_change, moves in group_by_score_change.items():
            if shuffle:
                random.shuffle(moves)
            for move in moves:
                ordered_moves.append((move, score_change))

        ordered_moves.sort(key=lambda x: x[1], reverse=True)

        return ordered_moves, has_capture

    def eval(self):
        if self.game.is_checkmate():
            self.eval_score = WHITE_WIN_SCORE if self.game.turn == chess.WHITE else BLACK_WIN_SCORE
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


class ChessAi:
    def __init__(self, max_depth=3):
        self.max_depth = max_depth
        self.cache = None

    def alpha_beta_pruning(self, root: Node, alpha: int, beta: int, multiple_moves_flag: bool) -> None:
        ordered_moves, has_capture = root.get_ordered_moves(multiple_moves_flag)

        if root.game.is_game_over():
            return
        elif root.depth >= self.max_depth and not has_capture:
            return

        if root.game.turn == chess.WHITE:
            max_score = BLACK_WIN_SCORE - 1
            for move, score_change in ordered_moves:
                child = Node(root.game, root.get_score() + score_change)
                child.add_parent(root)
                child.game.push(move)
                self.alpha_beta_pruning(child, alpha, beta, multiple_moves_flag)

                max_score = max(max_score, child.get_score())

                alpha = max(alpha, max_score)

                if beta <= alpha:
                    break
            root.eval_score = max_score
        else:
            min_score = WHITE_WIN_SCORE + 1
            for move, score_change in ordered_moves:
                child = Node(root.game, root.get_score() - score_change)
                child.add_parent(root)
                child.game.push(move)
                self.alpha_beta_pruning(child, alpha, beta, multiple_moves_flag)

                min_score = min(min_score, child.get_score())

                beta = min(beta, min_score)

                if beta <= alpha:
                    break
            root.eval_score = min_score

    def get_move(self, board: chess.Board):
        root = None

        if self.cache is None:
            root = Node(board, None)
            root.eval()
            self.alpha_beta_pruning(root, BLACK_WIN_SCORE-1, WHITE_WIN_SCORE+1, True)
        else:
            root = self.cache

        next_child = None

        for child in root.children:
            if child.get_score() == root.get_score():
                next_child = child
                break

        if (root.get_score() == WHITE_WIN_SCORE or root.get_score() == BLACK_WIN_SCORE) and len(next_child.children) > 0:
            for child in next_child.children:
                if child.get_score() == root.get_score():
                    self.cache = child
                    break
        else:
            self.cache = None

        return next_child.game.peek()
