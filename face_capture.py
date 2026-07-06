import cv2
import os

# Locate the Haar cascade file provided by opencv-python
cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
face_cascade = cv2.CascadeClassifier(cascade_path)

def capture_face(frame, margin_ratio=0.3):
    """
    Takes a BGR frame (from cv2). Returns a cropped square image of the largest face,
    or None if no face is found.
    margin_ratio adds context around the face so it's not just a tight crop of features.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray, 
        scaleFactor=1.1, 
        minNeighbors=5, 
        minSize=(100, 100)
    )
    
    if len(faces) == 0:
        return None
        
    # Find the largest face by area (w * h)
    largest_face = max(faces, key=lambda f: f[2] * f[3])
    x, y, w, h = largest_face
    
    # Calculate center of the detected face
    cx = x + w // 2
    cy = y + h // 2
    
    # Desired square side length with margin
    side = int(max(w, h) * (1 + margin_ratio * 2))
    half_side = side // 2
    
    # Calculate crop coordinates, bounded by frame dimensions
    y1 = max(0, cy - half_side)
    y2 = min(frame.shape[0], cy + half_side)
    x1 = max(0, cx - half_side)
    x2 = min(frame.shape[1], cx + half_side)
    
    # If the crop hit a boundary, it might not be square anymore. 
    # Force it to be a perfect square by shrinking the larger dimension.
    cropped = frame[y1:y2, x1:x2]
    ch, cw = cropped.shape[:2]
    if ch != cw:
        min_dim = min(ch, cw)
        # Recenter the crop
        ccx = cw // 2
        ccy = ch // 2
        cropped = cropped[
            ccy - min_dim//2 : ccy + min_dim//2,
            ccx - min_dim//2 : ccx + min_dim//2
        ]
        
    return cropped
