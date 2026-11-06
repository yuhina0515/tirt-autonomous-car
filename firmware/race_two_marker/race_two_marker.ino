// Practice candidate: first five-white lift, second five-white finish.
// No external library dependency. D12 uses the existing external bias circuit.
#include <Arduino.h>
#include "controller.h"
#ifdef TIRT_TELEMETRY
#include "telemetry.h"
#endif
race::Controller controller;
bool lastLow=false,released=false,running=false,stopped=false;
uint32_t changedAt=0;
void writeWheels(race::Wheels w){
 digitalWrite(7,w.left<0?HIGH:LOW);analogWrite(5,w.left<0?-w.left:w.left);
 digitalWrite(4,w.right<0?LOW:HIGH);analogWrite(6,w.right<0?-w.right:w.right);
}
void setup(){
#ifdef TIRT_TELEMETRY
 race_telemetry::begin();
#endif
 pinMode(12,INPUT);const uint8_t outputs[]={7,5,4,6};
 for(uint8_t p:outputs)pinMode(p,OUTPUT);
 for(uint8_t p=A1;p<=A5;p++)pinMode(p,INPUT);
 writeWheels(race::Wheels());lastLow=digitalRead(12)==LOW;changedAt=millis();
}
void loop(){
#ifdef TIRT_TELEMETRY
 static uint32_t previousLoopUs=0;static bool haveLoop=false;
 uint32_t loopUs=micros(),gapUs=haveLoop?loopUs-previousLoopUs:0;previousLoopUs=loopUs;haveLoop=true;
#endif
 uint32_t now=millis();bool low=digitalRead(12)==LOW;
 if(low!=lastLow){lastLow=low;changedAt=now;}
 if(now-changedAt>=25){
  if(!low)released=true;
  else if(released){released=false;if(running)stopped=true;else running=true;}
 }
#ifdef TIRT_TELEMETRY
 uint32_t scanStartUs=micros();uint16_t adc[5];
 for(uint8_t i=0;i<5;i++)adc[4-i]=analogRead(A1+i);
 uint32_t measuredScanUs=micros()-scanStartUs;
 race::Wheels applied;
 if(running&&!stopped)applied=controller.tick(millis(),adc);
 writeWheels(applied);
 race_telemetry::emit(scanStartUs,gapUs,measuredScanUs>65535?65535:uint16_t(measuredScanUs),adc,controller,applied,running,stopped);
#else
 if(!running||stopped){writeWheels(race::Wheels());return;}
 uint16_t adc[5];for(uint8_t i=0;i<5;i++)adc[4-i]=analogRead(A1+i);
 writeWheels(controller.tick(millis(),adc));
#endif
}
