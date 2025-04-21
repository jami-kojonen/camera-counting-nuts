import queue
import threading
import cv2
import numpy as np
import time
import uuid
import os
import tensorflow as tf
from gui.GUI_module import GUI

# Initialize a queue for communication between threads
gui_queue = queue.Queue()

# Parameters
min_confidence = 0.1
min_visible_area = 5
max_tracking_distance = 50
max_disappeared_frames = 10
line_y = 600
nut_classes = ["m6", "m8", "m10", "m12"]
nut_count = {nut: 0 for nut in nut_classes}  # Total nut count
colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255)]

tracked_nuts = []

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

class TrackedObject:
    def __init__(self, nut_type, position):
        self.id = str(uuid.uuid4())[:8]
        self.nut_type = nut_type
        self.position = position
        self.prev_position = position
        self.last_seen = time.time()
        self.counted = False

# Euclidean distance function to match or create new nut objects
def euclidean(p1, p2):
    return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

# Function to match or create new tracked nut objects
def match_or_create(nut_label, position):
    for nut in tracked_nuts:
        if nut.nut_type == nut_label and euclidean(nut.position, position) < max_tracking_distance:
            nut.prev_position = nut.position
            nut.position = position
            nut.last_seen = time.time()
            return nut
    new_nut = TrackedObject(nut_label, position)
    tracked_nuts.append(new_nut)
    return new_nut

# Preprocess input frame for inference
def preprocess_frame(frame):
    resized = cv2.resize(frame, (160, 160))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    if input_details[0]['dtype'] == np.int8:
        normalized = (gray.astype(np.float32) - 127.5) / 127.5
        input_frame = np.round(normalized * 127).astype(np.int8)
    else:
        input_frame = gray.astype(np.float32) / 255.0
    input_frame = np.expand_dims(input_frame, axis=-1)
    input_frame = np.expand_dims(input_frame, axis=0)
    return input_frame

# Camera processing in a separate thread
def run_camera(gui, gui_queue, stop_event):
    # Initialize camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            break

        # Create dictionary to keep track of visible nuts in this frame
        visible_now = {nut: 0 for nut in nut_classes}
        
        # Preprocess the frame for inference
        input_frame = preprocess_frame(frame)
        interpreter.set_tensor(input_details[0]['index'], input_frame)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])
        real_output = out_scale * (output.astype(np.float32) - out_zero_point)
        real_output = real_output[0]

        # Scales to map model output to frame dimensions
        model_w, model_h = 20, 20
        x_scale = frame.shape[1] / model_w
        y_scale = frame.shape[0] / model_h

        for idx, nut_label in enumerate(nut_classes):
            channel_map = real_output[:, :, idx + 1]
            conf_mask = channel_map > min_confidence
            visible_area = np.sum(conf_mask)

            if visible_area >= min_visible_area:
                row, col = np.unravel_index(np.argmax(channel_map), channel_map.shape)
                x, y = int(col * x_scale), int(row * y_scale)

                tracked = match_or_create(nut_label, (x, y))
                visible_now[nut_label] += 1

                # Check if the nut has crossed the counting line and hasn't been counted yet
                if not tracked.counted and tracked.prev_position[1] < line_y <= tracked.position[1]:
                    nut_count[nut_label] += 1
                    tracked.counted = True

                cv2.circle(frame, (x, y), 12, colors[idx], -1)
                cv2.putText(frame, f"{nut_label.upper()} #{tracked.id}", (x + 15, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[idx], 2)

        current_time = time.time()
        tracked_nuts[:] = [nut for nut in tracked_nuts if current_time - nut.last_seen <= max_disappeared_frames / 30.0]

        cv2.line(frame, (0, line_y), (frame.shape[1], line_y), (0, 0, 255), 2)
        cv2.putText(frame, "Counting Line", (10, line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Put the current and total counts in the queue
        gui_queue.put((visible_now, nut_count))

        cv2.imshow("Nut Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()  # Signal the camera thread to stop

    cap.release()
    cv2.destroyAllWindows()

# Function to update the GUI with data from the queue
def update_gui_from_queue(gui, gui_queue):
    try:
        # Retrieve the data from the queue
        visible_now, total = gui_queue.get_nowait()
        current = [visible_now[n] for n in nut_classes]
        total_values = [total[n] for n in nut_classes]
        gui.update_counts(current + [sum(current)], total_values + [sum(total_values)])
    except queue.Empty:
        pass  # No new data in the queue yet

# Main execution loop
if __name__ == "__main__":
    gui = GUI(current_values=[0, 0, 0, 0, 0], total_values=[0, 0, 0, 0, 0])

    # Flag to indicate when to stop the GUI loop
    running = True
    stop_event = threading.Event()  # Event to signal stopping the camera thread

    def stop_gui():
        global running
        running = False
        stop_event.set()  # Signal the camera thread to stop
        gui.quit()

    # Start the camera thread as soon as the program runs (before reset)
    cam_thread = threading.Thread(target=run_camera, args=(gui, gui_queue, stop_event), daemon=True)
    cam_thread.start()

    # GUI must be run on main thread
    while running:
        # Update the GUI's state only if the window is still open
        if gui.winfo_exists():
            gui.update()

            # Periodically check for new data from the camera thread
            update_gui_from_queue(gui, gui_queue)

            # Allow Tkinter to refresh and process events
            gui.after(100, lambda: None)

    # Clean up when quitting
    cv2.destroyAllWindows()
