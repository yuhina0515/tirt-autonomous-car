#pragma once
#include "motion_core.h"
#include "exit_motion.h"
namespace race {
using Wheels=race_motion::Wheels;
enum class Phase:uint8_t { BeforeLift,WaitLift,ExitLift,AfterLift,Finished,Fault };
enum class Fault:uint8_t { None,Manual,Timing,RunLimit,ExitTimeout,Motion,Uncertain };
struct Config {
 bool useSlowExit=false; // Temporarily disabled for final practice; true restores R2.
 uint16_t whiteOn[5]={70,70,70,70,70},whiteOff[5]={100,100,100,100,100};
 uint32_t whiteConfirmMs=30,liftWaitMs=27000,rearmMs=100,exitMs=1500,runMs=360000,uncertainMs=800;
};
class Controller {
 Config cfg;race_motion::Controller motion;race_motion::ExitFollower exitFollower;
 bool started=false,pending=false,clearPending=false,uncertain=false,recovering=false;
 uint32_t began=0,last=0,whiteAt=0,waitAt=0,exitAt=0,clearAt=0,uncertainAt=0,recoverAt=0,motionMs=0;
 uint8_t bits=0,count=0;
 Wheels fail(Fault reason){fault=reason;phase=Phase::Fault;return Wheels();}
public:
 Phase phase=Phase::BeforeLift;Fault fault=Fault::None;
 Controller(Config config=Config()):cfg(config){}
 uint8_t mask()const{return bits;}
 uint8_t events()const{return count;}
 const race_motion::State& motionState()const{return motion.state();}
 Wheels tick(uint32_t now,const uint16_t raw[5],bool stop=false){
  if(stop)return fail(Fault::Manual);
  if(phase==Phase::Fault||phase==Phase::Finished)return Wheels();
  uint32_t dt=started?now-last:0;
  if(!started){started=true;began=now;}
  last=now;
  if(dt>100)return fail(Fault::Timing);
  if(now-began>=cfg.runMs)return fail(Fault::RunLimit);
  uint16_t adc[5];
  for(uint8_t i=0;i<5;i++){
   uint8_t bit=uint8_t(16>>i);
   if(raw[i]<cfg.whiteOn[i])bits|=bit;
   else if(raw[i]>=cfg.whiteOff[i])bits&=uint8_t(~bit);
   adc[i]=(bits&bit)?35:500; // One canonical Schmitt state for both layers.
  }
  const bool allWhite=bits==31;
  const uint8_t inner=(bits>>1)&7;
  if(phase==Phase::WaitLift){
   if(now-waitAt<cfg.liftWaitMs)return Wheels();
   phase=Phase::ExitLift;exitAt=now;clearPending=false;motion.reset();motionMs=0;exitFollower.reset();
  }
  if(phase==Phase::ExitLift){
   // Expiry wins over a late line return. All-white here is the same marker.
   if(now-exitAt>=cfg.exitMs)return fail(Fault::ExitTimeout);
   Wheels exitWheels=cfg.useSlowExit?exitFollower.tick(now,bits):Wheels();
   if(race_motion::ExitFollower::clearMarker(bits)){
    if(!clearPending){clearPending=true;clearAt=now;}
    if(now-clearAt>=cfg.rearmMs){phase=Phase::AfterLift;pending=false;uncertain=false;if(cfg.useSlowExit){motion.reset();motionMs=0;}}
   }else clearPending=false;
   if(cfg.useSlowExit)return exitWheels;
   // Keep marker lockout, but let normal tracking run immediately.
   // A wide patch has no lateral position: use native startup speed until line appears.
   if(allWhite){uncertain=false;recovering=false;return Wheels(race_motion::Settings::stage1,race_motion::Settings::stage1); }
  }
  if(allWhite&&phase!=Phase::ExitLift){
   recovering=false; // White interrupts continuous narrow recovery, not its budget.
   // Stop on first observation; require continuous confirmation to count.
   if(!pending){pending=true;whiteAt=now;}
   if(now-whiteAt>=cfg.whiteConfirmMs){
    count++;pending=false;uncertain=false;
    if(phase==Phase::BeforeLift){phase=Phase::WaitLift;waitAt=now;}
    else phase=Phase::Finished;
   }
   return Wheels();
  }
  pending=false;
  if(uncertain&&now-uncertainAt>=cfg.uncertainMs)return fail(Fault::Uncertain);
  if(inner==0||inner==5||inner==7){
   recovering=false;
   if(!uncertain){uncertain=true;uncertainAt=now;}
   if(now-uncertainAt>=cfg.uncertainMs)return fail(Fault::Uncertain);
  }else if(uncertain){
   if(!recovering){recovering=true;recoverAt=now;}
   if(now-recoverAt>=30){uncertain=false;recovering=false;}
  }
  // Only active motion time advances the inherited search/acceleration timers.
  motionMs+=dt;Wheels result=motion.tick(motionMs,adc);
  if(motion.state().fault!=race_motion::Fault::None)return fail(Fault::Motion);
  return result;
 }
};
} // namespace race
