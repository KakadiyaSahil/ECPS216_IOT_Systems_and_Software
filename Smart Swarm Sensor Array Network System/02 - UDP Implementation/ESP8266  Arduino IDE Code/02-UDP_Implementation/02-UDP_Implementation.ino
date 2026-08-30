
#include <stdio.h>
#include <string.h>

#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <Ticker.h>

const char *ssid = "sahil";
const char *password = "Sahil9805";

// PhotoDiode Resi settings
#define LDR_PIN 17

// LED settings
#define LED_PIN 16

#define MAX_DATA_VALUE_STORE 20
#define MAX_AVERAGE_VALUE_STORE 5
#define DATA_USE_FOR_AVERAGE 5

#define LED_BLINK_PEROID 0.5
#define SENSOR_DATA_READ_PEROID 1
#define SENSOR_DATA_SEND_PEROID 2

// Tickers Software Tier Interrupt for action like- LED Blink, Sensor data read, sends UDP packets
Ticker ledTicker;
Ticker ldrTicker;
Ticker udpTicker;
Ticker waitTicker;

WiFiUDP udp;

enum CurrStatus
{
  IDEL = 0,
  CONFIGURED = 1,
  HANDSHAKE_DONE = 2,
  SENDING_DATA = 3,
};
// Struct to hold target ( RaspBerry PI ) device config
struct TargetDeviceConfig
{
  String DeviceTokenID = "RaspBerry_PI_5";
  String IP_address;
  int Listening_port;
  int sending_port;
} targetDeviceConfig;

// Struct to hold device  ( ESP8266 )config
struct DeviceConfig
{
  String IP_address;
  int Listening_port = 54321;
  int Sending_port = 244;
  CurrStatus currentStatus = IDEL;
} deviceConfig;

bool checkForConfigurationMessage(TargetDeviceConfig *config, DeviceConfig *DevConfig);
void sendUDPMessage(String message, TargetDeviceConfig *config);
void Target_deConfiguration(TargetDeviceConfig *config, DeviceConfig *DevConfig);
void system_Configuration(void);
// Software timer ISRs Function to act whenver those Interrupts Occcurs
void toggleLed();
void readLDR();
void sendAverage();

int LDRreadings[MAX_DATA_VALUE_STORE] = {0};         // Buffer to hold the  LDR Data Reading
float LDRAvgreadings[MAX_AVERAGE_VALUE_STORE] = {0}; // Buffer to hold the  Averaging of ythe data readed
bool LDRDataisReady = false;                         // uses as a flag to notify the system that data is ready to be sent
// Note :-  there are some requiremts to fullfill that the system has some worth data to be sent,
//          which is notify to the system if this reuirement completes.

// Check if we have enough data for averaging
int readingCount = 0;
float sum = 0;

void setup()
{
  Serial.begin(9600);
  delay(100);

  // GPIO pins setting
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // Turn off onboard LED (inverted logic)
  analogRead(LDR_PIN);         // the AnalogRead function handles all the setting for this port itself

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    delay(500); // delay statement is use because it will stop to trigger the watch dog timer
  }
  Serial.println("\nWiFi connected successfully.");
  deviceConfig.IP_address = WiFi.localIP().toString();
  Serial.println("IP address of our device : " + deviceConfig.IP_address);

  udp.begin(deviceConfig.Listening_port); //  Init the UDP settings on our preferred port
}

void loop()
{

  if (deviceConfig.currentStatus == IDEL) // a very 1st stage is the IDEL stage, where our ESP device is in waiting mode for the right handshake establishment
  {
    if (checkForConfigurationMessage(&targetDeviceConfig, &deviceConfig))
    {
      deviceConfig.currentStatus = HANDSHAKE_DONE;
    }
  }
  if (deviceConfig.currentStatus == HANDSHAKE_DONE) // After the handshake -> in 2st stage is the Configuration  stage, where our ESP device sets all the timer and setting for the collection of the data and doing other stuffs
  {
    system_Configuration();
  }
  if (deviceConfig.currentStatus == SENDING_DATA) // after setting all the configs -> in 3rd stage the system collects the data and sends to the  target device   and also waits for the other messeges for now it is the only one that is stop sync
  {
    if (checkForConfigurationMessage(&targetDeviceConfig, &deviceConfig))
    {
      Target_deConfiguration(&targetDeviceConfig, &deviceConfig);
    }
  }
  delay(1000);
}

/*******************************************************************************
* PURPOSE: This function essential checks the incomming messegs and notification form the targetd device

* INPUT:   Message: -> the Message to be send
           TargetDeviceConfig -> its struct which holds the setting of the targeted device

* OUTPUT:  No

* NAME: Sahil Mukeshbhai Kakadiya
* DATE: 10-18-2024
/*******************************************************************************/
bool checkForConfigurationMessage(TargetDeviceConfig *config, DeviceConfig *DevConfig)
{
  int packetSize = udp.parsePacket();
  if (packetSize)
  {
    Serial.println("Recieve Something with the packetSize: " + String(packetSize));
    char packetrecv[255];
    int len = udp.read(packetrecv, 255);
    packetrecv[len] = '\0'; // Null-terminate the string
    if ((len > 0))
    {
      Serial.println("the recv packet: " + String(packetrecv));
      String token = strtok(packetrecv, "@");
      Serial.println("the recv Token: " + token);
      if (token == config->DeviceTokenID) /* The Validation for the Correct Target DeviceTokenID whcih is a Raspberry PI  */
      {
        token = strtok(NULL, "@");
        Serial.println("the cmd extracted is : " + token);
        if (token == "START_SYNC") /* checks wheather it is start or stop cmd requested   */
        {
          Serial.println("recv the start synchronization : ");
          if (DevConfig->currentStatus == IDEL) /* checks wheather the Our device is reeady to configure the commication or not  */
          {
            Serial.println("setting the Device Configuration  ");
            config->IP_address = udp.remoteIP().toString();
            config->sending_port = udp.remotePort();
            config->Listening_port = config->sending_port;
            Serial.println("Gets START Syncronization form the right RaspBerry PI");
            return true;
          }
          else
          {
            return false;
          }
        }
        else if (token == "STOP_SYNC") /* checks wheather it is start or stop cmd requested   */
        {
          if (DevConfig->currentStatus == SENDING_DATA)
          {
            Serial.println("Gets START Syncronization form the right RaspBerry PI");
            return true;
          }
          else
          {
            return false;
          }
        }
      }
    }
  }
  return false;
}

