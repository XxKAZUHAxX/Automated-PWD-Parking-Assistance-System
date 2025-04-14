#include "Arduino_LED_Matrix.h"
#include <stdint.h>
#include <Servo.h>
#include "config.h"

ArduinoLEDMatrix matrix;
Servo myservo;  // create Servo object to control a servo

// The exact command we expect from the Pi
const String triggerOpenCommand = "OPEN";
const String triggerCloseCommand = "CLOSE";

unsigned long ledMatrixPrev = millis();

String cameraNumber, state;

void setup() {
  myservo.attach(9);
  Serial.begin(9600);
  // you can also load frames at runtime, without stopping the refresh
  matrix.loadSequence(frames);
  matrix.begin();
  // turn on autoscroll to avoid calling next() to show the next frame; the parameter is in milliseconds
  // matrix.autoscroll(300);
  matrix.play(true);
  pinMode(LED_BUILTIN, OUTPUT);
  myservo.write(0);
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
    // If it matches our trigger, actuate servo
    if (state == triggerOpenCommand) {
      actuateOpenServo();
    } else if (state == triggerCloseCommand) {
      actuateCloseServo();
    }

  }
  if (millis() - ledMatrixPrev >= 8000) {
    matrix.play(true);
    ledMatrixPrev = millis();
  }
}

void actuateOpenServo() {
  myservo.write(180);
}

void actuateCloseServo() {
  myservo.write(0);
}