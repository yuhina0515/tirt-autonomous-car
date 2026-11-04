#pragma once
#include <stdint.h>
constexpr uint8_t LOW=0,HIGH=1,INPUT=0,OUTPUT=1;
constexpr uint8_t A1=15,A2=16,A3=17,A4=18,A5=19;
void pinMode(uint8_t,uint8_t);
void digitalWrite(uint8_t,uint8_t);
void analogWrite(uint8_t,int);
int digitalRead(uint8_t);
int analogRead(uint8_t);
uint32_t millis();
