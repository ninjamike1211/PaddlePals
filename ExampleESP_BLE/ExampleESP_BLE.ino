// Credit to Evandro Copercini for original example code: 
// https://docs.espressif.com/projects/arduino-esp32/en/latest/api/bluetooth.html

// Credit to Rui Santos for example on interfacing the ESP-32 with outside components and processing messages
// as well as the web server used to upload sketches OTA (or over the air) (Credit to Espressif for original OTA code as well):
// https://randomnerdtutorials.com/esp32-bluetooth-classic-arduino-ide/
// https://randomnerdtutorials.com/esp32-over-the-air-ota-programming/

// Credit to Robin2 for help with parsing serial input:
// https://forum.arduino.cc/t/serial-input-basics/278284/2

// Credit to Adafruit and Random Nerd Tutorials for demo regarding MPU6050 accelerometer:
// https://randomnerdtutorials.com/esp32-mpu-6050-accelerometer-gyroscope-arduino/

// Linear Velocity to Angular Velocity:
// https://math.libretexts.org/Bookshelves/Precalculus/Book%3A_Trigonometry_(Sundstrom_and_Schlicker)/01%3A_The_Trigonometric_Functions/1.04%3A_Velocity_and_Angular_Velocity

// Credit to Instructables and Arduino project hub for help with Seven-Segment:
// https://www.instructables.com/7-Segment-Display-On-Arduino/
// https://projecthub.arduino.cc/aboda243/get-started-with-seven-segment-5754a8

// Credit to TechKnowLab for help with the FSR:
// https://techknowlab.com/thin-film-pressureor-force-sensor-with-arduino/


// Libraries for BLE communication
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// Libraries for sensor communication
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

// Libraries for OTA communication (allows for remote upload without serial)
// TEMPORARILY DISABLED TO SAVE SPACE
// #include <WiFi.h>
// #include <WiFiClient.h>
// #include <WebServer.h>
// #include <ESPmDNS.h>
// #include <Update.h>

// Library for button communication
#include <Button2.h>

// Button pins
#define button_increment_pin 18
#define button_decrement_pin 17

// Seven-segment pins - CHANGE LATER

// Segment pins for display 1
#define seg1_a 5
#define seg1_b 16
#define seg1_c 15
#define seg1_d 13
#define seg1_e 14
#define seg1_f 23
#define seg1_g 19

// Segment pins for display 2 (moved to avoid FSR conflicts)
#define seg2_a 32
#define seg2_b 12
#define seg2_c 4  // was 25 (conflicts with fsr_4_pin)
#define seg2_d 0
#define seg2_e 2
#define seg2_f 22
#define seg2_g 21  // was 33 (conflicts with fsr_2_pin)

// Pins for FSRs

#define fsr_1_pin 35
#define fsr_2_pin 34
#define fsr_3_pin 27
#define fsr_4_pin 25

// Pins for accelerometer
#define SCL_PIN 33
#define SDA_PIN 26

// Constants to connect to the ESP32 via OTA
// TEMPORARILY DISABLED TO SAVE SPACE
/*
const char* host = "esp32";
const char* ssid = "REPLACE_WITH_YOUR_SSID";
const char* password = "REPLACE_WITH_YOUR_PASSWORD";

// WebServer to use
WebServer server(80);

// Web page to display when connected to IP
const char* loginIndex = 
"<form name='f'><table width='20%' bgcolor='A09F9F' align='center'><tr><td colspan=2><center><b>ESP32 Login</b></center></td></tr><tr><td>User:</td><td><input type='text' size=15 name='u'></td></tr><tr><td>Pass:</td><td><input type='password' size=15 name='p'></td></tr><tr><td><input type='submit' onclick='check(this.form)' value='Login'></td></tr></table></form><script>function check(f){if(f.u.value=='admin'&&f.p.value=='admin'){window.open('/serverIndex')}else{alert('Error')}}</script>";

// Server Index page to allow for files to be uploaded
const char* serverIndex = 
"<script src='https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js'></script><form method='POST' action='#' enctype='multipart/form-data' id='f'><input type='file' name='update'><input type='submit' value='Update'></form><div id='p'>progress: 0%</div><script>$('form').submit(function(e){e.preventDefault();var f=$('#f')[0];var d=new FormData(f);$.ajax({url:'/update',type:'POST',data:d,contentType:false,processData:false,xhr:function(){var x=new window.XMLHttpRequest();x.upload.addEventListener('progress',function(evt){if(evt.lengthComputable){var per=evt.loaded/evt.total;$('#p').html('progress: '+Math.round(per*100)+'%');}},false);return x;},success:function(d,s){console.log('success!')},error:function(a,b,c){}});});</script>";
*/

