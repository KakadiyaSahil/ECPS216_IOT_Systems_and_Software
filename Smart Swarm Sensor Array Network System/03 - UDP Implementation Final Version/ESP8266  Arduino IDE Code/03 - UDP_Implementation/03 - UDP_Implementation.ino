/*
Name: Sahil Mukeshbhai Kakadiya
Profile: Master's Student
UCI Student ID: 93282494
University: University of California, Irvine (UCI)
Course: The Professional Master of Embedded and Cyber-Physical Systems
Major: Computer Engineering
Subject Name: ECPS 216 - F'24: IoT Systems & Software
Assignment Name: Programming Assignment 2 (Final version) - UDP Protocol Implementaed
({Raspberry Pi and 1 ESP8266 Swarm Communication Using LED Indicators and Light Sensors)

*/

/*  -----------------   Start of the Assignment ------------------*/



#include <stdio.h>
#include <string.h>

#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <Ticker.h>

const char *ssid = "sahil"; // WiFi credentials
const char *password = "Sahil9805";

// PhotoDiode Pin
#define LDR_PIN 17

// LED Pin
#define LED_PIN 16

// Define storage buffer sizes
#define MAX_DATA_VALUE_STORE 20
#define MAX_AVERAGE_VALUE_STORE 5
#define DATA_USE_FOR_AVERAGE 5

// Define timing intervals (in seconds)
#define LED_BLINK_PERIOD 0.5
#define SENSOR_DATA_READ_PERIOD 1
#define SENSOR_DATA_SEND_PERIOD 2

// Tickers for periodic interrupts to handle different tasks
Ticker ledTicker;
Ticker ldrTicker;
Ticker udpTicker;
Ticker waitTicker;

WiFiUDP udp; // UDP instance for communication

// Enum to track the current status of the ESP8266
enum CurrStatus
{
  IDEL = 0,           // Idle state, waiting for handshake
  CONFIGURED = 1,     // Configuration complete
  HANDSHAKE_DONE = 2, // Handshake successful
  SENDING_DATA = 3,   // Sending sensor data
};

// Struct to store the target device (Raspberry Pi) configuration
struct TargetDeviceConfig
{
  String DeviceTokenID = "RaspBerry_PI_5"; // Device ID for verification
  String IP_address;                       // IP address of the target device
  int Listening_port;                      // Listening port of target device
  int sending_port;                        // Sending port of target device
} targetDeviceConfig;

// Struct to store the ESP8266 configuration and sensor data
struct DeviceConfig
{
  String IP_address;                                   // IP address of the ESP8266
  int Listening_port = 54321;                          // Port for receiving messages
  int Sending_port = 244;                              // Port for sending messages
  CurrStatus currentStatus = IDEL;                     // Initial status is IDLE
  bool LDRDataisReady = false;                         // Flag to indicate if LDR data is ready
  int LDRreadings[MAX_DATA_VALUE_STORE] = {0};         // Buffer to store LDR sensor readings
  float LDRAvgreadings[MAX_AVERAGE_VALUE_STORE] = {0}; // Buffer to store averaged LDR readings
  int currSUM_DATA = 0;                                // Sum of recent sensor readings for averaging
} deviceConfig;

bool checkForConfigurationMessage(TargetDeviceConfig *config, DeviceConfig *DevConfig);
void sendUDPMessage(String message, TargetDeviceConfig *config);
void Target_deConfiguration(TargetDeviceConfig *config, DeviceConfig *DevConfig);
void system_Configuration(void);

// ISR functions for timer interrupts
void toggleLed();
void readLDR();
void sendAverage();

int readingCount = 0;

void setup()
{
  Serial.begin(9600); // Initialize serial communication
  delay(100);

  // GPIO configuration
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // Turn off onboard LED (inverted logic)
  analogRead(LDR_PIN);         // Configure analog pin for LDR reading

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print("."); // Show progress while connecting
    delay(500);        // Prevent watchdog reset by delaying here
  }
  Serial.println("\nWiFi connected successfully.");
  deviceConfig.IP_address = WiFi.localIP().toString();
  Serial.println("IP address of our device: " + deviceConfig.IP_address);

  // Start listening on the specified UDP port
  udp.begin(deviceConfig.Listening_port);
}

