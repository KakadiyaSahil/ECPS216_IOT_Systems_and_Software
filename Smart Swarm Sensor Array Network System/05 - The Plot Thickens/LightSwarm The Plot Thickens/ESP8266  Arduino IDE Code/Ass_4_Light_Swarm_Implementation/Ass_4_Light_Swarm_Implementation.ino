/*
Name: Sahil Mukeshbhai Kakadiya
Profile: Master's Student
UCI Student ID: 93282494
University: University of California, Irvine (UCI)
Course: The Professional Master of Embedded and Cyber-Physical Systems
Major: Computer Engineering
Subject Name: ECPS 216 - F'24: IoT Systems & Software
Assignment Name: Programming Assignment 4 
*/

/*  -----------------   Start of the Assignment ------------------*/

#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <Ticker.h>

// WiFi credentials
const char *ssid = "sahil";
const char *password = "Sahil9805";

// Define pin for photoresistor (LDR) and LEDs
#define LDR_PIN A0
#define LED_FLASH_PIN 15
#define LED_MASTER_PIN 2

// Define constants for device configurations and intervals
#define MAX_ESP_DEVICES 3
#define MAX_RPI_DEVICES 1
#define DATA_BROADCAST_INTERVAL 100 // Broadcast interval
#define COUNT_DOWN_CHECK_INTERVAl 1000
#define COUNT_DOWN 20
#define DEVICE_OWN_ID 0 // Interval to check master status

#define ONLINE_NOTIFICATION_INTERVAL 10000 // Interval to check master status
#define RESET_DELAY 3000                   // Delay for reset command
#define LDR_RAW_MIN 0
#define LDR_RAW_MAX 1023
#define FLASHING_FREQUENCY_MIN 1
#define FLASHING_FREQUENCY_MAX 21

// UDP and Ticker objects for managing communication and tasks
WiFiUDP udp;
Ticker onlineNotificationTicker, broadcastTicker, ConnectionCountDown;

// Device statuses for device role tracking
enum DeviceStatus
{
  IDLE = 0,
  ACTIVE = 1,
  MASTER = 2,
};

// Define the struct to store ESP device configurations
struct DeviceConfig
{
  String DeviceTokenID = "ESP_8266"; // Token to verify device identity
  String UniqueID;                   // Unique device identifier
  bool DeviceConfigured = false;     // Flag for device configuration status
  String IP_address;                 // IP address of the ESP device
  int Listening_port;                // Port for receiving data
  int sending_port;                  // Port for sending data
  int LDR_reading = 0;               // LDR sensor reading
  DeviceStatus status = IDLE;        // Device role status
  bool isESP8266Connected = false;   // Connection flag for ESP device
  int CountDown = COUNT_DOWN;
  bool isMaster = false; // Flag indicating if device is master
} deviceConfig[MAX_ESP_DEVICES];

// Define the struct to store server (RPi) configuration
struct ServerConfig
{
  String DeviceTokenID = "RaspBerry_PI_5"; // Token for server verification
  String UniqueID;                         // Unique ID for server
  bool DeviceConfigured = false;           // Flag for configuration status
  String IP_address;                       // IP of the server
  int Listening_port;                      // Listening port of server
  int sending_port;                        // Sending port of server
  int CountDown = COUNT_DOWN;
  bool isRPiConnected = false; // Flag to check server connection
} serverConfig;

// Define device types for tracking configuration
enum DeviceType
{
  Server,
  Device
};

// Network configuration variables
IPAddress broadcastIP(255, 255, 255, 255);
int broadcastPort = 54321;
int listenPort = 54321;

// Timing and state variables for packet tracking and sensor data
unsigned long lastPacketTime = 0;
bool networkSlient = true;
int currentReading = 0;

