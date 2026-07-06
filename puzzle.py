import cv2
import numpy as np
import random
import time
import math

class PuzzlePiece:
    def __init__(self, image, correct_x, correct_y):
        self.image = image
        self.correct_x = correct_x
        self.correct_y = correct_y
        self.x = 0
        self.y = 0
        self.grabbed_by_id = None
        self.is_locked = False
        
class Puzzle:
    def __init__(self, grid_size=3, snap_tolerance=45, board_size=450):
        self.grid_size = grid_size
        self.snap_tolerance = snap_tolerance
        self.board_size = board_size
        
        self.pieces = []
        self.is_solved = False
        self.start_time = None
        self.end_time = None
        
        self.board_cx = 0
        self.board_cy = 0

    def start(self, image, window_width, window_height):
        self.board_cx = window_width // 2
        self.board_cy = window_height // 2
        
        image = cv2.resize(image, (self.board_size, self.board_size))
        
        h, w = image.shape[:2]
        piece_h = h // self.grid_size
        piece_w = w // self.grid_size
        
        self.pieces = []
        board_tl_x = self.board_cx - self.board_size // 2
        board_tl_y = self.board_cy - self.board_size // 2
        
        all_initial_pieces = []
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                y = row * piece_h
                x = col * piece_w
                piece_img = image[y:y+piece_h, x:x+piece_w]
                correct_x = board_tl_x + x
                correct_y = board_tl_y + y
                piece = PuzzlePiece(piece_img, correct_x, correct_y)
                all_initial_pieces.append(piece)
                
        random.shuffle(all_initial_pieces)
        
        # Distribute pieces to left and right sides of the board
        left_spawn_x_min = 50
        left_spawn_x_max = max(50, board_tl_x - piece_w - 50)
        right_spawn_x_min = board_tl_x + self.board_size + 50
        right_spawn_x_max = window_width - piece_w - 50
        
        spawn_y_min = 100
        spawn_y_max = window_height - piece_h - 100
        
        for i, piece in enumerate(all_initial_pieces):
            if i % 2 == 0 and left_spawn_x_max > left_spawn_x_min:
                piece.x = random.randint(left_spawn_x_min, left_spawn_x_max)
            elif right_spawn_x_max > right_spawn_x_min:
                piece.x = random.randint(right_spawn_x_min, right_spawn_x_max)
            else:
                piece.x = random.randint(0, window_width - piece_w)
                
            piece.y = random.randint(spawn_y_min, spawn_y_max)
            self.pieces.append(piece)

        self.is_solved = False
        self.start_time = time.time()
        self.end_time = None

    def grab_piece(self, px, py, hand_id):
        if self.is_solved:
            return
            
        for piece in reversed(self.pieces):
            if not piece.is_locked and piece.grabbed_by_id is None:
                h, w = piece.image.shape[:2]
                if piece.x <= px <= piece.x + w and piece.y <= py <= piece.y + h:
                    piece.grabbed_by_id = hand_id
                    # Move grabbed piece to the end (draw on top)
                    self.pieces.remove(piece)
                    self.pieces.append(piece)
                    break

    def drag_piece(self, px, py, hand_id):
        for piece in self.pieces:
            if piece.grabbed_by_id == hand_id:
                h, w = piece.image.shape[:2]
                piece.x = px - w // 2
                piece.y = py - h // 2
                break

    def drop_piece(self, hand_id):
        for piece in self.pieces:
            if piece.grabbed_by_id == hand_id:
                piece.grabbed_by_id = None
                
                dist = math.hypot(piece.x - piece.correct_x, piece.y - piece.correct_y)
                if dist < self.snap_tolerance:
                    piece.x = piece.correct_x
                    piece.y = piece.correct_y
                    piece.is_locked = True
                    self.check_win()
                break

    def get_locked_count(self):
        return sum(1 for p in self.pieces if p.is_locked)

    def check_win(self):
        if self.get_locked_count() == len(self.pieces):
            self.is_solved = True
            self.end_time = time.time()

    def get_score(self):
        return self.get_locked_count()

    def get_time_elapsed(self):
        if self.start_time is None:
            return 0.0
        if self.end_time is not None:
            return self.end_time - self.start_time
        return time.time() - self.start_time
