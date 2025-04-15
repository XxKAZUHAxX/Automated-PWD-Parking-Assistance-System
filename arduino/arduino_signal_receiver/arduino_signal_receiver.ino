#include "Arduino_LED_Matrix.h"
#include <stdint.h>
#include "config.h"

ArduinoLEDMatrix matrix;

// The exact command we expect from the Pi
const String triggerOpenCommand = "OPEN";
const String triggerCloseCommand = "CLOSE";

unsigned long ledMatrixPrev = millis();

String cameraNumber, state;

// Define control pins
const int motorOneStepPin = 2;     // Connected to TB6600 "PUL+"
const int motorOneDirPin  = 3;     // Connected to TB6600 "DIR+"
const int motorTwoStepPin = 4;     // Connected to TB6600 "PUL+"
const int motorTwoDirPin  = 5;     // Connected to TB6600 "DIR+"

// Define steps for 90° turn (for a 200-step motor)
const int stepsFor90Degrees = 50;  // 90° / 1.8° per step

void setup() {
  Serial.begin(9600);
  pinMode(motorOneStepPin, OUTPUT);
  pinMode(motorOneDirPin, OUTPUT);
  pinMode(motorTwoStepPin, OUTPUT);
  pinMode(motorTwoDirPin, OUTPUT);

  // you can also load frames at runtime, without stopping the refresh
  matrix.loadSequence(frames);
  matrix.begin();
  // turn on autoscroll to avoid calling next() to show the next frame; the parameter is in milliseconds
  // matrix.autoscroll(300);
  matrix.play(true);
  pinMode(LED_BUILTIN, OUTPUT);

  // Set default rotation direction for motor one (optional)
  digitalWrite(motorOneDirPin, HIGH);
}

void loop() {
  // Check if data is available
  if (Serial.available() > 0) {
    // Read the incoming string until newline
    String incoming = Serial.readStringUntil('\n');
    incoming.trim();  // remove any \r or extra spaces
    
    // Debug print
    Serial.print("Received: ");
    Serial.println(incoming);

    int sepIndex = incoming.indexOf(':');
    if (sepIndex != -1) {
      cameraNumber = incoming.substring(0, sepIndex);
      state = incoming.substring(sepIndex + 1);
      Serial.print("Camera ID = "); Serial.println(cameraNumber);
      Serial.print("State = "); Serial.println(state);
    }
    
    // Convert cameraNumber from String to int
    int camNum = cameraNumber.toInt();
    
    // If it matches our trigger, actuate servo
    if (state == triggerOpenCommand) {
      actuateOpenServo(camNum);
    } else if (state == triggerCloseCommand) {
      actuateCloseServo(camNum);
    }
  }
  
  if (millis() - ledMatrixPrev >= 8000) {
    matrix.play(true);
    ledMatrixPrev = millis();
  }
}

void actuateOpenServo(int cameraNumber) {
  // Rotate motor 90°
  int dirPin, stepPin;
  switch (cameraNumber) {
    case 1:
      dirPin = motorOneDirPin;
      stepPin = motorOneStepPin;
      break;
    case 2:
      dirPin = motorTwoDirPin;
      stepPin = motorTwoStepPin;
      break;
    default:
      // Invalid camera number, do nothing
      return;
  }
  digitalWrite(dirPin, HIGH);
  for (int i = 0; i < stepsFor90Degrees; i++) {
    digitalWrite(stepPin, HIGH);
    delay(5);
    digitalWrite(stepPin, LOW);
    delay(5);
  }
}

void actuateCloseServo(int cameraNumber) {
  // Reverse motor for closing the barrier
  int dirPin, stepPin;
  switch (cameraNumber) {
    case 1:
      dirPin = motorOneDirPin;
      stepPin = motorOneStepPin;
      break;
    case 2:
      dirPin = motorTwoDirPin;
      stepPin = motorTwoStepPin;
      break;
    default:
      // Invalid camera number, do nothing
      return;
  }
  digitalWrite(dirPin, LOW);
  for (int i = 0; i < stepsFor90Degrees; i++) {
    digitalWrite(stepPin, HIGH);
    delay(5);
    digitalWrite(stepPin, LOW);
    delay(5);
  }
}