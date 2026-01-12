from flask import Flask, render_template, Response, jsonify, request
import cv2
import mediapipe as mp
import math
import numpy as np
import pyautogui
import time
import os

app = Flask(__name__)

camera_active = False
cap = None
current_vol = 50 
current_gesture = "NONE"

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

calibrated = False
min_dist = None
max_dist = None
calibration_samples = []
calibration_frames = 60

last_gesture_time = 0
gesture_cooldown = 0.5 

TIP = [4, 8, 12, 16, 20]
PIP = [3, 6, 10, 14, 18]
FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

def get_camera():
    global cap
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(4, 480)
    return cap

def calc_distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def get_finger_states(landmarks):
    states = []
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    if thumb_tip.x < thumb_ip.x:
        states.append(True)
    else:
        states.append(False)
    
    for tip_idx, pip_idx in zip(TIP[1:], PIP[1:]):
        tip_y = landmarks[tip_idx].y
        pip_y = landmarks[pip_idx].y
        states.append(tip_y < pip_y)
    
    return states

def get_finger_distances(landmarks, w, h):
    coords = {}
    for name, tip_id in zip(FINGER_NAMES, TIP):
        x = int(landmarks[tip_id].x * w)
        y = int(landmarks[tip_id].y * h)
        coords[name] = (x, y)
    
    distances = {}
    for finger in FINGER_NAMES[1:]:
        d = calc_distance(coords["Thumb"], coords[finger])
        distances[f"Thumb-{finger}"] = d
    
    return distances, coords

def classify_gesture(states, distances):
    thumb, index, middle, ring, pinky = states
    
    if not any(states):
        return "FIST", (0, 0, 255)
    
    if all(states):
        return "OPEN PALM", (0, 255, 255)
    
    if thumb and not index and not middle and not ring and not pinky:
        return "THUMBS UP", (255, 165, 0)
    
    if distances["Thumb-Index"] < 35 and middle and ring and pinky:
        return "OK SIGN", (0, 200, 100)
    
    if index and pinky and not middle and not ring:
        return "ROCK SIGN", (128, 0, 255)
    
    if distances["Thumb-Index"] < 250:
        return "VOLUME CONTROL", (0, 255, 0)
    
    return "UNKNOWN", (128, 128, 128)

def calibrate_distance(dist):
    global calibrated, min_dist, max_dist, calibration_samples
    calibration_samples.append(dist)
    if len(calibration_samples) >= calibration_frames:
        sorted_samples = sorted(calibration_samples)
        min_dist = sorted_samples[5]
        max_dist = sorted_samples[-5]
        if max_dist - min_dist < 50:
            max_dist = min_dist + 150
        calibrated = True

def generate_frames():
    global camera_active, cap, calibrated, min_dist, max_dist
    global last_gesture_time, calibration_samples, current_vol, current_gesture
    
    last_vol_change_time = 0
    
    while True:
        if not camera_active:
            break
            
        success, frame = get_camera().read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        h, w, _ = frame.shape
        current_gesture = "NO HAND"
        gesture_color = (128, 128, 128)
        current_time = time.time()
        
        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                lm = hand_lms.landmark
                finger_states = get_finger_states(lm)
                distances, coords = get_finger_distances(lm, w, h)
                thumb_pos = coords["Thumb"]
                index_pos = coords["Index"]
                thumb_index_dist = distances["Thumb-Index"]
                
                current_gesture, gesture_color = classify_gesture(finger_states, distances)
                
                if not calibrated:
                    calibrate_distance(thumb_index_dist)
                else:
                    if thumb_index_dist < min_dist: min_dist = thumb_index_dist
                    if thumb_index_dist > max_dist: max_dist = thumb_index_dist
                
                if current_time - last_gesture_time > gesture_cooldown:
                    if current_gesture == "FIST":
                        pyautogui.press('volumemute')
                        last_gesture_time = current_time
                
                if current_gesture == "VOLUME CONTROL" and calibrated:
                    if current_time - last_vol_change_time > 0.08:
                        mid_point = (min_dist + max_dist) / 2
                        if thumb_index_dist > mid_point + 15:
                            pyautogui.press('volumeup')
                            current_vol = min(100, current_vol + 2)
                        elif thumb_index_dist < mid_point - 15:
                            pyautogui.press('volumedown')
                            current_vol = max(0, current_vol - 2)
                        last_vol_change_time = current_time
                    cv2.line(frame, thumb_pos, index_pos, gesture_color, 3)
                
                mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)

        cv2.rectangle(frame, (30, 100), (70, 400), (50, 50, 50), -1)
        vol_bar = int(np.interp(current_vol, [0, 100], [400, 100]))
        cv2.rectangle(frame, (30, vol_bar), (70, 400), (0, 255, 0), -1)
        cv2.putText(frame, f"GESTURE: {current_gesture}", (100, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, gesture_color, 3)

        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def get_status():
    return jsonify({
        "volume": int(current_vol),
        "gesture": current_gesture
    })

@app.route('/video_feed')
def video_feed():
    if camera_active:
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return Response(status=204)

@app.route('/control_camera', methods=['POST'])
def control_camera():
    global camera_active, cap, calibrated, calibration_samples
    action = request.json.get('action')
    if action == 'start':
        camera_active = True
        calibrated = False
        calibration_samples = []
        get_camera()
    elif action == 'stop':
        camera_active = False
        if cap:
            cap.release()
            cap = None
    return jsonify({"status": "success", "active": camera_active})

if __name__ == "__main__":
    app.run(debug=True)