// Function declarations for various operations
String getUniqueIDFromMAC(void);
void broadcastData(void);
void processIncomingPackets(void);
void handleIncomingPacket(String packet, String IP_address, int Port);
void RPI_IncomingPackets(String packet, ServerConfig *config);
void ESP8266_IncomingPackets(String packet, DeviceConfig *config);
bool isdeviceConfigure(DeviceType type, String ID, int *deviceNUM);
void readLDR(void);
void sendToRPi(void);
void intensityIndication(void);
void OnlineNotification(void);
// Main setup function to initialize the system
void setup()
{
  Serial.begin(115200);

  // Initialize WiFi and LED pins
  WiFi.begin(ssid, password);
  pinMode(LED_FLASH_PIN, OUTPUT);
  pinMode(LED_MASTER_PIN, OUTPUT);
  digitalWrite(LED_MASTER_PIN, HIGH);

  // Connect to WiFi network
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");

  // Initialize UDP communication
  udp.begin(listenPort);

  // Set local IP as device IP and configure device ports
  deviceConfig[DEVICE_OWN_ID].IP_address = WiFi.localIP().toString();
  Serial.print("Device IP address: ");
  Serial.println(deviceConfig[0].IP_address);
  deviceConfig[DEVICE_OWN_ID].sending_port = broadcastPort;
  deviceConfig[DEVICE_OWN_ID].Listening_port = broadcastPort;

  // Assign unique ID using MAC address
  String ownID = getUniqueIDFromMAC();
  Serial.print("Unique Device ID: ");
  Serial.println(ownID);
  deviceConfig[DEVICE_OWN_ID].UniqueID = ownID;

  // Mark device as configured
  deviceConfig[DEVICE_OWN_ID].DeviceConfigured = true;

  // Initialize tickers for periodic tasks
  broadcastTicker.attach_ms(DATA_BROADCAST_INTERVAL, broadcastData);
  onlineNotificationTicker.attach_ms(ONLINE_NOTIFICATION_INTERVAL, OnlineNotification);
  ConnectionCountDown.attach_ms(COUNT_DOWN_CHECK_INTERVAl, CheckOnlineCountDown);
  if (deviceConfig[DEVICE_OWN_ID].DeviceConfigured)
  {
    Serial.println("This device is Confiure on the network");
    checkandsetMaster();
  }
}

// Main loop function
void loop()
{
  if (deviceConfig[DEVICE_OWN_ID].DeviceConfigured)
  {
    processIncomingPackets();
    readLDR();
  }
  else
  {
    Serial.println("This device is deConfiure form the by the the Server");
    Serial.println("This device needs to be restart");
    analogWrite(LED_FLASH_PIN, 255);
    digitalWrite(LED_MASTER_PIN, HIGH); // Turn off Master LED
  }
  delay(10);
}

/*******************************************************************************
 * PURPOSE: Process incoming UDP packets and update last packet time
 *******************************************************************************/
void processIncomingPackets(void)
{
  String sender_IP_address = "";
  int sender_port;
  String packetData = "";
  int packetSize = udp.parsePacket();
  if (packetSize)
  {
    networkSlient = false;
    char incomingPacket[255];
    int len = udp.read(incomingPacket, 255);
    incomingPacket[len] = '\0';
    packetData = String(incomingPacket);
    sender_IP_address = udp.remoteIP().toString();
    sender_port = udp.remotePort();
    handleIncomingPacket(packetData, sender_IP_address, sender_port);
    networkSlient = true;
  }
}

/*******************************************************************************
 * PURPOSE: Handle incoming packet based on device type and token
 *******************************************************************************/
