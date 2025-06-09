// Basic demonstration of 2-way connection between phone and ESP-32
// Credit to Evandro Copercini for original example code: 
// https://docs.espressif.com/projects/arduino-esp32/en/latest/api/bluetooth.html

// Credit to Rui Santos for example on interfacing the ESP-32 with outside components and processing messages:
// https://randomnerdtutorials.com/esp32-bluetooth-classic-arduino-ide/

// Credit to Robin2 for help with parsing serial input:
// https://forum.arduino.cc/t/serial-input-basics/278284/2

#include "BluetoothSerial.h"

String device_name = "ESP32-BT";

// Check if Bluetooth is available
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

BluetoothSerial SerialBT;

// Variable to store the points from Current Game
int pointsThisGame = 0;

// Variable to store the total points from all time
int totalPointsAllTime = 0;

// Variable to store the current max swing speed from Current Game
int currentMaxSwingSpeed = 0;

// Timer variables
// Stores last time temperature was published
unsigned long previousMillis = 0;    

// Time interval at which to publish data
const long interval = 5000;  

// String variables for sent and received messages
String entireMessageFromPhone = "";
String variableFromPhone = "";
char variableFromPhoneArr[50] = {0};

int valueFromPhone = 0;
String pointsString = "";
String newSwingString = "";
String maxSwingString = "";
bool messageFinishedSending = false;


void setup() {
  // put your setup code here, to run once:

  // Connect to serial port w/ baud rate 115200
  Serial.begin(115200);

  // Start Bluetooth Serial Connection with ESP-32 device
  SerialBT.begin(device_name);

  // Print that serial connection has been established
  Serial.printf("The device with name \"%s\" is started.\nNow you can pair it with Bluetooth!\n", device_name.c_str());
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
      // Generate random swing speed value
      int randSwingSpeed = random(0, 50);

      // Generate value from 0 to 100 for probability
      int randProbability = random(0, 100);

      // If value >= 50, increment, otherwise, don't
      // Basically 50/50 probability every 5 seconds if score is updated
      if (randProbability >= 50) {
        incrementPoints();
      }

      // Check the max swing speed
      int currentMax = checkMaxSwingSpeed(randSwingSpeed);

      // Send stats over in string format
      pointsString = "Current Number Of Points By This Player: " + String(pointsThisGame);
      newSwingString = "Newest Swing Speed: " + String(randSwingSpeed);
      maxSwingString = "Max Swing Speed: " + String(currentMax);
      
      SerialBT.println(pointsString);
      SerialBT.println(newSwingString);
      SerialBT.println(maxSwingString);
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

  if (messageFinishedSending) {
      // Convert message to char array and put string in it
      char charBuffer[entireMessageFromPhone.length() + 1];
      entireMessageFromPhone.toCharArray(charBuffer, entireMessageFromPhone.length() + 1);

      // Parse the string
      parseStringForValues(charBuffer);

      String messageSentBack = "";

      // Check the variable from phone, respond accordingly
      if (variableFromPhone == "past_total") {
        totalPointsAllTime = calculateTotalPointsAllTime(valueFromPhone);
        messageSentBack = "Total Points All Time: " + String(totalPointsAllTime);
      }
      else if (variableFromPhone == "num_of_past_games") {
        // Add 1 since we are including the current game
        float averagePointsPerGame = calculateAveragePointsPerGame(valueFromPhone + 1, totalPointsAllTime);
        messageSentBack = "Average Points per Game: " + String(averagePointsPerGame);
      }
      else if (variableFromPhone == "past_max_swing_speed") {
          if (checkAllTimeSwingSpeed(valueFromPhone)) {
            messageSentBack = "New Max Swing Speed: " + String(currentMaxSwingSpeed);
          }
          else {
            messageSentBack = "Sorry, no new record.";
          }
      }

      // Send the message back through SerialBT
      SerialBT.println(messageSentBack);

      // Mark message finished sending as false
      messageFinishedSending = false;
  }
}


// Functions for algorithms and operations

void incrementPoints() {
  pointsThisGame++;
}

int checkMaxSwingSpeed(int swingSpeed) {
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
