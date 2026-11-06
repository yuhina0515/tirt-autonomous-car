#include "../firmware/race_two_marker/controller.h"
#include <cassert>
#include <cstring>
#include <cstdio>
#include "../firmware/race_two_marker/race_two_marker.ino"
static uint32_t clockMs=0;static int button=LOW,outputs[20]={};
void pinMode(uint8_t,uint8_t){} void digitalWrite(uint8_t,uint8_t){}
void analogWrite(uint8_t pin,int value){outputs[pin]=value;}
int digitalRead(uint8_t){return button;}
int analogRead(uint8_t pin){return pin==A3?35:500;}
uint32_t millis(){return clockMs;}
static race::Wheels sample(race::Controller& c,uint32_t t,int mask){uint16_t a[5];for(int i=0;i<5;i++)a[i]=(mask&(16>>i))?35:500;return c.tick(t,a);}
static uint32_t lift(race::Controller& c,uint32_t start=0){for(uint32_t t=0;t<=30;t+=5){auto w=sample(c,start+t,31);assert(w.left==0&&w.right==0);}assert(c.events()==1&&c.phase==race::Phase::WaitLift);return start+30;}
static uint32_t after(race::Controller& c,uint32_t start=0){uint32_t at=lift(c,start);for(uint32_t d=5;d<27000;d+=5){auto w=sample(c,at+d,int(d/5)%32);assert(w.left==0&&w.right==0&&c.events()==1);}sample(c,at+27000,31);assert(c.phase==race::Phase::ExitLift);for(uint32_t d=5;d<=105;d+=5)sample(c,at+27000+d,4);assert(c.phase==race::Phase::AfterLift);return at+27105;}
int main(int argc,char**argv){assert(argc==2);const char* name=argv[1];
 if(!strcmp(name,"normal_exit")){
  race::Controller c;auto at=lift(c);for(int d=5;d<27000;d+=5)sample(c,at+d,31);
  auto w=sample(c,at+27000,31);assert(w.left==100&&w.right==100&&c.events()==1);
  w=sample(c,at+27005,8);assert(w.left<w.right&&w.right>45&&c.phase==race::Phase::ExitLift);
  for(int d=27010;d<=27105;d+=5)sample(c,at+d,12);
  assert(c.phase==race::Phase::AfterLift&&c.events()==1);
  for(int d=27110;d<=27140;d+=5)sample(c,at+d,31);
  assert(c.phase==race::Phase::Finished&&c.events()==2);
 }else if(!strcmp(name,"normal_exit_continuity")){
  race::Config cfg;cfg.liftWaitMs=50;race::Controller c(cfg);auto at=lift(c);
  for(int d=5;d<50;d+=5)sample(c,at+d,31);
  for(int d=50;d<=150;d+=5)sample(c,at+d,4);
  assert(c.phase==race::Phase::AfterLift&&c.motionState().straightElapsed>=90);
 }else if(!strcmp(name,"normal_exit_guards")){
  race::Controller c;auto at=lift(c);
  for(int d=5;d<=28500;d+=5){auto w=sample(c,at+d,31);assert(c.events()==1);if(d<27000||d>=28500)assert(w.left==0&&w.right==0);}
  assert(c.fault==race::Fault::ExitTimeout);
  race::Controller stoppedController;at=lift(stoppedController);
  for(int d=5;d<=27000;d+=5)sample(stoppedController,at+d,31);
  uint16_t raw[5]={500,35,500,500,500};auto w=stoppedController.tick(at+27005,raw,true);
  assert(w.left==0&&w.right==0&&stoppedController.fault==race::Fault::Manual);
 }else if(!strcmp(name,"patterns")){
  for(int mask=0;mask<32;mask++){race::Config slow;slow.useSlowExit=true;race::Controller c(slow);for(int t=0;t<=40;t+=5)sample(c,t,mask);assert(c.events()==(mask==31?1:0));}
  for(int mask=0;mask<32;mask++){race::Config slow;slow.useSlowExit=true;race::Controller c(slow);uint32_t t=after(c);for(int d=5;d<=45;d+=5)sample(c,t+d,mask);assert(c.events()==(mask==31?2:1));}
 }else if(!strcmp(name,"exit_patterns")){
  for(int mask=0;mask<32;mask++){race::Config slow;slow.useSlowExit=true;race::Controller c(slow);auto t=lift(c);for(int d=5;d<27000;d+=5)sample(c,t+d,31);for(int d=27000;d<=27105;d+=5)sample(c,t+d,mask);assert(c.events()==1);assert(c.phase==((mask==2||mask==4||mask==6||mask==8||mask==12)?race::Phase::AfterLift:race::Phase::ExitLift));}
 }else if(!strcmp(name,"exit_steering")){
  race::Config slow;slow.useSlowExit=true;race::Controller c(slow);auto at=lift(c);for(int d=5;d<27000;d+=5)sample(c,at+d,31);
  auto w=sample(c,at+27000,8);assert(w.left<w.right&&w.right<=45);assert(c.phase==race::Phase::ExitLift&&c.events()==1);
  w=sample(c,at+27005,2);assert(w.right<w.left&&w.left<=45);
 }else if(!strcmp(name,"exit_curved_rearm")){
  int masks[]={2,6,8,12};for(int mask: masks){race::Config slow;slow.useSlowExit=true;race::Controller c(slow);auto at=lift(c);for(int d=5;d<27000;d+=5)sample(c,at+d,31);
   for(int d=27000;d<=27100;d+=5)sample(c,at+d,mask);
   assert(c.phase==race::Phase::AfterLift&&c.events()==1);
   auto w=sample(c,at+27105,mask);assert(mask==8||mask==12?w.left<w.right:w.right<w.left);
   for(int d=27110;d<=27140;d+=5)sample(c,at+d,31);
   assert(c.phase==race::Phase::Finished&&c.events()==2);
  }
 }else if(!strcmp(name,"exit_loss")){
  race::Config cfg;cfg.liftWaitMs=50;cfg.useSlowExit=true;race::Controller c(cfg);auto at=lift(c);
  for(int d=5;d<50;d+=5)sample(c,at+d,31);
  auto w=sample(c,at+50,8);assert(w.left<w.right);
  for(int d=55;d<=165;d+=5){w=sample(c,at+d,0);assert(w.left<w.right&&c.events()==1);}
  w=sample(c,at+170,0);assert(w.left==0&&w.right==0);
  w=sample(c,at+175,2);assert(w.right<w.left&&c.phase==race::Phase::ExitLift);
  for(int d=180;d<=275;d+=5)sample(c,at+d,6);
  assert(c.phase==race::Phase::AfterLift&&c.events()==1);
 }else if(!strcmp(name,"exit_rearm_noise")){
  race::Config cfg;cfg.liftWaitMs=50;cfg.useSlowExit=true;race::Controller c(cfg);auto at=lift(c);
  for(int d=5;d<50;d+=5)sample(c,at+d,31);
  for(int d=50;d<=145;d+=5)sample(c,at+d,8);
  auto w=sample(c,at+150,31);assert(w.left==0&&w.right==0&&c.events()==1);
  for(int d=155;d<=250;d+=5)sample(c,at+d,8);
  assert(c.phase==race::Phase::ExitLift);sample(c,at+255,12);assert(c.phase==race::Phase::AfterLift);
 }else if(!strcmp(name,"exit_outer_and_split")){
  race::Config cfg;cfg.liftWaitMs=50;cfg.useSlowExit=true;race::Controller c(cfg);auto at=lift(c);
  for(int d=5;d<50;d+=5)sample(c,at+d,31);
  for(int d=50;d<=200;d+=5){auto w=sample(c,at+d,9);assert(w.left<w.right&&c.phase==race::Phase::ExitLift);}
  auto w=sample(c,at+205,10);assert(w.left==0&&w.right==0&&c.events()==1);
  uint16_t raw[5]={500,35,500,500,500};w=c.tick(at+210,raw,true);assert(w.left==0&&w.right==0&&c.fault==race::Fault::Manual);
 }else if(!strcmp(name,"exit_seeded")){
  // 1000 generated sensor sequences, not physics or real-car trials.
  uint32_t seed=7301;
  for(int trial=0;trial<1000;trial++){
   race::Config cfg;cfg.liftWaitMs=50;cfg.useSlowExit=true;race::Controller c(cfg);auto at=lift(c);
   for(int d=5;d<50;d+=5)sample(c,at+d,31);
   bool left=trial%2;int masks[3]={left?8:2,left?12:6,4};
   for(int d=50;d<=150;d+=5){seed=seed*1664525U+1013904223U;auto w=sample(c,at+d,masks[seed%3]);
    assert(w.left>=15&&w.right>=15&&w.left<=45&&w.right<=45&&c.events()==1);
    if(d<150)assert(c.phase==race::Phase::ExitLift);
   }
   assert(c.phase==race::Phase::AfterLift);
   for(int d=155;d<=185;d+=5){auto w=sample(c,at+d,31);assert(w.left==0&&w.right==0);}
   assert(c.phase==race::Phase::Finished&&c.events()==2);
  }
 }else if(!strcmp(name,"blips")){
  race::Config slow;slow.useSlowExit=true;race::Controller c(slow);for(int t=0;t<=800;t+=5)sample(c,t,t%100==95?4:0);assert(c.fault==race::Fault::Uncertain);
 }else if(!strcmp(name,"transitions")){
  for(int a=0;a<32;a++)for(int b=0;b<32;b++){race::Config slow;slow.useSlowExit=true;race::Controller c(slow);sample(c,0,a);sample(c,5,b);assert(c.events()==0);}
 }else if(!strcmp(name,"complete")){
  race::Config slow;slow.useSlowExit=true;race::Controller c(slow);auto t=after(c);for(int d=5;d<=35;d+=5){auto w=sample(c,t+d,31);assert(w.left==0&&w.right==0);}assert(c.events()==2&&c.phase==race::Phase::Finished);
  for(int i=0;i<32;i++){auto w=sample(c,t+40+i*5,i);assert(w.left==0&&w.right==0&&c.events()==2);}
 }else if(!strcmp(name,"noise")){
  race::Config slow;slow.useSlowExit=true;race::Controller c(slow);for(int t=0;t<200;t+=5)sample(c,t,t%30<25?31:4);assert(c.events()==0);
  race::Controller h;uint16_t a[5]={35,35,35,35,35};h.tick(0,a);for(auto& x:a)x=85;h.tick(5,a);assert(h.mask()==31);for(auto& x:a)x=100;h.tick(10,a);assert(h.mask()==0&&h.events()==0);
 }else if(!strcmp(name,"stuck")){
  race::Config slow;slow.useSlowExit=true;race::Controller c(slow);auto t=lift(c);for(int d=5;d<=28500;d+=5)sample(c,t+d,31);assert(c.events()==1&&c.fault==race::Fault::ExitTimeout);
 }else if(!strcmp(name,"deadline")){
  race::Config slow;slow.useSlowExit=true;race::Controller c(slow);auto at=lift(c);for(int d=5;d<=28495;d+=5)sample(c,at+d,d>=28400?4:31);sample(c,at+28500,4);assert(c.fault==race::Fault::ExitTimeout&&c.events()==1);
 }else if(!strcmp(name,"rollover")){
  race::Config slow;slow.useSlowExit=true;race::Controller c(slow);auto t=after(c,0xfffff000U);for(int d=5;d<=35;d+=5)sample(c,t+d,31);assert(c.phase==race::Phase::Finished);
 }else if(!strcmp(name,"stop")){
  race::Config slow;slow.useSlowExit=true;race::Controller c(slow);lift(c);uint16_t a[5]={35,35,35,35,35};c.tick(35,a,true);assert(c.phase==race::Phase::Fault);auto w=c.tick(40,a);assert(w.left==0&&w.right==0);
 }else if(!strcmp(name,"runlimit")){
  race::Config slow;slow.useSlowExit=true;race::Controller c(slow);for(uint32_t t=0;t<=360000;t+=5)sample(c,t,4);assert(c.fault==race::Fault::RunLimit);
 }else if(!strcmp(name,"timing")){
  race::Config slow;slow.useSlowExit=true;race::Controller c(slow);sample(c,0,4);sample(c,101,4);assert(c.fault==race::Fault::Timing);
 }else if(!strcmp(name,"adapter")){
  setup();for(clockMs=0;clockMs<=100;clockMs+=5)loop();assert(!running&&outputs[5]==0&&outputs[6]==0);
  button=HIGH;for(;clockMs<=140;clockMs+=5)loop();button=LOW;for(;clockMs<=180;clockMs+=5)loop();assert(running&&!stopped&&outputs[5]>0&&outputs[6]>0);
  for(;clockMs<=220;clockMs+=5)loop();assert(!stopped);
  button=HIGH;for(;clockMs<=260;clockMs+=5)loop();button=LOW;for(;clockMs<=300;clockMs+=5)loop();assert(stopped&&outputs[5]==0&&outputs[6]==0);
 }else if(!strcmp(name,"dump")){
  puts("mask,inner,left_at_0,right_at_0,left_at_40,right_at_40,phase_at_40,fault_at_40,events");
  for(int mask=0;mask<32;mask++){race::Config slow;slow.useSlowExit=true;race::Controller c(slow);auto first=sample(c,0,mask);race::Wheels last;for(int t=5;t<=40;t+=5)last=sample(c,t,mask);
   printf("%d,%d,%d,%d,%d,%d,%d,%d,%d\n",mask,(mask>>1)&7,first.left,first.right,last.left,last.right,int(c.phase),int(c.fault),c.events());}return 0;
 }else return 2;
 puts("ok");return 0;
}