void handleIncomingPacket(String packet, String IP_address, int Port)
{
  char tempBuffer[packet.length() + 1];
  strcpy(tempBuffer, packet.c_str());
  String token = strtok(tempBuffer, "@");

  if (token != NULL)
  {
    if (token == serverConfig.DeviceTokenID)
    {
      Serial.println("IncomingPacket is from: RaspBerry PI 5");
      token = strtok(NULL, "@");
      int deviceNUM = 0;
      if (!isdeviceConfigure(Server, token, &deviceNUM))
      {
        Serial.println("Configuring RaspBerry PI 5");
        serverConfig.IP_address = IP_address;
        serverConfig.UniqueID = token;
        serverConfig.sending_port = Port;
        serverConfig.Listening_port = Port;
        serverConfig.DeviceConfigured = true;
      }
      RPI_IncomingPackets(token, &serverConfig);
    }
    else if (token == deviceConfig[0].DeviceTokenID)
    {
      Serial.println("IncomingPacket is from: ESP8266");
      token = strtok(NULL, "@");
      int deviceNUM = 0;
      bool status = false;
      status = isdeviceConfigure(Device, token, &deviceNUM);
      if (!status)
      {
        Serial.println("Configuring ESP8266");

        for (int i = 0; i < MAX_ESP_DEVICES; i++)
        {
          if (!deviceConfig[i].DeviceConfigured)
          {
            deviceConfig[i].IP_address = IP_address;
            deviceConfig[i].UniqueID = token;
            deviceConfig[i].sending_port = Port;
            deviceConfig[i].Listening_port = Port;
            deviceConfig[i].CountDown = COUNT_DOWN;
            deviceConfig[i].DeviceConfigured = true;

            if (isdeviceConfigure(Device, token, &deviceNUM))
            {
              status = true;
              break;
            }
          }
        }
        Serial.println(status ? "ESP8266 Configured witha a slot number" + String(deviceNUM) : "No free slots for ESP8266");
      }
      if ((status == true) && (deviceNUM >= 0))
      {
        ESP8266_IncomingPackets(token, &deviceConfig[deviceNUM]);
      }
    }
  }
}

/*******************************************************************************
 * PURPOSE: Handle incoming packet from RPI devices.
 *******************************************************************************/
void RPI_IncomingPackets(String packet, ServerConfig *config)
{
  if (packet != NULL)
  {
    String cmd = strtok(NULL, "@"); // Extract command after '2nd @ to 3rd @'
    if (cmd != NULL)
    {
      if (cmd == "ONLINE")
      {
        config->CountDown = COUNT_DOWN;
        config->isRPiConnected = true;
        Serial.println("RaspBerry PI 5 is now online");
      }
      else if (cmd == "RESET")
      {
        Serial.println("RESET is activated");
        ESP.restart();
      }
      else
      {
        // Serial.println("cmd: {" + cmd + " } not matched:");
      }
    }
    else
    {
      // Serial.println("RPI_IncomingPackets {cmd} extraction Fails");
    }
  }
  else
  {
    Serial.println("RPI_IncomingPackets {packet} extraction Fails");
  }
}

/*******************************************************************************
 * PURPOSE: Handle incoming packet from ESP8266 devices.
 *******************************************************************************/
void ESP8266_IncomingPackets(String packet, DeviceConfig *config)
{
  if (packet != NULL)
  {
    String cmd = strtok(NULL, "@"); // Extract command after '2nd @ to 3rd @'
    if (cmd != NULL)
    {
      if (cmd == "ONLINE")
      {
        config->isESP8266Connected = true;
        config->CountDown = COUNT_DOWN;
        Serial.println(" the ESP8266 { " + config->UniqueID + " } is now online");
      }
      else if (cmd == "LDR")
      {
        String LDRreading = strtok(NULL, "@"); // Extract LDR reading after '3rd @ to 4th @'
        config->LDR_reading = atoi(LDRreading.c_str());
        Serial.println(" The LDR { " + String(config->LDR_reading) + " } reading of ESP8266 { " + String(config->UniqueID) + " } is recived ");
        checkandsetMaster();
      }
      else
      {
        Serial.println("cmd: {" + cmd + " } not matched:");
      }
    }
    else
    {
      Serial.println("ESP8266_IncomingPackets {cmd} extraction Fails");
    }
  }
  else
  {
    Serial.println("ESP8266_IncomingPackets {packet} extraction Fails");
  }
}

/*******************************************************************************
 * PURPOSE: checks the  devices is already configure or not
 *******************************************************************************/
