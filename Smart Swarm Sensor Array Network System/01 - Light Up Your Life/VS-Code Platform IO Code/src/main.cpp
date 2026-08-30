/*
Name: Sahil Mukeshbhai Kakadiya
Profile: Master's Student
UCI Student ID: 93282494
University: University of California, Irvine (UCI)
Course: The Professional Master of Embedded and Cyber-Physical Systems
Major: Computer Engineering
Subject Name: ECPS 216 - F'24: IoT Systems & Software
Assignment Name: Programming Assignment 1 - Light Up Your Life

TASK Description:

***Part 1:
- Connect RGB light sensor to ESP8266.
- Read sensor data every second and display it in the IDE console.
- Turn ON the onboard LED  if the average light intensity exceeds a set threshold.

***Part 2:
- Connect 3 external LEDs (Green, Yellow, Red).
- Use LEDs to indicate light intensity levels from the RGB sensor:
  - Low -> Green ON
  - Medium -> Yellow ON
  - High -> Red ON

***Part 3:
- Flash the onboard LED  if the average intensity exceeds the threshold.
- Increase the flash rate with higher readings.

DUE Date & Time: 11-10-2024, 11:00 PM
Submitted Date & Time: 10-10-2024, 11:00 PM
*/

/*  -----------------   Start of the Assignment ------------------*/

#include "Arduino.h"
#include "Adafruit_TCS34725.h" // Include the library provided by the Adafruit to communicate with TCS34725 RGB Color Sensor.,

/*
This line initializes an instance of the Adafruit_TCS34725 class, which represents the TCS34725 RGB color sensor.
TCS34725_INTEGRATIONTIME_50MS: This parameter sets the integration time of the sensor to 50 milliseconds.
                               The integration time determines how long the sensor collects light data;
                              a longer time allows for more light to be captured, improving accuracy in low-light conditions.
TCS34725_GAIN_4X: This parameter sets the gain of the sensor to 4x.
                  Gain affects the sensor's sensitivity to light; a higher gain increases the sensor's ability to detect lower light levels,
                  making it suitable for a wider range of lighting conditions.*/
Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);

// Pin Definitions
#define PUSH_BUTTON_PIN 14
#define BLUE_LED_PIN 16 //onBoard LED
#define RED_LED_PIN 2
#define YELLOW_LED_PIN 15
#define GREEN_LED_PIN 13

#define LOW_RANGE_MIN 0
#define LOW_RANGE_MAX 99
#define MEDIUM_RANGE_MIN 100
#define MEDIUM_RANGE_MAX 199
#define HIGH_RANGE_MIN 200
#define HIGH_RANGE_MAX 255

// Variables for Average Values
int thresholdAverage = 150, medAveragemin = 100, medAveragemax = 200, flashingRateValue = 0;
// Variables for  LED Intensity Values and its total Average
float blue, red, green, yellow, average = 0;
// Variable for the current Mode
int currMode = 0;
void Assignment_Part_1();
void Assignment_Part_2();
void Assignment_Part_3();
void getRGBValues();
IRAM_ATTR void modeChange();

