import cv2
import numpy as np
import math
import tensorflow as tf
import uuid
import time
import os

# Lataa TFLite-malli ja labels
here = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(here, "trained.tflite")
labels_path = os.path.join(here, "labels.txt")

interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Ladataan labelit
with open(labels_path, "r") as f:
    labels = [line.strip() for line in f.readlines()]

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
out_scale, out_zero_point = output_details[0]['quantization']

# Parametrit trackingiin ja laskentaan
min_confidence = 0.1         # Mallin kynnysarvo
min_visible_area = 5         # Kontuurien minimipinta-ala
max_tracking_distance = 50   # Maksimi etäisyys matchaukseen
max_disappeared_frames = 10  # Montako framea objektia voi olla näkymättömänä

nut_classes = ["m6", "m8", "m10", "m12"]
nut_count = {nut: 0 for nut in nut_classes}
line_y = 600  # Laskulinjan y-koordinaatti (esim. kuljetinhihnalla)

colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255)]

# Luokka seurattaville objekteille
class TrackedObject:
    def __init__(self, nut_type, position):
        self.id = str(uuid.uuid4())[:8]
        self.nut_type = nut_type
        self.position = position
        self.prev_position = position
        self.last_seen = time.time()
        self.counted = False

tracked_nuts = []

def euclidean_distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def match_or_create(nut_label, position):
    global tracked_nuts
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
        return new_nut

# Funktio, joka suorittaa TFLite-mallin inferenssin annetulle alueelle (ROI)
def run_tflite_inference(frame):
    # Muutetaan ROI mustavalkoiseksi, skaalataan ja normalisoidaan
    input_data = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    input_data = cv2.resize(input_data, (160, 160))
    input_data = input_data.astype(np.float32)
    input_data = (input_data - 127.5) / 127.5
    input_data = np.round(input_data * 127.5).astype(np.int8)
    input_data = np.expand_dims(input_data, axis=-1)  # lisää kanavaksi yksi ulottuvuus
    input_data = np.expand_dims(input_data, axis=0)   # lisää batch-ulottuvuus

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data

# Käynnistetään kamera
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Taustasubstraattori liikkeen havaitsemiseksi
object_detector = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=40)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    height, width, _ = frame.shape

    # Luodaan maski liikkeen havaitsemiseksi
    mask = object_detector.apply(frame)
    _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)

    # Etsitään kontuurit maskista
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 100:
            x, y, w, h = cv2.boundingRect(cnt)
            # Piirretään rajaus suorakulmio (henkilökohtaisesti voi halutessa poistaa myös tämän)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

            roi = frame[y:y+h, x:x+w]
            output_data = run_tflite_inference(roi)

            # Mallin output on oletettavasti vektori, jossa jokaisella elementillä on luokan todennäköisyys
            for i, output in enumerate(output_data[0]):
                value = np.array(output).flatten()[0]
                if value > 0.5:
                    if i < len(labels):
                        label = labels[i]
                    else:
                        label = f"Class {i}"
                    # Poistettu tämä cv2.putText, jotta tunnistuksen päällä ei näy mitään tekstiä:
                    # cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                    # Lisää objektille tracking ja laskenta vain, jos tunnistettu nut-luokka on haluttu
                    if label in nut_classes:
                        center = (int(x + w/2), int(y + h/2))
                        tracked = match_or_create(label, center)
                        # Kun objektin liike ylittää laskulinjan alaspäin, lasketaan se
                        if not tracked.counted and tracked.prev_position[1] < line_y <= tracked.position[1]:
                            nut_count[label] += 1
                            tracked.counted = True
                            print(f"{label} counted! ID={tracked.id} at {center}")
                        # Piirretään vain ympyrä itse objektille (ei lisätä ylimääräistä tekstiä)
                        cv2.circle(frame, center, 12, colors[nut_classes.index(label)], -1)

    # Poistetaan pitkäksi aikaa näkymättömät seurattavat objektit
    current_time = time.time()
    tracked_nuts = [t for t in tracked_nuts if current_time - t.last_seen <= max_disappeared_frames / 30.0]

    # Piirretään laskulinja
    cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 2)
    cv2.putText(frame, "Laskulinja", (10, line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Näytetään laskurit kuvan vasemmassa yläkulmassa
    y0 = 30
    for nut in nut_classes:
        text = f"{nut}: {nut_count[nut]}"
        cv2.putText(frame, text, (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        y0 += 30
    cv2.putText(frame, f"Total Nuts: {sum(nut_count.values())}", (10, y0),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
