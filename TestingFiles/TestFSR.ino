// Credit to Makerguides for this FSR test code:
// https://www.makerguides.com/fsr-arduino-tutorial/

// Used ChatGPT for suggestion on voltage ranges

/* Simple example code for Force Sensitive Resistor (FSR) 
  with Arduino. More info: https://www.makerguides.com */

// Define FSR pin:
#define fsrpin 36

//Define variable to store sensor readings:
int fsrreading; //Variable to store FSR value

void setup() {
  // Begin serial communication at a baud rate of 9600:
  Serial.begin(115200);

  // Ensure full 0–3.3 V range on ESP32 ADC
  analogSetPinAttenuation(fsrpin, ADC_11db);
}

void loop() {
  // Read the FSR pin and store the output as fsrreading:
  fsrreading = analogRead(fsrpin);

  // Print the fsrreading in the serial monitor:
  // Print the string "Analog reading = ".
  Serial.print("Analog reading = ");
  // Print the fsrreading:
  Serial.print(fsrreading);

  // We can set some threshholds to display how much pressure is roughly applied:
  if (fsrreading < 10) {
    Serial.println(" - No pressure");
  } else if (fsrreading < 200) {
    Serial.println(" - Light touch");
  } else if (fsrreading < 500) {
    Serial.println(" - Light squeeze");
  } else if (fsrreading < 800) {
    Serial.println(" - Medium squeeze");
  } else {
    Serial.println(" - Big squeeze");
  }

  delay(500); //Delay 500 ms.
}
