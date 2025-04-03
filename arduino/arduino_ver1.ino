char receivedChar;
boolean newData = false;

void setup() {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    receivedChar = Serial.read();
    newData = true;
  }
  if (newData) {
    if (receivedChar == '1') {
      digitalWrite(LED_BUILTIN, HIGH);
    } else if (receivedChar == '0') {
      digitalWrite(LED_BUILTIN, LOW);
    }
    newData = false;
  }
}
