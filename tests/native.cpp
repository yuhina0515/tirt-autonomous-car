#include "Arduino.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <initializer_list>
unsigned long mockNow=0;
int mockButton=1,mockRaw[20]={0},mockPwm[20]={0},mockDigital[20]={0};
SerialStub Serial;
#ifndef SKETCH_FILE
#define SKETCH_FILE "../firmware/practice_controller/practice_controller.ino"
#endif
#include SKETCH_FILE
unsigned checks=0;
uint32_t hashTrace=2166136261U;
void check(bool ok){if(!ok){printf("FAILED at check %u state=%ld reason=%ld mask=%ld now=%lu\n",checks,controlState,reason,maskF,mockNow);fflush(stdout);}assert(ok);++checks;}
void sample(int mask,unsigned long dt=10){
 mockNow+=dt;
 const int pins[]={A5,A4,A3,A2,A1};
 const long line[]={line0,line1,line2,line3,line4},background[]={background0,background1,background2,background3,background4};
 for(int i=0;i<5;++i)mockRaw[pins[i]]=(int)(mask&(16>>i)?line[i]:background[i]);
 loop();
 check(leftPwm>=0&&leftPwm<=maxPwm&&rightPwm>=0&&rightPwm<=maxPwm);
 check((maskF&17)==0);
 long values[]={controlState,reason,maskF,lastPosition,leftPwm,rightPwm,(long)rejected};
 for(auto value:values){hashTrace^=(uint32_t)value;hashTrace*=16777619U;}
}
void stable(int mask,int ticks){for(int i=0;i<ticks;++i)sample(mask);}
void reset(){mockNow=0;mockButton=1;setup();}
void start(){reset();configReady=1;stable(4,4);mockButton=0;stable(4,4);mockButton=1;stable(4,25);check(controlState==2);}
int main(){
#ifdef CAPTURE_TEST
 reset();configReady=1;
 for(int m=0;m<32;++m){mockButton=m%2;stable(m,30);check(controlState==6&&leftPwm==0&&rightPwm==0);}
#elif defined(FIELD_PROFILE_TEST)
 // Execute the measured, armed field profile, not the unarmed default profile.
 reset();check(configReady==1&&lapEnabled==0&&maxPwm==70&&basePwm==60&&maxRunMs==60000);
 stable(4,30);check(controlState==0&&leftPwm==0&&rightPwm==0); // Boot never starts motion.
 reset();mockButton=0;stable(4,30);check(controlState==0&&leftPwm==0&&rightPwm==0);
 start();check(controlState==2&&leftPwm==basePwm&&rightPwm==basePwm);
 for(int edge:{8,2}){
  start();stable(edge,15);check(controlState==2);
  if(edge==8)check(leftPwm<rightPwm);else check(rightPwm<leftPwm);
  stable(0,8);check(controlState==3&&reason==14);
  if(edge==8)check(leftPwm==0&&rightPwm==searchPwm);else check(rightPwm==0&&leftPwm==searchPwm);
  stable(edge,8);check(controlState==2);
  stable(0,80);check(controlState==5&&leftPwm==0&&rightPwm==0);
 }
 start();stable(0,8);check(controlState==3&&reason==15&&leftPwm==rightPwm);
 stable(4,8);check(controlState==2);
 start();stable(0,35);check(controlState==5&&leftPwm==0&&rightPwm==0);
 start();stable(14,45);check(controlState==5&&reason!=13); // Lap detection stays disabled.
 reset();stable(14,4);mockButton=0;stable(14,4);mockButton=1;stable(14,30);
 check(controlState==1&&leftPwm==0&&rightPwm==0); // Narrow-line start required.
 stable(14,200);check(controlState==5&&reason==9);
 start();mockButton=0;stable(4,4);check(controlState==4&&reason==7&&leftPwm==0&&rightPwm==0);
 start();sample(4,51);check(controlState==5&&reason==6&&leftPwm==0&&rightPwm==0);
 start();runAtMs=mockNow-maxRunMs;sample(4);check(controlState==4&&reason==10&&leftPwm==0&&rightPwm==0);
 // Outer detectors remain logged-only under the measured endpoints.
 for(int outer=0;outer<4;++outer){
  start();stable(4|((outer&1)?1:0)|((outer&2)?16:0),20);
  check(controlState==2&&lastPosition==0&&leftPwm==basePwm&&rightPwm==basePwm);
 }
#else
 reset();mockButton=0;stable(4,30);check(controlState==0&&leftPwm==0&&rightPwm==0); // Unarmed cannot drive.
 reset();configReady=1;mockButton=0;stable(4,30);check(controlState==0); // Held at boot cannot start.
 start();check(leftPwm==100&&rightPwm==100);
 // Short all-on white-text flash: reject, slow, never reinterpret as straight intersection.
 sample(14);check(controlState==3&&reason==16);check(leftPwm<=65&&rightPwm<=65);
 stable(4,2);check(controlState==3);stable(4,5);check(controlState==2&&derivative==0);
 // Sustained full-width, split and lost observations all have bounded motion.
 for(int m:{0,10,14}){start();stable(m,40);check(controlState==5&&leftPwm==0&&rightPwm==0);stable(4,20);check(controlState==5);}
 start();for(int i=0;i<20;++i)sample(i%2?0:10);check(controlState==5); // Alternation cannot reset watchdog.
 start();for(int i=0;i<50;++i)sample(i%2?4:14);check(controlState==5); // Brief valid blips cannot reset it.
 start();sample(8);check(controlState==3);stable(4,8);check(controlState==2&&lastPosition==0); // Reject brief side text.
 start();stable(8,15);check(controlState==2&&lastPosition<0&&leftPwm<rightPwm);
 start();stable(2,15);check(controlState==2&&lastPosition>0&&rightPwm<leftPwm);
 // Recent edge position selects a bounded tight turn with the inner wheel stopped.
 for(int edge:{8,2}){
  start();stable(edge,15);stable(0,8);check(controlState==3&&reason==14);
  if(edge==8)check(leftPwm==0&&rightPwm==searchPwm);else check(rightPwm==0&&leftPwm==searchPwm);
  stable(edge,8);check(controlState==2); // Continuous reacquisition exits recovery.
  stable(0,80);check(controlState==5&&leftPwm==0&&rightPwm==0);
 }
 start();stable(0,8);check(controlState==3&&reason==15&&leftPwm==rightPwm);
 stable(4,8);check(controlState==2); // Short centered gap is traversed without inventing a turn.
 start();stable(8,15);stable(4,15);stable(0,8);check(recoveryKind==1); // Old corner direction is not reused.
 start();stable(8,15);stable(0,3);unsigned long deadline=uncertainAtMs;
 for(int i=0;i<80;++i)sample(i%2?4:0);check(controlState==5&&uncertainAtMs==deadline);
 // Starting on the full-width patch drives straight; black at start remains unpowered.
 reset();configReady=1;stable(14,4);mockButton=0;stable(14,4);mockButton=1;
 stable(14,30);check(controlState==1&&reason==12&&leftPwm==departurePwm&&rightPwm==departurePwm&&departed==0);
 stable(4,40);check(controlState==2&&departed==1);
 stable(14,30);check(controlState==3); // Early full-width patch is not a finish.
 stable(4,10);check(controlState==2);
 // Only a new continuously wide patch after departure and the minimum lap time can finish.
 runAtMs=mockNow-minLapMs;stable(14,30);check(controlState==4&&reason==13&&leftPwm==0&&rightPwm==0);
 stable(4,30);check(controlState==4&&reason==13);
 mockButton=0;stable(4,4);check(controlState==1&&departed==0); // Manual restart resets the lap latch.
 start();stable(4,40);runAtMs=mockNow-minLapMs;stable(14,10);stable(4,8);
 check(controlState==2);stable(14,10);check(controlState==3); // White bursts do not accumulate.
 start();lapEnabled=0;stable(4,40);runAtMs=mockNow-minLapMs;stable(14,45);check(controlState==5&&reason!=13);
 reset();configReady=1;stable(0,4);mockButton=0;stable(0,4);stable(0,10);check(leftPwm==0&&rightPwm==0);
 reset();configReady=1;stable(14,4);mockButton=0;stable(14,4);stable(14,210);
 check(controlState==5&&reason==9&&leftPwm==0&&rightPwm==0); // Cannot leave start: acquisition deadline.
 start();runAtMs=mockNow-minLapMs;stable(14,45);check(departed==0&&controlState==5&&reason!=13);
 // Manual/timing stops override active corner search.
 start();stable(8,15);stable(0,5);mockButton=0;stable(0,4);check(controlState==4&&leftPwm==0&&rightPwm==0);
 start();stable(8,15);stable(0,5);sample(0,51);check(controlState==5&&reason==6&&leftPwm==0&&rightPwm==0);
 // Every center pattern responds identically under any raw outer detector values.
 for(int middle=0;middle<8;++middle){
  long reference[7]={};
  for(int outer=0;outer<4;++outer){
   start();int mask=(middle<<1)|((outer&1)?1:0)|((outer&2)?16:0);stable(mask,20);
   long value[]={controlState,reason,maskF,lastPosition,leftPwm,rightPwm,(long)rejected};
   if(!outer)memcpy(reference,value,sizeof(value));else check(memcmp(reference,value,sizeof(value))==0);
  }
 }
 // Mirroring must mirror steering for stable narrow shapes.
 for(int m:{2,4,6,8,12}){
  start();stable(m,20);long l=leftPwm,r=rightPwm;
  int mirror=((m&2)?8:0)|(m&4)|((m&8)?2:0);
  start();stable(mirror,20);if(leftPwm!=r||rightPwm!=l){printf("mirror m=%d mirror=%d old=%ld,%ld new=%ld,%ld pos=%ld\n",m,mirror,l,r,leftPwm,rightPwm,lastPosition);fflush(stdout);}check(leftPwm==r&&rightPwm==l);
 }
 // Mixed-polarity, sensor-specific calibration must preserve steering.
 start();line1=900;background1=100;line2=60;background2=850;line3=800;background3=100;
 stable(8,20);check(controlState==2&&leftPwm<rightPwm);
 start();sample(4,51);check(controlState==5&&reason==6&&leftPwm==0&&rightPwm==0&&timingFaults==1);
 start();mockButton=0;stable(4,4);check(controlState==4&&reason==7&&leftPwm==0&&rightPwm==0);
 start();maxRunMs=100;sample(4);check(controlState==4&&reason==10&&leftPwm==0);
 // ADC values at Schmitt boundaries; saturated normalization stays bounded.
 start();mockRaw[A4]=1023;mockRaw[A3]=0;mockRaw[A2]=1023;mockNow+=10;loop();
 check(norm1>=0&&norm1<=1000&&norm2>=0&&norm2<=1000);
 if(sizeof(unsigned long)==4){
  start();mockNow=0xfffffff0UL;lastTickMs=mockNow;logAtMs=mockNow;runAtMs=mockNow;
  sample(4,10);sample(4,10);check(controlState==2&&dtMs==10);
 }
#endif
 printf("PASS checks=%u trace=%08x capture=%ld long_bytes=%zu\n",checks,hashTrace,driveMode,sizeof(unsigned long));
}