// Create array to get quadrant hits
int quadrantHits[4] = {0, 0, 0, 0};  // Q1-Q4 hit counts

// Create table to store correct states for segments corresponding to digits
const bool digitSegments[16][7] = {
  {1,1,1,1,1,1,0}, // 0
  {0,1,1,0,0,0,0}, // 1
  {1,1,0,1,1,0,1}, // 2
  {1,1,1,1,0,0,1}, // 3
  {0,1,1,0,0,1,1}, // 4
  {1,0,1,1,0,1,1}, // 5
  {1,0,1,1,1,1,1}, // 6
  {1,1,1,0,0,0,0}, // 7
  {1,1,1,1,1,1,1}, // 8
  {1,1,1,1,0,1,1}, // 9
  {1,1,1,0,1,1,1}, // A
  {0,0,1,1,1,1,1}, // b
  {1,0,0,1,1,1,0}, // C
  {0,1,1,1,1,0,1}, // d
  {1,0,0,1,1,1,1}, // E
  {1,0,0,0,1,1,1}  // F
};

// Group the seven segment display pins based on display number
int segPins1[] = {seg1_a, seg1_b, seg1_c, seg1_d, seg1_e, seg1_f, seg1_g};
int segPins2[] = {seg2_a, seg2_b, seg2_c, seg2_d, seg2_e, seg2_f, seg2_g};

// Create Button2 buttons
Button2 buttonIncrement;
Button2 buttonDecrement;

String device_name = "ESP32-BT";

//BLE server name
#define bleServerName "ESP32_BLEServer"

// Characteristic UUIDs
#define SCORE_CHAR_UUID "27923275-9745-4b89-b6b2-a59aa7533495"
#define MAX_SWING_SPEED_CHAR_UUID "8b2c1a45-7d3e-4f89-a2b1-c5d6e7f8a9b0"
#define HIT_SUMMARY_CHAR_UUID "9c3d2b56-8e4f-5a90-b3c2-d6e7f8a9b0c1"

Adafruit_MPU6050 mpu;

// BLE Descriptor stuff:
// Service UUID
#define SERVICE_UUID "6c914f48-d292-4d61-a197-d4d5500b60cc"

// All characteristics as pointers - will be created via service
BLECharacteristic* scoreChar = nullptr;
BLECharacteristic* maxSwingSpeedChar = nullptr;
BLECharacteristic* hitSummaryChar = nullptr;

// Descriptors
BLEDescriptor* scoreDesc;
BLEDescriptor* maxSwingSpeedDesc;
BLEDescriptor* hitSummaryDesc;

// Bool to determine whether to use directional bias or not
const bool USE_DIRECTIONAL_BIAS = true;

// Boolean to check if device is connected
bool deviceConnected = false;

// Boolean to check if game has started
bool gameStarted = false;

// Variable to store the points from Current Game
int pointsThisGame = 0;

// Variable to store the opponent's points from Current Game
int opponentPoints = 0;

// Variable to store the total points from all time
int totalPointsAllTime = 0;

// Variable to store the current max swing speed from Current Game
float currentMaxSwingSpeed = 0.0;

// Variables for swing speed
bool swingActive = false;

// Variables to store the peak swing speed (weighed and raw)
float swingPeakWeighted = 0.0f;
float swingPeakMagnitude = 0.0f;

// Variable to store the time in which the swing started
unsigned long swingStartTime = 0;

// Adjusted threshold: 0.133 -> 0.4 -> 0.60 -> 0.70
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

// Char arrays for values
char pointsString[50];
char newSwingString[50];
char maxSwingString[50]; 
char latencyString[100];
bool messageFinishedSending = false;

// Seven-segment code
// Update seven segment displays
void updateSevenSegmentDisplays(int playerScore, int opponentScore) {
  displayDigit(playerScore, segPins1);   // left digit
  displayDigit(opponentScore, segPins2);  // right digit
}

// Clear seven segment displays
void clearSevenSegmentDisplays() {
  for (int i = 0; i < 7; i++) {
    digitalWrite(segPins1[i], HIGH);  // HIGH = off for common anode
    digitalWrite(segPins2[i], HIGH);
  }
}

