// Basic demonstration of 2-way connection between phone and ESP-32
// Credit to Evandro Copercini for original example code: 
// https://docs.espressif.com/projects/arduino-esp32/en/latest/api/bluetooth.html

// Credit to Rui Santos for example on interfacing the ESP-32 with outside components and processing messages:
// https://randomnerdtutorials.com/esp32-bluetooth-classic-arduino-ide/

// Credit to Robin2 for help with parsing serial input:
// https://forum.arduino.cc/t/serial-input-basics/278284/2

// Credit to Adafruit and Random Nerd Tutorials for demo regarding MPU6050 accelerometer:
// https://randomnerdtutorials.com/esp32-mpu-6050-accelerometer-gyroscope-arduino/

// Linear Velocity to Angular Velocity:
// https://math.libretexts.org/Bookshelves/Precalculus/Book%3A_Trigonometry_(Sundstrom_and_Schlicker)/01%3A_The_Trigonometric_Functions/1.04%3A_Velocity_and_Angular_Velocity
// Magnitude of Angular Velocity:

// Credit to Instructables and Arduino project hub for help with Seven-Segment:
// https://www.instructables.com/7-Segment-Display-On-Arduino/
// https://projecthub.arduino.cc/aboda243/get-started-with-seven-segment-5754a8

// Credit to TechKnowLab for help with the FSR:
// https://techknowlab.com/thin-film-pressureor-force-sensor-with-arduino/

// NOTE - NEED TO ADD INTERRUPT() FOR SWING SPEED!

// Libraries for BLE communication
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// Libraries for sensor communication
#include "BluetoothSerial.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

// Library for button communication
#include <Button2.h>

// Button pins
#define button_increment_pin 18
#define button_decrement_pin 17

// Seven-segment pins

#define seg_1_a 1
#define seg_1_b 1
#define seg_1_c 1
#define seg_1_d 1
#define seg_1_e 1
#define seg_1_f 1
#define seg_1_g 1

#define seg_2_a 1
#define seg_2_b 1
#define seg_2_c 1
#define seg_2_d 1
#define seg_2_e 1
#define seg_2_f 1
#define seg_2_g 1

#define fsr_1_pin 1
#define fsr_2_pin 1
#define fsr_3_pin 1
#define fsr_4_pin 1

// Create Button2 buttons
Button2 buttonIncrement;
Button2 buttonDecrement;

String device_name = "ESP32-BT";

//BLE server name
#define bleServerName "ESP32_BLEServer"

Adafruit_MPU6050 mpu;

// BLE Descriptor stuff:
// Service UUID
#define SERVICE_UUID "6c914f48-d292-4d61-a197-d4d5500b60cc"

// Score Characteristic and Descriptor
// Old UUID: 17923275-9745-4b89-b6b2-a59aa7533495
BLECharacteristic scoreChar("080c6fb5-ad9b-4372-a9e7-0e03fa5c4c01", BLECharacteristic::PROPERTY_NOTIFY);
BLEDescriptor* scoreDesc;

// Max Swing Speed Characteristic and Descriptor
BLECharacteristic maxSwingSpeedChar("84331acb-f95d-4ed1-baf2-714ca978878a", BLECharacteristic::PROPERTY_NOTIFY);
BLEDescriptor* maxSwingSpeedDesc;

// Newest Swing Speed Characteristic and Descriptor
BLECharacteristic newSwingSpeedChar("af2ce43c-03a4-4fc4-862f-510ebb114f19", BLECharacteristic::PROPERTY_NOTIFY);
BLEDescriptor* newSwingSpeedDesc;

// Current Temperature Characteristic and Descriptor
BLECharacteristic currentTempChar("c8e62f4c-a675-48a6-896a-3d2ec5e48075", BLECharacteristic::PROPERTY_NOTIFY);
BLEDescriptor* currentTempDesc;

// Bool to determine whether to use directional bias or not
const bool USE_DIRECTIONAL_BIAS = true;

// Boolean to check if device is connected
bool deviceConnected = false;

// Variable to store the points from Current Game
int pointsThisGame = 0;

// Variable to store the total points from all time
int totalPointsAllTime = 0;

// Variable to store the current max swing speed from Current Game
float currentMaxSwingSpeed = 0.0;

// Variables for swing speed
bool swingActive = false;
float swingPeakSpeed = 0.0;
unsigned long swingStartTime = 0;

