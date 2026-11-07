#define TIRT_TELEMETRY 1
#include "../firmware/race_two_marker/race_two_marker.ino"
#include <cassert>
#include <cstdio>
MockSerial Serial;
static uint32_t us=0;static int button=HIGH,outputs[20]={};
void pinMode(uint8_t,uint8_t){} void digitalWrite(uint8_t,uint8_t){}
void analogWrite(uint8_t pin,int value){outputs[pin]=value;}
int digitalRead(uint8_t){return button;}
int analogRead(uint8_t pin){us+=104;return pin==A3?35:500;}
uint32_t micros(){return us;}
uint32_t millis(){return us/1000;}
int main(int argc,char** argv){
 setup();assert(Serial.baud==115200);
 for(int i=0;i<60;i++){loop();us+=500;}
 assert(!running&&outputs[5]==0&&outputs[6]==0&&Serial.writes>0);
 button=LOW;for(int i=0;i<60;i++){loop();us+=500;}
 assert(running&&!stopped&&outputs[5]>0&&outputs[6]>0);
 int writes=Serial.writes;Serial.capacity=0;
 for(int i=0;i<60;i++){loop();us+=500;}
 assert(Serial.writes==writes&&outputs[5]>0&&outputs[6]>0);
 Serial.capacity=63;
 button=HIGH;for(int i=0;i<60;i++){loop();us+=500;}
 button=LOW;for(int i=0;i<60;i++){loop();us+=500;}
 assert(stopped&&outputs[5]==0&&outputs[6]==0);
 if(argc>1){FILE* f=fopen(argv[1],"wb");assert(f);fwrite(Serial.bytes.data(),1,Serial.bytes.size(),f);fclose(f);}
 puts("running telemetry adapter and backpressure ok");
}
