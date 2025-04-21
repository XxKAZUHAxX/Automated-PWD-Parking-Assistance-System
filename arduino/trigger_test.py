import serial
import time


# Adjust '/dev/ttyACM0' if your Arduino appears differently
ser = serial.Serial('COM4', 9600, timeout=1)
time.sleep(2)  # wait for Arduino reset

while True:
    user_input = input("Choose from either 1-4: ")
    if user_input == '1':
        ser.write(b'1:OPEN\n')
    elif user_input == '2':
        ser.write(b'1:CLOSE\n')
    elif user_input == '3':
        ser.write(b'2:OPEN\n')
    elif user_input == '4':
        ser.write(b'2:CLOSE\n')
    else:
        print("Invalid input")