// Adjusted threshold: 0.133 -> 0.4 -> 0.60
const float swingThreshold = 0.70;  // m/s threshold
const unsigned long swingCooldown = 500; // milliseconds
unsigned long lastSwingEndTime = 0;

// Timer variables
// Stores last time temperature was published
unsigned long previousMillis = 0;    

// Time interval at which to publish data
const long interval = 5000;  

// Global tracking variables (use for latency tracking and dealing with overflow)
uint64_t extendedMicros = 0;
unsigned long lastMicros = 0;
uint32_t microsOverflowCount = 0;

// Stores the start and ending times for transmissions via bluetooth, as well as the latency from the two
unsigned long startTransmissionTime;
unsigned long endTransmissionTime;
unsigned long latency;

// String for values
String pointsString = "";
String newSwingString = "";
String maxSwingString = "";
String currentTemperature = "";
String latencyString = "";
bool messageFinishedSending = false;

//Setup callbacks onConnect and onDisconnect
class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
  };
  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
  }
};

// Code to calibrate gyro
float gyroX_offset = 0.0;
float gyroY_offset = 0.0;
float gyroZ_offset = 0.0;

void calibrateGyro() {
  Serial.println("Hold the board still. Calibrating...");

  float sumX = 0, sumY = 0, sumZ = 0;
  const int samples = 200;

  for (int i = 0; i < samples; i++) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    sumX += g.gyro.x;
    sumY += g.gyro.y;
    sumZ += g.gyro.z;

    delay(5);  // small delay to simulate ~1kHz
  }

  gyroX_offset = sumX / samples;
  gyroY_offset = sumY / samples;
  gyroZ_offset = sumZ / samples;

  Serial.print("Calibration complete. Offsets: ");
  Serial.print(gyroX_offset, 4); Serial.print(", ");
  Serial.print(gyroY_offset, 4); Serial.print(", ");
  Serial.println(gyroZ_offset, 4);
}


