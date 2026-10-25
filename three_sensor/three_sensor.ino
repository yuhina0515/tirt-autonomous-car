int  LINE_THRESHOLD;
int  SPEED_STRAIGHT;
int  SPEED_BACKWARD;
int  sensorA1;
int  sensorA2;
int  sensorA3;
int  sensorA4;
int  sensorA5;
int  SPEED_TURN_INNER_FINE;
int  SPEED_TURN_INNER_MEDIUM;
int  SPEED_TURN_PIVOT;
int  sensorF;
int  WHITE_STOP_COUNT;
int  whiteCount;
int  CROSS_HOLD;
int  crossCount;
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
void forward() {
  digitalWrite(7,LOW);
  analogWrite(5,SPEED_STRAIGHT);
  digitalWrite(4,HIGH);
  analogWrite(6,SPEED_STRAIGHT);
}

/**
 * 描述此函式...
 */
void backward() {
  digitalWrite(7,HIGH);
  analogWrite(5,SPEED_BACKWARD);
  digitalWrite(4,LOW);
  analogWrite(6,SPEED_BACKWARD);
}

int  dist;
float ultrasonic_distance_9_10() {
  digitalWrite(9, LOW);
  digitalWrite(10, LOW);
  delayMicroseconds(5);
  digitalWrite(9, HIGH);
  delayMicroseconds(10);
  digitalWrite(9, LOW);
  unsigned long sonic_duration = pulseIn(10, HIGH);
  float distance_cm = (sonic_duration / 2.0) / 29.1;
  return distance_cm;
}

/**
 * 描述此函式...
 */
void ultrasonic_warn() {
  dist = 0;
  dist = ultrasonic_distance_9_10( );
  if (dist < 15) {
    colorled13(1,"#ff0000");
    tone(8,659,3000);
    stop2();
  } else if (dist < 50) {
    colorled13(1,"#ffff00");
    for (int count = 0; count < 3; count++) {
      tone(8,523,500);
    }
  } else if (dist < 100) {
    colorled13(1,"#33ff33");
  }
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
  SPEED_BACKWARD = 40;
  sensorA1 = 0;
  sensorA2 = 0;
  sensorA3 = 0;
  sensorA4 = 0;
  sensorA5 = 0;
  SPEED_TURN_INNER_FINE = 12;
  SPEED_TURN_INNER_MEDIUM = 5;
  SPEED_TURN_PIVOT = 95;
  sensorF = 0;
  WHITE_STOP_COUNT = 40;
  whiteCount = 0;
  CROSS_HOLD = 30;
  crossCount = 0;
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

  pinMode( 9 , OUTPUT);
  pinMode( 10 , INPUT);
  pinMode(8, OUTPUT);
}


void loop()
{
    colorled13(1,"#33ff33");
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
    sensorA1 = 1023;
    sensorA5 = 1023;
    sensorF = 0;
    if (sensorA1 < LINE_THRESHOLD) {
      sensorF = sensorF + 1;
    }
    if (sensorA2 < LINE_THRESHOLD) {
      sensorF = sensorF + 2;
    }
    if (sensorA3 < LINE_THRESHOLD) {
      sensorF = sensorF + 4;
    }
    if (sensorA4 < LINE_THRESHOLD) {
      sensorF = sensorF + 8;
    }
    if (sensorA5 < LINE_THRESHOLD) {
      sensorF = sensorF + 16;
    }
    sumW = 0;
    countOn = 0;
    if (sensorA1 < LINE_THRESHOLD) {
      sumW = sumW + 2;
      countOn = countOn + 1;
    }
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
    if (sensorA5 < LINE_THRESHOLD) {
      sumW = sumW + -2;
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
    if (sensorF == 31 || sensorF == 15 || sensorF == 23 || sensorF == 27 || sensorF == 29 || sensorF == 30 || crossCount > 0) {
      if (sensorF == 31 || sensorF == 15 || sensorF == 23 || sensorF == 27 || sensorF == 29 || sensorF == 30) {
        crossCount = CROSS_HOLD;
      } else {
        crossCount = crossCount - 1;
      }
      digitalWrite(7,LOW);
      analogWrite(5,SPEED_STRAIGHT);
      digitalWrite(4,HIGH);
      analogWrite(6,SPEED_STRAIGHT);
    } else if (sensorF == 10 || sensorF == 17 || sensorF == 27) {
    } else if (sensorF == 16) {
      digitalWrite(7,HIGH);
      analogWrite(5,SPEED_TURN_PIVOT);
      digitalWrite(4,HIGH);
      analogWrite(6,SPEED_STRAIGHT);
    } else if (sensorF == 1) {
      digitalWrite(7,LOW);
      analogWrite(5,SPEED_STRAIGHT);
      digitalWrite(4,LOW);
      analogWrite(6,SPEED_TURN_PIVOT);
    } else if (sensorF > 23) {
      digitalWrite(7,LOW);
      analogWrite(5,innerSpeed);
      digitalWrite(4,HIGH);
      analogWrite(6,SPEED_STRAIGHT);
    } else if (sensorA2 < LINE_THRESHOLD && sensorA1 < LINE_THRESHOLD) {
      digitalWrite(7,LOW);
      analogWrite(5,SPEED_STRAIGHT);
      digitalWrite(4,HIGH);
      analogWrite(6,innerSpeed);
    } else if (sensorA4 < LINE_THRESHOLD && sensorA2 > LINE_THRESHOLD) {
      if (sensorA3 < LINE_THRESHOLD) {
        digitalWrite(7,LOW);
        analogWrite(5,innerSpeed);
        digitalWrite(4,HIGH);
        analogWrite(6,SPEED_STRAIGHT);
      } else {
        digitalWrite(7,LOW);
        analogWrite(5,innerSpeed);
        digitalWrite(4,HIGH);
        analogWrite(6,SPEED_STRAIGHT);
      }
    } else if (sensorA2 < LINE_THRESHOLD && sensorA4 > LINE_THRESHOLD) {
      if (sensorA3 < LINE_THRESHOLD) {
        digitalWrite(7,LOW);
        analogWrite(5,SPEED_STRAIGHT);
        digitalWrite(4,HIGH);
        analogWrite(6,innerSpeed);
      } else {
        digitalWrite(7,LOW);
        analogWrite(5,SPEED_STRAIGHT);
        digitalWrite(4,HIGH);
        analogWrite(6,innerSpeed);
      }
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