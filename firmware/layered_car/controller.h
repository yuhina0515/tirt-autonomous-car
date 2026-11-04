#pragma once
#include "mission.h"
namespace layered {
enum class Fault:uint8_t { None,Configuration,Timing,Signal,Mission,RunLimit,ManualStop };
class Controller {
    Config config;Sensing sensing;Motion motion;Mission mission;
    bool started=false;uint32_t began=0,last=0;
public:
    Fault fault=Fault::None;
    Controller(Config c=Config::field(),const Step *route=nullptr,uint8_t n=0):config(c),mission(route,n){}
    Phase phase()const{return mission.phase;}
    uint8_t step()const{return mission.index;}
    Wheels tick(uint32_t now,const uint16_t adc[5],bool stop=false,bool liftReady=false){
        if(stop)fault=Fault::ManualStop;
        if(fault!=Fault::None)return Wheels();
        if(!config.valid()||!mission.valid()){fault=Fault::Configuration;return Wheels();}
        uint32_t dt=started?now-last:5;
        if(!started){started=true;began=now;mission.reset(now);}
        last=now;
        if(dt>50){fault=Fault::Timing;return Wheels();}
        if(now-began>=config.runMs){fault=Fault::RunLimit;return Wheels();}
        Observation o=sensing.read(adc,config);
        Demand d=mission.tick(now,o,config,liftReady);
        if(mission.phase==Phase::Fault){fault=Fault::Mission;return Wheels();}
        Wheels w=motion.tick(now,dt,o,d,config);
        if(motion.fault){fault=Fault::Signal;return Wheels();}
        return Wheels(bound(w.left,-config.ceiling,config.ceiling),bound(w.right,-config.ceiling,config.ceiling));
    }
};
} // namespace layered
