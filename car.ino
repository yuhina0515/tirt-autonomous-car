int  LINE_THRESHOLD;
int  SPEED_STRAIGHT;
int  sensorA1;
int  sensorA2;
int  sensorA3;
int  sensorA4;
int  sensorA5;
int  SPEED_TURN_INNER_MEDIUM;
int  sensorF;
int  WHITE_STOP_COUNT;
int  whiteCount;
int  sumW;
int  countOn;
int  absW;
int  innerSpeed;
int  TURN_KP;
int  rawA1;
int  rawA2;
int  rawA3;
int  rawA4;
int  rawA5;
#include <moto_NeoPixel.h>
moto_NeoPixel strip13= moto_NeoPixel(2,13, NEO_GRB + NEO_KHZ800);
void colorled13(int number,String c)
{
	long rgb_number = strtol(&c[1], NULL, 16);
   int r = rgb_number >> 16;
   int g = rgb_number >> 8 & 0xFF;
   int b = rgb_number & 0xFF;
   if(number <= 0) number = 0;
      else  number--;
   strip13.setPixelColor(number,strip13.Color(r,g,b));
   strip13.show();
}

/**
 * 描述此函式...
 */
void stop2() {
  digitalWrite(7,LOW);
  analogWrite(5,0);
  digitalWrite(4,HIGH);
  analogWrite(6,0);
}

void setup()
{
  Serial.begin(115200);
  strip13.begin();
  strip13.show();
  pinMode(12, INPUT);
  pinMode(A1, INPUT);
  pinMode(A2, INPUT);
  pinMode(A3, INPUT);
  pinMode(A4, INPUT);
  pinMode(A5, INPUT);
  pinMode(7, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(6, OUTPUT);
    LINE_THRESHOLD = 70;
  SPEED_STRAIGHT = 100;
  sensorA1 = 0;
  sensorA2 = 0;
  sensorA3 = 0;
  sensorA4 = 0;
  sensorA5 = 0;
  SPEED_TURN_INNER_MEDIUM = 5;
  sensorF = 0;
  WHITE_STOP_COUNT = 40;
  whiteCount = 0;
  sumW = 0;
  countOn = 0;
  absW = 0;
  innerSpeed = 0;
  TURN_KP = 75;
  rawA1 = 0;
  rawA2 = 0;
  rawA3 = 0;
  rawA4 = 0;
  rawA5 = 0;
  colorled13(1,"#0000ff");
  while ((digitalRead(12) == 1)) {
    delay(20);
  }
  colorled13(1,"#33ff33");

}


void loop()
{
  // Three-center-sensor baseline rewrite. A4/A3/A2 control
  // only; A5/A1 raw telemetry. PWM100, threshold70, TURN_KP75.
  // Button waits at boot only. LED behavior unchanged.
    colorled13(1,"#33ff33");
    // Read all five ADCs; preserve original raw telemetry.
    sensorA1 = analogRead(A1);
    sensorA2 = analogRead(A2);
    sensorA3 = analogRead(A3);
    sensorA4 = analogRead(A4);
    sensorA5 = analogRead(A5);
    rawA1 = sensorA1;
    rawA2 = sensorA2;
    rawA3 = sensorA3;
    rawA4 = sensorA4;
    rawA5 = sensorA5;
    // Exclude A1 and A5 from decisions; control uses A4/A3/A2 only.
    sensorA1 = 1023;
    sensorA5 = 1023;
    // Build F = 8*A4_on + 4*A3_on + 2*A2_on.
    sensorF = 0;
    if (sensorA2 < LINE_THRESHOLD) {
      sensorF = sensorF + 2;
    }
    if (sensorA3 < LINE_THRESHOLD) {
      sensorF = sensorF + 4;
    }
    if (sensorA4 < LINE_THRESHOLD) {
      sensorF = sensorF + 8;
    }
    // Position weights: A4=-1, A3=0, A2=+1. Integer proportional inner PWM; minimum5.
    sumW = 0;
    countOn = 0;
    if (sensorA2 < LINE_THRESHOLD) {
      sumW = sumW + 1;
      countOn = countOn + 1;
    }
    if (sensorA3 < LINE_THRESHOLD) {
      countOn = countOn + 1;
    }
    if (sensorA4 < LINE_THRESHOLD) {
      sumW = sumW + -1;
      countOn = countOn + 1;
    }
    absW = sumW;
    if (sumW < 0) {
      absW = 0 - sumW;
    }
    if (countOn > 0) {
      innerSpeed = SPEED_STRAIGHT - (absW * TURN_KP) / countOn;
    }
    if (innerSpeed < SPEED_TURN_INNER_MEDIUM) {
      innerSpeed = SPEED_TURN_INNER_MEDIUM;
    }
    // F=10: hold. Left/right: original proportional steering. F=0: hold 40 loops,
    // then stop. Otherwise forward. No latched stop or new route strategy.
    if (sensorF == 10) {
    } else if (sensorA4 < LINE_THRESHOLD && sensorA2 > LINE_THRESHOLD) {
      digitalWrite(7,LOW);
      analogWrite(5,innerSpeed);
      digitalWrite(4,HIGH);
      analogWrite(6,SPEED_STRAIGHT);
    } else if (sensorA2 < LINE_THRESHOLD && sensorA4 > LINE_THRESHOLD) {
      digitalWrite(7,LOW);
      analogWrite(5,SPEED_STRAIGHT);
      digitalWrite(4,HIGH);
      analogWrite(6,innerSpeed);
    } else if (sensorF == 0) {
      if (whiteCount < WHITE_STOP_COUNT) {
        whiteCount = whiteCount + 1;
      } else {
        stop2();
        colorled13(1,"#0000ff");
      }
    } else {
      digitalWrite(7,LOW);
      analogWrite(5,SPEED_STRAIGHT);
      digitalWrite(4,HIGH);
      analogWrite(6,SPEED_STRAIGHT);
    }
    // Original 115200-baud raw ADC/F telemetry; no new capture protocol.
    Serial.print((String("A1=") + String(rawA1)));
    Serial.print((String("A2=") + String(rawA2)));
    Serial.print((String("A3=") + String(rawA3)));
    Serial.print((String("A4=") + String(rawA4)));
    Serial.print((String("A5=") + String(rawA5)));
    Serial.println((String("F=") + String(sensorF)));
    if (sensorF > 0) {
      whiteCount = 0;
    }

}