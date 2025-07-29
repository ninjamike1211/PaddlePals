// Basic demonstration of 2-way connection between phone and ESP-32
// Credit to Evandro Copercini for original example code: 
// https://docs.espressif.com/projects/arduino-esp32/en/latest/api/bluetooth.html

// Credit to Rui Santos for example on interfacing the ESP-32 with outside components and processing messages:
// https://randomnerdtutorials.com/esp32-bluetooth-classic-arduino-ide/

// Credit to Robin2 for help with parsing serial input:
// https://forum.arduino.cc/t/serial-input-basics/278284/2

// Credit to Adafruit and Random Nerd Tutorials for demo regarding MPU6050 accelerometer:
// https://randomnerdtutorials.com/esp32-mpu-6050-accelerometer-gyroscope-arduino/

// NOTE - NEED TO ADD INTERRUPT() FOR SWING SPEED!

#include "BluetoothSerial.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

String device_name = "ESP32-BT";

// Check if Bluetooth is available
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

Adafruit_MPU6050 mpu;

BluetoothSerial SerialBT;

// Variable to store the points from Current Game
int pointsThisGame = 0;

// Variable to store the total points from all time
int totalPointsAllTime = 0;

// Variable to store the current max swing speed from Current Game
float currentMaxSwingSpeed = 0.0;

// Timer variables
// Stores last time temperature was published
unsigned long previousMillis = 0;    

// Time interval at which to publish data
const long interval = 1000;  

// Stores the start and ending times for transmissions via bluetooth, as well as the latency from the two
unsigned long startTransmissionTime;
unsigned long endTransmissionTime;
unsigned long latency;

// String variables for sent and received messages
String entireMessageFromPhone = "";
String variableFromPhone = "";
char variableFromPhoneArr[50] = {0};

int valueFromPhone = 0;
String pointsString = "";
String newSwingString = "";
String maxSwingString = "";
String currentTemperature = "";
String latencyString = "";
bool messageFinishedSending = false;


void setup() {
  // put your setup code here, to run once:

  // Connect to serial port w/ baud rate 115200
  Serial.begin(115200);

  // Start Bluetooth Serial Connection with ESP-32 device
  SerialBT.begin(device_name);

  // Print that serial connection has been established
  Serial.printf("The device with name \"%s\" is started.\nNow you can pair it with Bluetooth!\n", device_name.c_str());

  // Setup Accelerometer
  // Initialization
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  Serial.print("Accelerometer range set to: ");
  switch (mpu.getAccelerometerRange()) {
  case MPU6050_RANGE_2_G:
    Serial.println("+-2G");
    break;
  case MPU6050_RANGE_4_G:
    Serial.println("+-4G");
    break;
  case MPU6050_RANGE_8_G:
    Serial.println("+-8G");
    break;
  case MPU6050_RANGE_16_G:
    Serial.println("+-16G");
    break;
  }
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  Serial.print("Gyro range set to: ");
  switch (mpu.getGyroRange()) {
  case MPU6050_RANGE_250_DEG:
    Serial.println("+- 250 deg/s");
    break;
  case MPU6050_RANGE_500_DEG:
    Serial.println("+- 500 deg/s");
    break;
  case MPU6050_RANGE_1000_DEG:
    Serial.println("+- 1000 deg/s");
    break;
  case MPU6050_RANGE_2000_DEG:
    Serial.println("+- 2000 deg/s");
    break;
  }

  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);
  Serial.print("Filter bandwidth set to: ");
  switch (mpu.getFilterBandwidth()) {
  case MPU6050_BAND_260_HZ:
    Serial.println("260 Hz");
    break;
  case MPU6050_BAND_184_HZ:
    Serial.println("184 Hz");
    break;
  case MPU6050_BAND_94_HZ:
    Serial.println("94 Hz");
    break;
  case MPU6050_BAND_44_HZ:
    Serial.println("44 Hz");
    break;
  case MPU6050_BAND_21_HZ:
    Serial.println("21 Hz");
    break;
  case MPU6050_BAND_10_HZ:
    Serial.println("10 Hz");
    break;
  case MPU6050_BAND_5_HZ:
    Serial.println("5 Hz");
    break;
  }

  Serial.println("");
  delay(100);
}

