import pydobot
import math
import struct
from pydobot.message import Message

# Port mappings
PORT_GP1 = 0x00
PORT_GP2 = 0x01
PORT_GP4 = 0x02
PORT_GP5 = 0x03

class Dobot(pydobot.Dobot):
    def conveyor_belt_distance(self, speed_mm_per_sec, distance_mm, direction=1, interface=0):
        """
        Move the conveyor belt a specified distance at a given speed.
        
        Parameters:
        - speed_mm_per_sec (int): Speed in mm per second.
        - distance_mm (int): Distance to move in mm.
        - direction (int): Direction to move (1 for forward, -1 for reverse).
        - interface (int): Interface number for controlling the conveyor (default 0).
        """
        if speed_mm_per_sec > 100:
            raise pydobot.dobot.DobotException("Speed must be <= 100 mm/s")
        
        MM_PER_REV = 34 * math.pi  # Effective circumference of the wheel in mm
        STEP_ANGLE_DEG = 1.8  # Step angle for the stepper motor
        STEPS_PER_REV = 360.0 / STEP_ANGLE_DEG * 10.0 * 16.0 / 2.0  # Number of steps per revolution
        distance_steps = distance_mm / MM_PER_REV * STEPS_PER_REV  # Calculate steps for the given distance
        speed_steps_per_sec = speed_mm_per_sec / MM_PER_REV * STEPS_PER_REV * direction  # Speed in steps per second
        
        # Send the command to the Dobot to move the conveyor
        msg = Message()
        msg.id = 137
        msg.ctrl = 0x03  # Control code to move the conveyor
        msg.params = bytearray(struct.pack("!iiB", int(speed_steps_per_sec), int(distance_steps), interface))
        
        # Debugging: Print out the raw message sent to the device
        print("Sending message:", msg)

        # Directly return the response from the command
        msg_response = self._send_command(msg)

        # Debugging: Print out the response from the device
        print("Response from Dobot:", msg_response)
        return msg_response

# Test the conveyor movement
if __name__ == "__main__":
    # Instantiate the Dobot class with the correct COM port
    device = Dobot(port="COM3", verbose=True)
    print("Dobot connected and ready!")

    # Move the conveyor at a speed of 30 mm/s for 200 mm forward
    print("Starting conveyor movement...")
    response = device.conveyor_belt_distance(speed_mm_per_sec=30, distance_mm=200, direction=1)  # Moving forward
    print("Conveyor movement complete!")
    print("Response:", response)