void initAccelerometer() {
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

void initBLECharacteristics(BLEService* service) {

  // Setup Current Temperature descriptor
  currentTempDesc = new BLEDescriptor((uint16_t)0x2901);
  currentTempDesc->setValue("Current Temperature");

  // Add current temperature descriptor and notification/indication descriptor for communication to characteristics
  currentTempChar.addDescriptor(currentTempDesc);
  currentTempChar.addDescriptor(new BLE2902());

  // Add characteristic to service
  service->addCharacteristic(&currentTempChar);

  // Setup Max Swing Speed descriptor
  maxSwingSpeedDesc = new BLEDescriptor((uint16_t)0x2901);
  maxSwingSpeedDesc->setValue("Max Swing Speed");

  // Add max swing speed descriptor and notification/indication descriptor for communication to characteristics
  maxSwingSpeedChar.addDescriptor(maxSwingSpeedDesc);
  maxSwingSpeedChar.addDescriptor(new BLE2902());

  // Add characteristic to service
  service->addCharacteristic(&maxSwingSpeedChar);
  
  // Setup Newest Swing Speed descriptor
  newSwingSpeedDesc = new BLEDescriptor((uint16_t)0x2901);
  newSwingSpeedDesc->setValue("Newest Swing Speed");

  // Add new swing speed descriptor and notification/indication descriptor for communication to characteristics
  newSwingSpeedChar.addDescriptor(newSwingSpeedDesc);
  newSwingSpeedChar.addDescriptor(new BLE2902());

  // Add characteristic to service
  service->addCharacteristic(&newSwingSpeedChar);

  // Setup score descriptor
  scoreDesc = new BLEDescriptor((uint16_t)0x2901);
  scoreDesc->setValue("Current Score of Player");

  // Add score descriptor and notification/indication descriptor for communication to characteristics
  scoreChar.addDescriptor(scoreDesc);
  scoreChar.addDescriptor(new BLE2902());

  // Add characteristic to service
  service->addCharacteristic(&scoreChar);
}

// Function to get the "true" time accounting for overflows
uint64_t getSafeMicros() {
  // Get micros() value
  unsigned long currentMicros = micros();

  // Detect overflow (if micros() wrapped around)
  // If overflow occurred, new micros will be less than the last one
  if (currentMicros < lastMicros) {
    microsOverflowCount++;
  }

  // Update lastMicros()
  lastMicros = currentMicros;

  // Create a 64 bit value from the overflow count and the current micros() value
  // This allows for more microseconds to be represented and increases the time period for the timer to wrap around
  // Thereby practically removing the risk of overflow
  // E.g. 2^32 = 4,294,967,296 microseconds ≈ 71.6 minutes
  // 2^64 / (1,000,000 * 60 * 60 * 24 * 365.25) ≈ 584,542 years
  extendedMicros = (uint64_t)microsOverflowCount << 32 | currentMicros;

  // Return this value
  return extendedMicros;
}

void setup() {
  // put your setup code here, to run once:

  // Connect to serial port w/ baud rate 115200
  Serial.begin(115200);

  // Setup Accelerometer
  initAccelerometer();

  // Calibrate gyro
  calibrateGyro();

  // Setup buttons and their click handlers
  buttonIncrement.begin(button_increment_pin);
  buttonIncrement.setClickHandler(clickHandler);

  buttonDecrement.begin(button_decrement_pin);
  buttonDecrement.setClickHandler(clickHandler);

  // Create the BLE Device
  BLEDevice::init(bleServerName);

  // Create the BLE Server
  BLEServer *server = BLEDevice::createServer();
  server->setCallbacks(new MyServerCallbacks());

  // Create the BLE Service
  BLEService *service = server->createService(SERVICE_UUID);

  // Initialize the characteristics
  initBLECharacteristics(service);

  // Start the service
  service->start();

  // Start advertising
  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(SERVICE_UUID);
  server->getAdvertising()->start();

  Serial.println("ESP32 setup for data communication - connect Android App.");
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

  if (deviceConnected) {
    // Get the current millis
    unsigned long currentMillis = millis();

    // High-frequency swing polling
    static unsigned long lastPollTime = 0;

    // Poll for button presses
    buttonIncrement.loop();
    buttonDecrement.loop();

    // Try sending initial score
    // Track whether we've already sent the initial score
    static bool sentInitialScore = false;

    if (deviceConnected && !sentInitialScore) {
      scoreChar.setValue("0");
      scoreChar.notify();
      Serial.println("Initial score sent to connected device.");
      sentInitialScore = true;
    }

    // Use a 10ms loop to check for swings
    if (millis() - lastPollTime >= 10) {
      lastPollTime = millis();

      // Read gyro
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);

      // Get raw angular velocity values and subtract the offset
      float wx = g.gyro.x - gyroX_offset;
      float wy = g.gyro.y - gyroY_offset;
      float wz = g.gyro.z - gyroZ_offset;

      // Add a filter to filter out low gyro velocities below 0.10 rad/s
      float cleanX = (abs(wx) > 0.1) ? wx : 0.0;
      float cleanY = (abs(wy) > 0.1) ? wy : 0.0;
      float cleanZ = (abs(wz) > 0.1) ? wz : 0.0;
      float newSpeed = calculateSwingSpeed(cleanX, cleanY, cleanZ, USE_DIRECTIONAL_BIAS);

      // Use following for graphing purposes
      // Print the current time, the current swing speed, and if the swing is active
      // Will be used with a python script to graph swing speed along with threshold

      //unsigned long currentMillis = millis();
      //Serial.print(currentMillis);
      //Serial.print(",");
      //Serial.print(newSpeed);   // Current swing speed (m/s)
      //Serial.print(",");
      //Serial.println(swingActive ? "1" : "0");  // Optional: indicate active swing

      // Calculate magnitude of total acceleration - we wsill use this along with the swingThreshold to record a swing
      float accelMagnitude = sqrt(pow(a.acceleration.x, 2) + pow(a.acceleration.y, 2) + pow(a.acceleration.z, 2));

      if (!swingActive) {
        // Start of a new swing
        if (newSpeed > swingThreshold && accelMagnitude > 2.0 && (millis() - lastSwingEndTime > swingCooldown)) {
          swingActive = true;
          swingPeakSpeed = newSpeed;
          swingStartTime = millis();
        }
      } else {
        // In an active swing
        if (newSpeed > swingPeakSpeed) {
          swingPeakSpeed = newSpeed;
        }

        // End swing if speed drops below threshold (or fixed duration elapsed)
        if (newSpeed < swingThreshold || millis() - swingStartTime > 700) {
          swingActive = false;
          lastSwingEndTime = millis();

          // Record peak and update BLE logic
          newSwingString = String(swingPeakSpeed) + " m/s";
          float currentMax = checkMaxSwingSpeed(swingPeakSpeed);

          static char maxSwingArray[50];
          static char newSwingArray[50];
          maxSwingString = String(currentMax) + " m/s";
          maxSwingString.toCharArray(maxSwingArray, 50);
          newSwingString.toCharArray(newSwingArray, 50);

          maxSwingSpeedChar.setValue(maxSwingArray);
          maxSwingSpeedChar.notify();
          newSwingSpeedChar.setValue(newSwingArray);
          newSwingSpeedChar.notify();

          Serial.print("SWING DETECTED: ");
          Serial.println(newSwingString);
        }
      }
    }


    // If the interval has passed, get and send data to phone
    if (currentMillis - previousMillis >= interval) {
        previousMillis = currentMillis;

        // Get info from the accelerometer
        sensors_event_t a, g, temp;
        mpu.getEvent(&a, &g, &temp);

        // Generate value from 0 to 100 for probability
        // int randProbability = random(0, 100);

        // If value >= 50, increment, otherwise, don't
        // Basically 50/50 probability every 5 seconds if score is updated
        // if (randProbability >= 50) {
          // incrementPoints();
        // }

        // Send stats over in string format
        pointsString = String(pointsThisGame);
        currentTemperature = String(temp.temperature) + " Celsius";
        
        // After calculations, start the transmission timer
        // Note - this can overflow after 70 min of arduino runtime - might need to fix later
        startTransmissionTime = getSafeMicros();

        // Create static character arrays to send data and fill them
        static char scoreArray[50];
        pointsString.toCharArray(scoreArray, 50);
        
        static char currentTemperatureArray[50];
        currentTemperature.toCharArray(currentTemperatureArray, 50);

        scoreChar.setValue(scoreArray);
        scoreChar.notify();

        currentTempChar.setValue(currentTemperatureArray);
        currentTempChar.notify();

        endTransmissionTime = getSafeMicros();

        // Print to serial
        Serial.print("Current Score: ");
        Serial.println(pointsString);

        Serial.print("Current Temperature: ");
        Serial.println(currentTemperature);

        latency = endTransmissionTime - startTransmissionTime;

        // Turn latency into a string and print to serial (no need to send it over)
        latencyString = "Latency: " + String(latency) + " microseconds";

        Serial.println(latencyString);

        // Print an empty line to seperate data
        Serial.println();
    }
  }
}