void loop()
{
  // Handle different states of the ESP8266

  // Stage 1: Idle, waiting for handshake
  if (deviceConfig.currentStatus == IDEL)
  {
    Serial.println("Device is in Idle state, waiting for handshake.");
    while (deviceConfig.currentStatus == IDEL)
    {
      if (checkForConfigurationMessage(&targetDeviceConfig, &deviceConfig))
      {
        deviceConfig.currentStatus = HANDSHAKE_DONE; // Move to handshake done state if message is valid
      }
    }
  }

  // Stage 2: Handshake done, configure the system
  if (deviceConfig.currentStatus == HANDSHAKE_DONE)
  {
    Serial.println("Handshake completed, configuring system.");
    system_Configuration();
  }

  // Stage 3: Sending data, handle incoming commands (e.g., stop sync)
  if (deviceConfig.currentStatus == SENDING_DATA)
  {
    Serial.println("System is sending data.");
    if (checkForConfigurationMessage(&targetDeviceConfig, &deviceConfig))
    {
      Target_deConfiguration(&targetDeviceConfig, &deviceConfig);
    }
  }

  delay(1000); // Delay to control the loop frequency
}

/*******************************************************************************
 * PURPOSE: Check for incoming UDP messages and handle handshake/configuration.
 *******************************************************************************/
bool checkForConfigurationMessage(TargetDeviceConfig *config, DeviceConfig *DevConfig)
{
  int packetSize = udp.parsePacket(); // Check for UDP packet
  if (packetSize)
  {
    Serial.println("Received packet with size: " + String(packetSize));
    char packetrecv[255];
    int len = udp.read(packetrecv, 255); // Read the packet
    packetrecv[len] = '\0';              // Null-terminate the string
    Serial.println("Received packet content: " + String(packetrecv));

    String token = strtok(packetrecv, "@"); // Extract token before '@'
    Serial.println("Extracted token: " + token);
    if (token == config->DeviceTokenID) // Validate if the token matches the target device
    {
      Serial.println("the Command is excuted by the Authentic PI");
      String command = strtok(NULL, "@"); // Extract command after '@'
      Serial.println("Extracted command: " + command);
      if (command == "START_SYNC")
      {
        Serial.println("Received START_SYNC command.");
        if (DevConfig->currentStatus == IDEL) // Only start if in IDLE state
        {
          Serial.println("Setting up device configuration.");
          config->IP_address = udp.remoteIP().toString(); // Set target IP and port
          config->sending_port = udp.remotePort();
          config->Listening_port = config->sending_port;
          return true;
        }
        else
        {
          Serial.println("The device is not an IDEL, so the  START_SYNC command will not work.");
        }
      }
      else if (command == "STOP_SYNC")
      {
        if (DevConfig->currentStatus == SENDING_DATA)
        {
          Serial.println("Received STOP_SYNC command.");
          return true;
        }
        else
        {
          Serial.println("the communication is established yet,  so the  STOP_SYNC command will not work.");
        }
      }
      else
      {
        Serial.println("Extracted command: " + command + "is not vaild");
      }
    }
    else
    {
      Serial.println("Extracted token: " + token + "is not vaild");
    }
  }
  return false;
}

/*******************************************************************************
 * PURPOSE: Send a UDP message to the target device.
 *******************************************************************************/
void sendUDPMessage(String message, TargetDeviceConfig *config)
{
  Serial.println("Sending UDP message: " + message + " to IP: " + config->IP_address + " Port: " + config->Listening_port);
  udp.beginPacket(config->IP_address.c_str(), config->Listening_port);
  udp.print(message);
  udp.endPacket();
}

/*******************************************************************************
 * PURPOSE: Configure system for sending data and activate timers.
 *******************************************************************************/
