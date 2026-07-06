<<<<<<< HEAD
# Face Puzzle

A webcam-based desktop app that captures your face, slices it into a 3x3 jigsaw puzzle, and lets you solve it hands-free using hand gestures.

## Setup

1. Make sure Python 3 is installed.
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

Run the main script:
```bash
python main.py
```

Press `ESC` at any time to quit the app.

## Gestures and Controls

This app uses two distinct hand gestures for interaction. It tracks your hand using your webcam.

### 1. Point-and-Hold (Dwell Tap)
- **Action**: Extend your index finger and hold the tip over a UI button.
- **Usage**: Used to activate menu buttons (Capture, Use This, Retake, Start Puzzle, Play Again, New Photo).
- **Feedback**: A ring will fill around your fingertip. Once full (about 0.7 seconds), the button activates. Move your finger away and back to activate it again.

### 2. Pinch
- **Action**: Bring the tip of your thumb and the tip of your index finger together.
- **Usage**: Used ONLY to grab, drag, and drop puzzle pieces during gameplay.
- **Details**: The midpoint between your thumb and index finger acts as the drag point. Release the pinch to drop the piece. If you drop it near the correct slot, it snaps into place!

## Tuning Notes
If the gestures feel too sensitive or too sluggish, you can tune constants in the code:
- **Pinch Thresholds**: Adjusted in `hand_tracker.py` (`PINCH_START_THRESHOLD`, `PINCH_RELEASE_THRESHOLD`).
- **Dwell Time**: Adjusted in `ui.py` (`DWELL_TIME_SECONDS`).
- **Grid Size and Snap Tolerance**: Adjusted in `puzzle.py` (`GRID_SIZE`, `SNAP_TOLERANCE`).

## Pushing to GitHub
To push this project to a GitHub repository:
1. Initialize a git repository: `git init`
2. Add files: `git add .`
3. Commit: `git commit -m "Initial commit"`
4. Create a repository on GitHub.
5. Add the remote: `git remote add origin <your-repo-url>`
6. Push: `git push -u origin main`
=======
# _face_puzzle
>>>>>>> 9897e30dfcef26661fb368c63ac8c882eb01020d
