// Libraries for sensor communication
#include "BluetoothSerial.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

// Source: ChatGPT for help regarding the test script

Adafruit_MPU6050 mpu;

void setup() {
  // put your setup code here, to run once:

  // Connect to serial port w/ baud rate 115200
  Serial.begin(115200);

  // Setup Accelerometer
  initAccelerometer();

  Serial.println("ESP32 setup for data communication - connect Android App.");
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

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  float wx = g.gyro.x;
  float wy = g.gyro.y;
  float wz = g.gyro.z;

  // Optional: Apply deadzone
  if (abs(wx) < 0.1) wx = 0;
  if (abs(wy) < 0.1) wy = 0;
  if (abs(wz) < 0.1) wz = 0;

  // Check for dominant axis
  if (abs(wx) > abs(wy) && abs(wx) > abs(wz)) {
    Serial.println("X-axis dominant (pitch) swing");
  } else if (abs(wy) > abs(wz)) {
    Serial.println("Y-axis dominant (yaw) swing");
  } else {
    Serial.println("Z-axis dominant (roll) swing");
  }

  delay(200); // Wait a bit to avoid spamming
}