import cv2
import numpy as np
import tensorflow as tf
import uuid
import time

# Ladataan TFLite-malli
model_path = "C:/Users/tiitu/github_projects/camera-counting-nuts/nuts_conveyor/Inference - impulse 1 - 160 x 160/trained.tflite"
interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Ladataan labelit
with open("C:/Users/tiitu/github_projects/camera-counting-nuts/nuts_conveyor/Inference - impulse 1 - 160 x 160/labels.txt", "r") as f:
    labels = [line.strip() for line in f.readlines()]

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
out_scale, out_zero_point = output_details[0]['quantization']

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# 🔽 Pienennetään herkkyysrajaa → havaitsee heikommatkin mutterit
min_confidence = 0.1
min_visible_area = 5
max_tracking_distance = 50
max_disappeared_frames = 10

colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255)]

nut_classes = ["m6", "m8", "m10", "m12"]
nut_count = {nut: 0 for nut in nut_classes}

# 🔻 Laskulinjan korkeus (alareuna)
line_y = 100

class TrackedObject:
    def __init__(self, nut_type, position):
        self.id = str(uuid.uuid4())[:8]
        self.nut_type = nut_type
        self.position = position
        self.prev_position = position
        self.last_seen = time.time()
        self.frames_missing = 0
        self.counted = False

tracked_nuts = []

def preprocess_frame(frame):
    resized_frame = cv2.resize(frame, (160, 160))
    gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
    normalized = gray_frame.astype(np.float32) / 255.0
    input_frame = np.expand_dims(normalized, axis=-1)
    input_frame = np.expand_dims(input_frame, axis=0)
    if input_details[0]['dtype'] == np.int8:
        input_frame = (input_frame * 255).astype(np.int8)
    return input_frame

def euclidean(p1, p2):
    return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def match_or_create(nut_label, position):
    global tracked_nuts
    matched = None
    for nut in tracked_nuts:
        if nut.nut_type == nut_label and euclidean(nut.position, position) < max_tracking_distance:
            matched = nut
            break

    if matched:
        matched.prev_position = matched.position
        matched.position = position
        matched.last_seen = time.time()
        matched.frames_missing = 0
        return matched
    else:
        new_nut = TrackedObject(nut_label, position)
        tracked_nuts.append(new_nut)
        return new_nut

while True:
    ret, frame = cap.read()
    if not ret:
        break

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
        channel_idx = idx + 1
        channel_map = real_output[:, :, channel_idx]
        conf_mask = channel_map > min_confidence
        visible_area = np.sum(conf_mask)

        if visible_area >= min_visible_area:
            row, col = np.unravel_index(np.argmax(channel_map), channel_map.shape)
            x, y = int(col * x_scale), int(row * y_scale)

            tracked = match_or_create(nut_label, (x, y))

            # 🔽 Lasketaan vain, jos mutteri on ylittänyt laskulinjan ylhäältä alas
            if not tracked.counted and tracked.prev_position[1] < line_y <= tracked.position[1]:
                nut_count[nut_label] += 1
                tracked.counted = True
                print(f"{nut_label} counted! ID={tracked.id} at ({x}, {y})")

            cv2.circle(frame, (x, y), 12, colors[idx], -1)
            cv2.putText(frame, f"{nut_label} #{tracked.id}", (x+10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[idx], 2)

    # Poista kadonneet
    current_time = time.time()
    tracked_nuts = [nut for nut in tracked_nuts if current_time - nut.last_seen <= max_disappeared_frames / 30.0]

    # 🔻 Piirrä laskulinja ruudulle
    cv2.line(frame, (0, line_y), (frame.shape[1], line_y), (0, 0, 255), 2)
    cv2.putText(frame, "Laskulinja", (10, line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Piirrä laskurit
    y0 = 30
    for nut_label in nut_classes:
        text = f"{nut_label}: {nut_count[nut_label]}"
        cv2.putText(frame, text, (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        y0 += 30
    cv2.putText(frame, f"Total Nuts: {sum(nut_count.values())}", (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
