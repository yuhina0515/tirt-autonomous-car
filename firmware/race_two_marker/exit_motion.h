#pragma once
#include "motion_core.h"

namespace race_motion {
// Low-speed reacquisition is independent of mission marker eligibility.
class ExitFollower {
 bool seen=false;
 int8_t direction=0;
 uint32_t lineAt=0;
public:
 static bool narrow(uint8_t mask){
  uint8_t inner=(mask>>1)&7;
  return inner!=0&&inner!=5&&inner!=7;
 }
 static bool clearMarker(uint8_t mask){return !(mask&17)&&narrow(mask);}
 void reset(){seen=false;direction=0;lineAt=0;}
 Wheels tick(uint32_t now,uint8_t mask){
  uint8_t inner=(mask>>1)&7;
  if(narrow(mask)){
   // Centroid of A4/A3/A2; outer sensors do not choose the steering side.
   int8_t left=(inner&4)?1:0,center=(inner&2)?1:0,right=(inner&1)?1:0;
   int16_t correction=30*(right-left)/(left+center+right);
   direction=correction<0?-1:correction>0?1:0;lineAt=now;seen=true;
   return Wheels(45+(correction<0?correction:0),45-(correction>0?correction:0));
  }
  if(inner==5)return Wheels(); // Split observation has no unique steering target.
  if(!seen)return Wheels(45,45); // Leave the initial patch; mission bounds duration.
  if(inner==0&&now-lineAt<120){
   return Wheels(direction<0?15:45,direction>0?15:45);
  }
  return Wheels(); // Expired loss or a new wide patch: no blind continued drive.
 }
};
} // namespace race_motion
