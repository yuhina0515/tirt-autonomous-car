#pragma once
#include <stdint.h>
const int A1=15,A2=16,A3=17,A4=18,A5=19;
const int INPUT=0,OUTPUT=1,LOW=0,HIGH=1;
extern unsigned long mockNow;
extern int mockButton,mockRaw[20],mockPwm[20],mockDigital[20];
inline unsigned long millis(){return mockNow;}
inline void pinMode(int,int){}
inline int analogRead(int p){return mockRaw[p];}
inline int digitalRead(int){return mockButton;}
inline void analogWrite(int p,int v){mockPwm[p]=v;}
inline void digitalWrite(int p,int v){mockDigital[p]=v;}
struct SerialStub {
 void begin(int){}
 template<typename T> void print(T){}
 template<typename T> void println(T){}
};
extern SerialStub Serial;