bool isdeviceConfigure(DeviceType type, String ID, int *deviceNUM)
{
  // Serial.println("Checks the  device is already configure or not ? ");
  switch (type)
  {
  case Server:
  {
    if (serverConfig.UniqueID == ID)
    {
      // Serial.println("server device is already configure");
      return true;
    }
    break;
  }
  case Device:
  {
    for (int i = 0; i < MAX_ESP_DEVICES; i++)
    {
      if (deviceConfig[i].UniqueID == ID)
      {
        *deviceNUM = i;
        // Serial.println("device is already configure");
        return true;
      }
    }
    break;
  }
  }
  Serial.println("device is not configure !!!!!!!!! ");
  return false;
}

/*******************************************************************************
 * PURPOSE:
 *******************************************************************************/
void device_deConfigure(DeviceType type, int deviceNumber)
{
  switch (type)
  {
  case Server:
  {
    serverConfig.DeviceConfigured = false;
    Serial.println("Server : { " + serverConfig.UniqueID + " } is now de-Configure");
    serverConfig.UniqueID = "";
    serverConfig.IP_address = "";
    serverConfig.Listening_port = 0;
    serverConfig.sending_port = 0;
    serverConfig.CountDown = COUNT_DOWN;
    serverConfig.isRPiConnected = false;
  }
  break;
  case Device:
  {
    deviceConfig[deviceNumber].DeviceConfigured = false;
    Serial.println("Device : { " + deviceConfig[deviceNumber].UniqueID + " } is now de-Configure");
    deviceConfig[deviceNumber].UniqueID = "";
    deviceConfig[deviceNumber].IP_address = "";
    deviceConfig[deviceNumber].Listening_port = 0;
    deviceConfig[deviceNumber].sending_port = 0;
    deviceConfig[deviceNumber].LDR_reading = 0;
    deviceConfig[deviceNumber].isESP8266Connected = false;
    deviceConfig[deviceNumber].CountDown = COUNT_DOWN;
    deviceConfig[deviceNumber].isMaster = false;
  }
  break;
  }
}

/*******************************************************************************
 * PURPOSE: Set the highest reading ESP8266 device as the Master device
 *******************************************************************************/
void checkandsetMaster()
{
  int masterdata = -1;  // Initialize to a low value
  int masterIndex = -1; // Variable to store the index of the master device

  // Reset all devices' isMaster flag
  for (int i = 0; i < MAX_ESP_DEVICES; i++)
  {
    deviceConfig[i].isMaster = false;
  }

  // Find the device with the highest LDR reading
  for (int i = 0; i < MAX_ESP_DEVICES; i++)
  {
    if (!deviceConfig[i].DeviceConfigured)
    { // Check if device is configured
      continue;
    }
    if (deviceConfig[i].LDR_reading > masterdata)
    {
      masterdata = deviceConfig[i].LDR_reading;
      masterIndex = i; // Update the masterIndex to current highest device
    }
  }
  // Set the highest reading device as Master, if found
  if (masterIndex != -1)
  {
    deviceConfig[masterIndex].isMaster = true;
    Serial.println("Device : " + deviceConfig[masterIndex].UniqueID + " is now the Master");
  }
  // Set/Reset the LED based on this  device is  as Master or not
  if (deviceConfig[DEVICE_OWN_ID].isMaster)
  {
    digitalWrite(LED_MASTER_PIN, LOW); // Turn on Master LED
  }
  else
  {
    digitalWrite(LED_MASTER_PIN, HIGH); // Turn off Master LED
  }
}

/*******************************************************************************
 * PURPOSE: Broadcast LDR data over the network when idle for 200ms.
 *******************************************************************************/
void broadcastData(void)
{
  if (networkSlient)
  {
    String seperator = "@";
    if (deviceConfig[DEVICE_OWN_ID].DeviceConfigured)
    {
      String message = deviceConfig[DEVICE_OWN_ID].DeviceTokenID + seperator + deviceConfig[DEVICE_OWN_ID].UniqueID + seperator + "LDR" + seperator + String(deviceConfig[DEVICE_OWN_ID].LDR_reading);
      // Serial.println("Network is Silent");
      // Serial.println("Broadcasting the data: " + message);
      udp.beginPacket(broadcastIP, broadcastPort);
      udp.print(message);
      udp.endPacket();
    }
  }
  else
  {
    Serial.println("Network is not Silent");
  }
}

