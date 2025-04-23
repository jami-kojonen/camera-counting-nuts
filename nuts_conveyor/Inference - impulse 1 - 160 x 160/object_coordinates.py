import cv2
import numpy as np
import math
import tensorflow as tf
import uuid
import time
import os
import csv
from datetime import datetime

# Load TFLite model and labels
here = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(here, "trained.tflite")
labels_path = os.path.join(here, "labels.txt")

interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()


with open(labels_path, "r") as f:
    labels = [line.strip() for line in f.readlines()]

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
out_scale, out_zero_point = output_details[0]['quantization']

# Parameters
max_tracking_distance = 50
max_disappeared_frames = 10
MAX_TRACKED_OBJECTS = 10  # Limit of tracked objects

nut_classes = ["m6", "m8", "m10", "m12"]
colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255)]

#CSV logging
log_filename = os.path.join(here, f"nut_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
with open(log_filename, mode='w', newline='') as log_file:
    writer = csv.writer(log_file)
    writer.writerow(["Timestamp", "Nut Type", "Camera X", "Camera Y", "Robot X", "Robot Y"])

class TrackedObject:
    def __init__(self, nut_type, position):
        self.id = str(uuid.uuid4())[:8]
        self.nut_type = nut_type
        self.position = position
        self.prev_position = position
        self.last_seen = time.time()

tracked_nuts = []

def euclidean_distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def camera_to_robot_coords(camera_coords, frame_width=640, frame_height=480):
    x, y = camera_coords
    robot_x = np.interp(x, [0, frame_width], [-120, 320])
    robot_y = np.interp(y, [0, frame_height], [320, -300])
    return (int(robot_x), int(robot_y))

def match_or_create(nut_label, position):
    global tracked_nuts

    robot_pos = camera_to_robot_coords(position)
    print(f"[INFO] Detected '{nut_label}' at Camera: {position}, Robot: {robot_pos}")

    matched = None
    for nut in tracked_nuts:
        if nut.nut_type == nut_label and euclidean_distance(nut.position, position) < max_tracking_distance:
            matched = nut
            break

    if matched:
        matched.prev_position = matched.position
        matched.position = position
        matched.last_seen = time.time()
        return matched
    else:
        new_nut = TrackedObject(nut_label, position)
        tracked_nuts.append(new_nut)

        if len(tracked_nuts) > MAX_TRACKED_OBJECTS:
            tracked_nuts.sort(key=lambda x: x.last_seen)
            tracked_nuts = tracked_nuts[-MAX_TRACKED_OBJECTS:]

        return new_nut

def run_tflite_inference(frame):
    input_data = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    input_data = cv2.resize(input_data, (160, 160))
    input_data = input_data.astype(np.float32)
    input_data = (input_data - 127.5) / 127.5
    input_data = np.round(input_data * 127.5).astype(np.int8)
    input_data = np.expand_dims(input_data, axis=-1)
    input_data = np.expand_dims(input_data, axis=0)

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data

# Initialize camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

object_detector = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=40)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    height, width, _ = frame.shape

    # Motion detection
    mask = object_detector.apply(frame)
    _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    moving_objects = {}

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 100:
            x, y, w, h = cv2.boundingRect(cnt)
            center = (int(x + w/2), int(y + h/2))
            robot_coords = camera_to_robot_coords(center, width, height)

            moving_objects[center] = {
                'cam_coords': center,
                'robot_coords': robot_coords,
                'size': (w, h)
            }

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            coord_text = f"Coordinates: {robot_coords}"
            cv2.putText(frame, coord_text, (center[0] + 15, center[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            roi = frame[y:y+h, x:x+w]
            output_data = run_tflite_inference(roi)

            for i, output in enumerate(output_data[0]):
                value = np.array(output).flatten()[0]
                if value > 0.5:
                    label = labels[i] if i < len(labels) else f"Class {i}"
                    if label in nut_classes:
                        tracked = match_or_create(label, center)

                        cv2.circle(frame, center, 12, colors[nut_classes.index(label)], -1)
                        nut_text = f"{label} {robot_coords}"
                        cv2.putText(frame, nut_text, (center[0] + 15, center[1] + 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                        with open(log_filename, mode='a', newline='') as log_file:
                            writer = csv.writer(log_file)
                            writer.writerow([
                                datetime.now().isoformat(timespec='seconds'),
                                label,
                                center[0], center[1],
                                robot_coords[0], robot_coords[1]
                            ])

   
    current_time = time.time()
    tracked_nuts = [t for t in tracked_nuts if current_time - t.last_seen <= max_disappeared_frames / 30.0]

    # Display moving object count
    cv2.putText(frame, f"Moving objects: {len(moving_objects)}", (width - 200, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
