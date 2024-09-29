# Counting Metric Nuts on a Conveyor Belt with OpenMV Cam RT-1062 and FOMO

## Intro

This tutorial shows how you can use FOMO in Edge Impulse with the OpenMV Cam RT-1062 to count different sizes of nuts on a moving conveyor belt.  The solution automates the process of detecting and counting objects on a conveyor belt, improving efficiency and reducing manual labor. The real-time visualization provides immediate feedback, allowing operators to monitor and control processes accurately.

The hardware used in this project was the aforementioned OpenMV Cam RT-1062, together with a Dobot conveyor belt. The reason for why this camera was chosen, was that it being a very powerful camera with its own microcontroller, and being fully supported by Edge Impulse, it's very easy to get started with. The main steps in this tutorial are collecting data with the camera, training and deploying from Edge Empulse, and finally testing on the moving conveyor belt.

A video is found [here](https://youtu.be/gKTWJUO_nzo), or a shorter GIF-video at the end of this tutorial

![](/Images/OpenMV_RT-1062_with_case_compressed.jpg)

## Use-case Explanation

Counting objects moving on a conveyor belt offers significant advantages for businesses. It enhances inventory management by providing accurate counts that help maintain optimal stock levels, preventing shortages or overstock situations. Additionally, monitoring the count of products ensures quality control, allowing for the detection of defects or missing items, thus upholding product standards.

The OpenMV cameras directly run MicroPython, and in addition to machine learning, they also provides more traditional computer vision algorithms. You can read more about the RT-1062 camera [here](https://openmv.io/products/openmv-cam-rt). The conveyor belt chosen in this tutorial was from [Dobot](https://www.amazon.com/DOBOT-Conveyor-Belt-Simplest-Production/dp/B073NXVW1H), but pretty much any belt can be used.

![](/Images/Conveyor_belt_compressed.jpg)


## Components and Hardware/Software Configuration

### Components Needed

- A supported computer, pretty much anyone with a USB-port for the camera, the Dobot conveyor belt is connected to a Dobot Magician robot, als through USB.
- I strongly recommend to 3D-print a case for the camera, official STL-files are nowadays found [here](https://grabcad.com/library/openmv-cam-rt1062-v4-case-1), but as they were not available earlier, I forked an earlier version and made some adjustments, resulting in this [STL-file](/Images/OpenMV_RT-1062_case.stl).
    - I've printed with semitransparent TPU as it's more flexible and as the LED light shines through the case
    - I recommend to mount the camera to some type of tripod like I did.


![](/Images/OpenMV_RT-1062_case_with_lid.png)


### Hardware and Software Configuration

This is pretty straightforward, and by following the same [tutorial](https://docs.edgeimpulse.com/docs/tutorials/end-to-end-tutorials/image-classification/image-classification-openmv) as I did, you'll be up and running in just a few minutes. While the tutorial is for another older OpenMV camera, I found that the steps are the same.

- When it comes to the ```Dataset_Capture_Script.py``` program used to capture images, I wanted the camera to only see the black conveyor belt, hence I played with the ```img.scale``` function until I found the correct coordinates (see code snippet below). I also added lens correction although I'm not sure it makes a difference. Remember to later use exactly same code lines in the inferencing program!

```
...
while(True):
    clock.tick()
    img = sensor.snapshot()
    img.scale(x_scale=1.2, roi=(50, 55, 540, 240))     # <<<<======   Results in a resolution of 324 x 222
    
    # Apply lens correction if you need it.
    img.lens_corr()
...
```

- In this tutorial I created a [Python program](/nuts_conveyor/Dobot%20conveyor%20-%20object%20counting.py) for controlling the conveyor belt, showing a live video feed, and visualizing the counting. You can use any programming language or environment, as the OpenMV camera is just using the serial terminal to transmit the total count of objects it found in the frame, followed by each class and its corresponding count. E.g. this string ```"3, M10: 2, M8:1"``` means that 3 nuts were found, 2 M10's and 1 M8.
    - The live feed in the program needs a separate camera, the OpenMV camera can't be used as its serial port is occupied by transmitting inferencing data. Starting from around row 102 in the program, you'll find the function ```show_video_feed()```, the camera can if needed be changed from 0 to another in ```cap = cv2.VideoCapture(0)```.


## Data Collection Process

The process of capturing and uploading the images is described in the previous mentioned [tutorial](https://docs.edgeimpulse.com/docs/tutorials/end-to-end-tutorials/image-classification/image-classification-openmv).

For this use case, I suspected beforehand that lighting would play a crucial role, and that one nut might look quite similar to another nut, even if they are of different sizes. To mitigate possible issues, I decided to take pictures with partially different lighting, ending up with approximately 60 pictures per class. 

The picture shows the following four different sizes I used: **M12, M10, M8, M6**

![Nut sizes: M12, M10, M8, M6](/Images/nut_sizes_compressed.jpg)


## Training and Building the Model

After you've uploaded data to Edge Impulse, the next steps are to set up the ML-project in the platform. It's made so easy so I did not need to use a tutorial, but for a newcomer I warmly recommend this tutorial [Detect objects with FOMO](https://docs.edgeimpulse.com/docs/tutorials/end-to-end-tutorials/object-detection/detect-objects-using-fomo).

I played around with different image sizes, and found the sweet spot to be 180 x 180.

![Nut sizes: M12, M10, M8, M6](/Images/Create_impulse_compressed.png)

### Creating an Impulse

Again, this is quite straightforward in Edge Impulse, you need to create an impulse by selecting a few parameters. In this project I experimented with a few alternatives, with and without sliding windows, but found out that a sample window of 2 seconds, using Spectral Analysis as processing block, and Classification as learning block was optimal. As there are in practice no memory or latency constraints when using a computer compared to using a microcontroller, there's no need to try to optimize memory usage or processing time.

![](Images/EI-08.jpg)

### Configuring Spectral Features

Following configuration is what I found to be optimal for this use case. Whenever you change any of these, do remember to change same setting in the Python-program as well.
- Click on `Save parameters` and in next screen `Generate features`.

![](Images/EI-10.jpg)

### Training the Model

After some experimentation I found an optimal Neural network settings to be 2 dense layers of 20 and 40 neurons each, with a dropout rate of 0.25 to reduce the risk of overfitting the model exactly to the underlying data. As a computer later will run inferencing, there's no need to create an Int8 quantized model. As the results show, the training performance in this case is 100 %.

![](Images/EI-13.jpg)

### Testing the Model

Before deploying the model to the target device, it is strongly recommended that you test it with data it has not seen before. This is where you use the `Model testing` functionality in Edge Impulse. For this purpose Edge Impulse puts by default approximately 20 % of the data aside. Just click on `Classify all` to start the testing.

In this project the test results were quite good with an accuracy of 88 %, so I decided this was good enough to start testing the model in practice. If this were a project to be deployed to end users, the accuracy would probably need to be much higher.   

![](Images/EI-15.jpg)

## Model Deployment

First part is in this case extremely simple, just head over to `Dashboard` and download the `TensorFlow Lite (float32)` model. This model file should be copied to same directory as where the Python-program is.

![](Images/EI-17.jpg)

Second part is to check the Python-program (EEG-robot.py) and secure you have correct configuration:
- Around row 82 you'll find the below code, change the model_path to the exact name of the file you just downloaded
    ```
    # Load the TensorFlow Lite model
    model_path = "ei-muse-eeg-robot-blinks-classifier-tensorflow-lite-float32-model (1).lite"
    ```
- Start the robot, the first time without providing power to the wheel servos, once you have established communication you can provide power to the servos.
- Run the Python program, as this project is all about controlling an external robot, there's no fancy UI. What though will be shown in the terminal window is the result of the inference, i.e. left, right, or background. Remember, left is a 'normal' blink, right is a 'deep' blink, and background is no blinks at all (= the robot moves straight forward).
- If everything works as it should (which it sometimes does even the first time), you can now control your robot by blinking!
    - As there are several devices, programs, libraries etc. involved, there's of course a risk that you'll end up having problems, mainly with device communication or with the model accuracy. As this is neither rocket science or brain surgery, just troubleshoot each issue methodically,    


## Results

The results from this project were initially a bit disappointing due to the inconsistencies I could not understand the reasons for. As mentioned earlier I needed to lower my ambition level and use blinks instead of hand movement tries. Still, even then the accuracy was sometimes unexpectedly low. First when I discovered that one major culprit was interference, and I found an exact sweet spot where to sit, I was able to achieve good results in a real setting. Now I believe that my initial goal might be easier to achieve when I know how to reduce interference.

When trying to control a physical robot, you most probably want to look what it's doing or where it's going. This action, i.e. watching the robot, was though in my case a bit different than when collecting blinks where I only focused my eyes on the computer screen. In practice I noticed that this difference caused some misclassifications when I sat on the floor and watched the robot. A lesson learned from this is to record blinks in different settings and positions to improve the accuracy. Still, the accuracy was good enough so I could control the robot to give me a well deserved cold beverage!

![](/Videos/Counting_nuts_with_conveyor_belt.gif)

## Conclusion

The goal of this tutorial was to show how to control a mobile robot using brain waves, and despite the few pitfalls on the road, the goal was achieved. To scale up from this proof of concept level, one would need to take measures to minimize or mitigate electric and radio interference, physically and/or by filtering it out in the software. The physical device being controlled, in this case a mobile robot, also needs to have fail-safe modes so it does not harm others or itself. I actually tried to implement logic on the robot so it would stop if the communication was interupted for a few seconds, but I was not able to get it working reliably. In addition, it would be nice to have a few more commands available, e.g. double-blinking for stopping or starting the robot, triple-blinking for reversing etc. Technically this is quite easy, the major work needs to be done in designing the ML-model and collecting data.

This ends - at least for now - the tutorial series of applying machine learning to EEG-data. While not everything has gone according to initial plans, there has been way more successes than failures. Most satisfying was everything I've learned on the way, and most surprising learning that this concept even is possible with a consumer EEG-device! Luckily I did not listen to one professor telling me it is probably not possible to successfully classify brain waves from the motor cortex with this type of EEG-device!