/*******************************************************************************
 * PURPOSE:
 *******************************************************************************/
void OnlineNotification(void)
{
  String seperator = "@";
  if (deviceConfig[DEVICE_OWN_ID].DeviceConfigured)
  {
    String message = deviceConfig[DEVICE_OWN_ID].DeviceTokenID + seperator + deviceConfig[DEVICE_OWN_ID].UniqueID + seperator + "ONLINE";
    // Serial.println("Broadcasting the I am Online: " + message);
    udp.beginPacket(broadcastIP, broadcastPort);
    udp.print(message);
    udp.endPacket();
    // Mark device as configured
    deviceConfig[DEVICE_OWN_ID].CountDown = COUNT_DOWN;
  }
}

/*******************************************************************************
 * PURPOSE:
 *******************************************************************************/
void CheckOnlineCountDown(void)
{
  for (int i = 0; i < MAX_ESP_DEVICES; i++)
  {
    if (deviceConfig[i].DeviceConfigured)
    {
      deviceConfig[i].CountDown--;
      // Serial.println("Device : { " + deviceConfig[i].UniqueID + " } should send the Online in the Count  down: { " + String(deviceConfig[i].CountDown) + " } ");
      if (deviceConfig[i].CountDown == 0)
      {
        device_deConfigure(Device, i);
      }
    }
  }
  if (serverConfig.DeviceConfigured)
  {
    serverConfig.CountDown--;
    if (serverConfig.CountDown == 0)
    {
      device_deConfigure(Server, 0);
    }
  }
}

/*******************************************************************************
 * PURPOSE: Send LDR data to Raspberry Pi server
 *******************************************************************************/
void sendToRPi(void)
{
  String seperator = "@";
  checkandsetMaster();
  if (deviceConfig[0].isMaster)
  {
    String message = deviceConfig[DEVICE_OWN_ID].DeviceTokenID + seperator + "MASTER" + seperator + deviceConfig[DEVICE_OWN_ID].UniqueID + seperator + "LDR" + seperator + String(deviceConfig[DEVICE_OWN_ID].LDR_reading);
    // Serial.println("I am the Master");
    // Serial.println("sending the data to the PI: " + message);
    udp.beginPacket(broadcastIP, broadcastPort);
    udp.print(message);
    udp.endPacket();
  }
}

/*******************************************************************************
 * PURPOSE: Read LDR sensor data and compute running average.
 *******************************************************************************/
void readLDR(void)
{
  static int counter = 0;
  counter++;
  deviceConfig[DEVICE_OWN_ID].LDR_reading = analogRead(LDR_PIN); // Insert new reading
  // Serial.println("LDR Reading -> : " + String(deviceConfig[0].LDR_reading));
  intensityIndication();
  if (counter >= 10)
  {
    counter = 0;
    sendToRPi();
  }
}
/*******************************************************************************
 * PURPOSE: Read LDR sensor data and compute running average.
 *******************************************************************************/
String getUniqueIDFromMAC(void)
{
  uint8_t mac[6];
  WiFi.macAddress(mac); // Get MAC address

  // Create a String from the last 4 bytes
  String uniqueID = "";
  for (int i = 2; i < 6; i++)
  {                                  // Use only the last 4 bytes
    uniqueID += String(mac[i], HEX); // Convert to hexadecimal format
  }

  uniqueID.toUpperCase(); // Optional: convert to uppercase for consistency
  return uniqueID;
}
void intensityIndication(void)
{
  int flashingRateValue = map(deviceConfig[DEVICE_OWN_ID].LDR_reading, LDR_RAW_MIN, LDR_RAW_MAX, FLASHING_FREQUENCY_MIN, FLASHING_FREQUENCY_MAX);
  analogWriteFreq(flashingRateValue);
  // Serial.print("Flashing Rate Value:\t" + String(int(flashingRateValue)) + "\n");
  analogWrite(LED_FLASH_PIN, 50);
}
