import numpy as np                                                      # Numpy-kirjaston tuonti numeerisiin operaatioihin.
import cv2                                                              # OpenCV-kirjaston tuonti kuvankäsittelyyn.
import tensorflow as tf                                                 # TensorFlow-kirjaston tuonti ML-malleihin.
import pydobot, serial                                                  # Pydobot- ja serial-kirjastojen tuonti Dobotin ohjaukseen.

# Vakiot
CAM_PORT = 0                                                            # Määritä kameran portti (yleensä 0).
MODEL_PATH = "ei-sort_defects-transfer-learning-tensorflow-lite-float32-model (5).lite"  # Mallin tiedostopolku.
LABELS = ("circle dirty", "circle ok", "nothing", "square dirty", "square ok", "triangle dirty", "triangle ok")  # Määritä tunnisteet.

device = pydobot.Dobot(port='COM18')                                    # Yhdistä Dobot Magician -laitteeseen, korvaa 'COM18' sopivalla portilla.
x, y, z, r = 180, 0, -0, 0                                              # Alkuperäiset koordinaatit ja rotaatio Dobotille.
start_z = 0                                                             # Alkuperäinen Z-koordinaatti.
delta_z = 67                                                            # Muutos Z-koordinaatissa kalibrointia varten.
close_dist = 20
speed = 300                                                             # Liikenopeus.
acceleration = 300                                                      # Liikkeen kiihtyvyys.
device.speed(speed, acceleration)                                       # Asetetaan Dobotin nopeus ja kiihtyvyys.

global camera

def vacuum_on():                                                        # Imupumpun päällekytkentä.
    device.suck(True)                                                   # Aktivoi imupumpun.

def vacuum_off():                                                       # Imupumpun pois kytkentä.
    device.suck(False)                                                  # Deaktivoi imupumpun.

def wait(ms):                                                           # Odottamisen toteutus.
    device.wait(ms)                                                     # Dobot odottaa määritetyn ajan millisekunteina.

def center():                                                           # Dobotin siirto keskiasentoon.
    device.move_to(180, 0, start_z + 20, r, wait=True)                  # Siirrä Dobot keskiasentoon ja hieman ylös jottei olisi kamerakuvassa

def left45():                                                           # Dobotin kääntö 45 astetta vasemmalle.
    device.move_to(150, 147, start_z, r, wait=True)                     # Siirrä Dobot 45 astetta vasemmalle.

def right45():                                                          # Dobotin kääntö 45 astetta oikealle.
    device.move_to(150, -147, start_z, r, wait=True)                    # Siirrä Dobot 45 astetta oikealle.

def down():                                                             # Dobotin siirto ala-asentoon.
    (x1, y1, z1, r, j1, j2, j3, j4) = device.pose()                     # Hae nykyinen asento.
    device.move_to(x1, y1, start_z - delta_z, r, wait=True)             # Siirrä Dobot alas.

def almost_down():                                                      # Dobotin siirto melkein ala-asentoon.
    (x1, y1, z1, r, j1, j2, j3, j4) = device.pose()                     # Hae nykyinen asento.
    device.move_to(x1, y1, start_z - delta_z + close_dist, r,wait=True) # Siirrä Dobot melkein alas.

def up():                                                               # Dobotin siirto ylä-asentoon.
    (x1, y1, z1, r, j1, j2, j3, j4) = device.pose()                     # Hae nykyinen asento.
    device.move_to(x1, y1, start_z, r, wait=True)                       # Siirrä Dobot ylös.
    
def fetch_object():                                                     # Hakee objekti
    vacuum_on()                                                         # Imupumppu päälle
    almost_down()                                                       # Siirry lähellä pintaa
    down()                                                              # Kokonaan alas
    up()                                                                # Ylös    
    
def release_object():                                                   # Pudota objekti
    almost_down()                                                       # Siirry lähellä pintaa
    vacuum_off()                                                        # Imupumppu pois päältä
    up()                                                                # Ylös


# Tästä eteenpäin voit yhdistää kuvantunnistuksen tulokset Dobotin ohjaukseen.
#
# Kameran ja mallin alustus
def initialize_camera(port=CAM_PORT):                                   # Kameran alustusfunktio.
    return cv2.VideoCapture(port, cv2.CAP_DSHOW)                        # Palauta kameran kaappausobjekti.

def load_tflite_model(model_path=MODEL_PATH):                           # TensorFlow Lite -mallin latausfunktio.
    interpreter = tf.lite.Interpreter(model_path=model_path)            # Lataa TFLite-malli.
    interpreter.allocate_tensors()                                      # Allokoi tensorit tulkkille.
    return interpreter                                                  # Palauta mallin tulkki.

def capture_image(camera):                                              # Kuvan kaappaamisfunktio kamerasta.
    ret, frame = camera.read()                                          # Lue kuva kamerasta.
    if not ret:                                                         # Jos kuvan lukeminen epäonnistuu,
        raise RuntimeError("Failed to capture image")                   # heitä RuntimeError.
    return frame                                                        # Palauta kaapattu kuva.