// Switch behavior so it sends statistics over time
void loop() {
  // put your main code here, to run repeatedly:
  // PLAN: Generate random number for swing speed, increment total points every 5 seconds
  // Use functions to check max swing speed
  // Print number of points this game, current max swing speed, recent swing speed
  // If you receive messages from the phone detailing the past total points from all time and past max swing speed, react accordingly
  // E.g. if it gives the past number of points, return the new total
  // Or if it gives the number of games played and the total points, calculate the average PPG

  // Get the current millis
  unsigned long currentMillis = millis();

  // If the interval has passed, get and send data to phone
  if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;

      // Get info from the accelerometer
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);

      // Generate value from 0 to 100 for probability
      int randProbability = random(0, 100);

      // If value >= 50, increment, otherwise, don't
      // Basically 50/50 probability every 5 seconds if score is updated
      if (randProbability >= 50) {
        incrementPoints();
      }

      // Get the newest swing speed
      float newSwingSpeed = calculateSwingSpeed(g.gyro.x, g.gyro.y, g.gyro.z);

      // Check the max swing speed
      float currentMax = checkMaxSwingSpeed(newSwingSpeed);

      // Send stats over in string format
      pointsString = "Current Number Of Points By This Player: " + String(pointsThisGame);
      newSwingString = "Newest Swing Speed: " + String(newSwingSpeed) + " m/s";
      maxSwingString = "Max Swing Speed: " + String(currentMax) + " m/s";
      currentTemperature = "Current Temperature: " + String(temp.temperature) + " Celsius";
      
      // After calculations, start the transmission timer
      // Note - this can overflow after 70 min of arduino runtime - might need to fix later

      startTransmissionTime = micros();

      SerialBT.println(pointsString);
      SerialBT.println(newSwingString);
      SerialBT.println(maxSwingString);
      SerialBT.println(currentTemperature);

      endTransmissionTime = micros();
      latency = endTransmissionTime - startTransmissionTime;

      // Turn latency into a string and send
      latencyString = "Latency: " + String(latency) + " microseconds";

      SerialBT.println(latencyString);

      // Print an empty line to seperate data
      SerialBT.println();
  }

  // Check for received messages from phone
  if (SerialBT.available()) {
    // Get incoming chars and append to string
    char charFromPhone = SerialBT.read();

    // Keep reading in chars into message unless new line is hit, in which case, clear the message
    if (charFromPhone != '\n') {
      entireMessageFromPhone += String(charFromPhone);
    }
    else {
      // Clear the message
      entireMessageFromPhone = "";

      // Indicate that the message finished sending
      messageFinishedSending = true;
    }

    // Write the chars to serial
    Serial.write(charFromPhone);
  }
}


// Functions for algorithms and operations

void incrementPoints() {
  pointsThisGame++;
}

float checkMaxSwingSpeed(float swingSpeed) {
  if (swingSpeed > currentMaxSwingSpeed) {
    currentMaxSwingSpeed = swingSpeed;
  }
  return currentMaxSwingSpeed;
}

int calculateTotalPointsAllTime(int pastNumberOfPoints) {
    pastNumberOfPoints = pastNumberOfPoints + pointsThisGame;
    return pastNumberOfPoints;
}

bool checkAllTimeSwingSpeed(int pastMaxSwingSpeed) {
    if (currentMaxSwingSpeed > pastMaxSwingSpeed) {
        return true;
    }
    return false;
}

float calculateAveragePointsPerGame(int numberOfGames, int totalNumberOfPoints) {
  float averagePoints = totalNumberOfPoints / numberOfGames;
  return averagePoints;
}

void parseStringForValues(char charBufferMessage[]) {
  // Split string into parts

  // Create char pointer for strtok() to use as index
  char * strtokIndx;

  // Get the string portion of the message
  strtokIndx = strtok(charBufferMessage, ",");
  
  // Copy it to variable from phone array
  strcpy(variableFromPhoneArr, strtokIndx);

  // Turn variableFromPhoneArr into string and store
  variableFromPhone = String(variableFromPhoneArr);

  // Get the int part of the message
  strtokIndx = strtok(NULL, ",");

  // Convert string to int and copy it
  valueFromPhone = atoi(strtokIndx);
}

float calculateSwingSpeed(float xVelocity, float yVelocity, float zVelocity) {
  // Assume "r" - or the distance to the rotation center - is 10 cm.
  float r = 0.10;

  // Calculate magnitude of the total angular velocity
  float angVelocity = sqrt(pow(xVelocity, 2) + pow(yVelocity, 2) + pow(zVelocity, 2));

  // Calculate final swing speed
  float finalSwingSpeed = angVelocity * r;

  return finalSwingSpeed;
}
