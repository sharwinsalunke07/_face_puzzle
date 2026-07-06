import cv2
import time
import numpy as np
import math

def draw_rounded_rectangle(img, pt1, pt2, color, thickness, r):
    """Draws a rectangle with rounded corners."""
    x1, y1 = pt1
    x2, y2 = pt2
    
    # Corners
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness, cv2.LINE_AA)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness, cv2.LINE_AA)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness, cv2.LINE_AA)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness, cv2.LINE_AA)
    
    # Edges
    if thickness > 0:
        cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness, cv2.LINE_AA)
    
    if thickness < 0:
        cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1, cv2.LINE_AA)
        cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1, cv2.LINE_AA)

class Button:
    def __init__(self, text, x, y, w, h, dwell_time=0.7):
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.dwell_time = dwell_time
        
        self.hover_start_time = None
        self.is_fired = False

    def contains(self, px, py):
        return (self.x <= px <= self.x + self.w) and (self.y <= py <= self.y + self.h)

    def update(self, px, py):
        if px is None or py is None or not self.contains(px, py):
            self.hover_start_time = None
            self.is_fired = False
            return False
            
        if self.is_fired:
            return False
            
        if self.hover_start_time is None:
            self.hover_start_time = time.time()
            return False
            
        elapsed = time.time() - self.hover_start_time
        if elapsed >= self.dwell_time:
            self.is_fired = True
            return True
            
        return False
        
    def get_progress(self):
        if self.hover_start_time is None or self.is_fired:
            return 0.0
        elapsed = time.time() - self.hover_start_time
        return min(1.0, elapsed / self.dwell_time)

    def draw(self, frame):
        progress = self.get_progress()
        overlay = frame.copy()
        
        # Color transition while dwelling (BGR)
        color = (100, 200, 100) if self.is_fired else (180, 100, 100)
        if progress > 0 and not self.is_fired:
            color = (180 - int(80 * progress), 100 + int(100 * progress), 100)
            
        # Draw shadow
        draw_rounded_rectangle(overlay, (self.x + 6, self.y + 6), (self.x + self.w + 6, self.y + self.h + 6), (20, 20, 20), -1, 15)
        
        # Draw button box
        draw_rounded_rectangle(overlay, (self.x, self.y), (self.x + self.w, self.y + self.h), color, -1, 15)
        draw_rounded_rectangle(overlay, (self.x, self.y), (self.x + self.w, self.y + self.h), (255, 255, 255), 2, 15)
        
        # Alpha blend for glass effect
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        
        # Draw centered text (AA)
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(self.text, font, 1, 2)[0]
        tx = self.x + (self.w - text_size[0]) // 2
        ty = self.y + (self.h + text_size[1]) // 2
        cv2.putText(frame, self.text, (tx + 2, ty + 2), font, 1, (50, 50, 50), 2, cv2.LINE_AA) # Shadow
        cv2.putText(frame, self.text, (tx, ty), font, 1, (255, 255, 255), 2, cv2.LINE_AA)


def draw_dwell_ring(frame, px, py, progress):
    if progress > 0 and progress < 1.0:
        # Pulse effect
        radius = 30 + int(5 * math.sin(progress * math.pi * 4))
        angle = int(360 * progress)
        cv2.ellipse(frame, (px, py), (radius, radius), -90, 0, angle, (0, 220, 255), 5, cv2.LINE_AA)
        # Inner glow
        cv2.ellipse(frame, (px, py), (radius, radius), -90, 0, angle, (200, 255, 255), 2, cv2.LINE_AA)

def draw_cursor(frame, hand_data, mode="point"):
    if mode == "point":
        px, py = hand_data['index_tip']
        cv2.circle(frame, (px + 2, py + 2), 9, (40, 40, 40), -1, cv2.LINE_AA) # Shadow
        cv2.circle(frame, (px, py), 8, (80, 80, 255), -1, cv2.LINE_AA)
    elif mode == "pinch":
        px, py = hand_data['pinch_midpoint']
        color = (100, 255, 100) if hand_data['is_pinching'] else (240, 240, 240)
        
        cv2.circle(frame, (px + 3, py + 3), 10, (40, 40, 40), -1, cv2.LINE_AA) # Shadow
        cv2.circle(frame, (px, py), 10, color, -1, cv2.LINE_AA)
        
        if hand_data['is_pinching']:
            cv2.circle(frame, (px, py), 16, (100, 255, 100), 3, cv2.LINE_AA)