void setup()
{
  /*
   The command Serial.begin(9600) initializes serial communication at a baud rate of 9600 bits per second.
   This allows the ESP8266 to send and receive data over the serial port,
   enabling you to monitor output in the IDE console for debugging and data display.*/
  Serial.begin(9600);

  /*
  GPIO Pin Configuration
  This section initializes the necessary GPIO pins with their required settings for the entire assignment.*/
  pinMode(BLUE_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(PUSH_BUTTON_PIN, INPUT);
  /*This call to attachInterrupt activates the interrupt, allowing the user to change modes*/
  attachInterrupt(digitalPinToInterrupt(PUSH_BUTTON_PIN), modeChange, RISING);
  digitalWrite(BLUE_LED_PIN, HIGH);  // Active LOW Logic

  /*Calling the function begin to start the RGB sensor with all the setting given by earlier  */
  while (!tcs.begin())
  {
    /* Serial.Print Allows o not activate the WDT and our system will not crash by WDT*/
    Serial.print(".");
  }
  Serial.println("Found RGB Sensor!");

  /*The RGB values are initialized, with the first few readings (e.g., the first 4 to 10 values) potentially containing noise or garbage data.
  This initial setup helps stabilize the readings, allowing accurate and reliable RGB sensor values for subsequent processing.*/
  for (int i = 0; i < 4; i++)
  {
    Serial.println("setting initial value...");
    tcs.getRGB(&blue, &green, &blue); // This function return normalized rgb value (0-255)
    red += red;
    green += green;
    blue += blue;
    delay(500);
  }
  red /= 4;
  green /= 4;
  blue /= 4;
  average = (red + green + blue) / 3;

  Serial.print("R:\t" + String(int(red)) + "\tG:\t" + String(int(green)) + "\tB:\t" + String(int(blue)) + "\n");
  average = (red + green + blue) / 3;
  Serial.print("Average:\t" + String(int(average)) + "\tthresholdAverage:\t" + String(int(thresholdAverage)) + "\n");
}

void loop()
{

  getRGBValues();

  switch (currMode)
  {
  case 1:
  {
    Assignment_Part_1();
    break;
  }
  case 2:
  {
    Assignment_Part_2();
    break;
  }
  case 3:
  {
    Assignment_Part_3();
    break;
  }
  default:
  {
    Serial.println("Please selects the Mode/Part of the Assignment : ");
    break;
  }
  }
  /*The delay(1000) function pauses the procedure for 1 second, ensuring the loop runs every second.*/
  delay(1000);
}
/*******************************************************************************
 * PROCEDURE: Reading the RGB values --  A Todo list that each of the part of the assigment is goning to be used
 * PURPOSE: It reads the RGB sensor Values and average of all.
 * NAME: Sahil Mukeshbhai Kakadiya
 * DATE: 10-10-2024
 *******************************************************************************/
void getRGBValues()
{
  tcs.getRGB(&red, &green, &blue); // This function return normalized rgb value (0-255)
  Serial.print("R:\t" + String(int(red)) + "\tG:\t" + String(int(green)) + "\tB:\t" + String(int(blue)) + "\n");
  average = (red + green + blue) / 3;
  Serial.print("Average:\t" + String(int(average)) + "\tthresholdAverage:\t" + String(int(thresholdAverage)) + "\n");
}
/*******************************************************************************
 * PROCEDURE: Part 1 of the Assigment
 * PURPOSE: Use LEDs to indicate light intensity levels from RGB sensor:
 * NAME: Sahil Mukeshbhai Kakadiya
 * DATE: 10-10-2024
 *******************************************************************************/
void Assignment_Part_1()
{
  Serial.println(" Selecting the part 1 of the Assigment ");
  /* If the Average light intensity exceeds the specified threshold, the blue LED indicator will light up. */
  if (average > thresholdAverage)
  {
    Serial.println(" Threshold is excessed  Status Indication by Blue color LED");
    digitalWrite(BLUE_LED_PIN, LOW); // Active LOW Logic
  }
  else
  {
    digitalWrite(BLUE_LED_PIN, HIGH);  // Active LOW Logic
  }
}
/*******************************************************************************
 * PROCEDURE: Part 2 of the Assigment
 * PURPOSE: Use LEDs to indicate light intensity levels from RGB sensor:
 * NAME: Sahil Mukeshbhai Kakadiya
 * DATE: 10-10-2024
 *******************************************************************************/
void Assignment_Part_2()
{
  Serial.println("Selecting the part 2 of the Assigment ");
  /* If the average light intensity falls within a specified range, the only corresponding LED will light up. */
  if ((average >= LOW_RANGE_MIN) && (average <= LOW_RANGE_MAX))
  {
    Serial.println(" LOW Status Indication by Green color LED ");
    digitalWrite(GREEN_LED_PIN, HIGH);
    digitalWrite(YELLOW_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, LOW);
  }
  else if ((average >= MEDIUM_RANGE_MIN) && (average <= MEDIUM_RANGE_MAX))
  {
    Serial.println(" Medium Status Indication by Yellow color LED");
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(YELLOW_LED_PIN, HIGH);
    digitalWrite(RED_LED_PIN, LOW);
  }
  else if ((average >= HIGH_RANGE_MIN) && (average <= HIGH_RANGE_MAX))
  {
    Serial.println(" HIGH Status Indication by Red color LED");
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(YELLOW_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, HIGH);
  }
}
/*******************************************************************************
 * PROCEDURE: Part 3 of the Assigment
 * PURPOSE: Flash (onboard LED) if average intensity  exceeds the threshold.
 * it will Increase flash rate with higher readings when it exceeds.
 * NAME: Sahil Mukeshbhai Kakadiya
 * DATE: 10-10-2024
 *******************************************************************************/
void Assignment_Part_3()
{
  Serial.println("Selecting the part 3 of the Assigment ");
  if (average > thresholdAverage)
  {
    Serial.println(" Threshold is reached  Status Indication ");
    /*The sensor value is mapped to the PWM frequency, allowing dynamic adjustment of the LED blinking rate.
    As the sensor reading increases, the LED blinks faster, providing real-time feedback based on the intensity.*/
    /* thresholdAverage - 255 = 105 ==>  105/5 = 21:  Means the rate will be increase by 1 wth step of 5 point increase in average value */
    flashingRateValue = map(average, thresholdAverage, 255, 1, 21);
    /*analogWriteFreq Writes the determine the freq used based on the Intensity Averaged value */
    Serial.print("Flashing Rate Value:\t" + String(int(flashingRateValue)) + "\n");
    /*analogWriteFreq Writes the determine the freq used based on the Intensity Averaged value */
    analogWriteFreq(flashingRateValue);
    Serial.println(" Threshold is excessed  Status Indication by Blue color LED with varies its blinking speed");
    /*analogWrite Writes  value to pin with the duty cycle of 50%, so that we can see the blinking of the LED */
    analogWrite(BLUE_LED_PIN, 50); 
  }
  else
  {
    digitalWrite(BLUE_LED_PIN, HIGH);  // Active LOW Logic
  }
}

/*******************************************************************************
 * PROCEDURE: modeChange
 * PURPOSE: This ISR function is triggered when the button is pressed.
 * Each button press advances the program to the next mode (Part 1, Part 2, or Part 3).
 * It cycles through the modes, allowing you to switch parts without reprogramming the ESP8266.
 * NAME: Sahil Mukeshbhai Kakadiya
 * DATE: 10-10-2024
 *******************************************************************************/
IRAM_ATTR void modeChange()
{
  /*This detachInterrupt reduces the effects of button debounce and 
  prevents multiple a hardware interrupts from being triggered by a single button press.*/
  detachInterrupt(digitalPinToInterrupt(PUSH_BUTTON_PIN));

  /*Each button press advances the program to the next mode.*/
  if (currMode < 3)
    currMode = currMode + 1;
  else
    currMode = 1;

  /*It ensures only the LEDs used in current part/Mode is the only one to active and others are going to LOW*/
  if ((currMode == 1) || (currMode == 3))
  {
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(YELLOW_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, LOW);
  }
  else
  {
    digitalWrite(BLUE_LED_PIN, HIGH);  // Active LOW Logic
  }
  /*This call to delayMicroseconds creates the small  delay to for reactivitin the the interrupt, so that the debounce is settled */
  delayMicroseconds(10000);
  /*This call to attachInterrupt reactivates the interrupt, allowing the user to change modes again once the debounce effect has settled.*/
  attachInterrupt(digitalPinToInterrupt(PUSH_BUTTON_PIN), modeChange, RISING);
}