void system_Configuration(void)
{
  Serial.println("Starting data collection and transmission.");
  ledTicker.attach(LED_BLINK_PERIOD, toggleLed);          // Blink LED
  ldrTicker.attach(SENSOR_DATA_READ_PERIOD, readLDR);     // Read LDR data
  udpTicker.attach(SENSOR_DATA_SEND_PERIOD, sendAverage); // Send averaged data
  deviceConfig.currentStatus = SENDING_DATA;
}

/*******************************************************************************
 * PURPOSE: Deconfigure system, stop timers, and reset variables.
 *******************************************************************************/
void Target_deConfiguration(TargetDeviceConfig *config, DeviceConfig *Devconfig)
{
  Serial.println("Stopping data collection and resetting configuration.");
  ledTicker.detach();
  ldrTicker.detach();
  udpTicker.detach();

  config->IP_address = "";
  config->Listening_port = 0;
  config->sending_port = 0;

  memset(deviceConfig.LDRreadings, 0, sizeof(deviceConfig.LDRreadings)); // Clear sensor data buffers
  memset(deviceConfig.LDRAvgreadings, 0, sizeof(deviceConfig.LDRAvgreadings));

  deviceConfig.LDRDataisReady = false;
  deviceConfig.currSUM_DATA = 0;
  readingCount = 0;

  Devconfig->currentStatus = IDEL;
}

/*******************************************************************************
 * PURPOSE: Toggle the LED state for visual indication.
 *******************************************************************************/
void toggleLed()
{
  static bool ledState = digitalRead(LED_PIN);
  if (ledState)
  {
    ledState = false;
  }

  else
  {
    ledState = true;
  }
  digitalWrite(LED_PIN, ledState); // Toggle LED
}

/*******************************************************************************
 * PURPOSE: Read LDR sensor data and compute running average.
 *******************************************************************************/
void readLDR()
{
  for (int i = MAX_DATA_VALUE_STORE - 1; i > 0; i--)
  {
    deviceConfig.LDRreadings[i] = deviceConfig.LDRreadings[i - 1]; // Shift readings
  }
  deviceConfig.LDRreadings[0] = analogRead(LDR_PIN); // Insert new reading
  Serial.println("****** Current LDR Reading -> : " + String(deviceConfig.LDRreadings[0]));
  //////////////////////////////////////////
  if (!deviceConfig.LDRDataisReady)
  {
    readingCount++;
    deviceConfig.currSUM_DATA += deviceConfig.LDRreadings[0]; // Sum the values for averaging
  }
  else
  {
    deviceConfig.currSUM_DATA = deviceConfig.currSUM_DATA - deviceConfig.LDRreadings[DATA_USE_FOR_AVERAGE] + deviceConfig.LDRreadings[0];
  }
  Serial.println("Current Summation data -> : " + String(deviceConfig.LDRreadings[0]) + " with a set of " + String(DATA_USE_FOR_AVERAGE) + " data reading");
  //////////////////////////////////////////
  if (readingCount == DATA_USE_FOR_AVERAGE)
  {
    for (int i = MAX_AVERAGE_VALUE_STORE - 1; i > 0; i--)
    {
      deviceConfig.LDRAvgreadings[i] = deviceConfig.LDRAvgreadings[i - 1]; // Shift averaged readings
    }
    deviceConfig.LDRAvgreadings[0] = deviceConfig.currSUM_DATA / DATA_USE_FOR_AVERAGE; // Compute new average
    Serial.println("Average of LDR reading : " + String(deviceConfig.LDRAvgreadings[0]) + " with a set of " + String(DATA_USE_FOR_AVERAGE) + " data reading");
    deviceConfig.LDRDataisReady = true; // Indicate data is ready for averaging
  }
  //////////////////////////////////////////
}

/*******************************************************************************
 * PURPOSE: Send averaged LDR sensor data via UDP.
 *******************************************************************************/
void sendAverage()
{
  if (deviceConfig.LDRDataisReady)
  {
    Serial.println("Sending average LDR reading: " + String(deviceConfig.LDRAvgreadings[0]));
    sendUDPMessage(String(deviceConfig.LDRAvgreadings[0]), &targetDeviceConfig); // Send the average via UDP
  }
}
/*  -----------------   end of the Assignment ------------------*/
