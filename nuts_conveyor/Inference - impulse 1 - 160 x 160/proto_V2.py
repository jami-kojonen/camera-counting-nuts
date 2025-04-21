import cv2
import numpy as np
import tensorflow as tf
import uuid
import time
import threading
import os
import sys



from gui.GUI_module import GUI

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
min_confidence = 0.1
min_visible_area = 5
max_tracking_distance = 50
max_disappeared_frames = 10
line_y = 600

colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255)]
nut_classes = ["m6", "m8", "m10", "m12"]
# Create a dictionary to keep track of the total nuts and their counts
# The nut counts are initialized to 0
nut_count = {nut: 0 for nut in nut_classes}
tracked_nuts = []

class TrackedObject:
    def __init__(self, nut_type, position):
        self.id = str(uuid.uuid4())[:8]
        self.nut_type = nut_type
        self.position = position
        self.prev_position = position
        self.last_seen = time.time()
        self.counted = False

def euclidean(p1, p2):
    return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def match_or_create(nut_label, position):
    # Check if the nut is already being tracked and if it's within the tracking distance
    # in that case update its position and last seen time
    # and return the tracked nut
    # otherwise create a new tracked nut and return it

    for nut in tracked_nuts:
        if nut.nut_type == nut_label and euclidean(nut.position, position) < max_tracking_distance: 
            nut.prev_position = nut.position
            nut.position = position
            nut.last_seen = time.time()
            return nut
    new_nut = TrackedObject(nut_label, position)
    tracked_nuts.append(new_nut)
    return new_nut

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

def run_camera(gui):
    # Initialize the camera
    # Change the camera index if needed (Usually 0 for built-in, 1 for external)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Create dictionary to keep track of visible nuts
        # and their counts in the current frame

        visible_now = {nut: 0 for nut in nut_classes}
        input_frame = preprocess_frame(frame)

        interpreter.set_tensor(input_details[0]['index'], input_frame)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])
        real_output = out_scale * (output.astype(np.float32) - out_zero_point)
        real_output = real_output[0]

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
                # Then count it and mark it as counted
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

        # Update the GUI with the current and total counts
        # The current counts are the number of visible nuts in the current frame
        # The total counts are the total number of nuts counted which have crossed the counting line so far
        # The update_counts method takes two lists of length 5 as arguments
        # We need to access the values from the visible_now and nut_count dictionaries to pass them to the method
        current = [visible_now[n] for n in nut_classes]
        total = [nut_count[n] for n in nut_classes]
        gui.update_counts(current + [sum(current)], total + [sum(total)])
        
        # Check if the reset button was pressed
            # Reset the counts in the GUI and the nut_count dictionary
        if gui.was_reset_pressed():
            zero_values = [0, 0, 0, 0, 0]
            gui.update_counts(zero_values, zero_values)
            for nut in nut_classes:
                nut_count[nut] = 0

        cv2.imshow("Nut Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    cap.release()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    gui = GUI(current_values=[0, 0, 0, 0, 0], total_values=[0, 0, 0, 0, 0])

    # Start the camera in a separate thread instead
    cam_thread = threading.Thread(target=run_camera, args=(gui,), daemon=True)
    cam_thread.start()

    # GUI must be run on main thread!
    gui.mainloop()

