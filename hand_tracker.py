import cv2
import mediapipe as mp
import math
import os
import time

class HandTracker:
    def __init__(self, pinch_start_threshold=0.06, pinch_release_threshold=0.09):
        self.pinch_start_threshold = pinch_start_threshold
        self.pinch_release_threshold = pinch_release_threshold
        
        self.alpha = 0.45  # EMA smoothing factor
        
        # State for multi-hand tracking across frames
        self.active_hands = {} # id -> dict of state
        self.next_hand_id = 0
        self.max_dist_for_match = 150 # pixels
        self.hand_timeout = 0.5 # seconds
        
        model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"MediaPipe model missing at {model_path}. Please download it.")
            
        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.landmarker = HandLandmarker.create_from_options(options)

    def process_frame(self, frame):
        h, w, _ = frame.shape
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = self.landmarker.detect(mp_image)
        
        now = time.time()
        
        # Cleanup old hands
        dead_ids = [hid for hid, state in self.active_hands.items() if now - state['last_seen'] > self.hand_timeout]
        for hid in dead_ids:
            del self.active_hands[hid]
        
        hands_data = []
        
        if result.hand_landmarks:
            for hand_landmarks in result.hand_landmarks:
                index_tip_lm = hand_landmarks[8]
                thumb_tip_lm = hand_landmarks[4]
                
                index_tip = (int(index_tip_lm.x * w), int(index_tip_lm.y * h))
                thumb_tip = (int(thumb_tip_lm.x * w), int(thumb_tip_lm.y * h))
                
                midpoint = (
                    (index_tip[0] + thumb_tip[0]) // 2,
                    (index_tip[1] + thumb_tip[1]) // 2
                )
                
                dx = index_tip_lm.x - thumb_tip_lm.x
                dy = index_tip_lm.y - thumb_tip_lm.y
                dist = math.hypot(dx, dy)
                
                # Match to existing hand ID
                best_id = None
                best_dist = float('inf')
                
                for hid, state in self.active_hands.items():
                    if state['updated_this_frame']:
                        continue
                    # Distance from EMA midpoint to new midpoint
                    dist_to_prev = math.hypot(midpoint[0] - state['ema_pinch_mid'][0], midpoint[1] - state['ema_pinch_mid'][1])
                    if dist_to_prev < best_dist and dist_to_prev < self.max_dist_for_match:
                        best_dist = dist_to_prev
                        best_id = hid
                        
                if best_id is None:
                    best_id = self.next_hand_id
                    self.next_hand_id += 1
                    self.active_hands[best_id] = {
                        'ema_index_tip': index_tip,
                        'ema_pinch_mid': midpoint,
                        'was_pinching': False,
                        'last_seen': now,
                        'updated_this_frame': True
                    }
                else:
                    self.active_hands[best_id]['updated_this_frame'] = True
                    self.active_hands[best_id]['last_seen'] = now
                    
                state = self.active_hands[best_id]
                
                # Update EMA
                state['ema_index_tip'] = (
                    int(self.alpha * index_tip[0] + (1 - self.alpha) * state['ema_index_tip'][0]),
                    int(self.alpha * index_tip[1] + (1 - self.alpha) * state['ema_index_tip'][1])
                )
                state['ema_pinch_mid'] = (
                    int(self.alpha * midpoint[0] + (1 - self.alpha) * state['ema_pinch_mid'][0]),
                    int(self.alpha * midpoint[1] + (1 - self.alpha) * state['ema_pinch_mid'][1])
                )
                
                is_pinching = False
                if dist < self.pinch_start_threshold:
                    is_pinching = True
                elif dist > self.pinch_release_threshold:
                    is_pinching = False
                else:
                    is_pinching = state['was_pinching']
                    
                state['was_pinching'] = is_pinching
                
                hands_data.append({
                    'id': best_id,
                    'index_tip': state['ema_index_tip'],
                    'pinch_midpoint': state['ema_pinch_mid'],
                    'is_pinching': is_pinching,
                    'landmarks': hand_landmarks
                })
                
        # Reset updated_this_frame flag
        for hid in self.active_hands:
            self.active_hands[hid]['updated_this_frame'] = False
            
        return hands_data

    def close(self):
        if self.landmarker:
            self.landmarker.close()