/*******************************************************************************
* PURPOSE: Sends the UDP message  to the respective device

* INPUT:   Message: -> the Message to be send
           TargetDeviceConfig -> its struct which holds the setting of the targeted device

* OUTPUT:  No

* NAME: Sahil Mukeshbhai Kakadiya
* DATE: 10-14-2024
/*******************************************************************************/
void sendUDPMessage(String message, TargetDeviceConfig *config)
{
  /* Send UDP PMessage */
  Serial.println("Sending the UDP Message: " + message + " to the targeted IP address : " + config->IP_address + " Listening port: " + config->Listening_port);
  udp.beginPacket(config->IP_address.c_str(), config->Listening_port);
  udp.print(message);
  udp.endPacket();
}

/*******************************************************************************
* PURPOSE: it configure the setting  set in the system, for futher the communication

* INPUT: No

* OUTPUT: No

* NAME: Sahil Mukeshbhai Kakadiya
* DATE: 10-14-2024
/*******************************************************************************/
void system_Configuration(void)
{

  Serial.println("Start Sending the Sensor Data.");
  ledTicker.attach(LED_BLINK_PEROID, toggleLed);          // Flash LED every 0.5 seconds
  ldrTicker.attach(SENSOR_DATA_READ_PEROID, readLDR);     // Read LDR every 1 second
  udpTicker.attach(SENSOR_DATA_SEND_PEROID, sendAverage); // Send average every 2 seconds
  Serial.println("Making the Device  for starting  to sends the DATA ");
  deviceConfig.currentStatus = SENDING_DATA;
}

/*******************************************************************************
* PURPOSE: it deconfigure the setting which was set in the system, for fill up the variable in next communication

* INPUT: TargetDeviceConfig -> its struct which holds the setting of the targeted device
         DeviceConfig -> its struct which holds the setting of the our device

* OUTPUT: No

* NAME: Sahil Mukeshbhai Kakadiya
* DATE: 10-18-2024
/*******************************************************************************/
void Target_deConfiguration(TargetDeviceConfig *config, DeviceConfig *Devconfig)
{

  Serial.println("Stop Sending the Sensor Data.");
  ledTicker.detach();
  ldrTicker.detach();
  udpTicker.detach();

  Serial.println("deleting the Device Configuration  ");
  config->IP_address = "";
  config->Listening_port = 0;
  config->Listening_port = 0;

  Serial.println("deleting the the previous data stored  ");
  LDRreadings[MAX_DATA_VALUE_STORE] = {0};
  LDRAvgreadings[MAX_AVERAGE_VALUE_STORE] = {0};
  LDRDataisReady = false;
  readingCount = 0;
  sum = 0;

  Serial.println("Making the Device to the IDel for strating further commuication ");
  Devconfig->currentStatus = IDEL;
}

/*******************************************************************************
* PURPOSE: Toggles the LED each time it is called based on the previous values

* INPUT: No  Basically its a software timer interrupt call-back function

* OUTPUT: No

* NAME: Sahil Mukeshbhai Kakadiya
* DATE: 10-18-2024
/*******************************************************************************/
void toggleLed()
{

  static bool ledState = digitalRead(LED_PIN); // its reads the current value and based on that it will toggel
  {
    if (ledState)
    {
      ledState = false;
    }
    else
    {
      ledState = true;
    }
    digitalWrite(LED_PIN, ledState); // toggels based on the  previous one
  }
}

/*******************************************************************************
* PURPOSE: Reads  the Sensor's data each time it called by the software timer and also does the Average of them

* INPUT: No Basically its a software timer interrupt call-back function

* OUTPUT: No

* Note:- 1) it will do the right shifing process in the data arry,
         after checking some flags which allows it to knows that is the data is ready to send or not!!

* NAME: Sahil Mukeshbhai Kakadiya
* DATE: 10-18-2024
/*******************************************************************************/
void readLDR()
{
  LDRreadings[0] = analogRead(LDR_PIN);
  LDRDataisReady = true;
}

/*******************************************************************************
* PURPOSE: Sends the Sensor's Average Data to the targeted Device

* INPUT: No  Basically its a software timer interrupt call-back function

* OUTPUT: No

* Note:- It does calls the actual sendUDPMessage function,
         after checking some flags which allows it to knows that is the data is ready to send or not!!

* NAME: Sahil Mukeshbhai Kakadiya
* DATE: 10-18-2024
/*******************************************************************************/
void sendAverage()
{
  if ((deviceConfig.currentStatus == SENDING_DATA) && (LDRDataisReady == true))
  {
    sendUDPMessage(String(LDRreadings[0]), &targetDeviceConfig);
  }
}