def preprocess(frame, alpha=1, beta=50):                                # Kuvan esikäsittelyfunktio ennustusta varten.
    processed = cv2.convertScaleAbs(frame)                              # Sovella mittakaavan muunnosta kuvaan.
    processed = cv2.resize(processed, (160, 160))                       # Muuta kuvan kokoa mallin odottamaan kokoon.
    processed = processed / 255.0                                       # Normalisoi pikseliarvot välille [0, 1].
    processed = np.expand_dims(processed, axis=0).astype(np.float32)    # Lisää eräulottuvuus ja varmista, että tyyppi on float32.
    return processed                                                    # Palauta esikäsitelty kuva.

def predict(interpreter, image):                                        # Ennustusfunktio käyttäen TensorFlow Lite -mallia.
    input_details = interpreter.get_input_details()                     # Hae mallin syötetiedot.
    output_details = interpreter.get_output_details()                   # Hae mallin tulostetiedot.
    interpreter.set_tensor(input_details[0]['index'], image)            # Aseta syötetensori.
    interpreter.invoke()                                                # Suorita ennustus.
    output_data = interpreter.get_tensor(output_details[0]['index'])    # Hae tulostetiedot.
    return output_data                                                  # Palauta ennustustulokset.

def return_prediction(camera, model):
    frame = capture_image(camera)                                       # Kaappaa kuva kamerasta.
    preprocessed_frame = preprocess(frame)                              # Esikäsittele kaapattu kuva.
    cv2.imshow("Preprocessed Frame", frame)                             # Näytä esikäsitelty kuva.
    output = predict(model, preprocessed_frame)                         # Tee ennustus esikäsitellylle kuvalle.
    predicted_label = LABELS[np.argmax(output)]                         # Hae ennustettu tunniste.
    return predicted_label, frame


def show_captured_frame(captured_frame):                            
    cv2.imshow("Preprocessed Frame", captured_frame)                    # Näytä kuva
    cv2.waitKey(50)                                                     # Ilman tätä kuva ei näy

def close_camera(camera):
    camera.release()                                                    # Suljetaan kamera
    
def move_bin1(camera, frame, label):
    show_captured_frame(frame)                                          # Näytä otettu kuva
    print("MOVING: ", label)                                            # Tulosta tunnistettu objekti
    fetch_object()
    right45()
    release_object()
    center()
    close_camera(camera)                                                # Sulje kamera, muuten edellinen kuva jäi muistiin ja tunnistetaan uudelleen vaikka objekti olisi jo siirretty
    camera = initialize_camera()                                        # Avaa kamera uudelleen
    return camera

def move_bin2(camera, frame, label):
    show_captured_frame(frame)                                          # Näytä otettu kuva
    print("MOVING: ", label)                                            # Tulosta tunnistettu objekti
    fetch_object()
    left45()
    release_object()
    center()
    close_camera(camera)                                                # Sulje kamera, muuten edellinen kuva jäi muistiin ja tunnistetaan uudelleen vaikka objekti olisi jo siirretty
    camera = initialize_camera()                                        # Avaa kamera uudelleen
    return camera


# Pääohjelma
def main():                                                             # Pääfunktio.

    camera = initialize_camera()                                        # Alusta kamera.
    model = load_tflite_model()                                         # Lataa TensorFlow Lite -malli.
    
    center()

    while True:                                                         # Aloita ääretön silmukka.
        predicted_label, captured_frame = return_prediction(camera, model)
        print("Predicted label:", predicted_label)                      # Tulosta ennustettu tunniste.

        # Tässä kohtaa voit määrittää, miten Dobot toimii eri ennustetunnisteiden perusteella.
        # Esimerkiksi jos ennustettu tunniste on 'circle ok':
        
        if predicted_label == 'circle ok':
            center()
            
        elif predicted_label == 'circle dirty':
            center()
            
        elif predicted_label == 'square dirty':
            camera = move_bin1(camera, captured_frame, predicted_label)
            
        elif predicted_label == 'square ok':
            camera = move_bin2(camera, captured_frame, predicted_label)
            
        elif predicted_label == 'triangle ok':
            center()
            
        elif predicted_label == 'triangle dirty':
            center()
       
        # Lisää muita ehtoja ja toimintoja tarpeen mukaan.
        if cv2.waitKey(1) & 0xFF == 27:                                 # Jos ESC-näppäintä painetaan,
            center()
            break                                                       # poistu silmukasta.

        # Odota hieman ennen seuraavan kuvan ottamista, tarvittaessa.
        # wait(5)                                     # Odottaa hieman ennen seuraavan toiminnon suorittamista.

    # Lopuksi vapauta resurssit
    camera.release()                                  # Vapauta kamera.
    cv2.destroyAllWindows()                           # Sulje kaikki OpenCV-ikkunat.
    device.close()                                    # Sulje Dobot-yhteys.


if __name__ == "__main__":                            # Jos tämä skripti suoritetaan suorana,
    main()                                            # suorita pääfunktio.
