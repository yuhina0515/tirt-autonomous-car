#include "../firmware/race_two_marker/controller.h"
#include <cassert>
#include <cstdio>
static race::Wheels tick(race::Controller& c,uint32_t t,int mask,bool stop=false){
 uint16_t a[5];for(int i=0;i<5;i++)a[i]=(mask&(16>>i))?35:500;
 return c.tick(t,a,stop);
}
static void bounds(race::Wheels w){assert(w.left>=-255&&w.left<=255&&w.right>=-255&&w.right<=255);}
static void zero(race::Wheels w){assert(w.left==0&&w.right==0);}
int main(){
 // All32 masks in real27s wait and in both exit strategies.
 for(int slow=0;slow<2;slow++)for(int mask=0;mask<32;mask++){
  race::Config cfg;cfg.useSlowExit=slow;race::Controller c(cfg);
  for(int t=0;t<=30;t+=5)zero(tick(c,t,31));
  assert(c.phase==race::Phase::WaitLift&&c.events()==1);
  for(int t=35;t<27030;t+=5){zero(tick(c,t,mask));assert(c.events()==1);}
  for(int t=27030;t<=27050;t+=5){bounds(tick(c,t,mask));assert(c.events()==1);}
  zero(tick(c,27055,mask,true));assert(c.fault==race::Fault::Manual);
  for(int other=0;other<32;other++)zero(tick(c,27060+5*other,other));
 }
 // Variable-dt sensor histories with terminal-stop and count invariants.
 uint32_t random=0x1107;
 for(int trial=0;trial<1000;trial++){
  race::Config cfg;cfg.liftWaitMs=50;cfg.useSlowExit=trial%2;
  race::Controller c(cfg);uint32_t t=trial%2?0xfffff000U:0;uint8_t previous=0;
  for(int step=0;step<700;step++){
   random=random*1664525U+1013904223U;t+=1+(random%12);
   int mask=step<8?31:int((random>>12)&31);
   bool terminal=c.phase==race::Phase::Fault||c.phase==race::Phase::Finished;
   auto w=tick(c,t,mask,step==600);bounds(w);
   if(terminal||c.phase==race::Phase::Fault||c.phase==race::Phase::Finished||c.phase==race::Phase::WaitLift)zero(w);
   assert(c.events()>=previous&&c.events()<=2);previous=c.events();
  }
 }
 // Run/timing expiry must win even over a new white marker.
 {race::Config cfg;cfg.runMs=30;race::Controller c(cfg);zero(tick(c,0,31));zero(tick(c,30,31));assert(c.fault==race::Fault::RunLimit&&c.events()==0);}
 {race::Controller c;tick(c,0,4);zero(tick(c,101,31));assert(c.fault==race::Fault::Timing&&c.events()==0);}
 // Full-white exit override must not carry an old uncertain window back into tracking.
 {race::Config cfg;cfg.liftWaitMs=50;race::Controller c(cfg);
  for(int t=0;t<=30;t+=5)zero(tick(c,t,31));
  for(int t=35;t<80;t+=5)zero(tick(c,t,31));
  tick(c,80,31);tick(c,85,14);
  for(int t=90;t<=940;t+=5)tick(c,t,31);
  auto w=tick(c,945,4);assert(c.fault==race::Fault::None&&w.left>0&&w.right>0);
  for(int t=950;t<=1045;t+=5)tick(c,t,4);
  assert(c.phase==race::Phase::AfterLift&&c.events()==1);
 }
 // White/loss alternation may renew uncertainty, never the absolute exit deadline.
 {race::Config cfg;cfg.liftWaitMs=50;race::Controller c(cfg);
  for(int t=0;t<=30;t+=5)zero(tick(c,t,31));
  for(int t=35;t<80;t+=5)zero(tick(c,t,31));
  for(int t=80;t<1580;t+=5){bounds(tick(c,t,(t-80)%200==0?31:0));assert(c.fault==race::Fault::None&&c.events()==1);}
  zero(tick(c,1580,31));assert(c.fault==race::Fault::ExitTimeout&&c.events()==1);
 }
 // A white blip breaks narrow recovery continuity without renewing its800ms budget.
 {race::Controller c;
  for(int t=0;t<700;t+=5)tick(c,t,0);
  for(int t=700;t<=720;t+=5)tick(c,t,4);
  for(int t=725;t<=745;t+=5)zero(tick(c,t,31));
  for(int t=750;t<=765;t+=5)tick(c,t,4);
  for(int t=770;t<=800;t+=5)tick(c,t,0);
  assert(c.fault==race::Fault::Uncertain&&c.events()==0);
 }
 puts("priority invariants ok:64 wait/exit matrices,1000 histories");
}