// Seven segment display logic
void displayDigit(int digit, int segPins[]) {
  // Go through table for the digit, turn segments on/off based on if they are 1 or 0
  for (int i = 0; i < 7; i++) {
    // If 1, set as low - else, set as high
    digitalWrite(segPins[i], digitSegments[digit][i] ? LOW : HIGH);
  }
}

//Setup callbacks onConnect and onDisconnect
class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    Serial.println("Device connected via BLE");
  };
  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    Serial.println("Device disconnected from BLE");
    // Restart advertising
    BLEDevice::getAdvertising()->start();
  }
};

// Callback for when notifications are enabled/disabled
class MyCharacteristicCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* pChar) override {
    String val = pChar->getValue();
    Serial.print("Write received on ");
    Serial.print(pChar->getUUID().toString().c_str());
    Serial.print(": ");
    Serial.println(val.c_str());

    // Only respond to writes on the SCORE_CHAR_UUID
    if (pChar->getUUID().toString() == SCORE_CHAR_UUID) {
      if (val == "RESET") {
        // Reset game state
        pointsThisGame  = 0;
        opponentPoints = 0;
        gameStarted = false;
        clearSevenSegmentDisplays();

        // Update the 7‑segment displays with 0s
        updateSevenSegmentDisplays(pointsThisGame, opponentPoints);

        // Clear hit detection
        for (int i = 0; i < 4; i++) {
          quadrantHits[i] = 0;
        }

        // Notify the phone of the new score
        char buf[20];
        snprintf(buf, sizeof(buf), "%d,%d,%d", pointsThisGame, opponentPoints, gameStarted);
        scoreChar->setValue(buf);
        scoreChar->notify();
        
        // Notify the phone of the reset hit summary
        char hitArray[100];
        snprintf(hitArray, sizeof(hitArray), "%d,%d,%d,%d", 
                 quadrantHits[0], quadrantHits[1], quadrantHits[2], quadrantHits[3]);
        if (hitSummaryChar != nullptr) {
          hitSummaryChar->setValue(hitArray);
          hitSummaryChar->notify();
        }
        
        Serial.println("Scores reset to 0,0");
      }
    }
  }

  void onNotify(BLECharacteristic* pCharacteristic) {
    Serial.println("Notification sent for characteristic: " + String(pCharacteristic->getUUID().toString().c_str()));
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
  Serial.println("Initializing BLE characteristics...");
  
  // Create score characteristic
  Serial.println("Creating score characteristic...");
  scoreChar = service->createCharacteristic(
    SCORE_CHAR_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_WRITE
  );
  
  if (scoreChar == nullptr) {
    Serial.println("ERROR: Failed to create score characteristic!");
    return;
  }
  
  // Add descriptors to score characteristic
  scoreDesc = new BLEDescriptor((uint16_t)0x2901);
  scoreDesc->setValue("Current Score of Player");
  scoreChar->addDescriptor(scoreDesc);
  
  // Add CCCD for notifications
  BLE2902* scoreCCCD = new BLE2902();
  scoreCCCD->setNotifications(true);
  scoreChar->addDescriptor(scoreCCCD);
  
  // Add callback
  scoreChar->setCallbacks(new MyCharacteristicCallbacks());
  Serial.println("Score characteristic setup complete");

    // Create max swing speed characteristic
  Serial.println("Creating max swing speed characteristic...");
  maxSwingSpeedChar = service->createCharacteristic(
    MAX_SWING_SPEED_CHAR_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  
  if (maxSwingSpeedChar == nullptr) {
    Serial.println("ERROR: Failed to create max swing speed characteristic!");
    return;
  }
  
  maxSwingSpeedDesc = new BLEDescriptor((uint16_t)0x2901);
	maxSwingSpeedDesc->setValue("Max Swing Speed");

  maxSwingSpeedChar->addDescriptor(maxSwingSpeedDesc);
  maxSwingSpeedChar->addDescriptor(new BLE2902());
  Serial.println("Max swing speed characteristic setup complete");

  Serial.println("Creating hit summary characteristic...");
  hitSummaryChar = service->createCharacteristic(
    HIT_SUMMARY_CHAR_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  
  if (hitSummaryChar == nullptr) {
    Serial.println("ERROR: Failed to create new hit summary characteristic!");
    return;
  }
  
  hitSummaryDesc = new BLEDescriptor((uint16_t)0x2901);
  hitSummaryDesc->setValue("Hit Summary");
  hitSummaryChar->addDescriptor(hitSummaryDesc);
  hitSummaryChar->addDescriptor(new BLE2902());
  Serial.println("Hit summary setup complete");

  
  Serial.println("BLE characteristics initialization complete");

}

void initSevenSegmentDisplays() {
  // Write all of the pins as output + high (since with common anode, low = on, high = off)
  for (int i = 0; i < 7; i++) {
    pinMode(segPins1[i], OUTPUT);
    pinMode(segPins2[i], OUTPUT);
    digitalWrite(segPins1[i], HIGH);
    digitalWrite(segPins2[i], HIGH);
  }
}


// Initialization code to setup web server
// TEMPORARILY DISABLED TO SAVE SPACE
/*
void initWebServer() {
  // Connect to WiFi network
  WiFi.begin(ssid, password);
  Serial.println("");

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // use mdns for host name resolution
  if (!MDNS.begin(host)) { //http://esp32.local
    Serial.println("Error setting up MDNS responder!");
    while (1) {
      delay(1000);
    }
  }
  Serial.println("mDNS responder started");
  // return index page which is stored in serverIndex
  server.on("/", HTTP_GET, []() {
    server.sendHeader("Connection", "close");
    server.send(200, "text/html", loginIndex);
  });
  server.on("/serverIndex", HTTP_GET, []() {
    server.sendHeader("Connection", "close");
    server.send(200, "text/html", serverIndex);
  });
  // handling uploading firmware file
  server.on("/update", HTTP_POST, []() {
    server.sendHeader("Connection", "close");
    server.send(200, "text/plain", (Update.hasError()) ? "FAIL" : "OK");
    ESP.restart();
  }, []() {
    HTTPUpload& upload = server.upload();
    if (upload.status == UPLOAD_FILE_START) {
      Serial.printf("Update: %s\n", upload.filename.c_str());
      if (!Update.begin(UPDATE_SIZE_UNKNOWN)) { //start with max available size
        Update.printError(Serial);
      }
    } else if (upload.status == UPLOAD_FILE_WRITE) {
      // flashing firmware to ESP
      if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
        Update.printError(Serial);
      }
    } else if (upload.status == UPLOAD_FILE_END) {
      if (Update.end(true)) { //true to set the size to the current progress
        Serial.printf("Update Success: %u\nRebooting...\n", upload.totalSize);
      } else {
        Update.printError(Serial);
      }
    }
  });
  server.begin();
}
*/

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

// Functions for algorithms and operations
void incrementPoints() {
  pointsThisGame++;
}

void clickHandler(Button2& btn) {
  bool scoreChanged = false;
  // Start the game
  if (btn == buttonIncrement && !gameStarted) {
    gameStarted = true;
    clearSevenSegmentDisplays();
  }
  else if (btn == buttonIncrement && pointsThisGame <= 15 && gameStarted) {
    pointsThisGame++;
    Serial.println("Player score incremented");
    scoreChanged = true;
  }
  else if (btn == buttonDecrement && opponentPoints <= 15 && gameStarted) {
    opponentPoints++;
    Serial.println("Opponent score incremented");
    scoreChanged = true;
  }
  else if (pointsThisGame + 1 > 15 && gameStarted) {
    Serial.println("Player Score is 15 - increment ignored");
  }
  else if (opponentPoints + 1 > 15 && gameStarted) {
    Serial.println("Opponent Score is 15 - increment ignored");
  }
  else {
    Serial.println("Game isn't started - hit the player score button!");
  }

  // Immediately update BLE if connected
  if (deviceConnected) {
    static char scoreArray[50];
    snprintf(scoreArray, sizeof(scoreArray), "%d,%d,%d", pointsThisGame, opponentPoints, gameStarted);
    
    if (&scoreChar == nullptr) {
      Serial.println("ERROR: scoreChar is NULL");
    } else {
      scoreChar->setValue(scoreArray);
      scoreChar->notify();
    }
  }

  // Update seven-segment displays if score changed
  if (scoreChanged) {
    updateSevenSegmentDisplays(pointsThisGame, opponentPoints);
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
  if (numberOfGames == 0) return 0.0;
  float averagePoints = (float)totalNumberOfPoints / numberOfGames;
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

float calculateForce(int analogValue) {
  // Convert ADC to voltage (assuming ESP32 12-bit ADC and 3.3V)
  float voltage = analogValue * (3.3 / 4095.0);

  // Avoid divide-by-zero errors
  if (voltage <= 0.01) return 0;

  // Calculate resistance of the FSR
  const float R_FIXED = 10000.0;  // 10k Ohm resistor
  float resistance = (3.3 - voltage) * R_FIXED / voltage;

  // From datasheet: R = 153.18 / Force
  // Use approximate equation F = K/R due to linear relationship in log-log graph from data
  // Technically it's more like F = (R / 153.18)^(-1.43), but this is approximately close enough.
  // F is in Kg
  float force = 153.18 / resistance;  // in kg (approximate)

  // Convert to grams
  return force * 1000.0;
}

void updateQuadrantHits() {
  // TODO: Remove this cooldown when integrating into swing detection logic
  // Future: Use "one hit per swing" instead of global cooldown
  static unsigned long lastHitTime = 0;
  const unsigned long HIT_COOLDOWN = 1000;  // 1 second between hits (temporary for testing)
  
  // Skip if still in cooldown period
  if (millis() - lastHitTime < HIT_COOLDOWN) {
    return;
  }
  
  // For testing: only check FSR 1 (pin 36), set others to 0
  int analogValues[4] = {
    analogRead(fsr_1_pin),  // Only connected FSR
    0,                      // Disconnected - force to 0
    0,                      // Disconnected - force to 0
    0                       // Disconnected - force to 0
  };

  float forces[4];
  for (int i = 0; i < 4; i++) {
    forces[i] = calculateForce(analogValues[i]);
  }

  // Debug: Print raw values for FSR 1
  static unsigned long lastDebugTime = 0;
  if (millis() - lastDebugTime > 1000) {  // Print every second
    Serial.print("FSR1 raw: ");
    Serial.print(analogValues[0]);
    Serial.print(" -> ");
    Serial.print(forces[0]);
    Serial.println("g");
    lastDebugTime = millis();
  }

  // Find max force and index
  int maxIndex = 0;
  float maxForce = forces[0];
  for (int i = 1; i < 4; i++) {
    if (forces[i] > maxForce) {
      maxForce = forces[i];
      maxIndex = i;
    }
  }

  // Only count hits above noise threshold  
  const float HIT_THRESHOLD_GRAMS = 500.0;  // raised to reduce false positives
  if (maxForce >= HIT_THRESHOLD_GRAMS) {
    quadrantHits[maxIndex]++;
    lastHitTime = millis();  // Reset cooldown timer

    // Format BLE message
    static char hitArray[100];
    snprintf(hitArray, sizeof(hitArray), "%d,%d,%d,%d", 
             quadrantHits[0], quadrantHits[1], quadrantHits[2], quadrantHits[3]);

    Serial.println(hitArray);

    if (hitSummaryChar != nullptr) {
      hitSummaryChar->setValue(hitArray);
      hitSummaryChar->notify();
    }
  }
}


void setup() {
  // put your setup code here, to run once:

  // Connect to serial port w/ baud rate 115200
  Serial.begin(115200);

  // Setup Web Server
  // initWebServer(); // TEMPORARILY DISABLED TO SAVE SPACE

  // Setup Accelerometer
  initAccelerometer();

  // Setup seven-segment displays
  initSevenSegmentDisplays();

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

  advertising->setScanResponse(false);
  advertising->setMinPreferred(0x0);

  server->getAdvertising()->start();

  Serial.println("ESP32 setup for data communication - connect Android App.");

  Serial.println("BLE Service started and advertising...");
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

  // Outside of device connected loop, handle web server operations
  // server.handleClient(); // TEMPORARILY DISABLED TO SAVE SPACE

  // Delay for 1 ms to prevent problems
  delay(1);

  if (deviceConnected) {

    // Get the current millis
    unsigned long currentMillis = millis();

    // High-frequency swing polling
    static unsigned long lastPollTime = 0;

    // Poll for button presses
    buttonIncrement.loop();
    buttonDecrement.loop();

    // Check FSR sensors for quadrant hits (temporary for testing)
    updateQuadrantHits();

    // Try sending initial score - but only after a small delay to ensure BLE is ready
    static bool sentInitialScore = false;

    static unsigned long connectionTime = 0;
    
    // Record when we first connected
    if (!sentInitialScore && connectionTime == 0) {
      connectionTime = millis();
    }

        // Wait 1 second after connection before sending initial score
    if (deviceConnected && !sentInitialScore && (millis() - connectionTime > 1000)) {
      if (scoreChar != nullptr) {
        scoreChar->setValue("0");
        scoreChar->notify();
        Serial.println("Initial score sent to connected device.");
        Serial.println("Notification attempt result: " + String(scoreChar->getValue().c_str()));
        sentInitialScore = true;
      }
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

      // Compute weighted swing speed
      float weightedSpeed = calculateSwingSpeed(cleanX, cleanY, cleanZ, USE_DIRECTIONAL_BIAS);

      // Compute true (unbiased) swing speed for reporting
      float magnitudeSpeed  = calculateSwingSpeed(cleanX, cleanY, cleanZ, /*useBias*/ false);

      // Use following for graphing purposes
      // Print the current time, the current swing speed, and if the swing is active
      // Will be used with a python script to graph swing speed along with threshold

      //unsigned long currentMillis = millis();
      //Serial.print(currentMillis);
      //Serial.print(",");
      //Serial.print(weightedSpeed);   // Current swing speed (m/s)
      //Serial.print(",");
      //Serial.println(swingActive ? "1" : "0");  // Optional: indicate active swing

      // Calculate magnitude of total acceleration - we wsill use this along with the swingThreshold to record a swing
      float accelMagnitude = sqrt(pow(a.acceleration.x, 2) + pow(a.acceleration.y, 2) + pow(a.acceleration.z, 2));
      // Remove gravity from triggering swings by itself
      float accDynamic = fabs(accelMagnitude - 9.80665f);     // remove gravity

      if (!swingActive) {
        // Start of a new swing
        if (weightedSpeed > swingThreshold && accDynamic > 2.0 && (millis() - lastSwingEndTime > swingCooldown)) {
          swingActive = true;
          swingPeakWeighted = weightedSpeed;
          // Get the raw magnitude speed
          swingPeakMagnitude = magnitudeSpeed;
          swingStartTime = millis();
        }
      } else {
        // In an active swing
        if (weightedSpeed > swingPeakWeighted) {
          swingPeakWeighted = weightedSpeed;
          // Update the corresponding raw magnitude
          swingPeakMagnitude = magnitudeSpeed;
        }

        // End swing if speed drops below threshold (or fixed duration elapsed)
        if (weightedSpeed < swingThreshold || millis() - swingStartTime > 700) {
          swingActive = false;
          lastSwingEndTime = millis();

          // report the raw magnitude peak over BLE
          snprintf(newSwingString, sizeof(newSwingString), "%.2f m/s", swingPeakMagnitude);
          float currentMax = checkMaxSwingSpeed(swingPeakMagnitude);

          static char maxSwingArray[50];
          snprintf(maxSwingString, sizeof(maxSwingString), "%.2f m/s", currentMax);
          snprintf(maxSwingArray, sizeof(maxSwingArray), "%.2f m/s", currentMax);
          if (maxSwingSpeedChar) {
            maxSwingSpeedChar->setValue(maxSwingArray);
            maxSwingSpeedChar->notify();
          }

          Serial.print("SWING DETECTED: ");
          Serial.println(newSwingString);
          Serial.print("Current Max: ");
          Serial.println(maxSwingString);
        }
      }
    }


    // If the interval has passed, get and send data to phone
    if (currentMillis - previousMillis >= interval) {
        previousMillis = currentMillis;


        // Generate value from 0 to 100 for probability
        // int randProbability = random(0, 100);

        // If value >= 50, increment, otherwise, don't
        // Basically 50/50 probability every 5 seconds if score is updated
        // if (randProbability >= 50) {
          // incrementPoints();
        // }

        // Send stats over in string format
        snprintf(pointsString, sizeof(pointsString), "%d,%d,%d", pointsThisGame, opponentPoints, gameStarted);
        
        // After calculations, start the transmission timer
        // Note - this can overflow after 70 min of arduino runtime - might need to fix later
        startTransmissionTime = getSafeMicros();

        
        if (scoreChar != nullptr) {
          scoreChar->setValue(pointsString);
          scoreChar->notify();
        }


        endTransmissionTime = getSafeMicros();

        // Print to serial
        Serial.print("Current Score: ");
        Serial.println(pointsString);


        latency = endTransmissionTime - startTransmissionTime;

        // Turn latency into a string and print to serial (no need to send it over)
        snprintf(latencyString, sizeof(latencyString), "Latency: %lu microseconds", latency);

        Serial.println(latencyString);

        // Print an empty line to seperate data
        Serial.println();
    }
  } else {
    // Reset connection tracking when disconnected
    static unsigned long connectionTime = 0;
    static bool sentInitialScore = false;
    connectionTime = 0;
    sentInitialScore = false;
  }
}

