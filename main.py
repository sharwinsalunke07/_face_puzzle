import cv2
import time
import math

from hand_tracker import HandTracker
from face_capture import capture_face
from puzzle import Puzzle
import ui

class FacePuzzleApp:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        self.hand_tracker = HandTracker()
        self.puzzle = Puzzle(grid_size=3, snap_tolerance=45, board_size=450)
        
        self.state = "CAPTURE_LIVE"
        self.face_image = None
        self.frozen_frame = None
        
        self.btn_capture = ui.Button("Capture", 50, 50, 200, 80)
        self.btn_use_this = ui.Button("Use This", 50, 50, 200, 80)
        self.btn_retake = ui.Button("Retake", 300, 50, 200, 80)
        self.btn_start = ui.Button("Start Puzzle", 50, 50, 250, 80)
        self.btn_play_again = ui.Button("Play Again", 50, 50, 250, 80)
        self.btn_new_photo = ui.Button("New Photo", 350, 50, 250, 80)
        
        self.msg_timer = 0
        self.msg_text = ""
        self.countdown_start_time = 0
        
        # Track pinch state per hand_id
        self.prev_pinching = {}
        
        cv2.namedWindow("Face Puzzle", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Face Puzzle", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def show_msg(self, text, duration_frames=60):
        self.msg_text = text
        self.msg_timer = duration_frames

    def run(self):
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                break
                
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hands_data = self.hand_tracker.process_frame(rgb_frame)
            
            # Primary hand for UI interactions
            primary_hand = hands_data[0] if hands_data else None
            
            px, py = None, None
            if primary_hand:
                if self.state == "PLAYING":
                    px, py = primary_hand['pinch_midpoint']
                else:
                    px, py = primary_hand['index_tip']

            # Background rendering strategy
            # Only use frozen frame during CAPTURE_PREVIEW. Let the rest be live.
            if self.state in ["CAPTURE_PREVIEW"] and self.frozen_frame is not None:
                display_frame = self.frozen_frame.copy()
            else:
                display_frame = frame.copy()
            
            for hand in hands_data:
                ui.draw_hand_landmarks(display_frame, hand)
                
            # STATE MACHINE
            if self.state == "CAPTURE_LIVE":
                self.btn_capture.draw(display_frame)
                if primary_hand:
                    ui.draw_cursor(display_frame, primary_hand, mode="point")
                    progress = self.btn_capture.get_progress()
                    ui.draw_dwell_ring(display_frame, px, py, progress)
                    
                    if self.btn_capture.update(px, py):
                        self.state = "CAPTURE_COUNTDOWN"
                        self.countdown_start_time = time.time()
                else:
                    self.btn_capture.update(None, None)
                    
            elif self.state == "CAPTURE_COUNTDOWN":
                elapsed = time.time() - self.countdown_start_time
                remaining = 5.0 - elapsed
                
                if remaining <= 0:
                    self.frozen_frame = frame.copy()
                    self.state = "CAPTURE_PREVIEW"
                    self.btn_use_this.update(None, None)
                    self.btn_retake.update(None, None)
                else:
                    # Draw massive countdown
                    text = str(math.ceil(remaining))
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    text_size = cv2.getTextSize(text, font, 7, 12)[0]
                    
                    # Shadow
                    cv2.putText(display_frame, text, (w//2 - text_size[0]//2 + 5, h//2 + text_size[1]//2 + 5), font, 7, (30, 30, 30), 12, cv2.LINE_AA)
                    # Text
                    cv2.putText(display_frame, text, (w//2 - text_size[0]//2, h//2 + text_size[1]//2), font, 7, (100, 100, 255), 12, cv2.LINE_AA)
                    
                    if primary_hand:
                        ui.draw_cursor(display_frame, primary_hand, mode="point")
                        
            elif self.state == "CAPTURE_PREVIEW":
                self.btn_use_this.draw(display_frame)
                self.btn_retake.draw(display_frame)
                
                if primary_hand:
                    ui.draw_cursor(display_frame, primary_hand, mode="point")
                    prog = max(self.btn_use_this.get_progress(), self.btn_retake.get_progress())
                    ui.draw_dwell_ring(display_frame, px, py, prog)
                    
                    if self.btn_use_this.update(px, py):
                        cropped = capture_face(self.frozen_frame)
                        if cropped is not None:
                            self.face_image = cropped
                            self.state = "READY"
                        else:
                            self.show_msg("No face detected! Retake.", 90)
                            self.btn_use_this.update(None, None)
                    elif self.btn_retake.update(px, py):
                        self.state = "CAPTURE_LIVE"
                else:
                    self.btn_use_this.update(None, None)
                    self.btn_retake.update(None, None)
                    
            elif self.state == "READY":
                if self.face_image is not None:
                    thumb = cv2.resize(self.face_image, (150, 150))
                    display_frame[20:170, w-170:w-20] = thumb
                    cv2.rectangle(display_frame, (w-170, 20), (w-20, 170), (255, 255, 255), 2, cv2.LINE_AA)
                    
                self.btn_start.draw(display_frame)
                
                if primary_hand:
                    ui.draw_cursor(display_frame, primary_hand, mode="point")
                    ui.draw_dwell_ring(display_frame, px, py, self.btn_start.get_progress())
                    
                    if self.btn_start.update(px, py):
                        self.puzzle.start(self.face_image, w, h)
                        self.state = "PLAYING"
                else:
                    self.btn_start.update(None, None)
                    
            elif self.state == "PLAYING":
                current_hand_ids = set()
                
                for hand in hands_data:
                    hid = hand['id']
                    current_hand_ids.add(hid)
                    
                    hx, hy = hand['pinch_midpoint']
                    is_pinching = hand['is_pinching']
                    prev_pinch = self.prev_pinching.get(hid, False)
                    
                    if is_pinching and not prev_pinch:
                        self.puzzle.grab_piece(hx, hy, hid)
                    elif is_pinching:
                        self.puzzle.drag_piece(hx, hy, hid)
                    elif not is_pinching and prev_pinch:
                        self.puzzle.drop_piece(hid)
                        
                    self.prev_pinching[hid] = is_pinching
                    
                # Drop pieces for hands that disappeared
                missing_ids = set(self.prev_pinching.keys()) - current_hand_ids
                for hid in missing_ids:
                    if self.prev_pinching[hid]:
                        self.puzzle.drop_piece(hid)
                    del self.prev_pinching[hid]
                
                ui.draw_puzzle_board(display_frame, self.puzzle)
                ui.draw_hud(display_frame, self.puzzle)
                
                # Draw cursor last so it overlays pieces
                for hand in hands_data:
                    ui.draw_cursor(display_frame, hand, mode="pinch")
                
                if self.puzzle.is_solved:
                    self.state = "SOLVED"
                    self.btn_play_again.update(None, None)
                    self.btn_new_photo.update(None, None)
                    # Drop everything on solve
                    for hid in list(self.prev_pinching.keys()):
                        self.puzzle.drop_piece(hid)
                        del self.prev_pinching[hid]
                    
            elif self.state == "SOLVED":
                score = self.puzzle.get_score()
                time_taken = self.puzzle.get_time_elapsed()
                
                font = cv2.FONT_HERSHEY_SIMPLEX
                
                # Glassy backdrop for score
                overlay = display_frame.copy()
                ui.draw_rounded_rectangle(overlay, (w//2 - 200, h//2 - 150), (w//2 + 200, h//2 + 80), (30, 30, 30), -1, 20)
                cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0, display_frame)
                
                cv2.putText(display_frame, "Puzzle Solved!", (w//2 - 150, h//2 - 80), font, 1.2, (100, 255, 100), 3, cv2.LINE_AA)
                cv2.putText(display_frame, f"Score: {score}/10", (w//2 - 150, h//2 - 20), font, 1.2, (255, 200, 100), 3, cv2.LINE_AA)
                cv2.putText(display_frame, f"Time: {time_taken:.1f}s", (w//2 - 150, h//2 + 40), font, 1.2, (255, 200, 100), 3, cv2.LINE_AA)
                
                self.btn_play_again.draw(display_frame)
                self.btn_new_photo.draw(display_frame)
                
                if primary_hand:
                    ui.draw_cursor(display_frame, primary_hand, mode="point")
                    prog = max(self.btn_play_again.get_progress(), self.btn_new_photo.get_progress())
                    ui.draw_dwell_ring(display_frame, px, py, prog)
                    
                    if self.btn_play_again.update(px, py):
                        self.puzzle.start(self.face_image, w, h)
                        self.state = "PLAYING"
                    elif self.btn_new_photo.update(px, py):
                        self.state = "CAPTURE_LIVE"
                else:
                    self.btn_play_again.update(None, None)
                    self.btn_new_photo.update(None, None)

            if self.msg_timer > 0:
                text_size = cv2.getTextSize(self.msg_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                cv2.putText(display_frame, self.msg_text, (w//2 - text_size[0]//2 + 2, h - 48), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (30, 30, 30), 2, cv2.LINE_AA)
                cv2.putText(display_frame, self.msg_text, (w//2 - text_size[0]//2, h - 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 255), 2, cv2.LINE_AA)
                self.msg_timer -= 1

            cv2.imshow("Face Puzzle", display_frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break
                
        self.cap.release()
        self.hand_tracker.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = FacePuzzleApp()
    app.run()
