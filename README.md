# Gesture-Based Volume Control

A Flask-based web application that allows you to control your system volume using hand gestures. It utilizes OpenCV and MediaPipe for real-time hand tracking and gesture recognition.

## Features

- **Real-time Video Feed**: View the camera feed with gesture overlays via a web interface.
- **Hand Gesture Recognition**: Detects various hand gestures using MediaPipe.
- **Volume Control**:
  - **Adjust Volume**: Pinch thumb and index finger (distance-based) to increase or decrease volume.
  - **Mute**: Make a "Fist" gesture to mute/unmute.
- **Visual Feedback**:
  - Highlights hand landmarks and connections.
  - Displays the current detected gesture and volume level.
  - Dynamic color coding for different gestures.
- **Auto-Calibration**: Adapts to the user's hand size and distance from the camera for accurate volume control scaling.

## Supported Gestures

| Gesture | Action |
| :--- | :--- |
| **Volume Control** | **Thumb & Index** distance controls volume level (Pinch to adjust). |
| **Fist** | Toggles System **Mute**. |
| **Open Palm** | Detected as "OPEN PALM" (Idle state). |
| **Thumbs Up** | Detected as "THUMBS UP". |
| **Ok Sign** | Detected as "OK SIGN". |
| **Rock Sign** | Detected as "ROCK SIGN". |

## Prerequisites

- **Python 3.x**
- **Webcam**

## Installation

1.  **Clone the repository** :
    ```bash
    cd "Gesture-Based Volume Control"
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application**:
    ```bash
    python app.py
    ```

2.  **Access the Web Interface**:
    Open your web browser and go to: `http://127.0.0.1:5000/`

3.  **Control**:
    - Click **"Start Camera"** on the web page.
    - Show your hand to the camera.
    - Use gestures to control volume.
    - Click **"Stop Camera"** to end the session.

## Architecture

- **Backend**: Python (Flask) handles the web server and video streaming.
- **Computer Vision**: OpenCV captures frames; MediaPipe Hands processes them for landmark detection.
- **System Control**: `pyautogui` interfaces with the operating system to change volume.
- **Frontend**: HTML/JS (served by Flask) displays the video feed and control buttons.

## Troubleshooting

- **Camera not opening**: Ensure no other application is using the webcam.
- **Gestures not detected**: Improve lighting conditions and ensure your hand is fully visible in the frame.
- **Volume jumps**: Try to move your hand smoothly. The system auto-calibrates, so give it a moment to adjust to your hand range.
