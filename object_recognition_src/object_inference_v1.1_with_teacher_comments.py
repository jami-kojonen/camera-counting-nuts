import numpy as np                                                      # Import the NumPy library for numerical operations.
import cv2                                                              # Import the OpenCV library for image processing.
import tensorflow as tf                                                 # Import the TensorFlow library for ML models.
import time


# Constants
CAM_PORT = 0                                                            # Define the camera port (default is usually 0).
MODEL_PATH = "ei-sort_defects-transfer-learning-tensorflow-lite-float32-model (5).lite"   # Model file path.
LABELS = ("circle dirty", "circle ok", "nothing", "square dirty", "square ok", "triangle dirty", "triangle ok")  # Define labels.

def initialize_camera(port=CAM_PORT):                                   # Function to initialize the camera.
    # Initialize the camera 
    return cv2.VideoCapture(port, cv2.CAP_DSHOW)                        # Return the camera capture object.

def load_tflite_model(model_path=MODEL_PATH):                           # Function to load a TensorFlow Lite model.
    # Load the TensorFlow Lite model 
    interpreter = tf.lite.Interpreter(model_path=model_path)            # Load TFLite model.
    interpreter.allocate_tensors()                                      # Allocate tensors for the interpreter.
    return interpreter                                                  # Return the model interpreter.

def capture_image(camera):                                              # Function to capture an image from the camera.
    # Capture an image from the camera 
    ret, frame = camera.read()                                          # Read a frame from the camera.
    if not ret:                                                         # If frame reading failed,
        raise RuntimeError("Failed to capture image")                   # raise a RuntimeError.
    return frame                                                        # Return the captured frame.

def preprocess(frame, alpha=1, beta=1):                                 # Function to preprocess the frame for prediction.
    # Preprocess the frame for prediction 
    
    brightened_frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
    cv2.imshow("Preprocessed Frame", brightened_frame)                  # Näytä esikäsitelty kuva.
    processed = cv2.convertScaleAbs(brightened_frame)                   # Apply scale conversion to frame.
    processed = cv2.resize(processed, (160, 160))                       # Resize frame to model's expected size.
    processed = processed / 255.0                                       # Normalize pixel values to [0, 1].
    processed = np.expand_dims(processed, axis=0).astype(np.float32)    # Add batch dimension, ensure type is float32.
    return processed                                                    # Return the preprocessed frame.

def predict(interpreter, image):                                        # Function to perform prediction using the TFLite model.
    # Make a prediction using the TensorFlow Lite model 
    input_details = interpreter.get_input_details()                     # Get model input details.
    output_details = interpreter.get_output_details()                   # Get model output details.
    interpreter.set_tensor(input_details[0]['index'], image)            # Set input tensor.
    interpreter.invoke()                                                # Run inference.
    output_data = interpreter.get_tensor(output_details[0]['index'])    # Get output data.
    return output_data                                                  # Return the prediction results.

def process_image(camera):
    frame = capture_image(camera)
    preprocessed_frame = preprocess(frame)                              # Esikäsittele kaapattu kuva.
    return frame, preprocessed_frame

def return_prediction(camera, model):
    # frame = capture_image(camera)                                     # Kaappaa kuva kamerasta.
    # preprocessed_frame = preprocess(frame)                            # Esikäsittele kaapattu kuva.
    
    frame, preprocessed_frame = process_image(camera)
    # cv2.imshow("Preprocessed Frame", frame)                           # Näytä esikäsitelty kuva.
    output = predict(model, preprocessed_frame)                         # Tee ennustus esikäsitellylle kuvalle.
    predicted_label = LABELS[np.argmax(output)]                         # Hae ennustettu tunniste.
    return predicted_label


def main():                                                             # Main function.
    camera = initialize_camera()                                        # Initialize camera.
    model = load_tflite_model()                                         # Load the TensorFlow Lite model.
    
    
    while True:                                                         # Start an infinite loop.
        try:
            predicted_label = return_prediction(camera, model)
            print("Predicted label:", predicted_label)                  # Print the predicted label.
            
            if predicted_label == 'square ok':
                print("Found: ", predicted_label)
                
            if cv2.waitKey(1) & 0xFF == 27:                             # If ESC key is pressed,
                break                                                   # exit the loop.

        except RuntimeError as e:                                       # If a RuntimeError occurs,
            print(e)                                                    # print the error.
            break                                                       # and break the loop.

    camera.release()                                                    # Release the camera.
    cv2.destroyAllWindows()                                             # Close all OpenCV windows.

if __name__ == "__main__":                                              # If this script is run as the main program,
    main()                                                              # call the main function.