def draw_hand_landmarks(frame, hand_data):
    landmarks = hand_data.get('landmarks', [])
    if not landmarks:
        return
        
    h, w = frame.shape[:2]
    pts = []
    for lm in landmarks:
        pts.append((int(lm.x * w), int(lm.y * h)))
        
    connections = [
        (0,1), (1,2), (2,3), (3,4),       # Thumb
        (0,5), (5,6), (6,7), (7,8),       # Index
        (5,9), (9,10), (10,11), (11,12),  # Middle
        (9,13), (13,14), (14,15), (15,16),# Ring
        (13,17), (17,18), (18,19), (19,20),# Pinky
        (0,17)                            # Palm base
    ]
    
    # Draw connections
    for start_idx, end_idx in connections:
        if start_idx < len(pts) and end_idx < len(pts):
            cv2.line(frame, pts[start_idx], pts[end_idx], (255, 200, 100), 2, cv2.LINE_AA)
            
    # Draw joints
    for pt in pts:
        cv2.circle(frame, pt, 4, (100, 255, 100), -1, cv2.LINE_AA)

def draw_puzzle_board(frame, puzzle):
    board_tl_x = puzzle.board_cx - puzzle.board_size // 2
    board_tl_y = puzzle.board_cy - puzzle.board_size // 2
    
    # Draw empty slots (Glassy backdrop)
    piece_w = puzzle.board_size // puzzle.grid_size
    piece_h = puzzle.board_size // puzzle.grid_size
    
    overlay = frame.copy()
    cv2.rectangle(overlay, (board_tl_x, board_tl_y), (board_tl_x + puzzle.board_size, board_tl_y + puzzle.board_size), (40, 40, 40), -1)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
    
    for row in range(puzzle.grid_size):
        for col in range(puzzle.grid_size):
            tx = board_tl_x + col * piece_w
            ty = board_tl_y + row * piece_h
            cv2.rectangle(frame, (tx, ty), (tx + piece_w, ty + piece_h), (120, 120, 120), 1, cv2.LINE_AA)
            
    # Draw pieces
    for piece in puzzle.pieces:
        h, w = piece.image.shape[:2]
        
        y1, y2 = piece.y, piece.y + h
        x1, x2 = piece.x, piece.x + w
        
        fy1, fy2 = max(0, y1), min(frame.shape[0], y2)
        fx1, fx2 = max(0, x1), min(frame.shape[1], x2)
        
        # Add a drop shadow if it's grabbed (floating effect)
        if piece.grabbed_by_id is not None:
            shadow_offset = 8
            sy1, sy2 = fy1 + shadow_offset, fy2 + shadow_offset
            sx1, sx2 = fx1 + shadow_offset, fx2 + shadow_offset
            
            # Clip shadow to frame bounds
            scy1, scy2 = max(0, sy1), min(frame.shape[0], sy2)
            scx1, scx2 = max(0, sx1), min(frame.shape[1], sx2)
            
            if scy1 < scy2 and scx1 < scx2:
                roi = frame[scy1:scy2, scx1:scx2]
                black_rect = np.zeros_like(roi)
                frame[scy1:scy2, scx1:scx2] = cv2.addWeighted(roi, 0.5, black_rect, 0.5, 0)
        
        if fy1 < fy2 and fx1 < fx2:
            py1, py2 = fy1 - y1, fy2 - y1
            px1, px2 = fx1 - x1, fx2 - x1
            frame[fy1:fy2, fx1:fx2] = piece.image[py1:py2, px1:px2]
            
        if piece.is_locked:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (50, 255, 50), 3, cv2.LINE_AA)
        elif piece.grabbed_by_id is not None:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 230, 255), 4, cv2.LINE_AA)
        else:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1, cv2.LINE_AA)

def draw_hud(frame, puzzle):
    time_elapsed = puzzle.get_time_elapsed()
    locked = puzzle.get_locked_count()
    total = puzzle.grid_size * puzzle.grid_size
    
    text = f"Pieces: {locked}/{total}  Time: {time_elapsed:.1f}s"
    # Shadow text for readability
    cv2.putText(frame, text, (22, 42), cv2.FONT_HERSHEY_SIMPLEX, 1, (30, 30, 30), 2, cv2.LINE_AA)
    cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 100), 2, cv2.LINE_AA)