// Functions for algorithms and operations

void incrementPoints() {
  pointsThisGame++;
}

void clickHandler(Button2& btn) {
  if (btn == buttonIncrement) {
    pointsThisGame++;
    Serial.println("Increment Button pressed - score incremented");


    // Immediately send a notify message
    static char scoreArray[50];
    pointsString = String(pointsThisGame);
    pointsString.toCharArray(scoreArray, 50);

    if (scoreChar == nullptr) {
      Serial.println("ERROR: scoreChar is NULL");
    }

    scoreChar.setValue(scoreArray);
    scoreChar.notify();
  }
  else if (btn == buttonDecrement) {
    if (pointsThisGame > 0) {
      pointsThisGame--;
      Serial.println("Decrement Button pressed - score decremented");

      // Immediately send a notify message
      static char scoreArray[50];
      pointsString = String(pointsThisGame);
      pointsString.toCharArray(scoreArray, 50);

      
      if (scoreChar == nullptr) {
        Serial.println("ERROR: scoreChar is NULL");
      }

      scoreChar.setValue(scoreArray);
      scoreChar.notify();
    }
    else {
      Serial.println("Score is currently 0 - ignoring.");
    }
  }
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

float calculateSwingSpeed(float xVelocity, float yVelocity, float zVelocity, bool useBias) {
  // Assume "r" - or the distance to the rotation center - is 10 cm.
  float r = 0.10;

  // Calculate magnitude of the total angular velocity
  float angVelocity;

  if (useBias) {
    // Bias towards the x direction, since given the orientation and forehand/backhand, moving moreso on x axis
    angVelocity = sqrt(1.0 * pow(xVelocity, 2) + 0.3 * pow(yVelocity, 2) + 0.4 * pow(zVelocity, 2));
  }
  else {
    angVelocity = sqrt(pow(xVelocity, 2) + pow(yVelocity, 2) + pow(zVelocity, 2));
  }

  // Calculate final swing speed
  float finalSwingSpeed = angVelocity * r;

  return finalSwingSpeed;
}

float calculateForce(float sensorValue) {
  // Get the voltage from the analog value
  float voltage = sensorValue * (3.3 / 1023.0);

  float resistance;

  // Use the voltage divider equation to calculate resistance
  // Vout = Vcc * (R_s / (R_s + R_f))

  // Using 10k resistor - solve for R_f
  resistance = ((3.3 - voltage) * 10000)/voltage;
}
