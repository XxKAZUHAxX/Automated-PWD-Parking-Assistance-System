import serial
import time


# Adjust '/dev/ttyACM0' if your Arduino appears differently
ser = serial.Serial('COM4', 9600, timeout=1)
time.sleep(2)  # wait for Arduino reset

while True:
    user_input = input("Choose '1' for OPEN or '2' for CLOSE: ")
    if user_input == '1':
        ser.write(b'OPEN\n')
        # ser.close()
    elif user_input == '2':
        ser.write(b'CLOSE\n')
        # ser.close()
    else:
        print("Invalid input")

