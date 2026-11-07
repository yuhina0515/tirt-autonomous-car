#pragma once
#include "motion.h"

namespace layered {
enum class Event:uint8_t { Wide,Split };
enum class Action:uint8_t { Straight,Left,Right,Lift,Finish };
// Each observed landmark must be physically verified for the configured route.
// min/max are plausibility windows, not a substitute for event detection.
struct Step { Event trigger; Action action; uint32_t minMs,maxMs; };
enum class Phase:uint8_t { Cruise,Turning,Crossing,Waiting,Exiting,Finished,Fault };
class Mission {
    const Step *route;uint8_t count;
    bool armed=false,clearPending=false,eventPending=false,departed=false,confirm=false;
    Event pending=Event::Wide;
    uint32_t at=0,stepAt=0,clearAt=0,eventAt=0,confirmAt=0;
    void fail(){phase=Phase::Fault;}
    void advance(uint32_t now){++index;stepAt=now;phase=Phase::Cruise;confirm=false;}
public:
    Phase phase=Phase::Cruise;uint8_t index=0;int8_t direction=0;
    Mission(const Step *r=nullptr,uint8_t n=0):route(r),count(n){}
    bool valid()const{
        if(count&&!route)return false;
        for(uint8_t i=0;i<count;++i)if(uint8_t(route[i].trigger)>1||uint8_t(route[i].action)>4||
            route[i].maxMs==0||route[i].minMs>=route[i].maxMs||route[i].maxMs>360000||
            (route[i].action==Action::Finish&&i!=count-1))return false;
        return true;
    }
    void reset(uint32_t now){phase=Phase::Cruise;index=0;direction=0;stepAt=now;
        armed=clearPending=eventPending=departed=confirm=false;}
    Demand tick(uint32_t now,const Observation &o,const Config &c,bool liftReady){
        if(phase==Phase::Fault||phase==Phase::Finished)return Demand(Mode::Hold);
        if(phase==Phase::Waiting){
            if(now-at>=c.liftWaitMs+5000){fail();return Demand(Mode::Hold);}
            if(now-at>=c.liftWaitMs&&(!c.requireLiftReady||liftReady)){
                phase=Phase::Exiting;at=now;confirm=false;
            }
            return Demand(Mode::Hold);
        }
        if(phase==Phase::Turning||phase==Phase::Crossing||phase==Phase::Exiting){
            const uint32_t limit=phase==Phase::Exiting?1500:800;
            if(now-at>=limit){fail();return Demand(Mode::Hold);}
            // A wide trigger is not proof that the requested branch was taken.
            // Require chosen-side narrow observation before central return.
            if(phase==Phase::Turning&&o.trusted&&
                (direction<0?o.position<-250:o.position>250))departed=true;
            bool returned=(phase!=Phase::Turning||departed)&&o.centered&&now-at>=30;
            if(returned){if(!confirm){confirm=true;confirmAt=now;}
                if(now-confirmAt>=30){advance(now);return Demand();}}
            else confirm=false;
            return phase==Phase::Turning?Demand(Mode::Turn,direction):Demand(Mode::Straight,0,45);
        }
        // No route is deliberately line practice, not an invented official lap.
        if(!count)return Demand();
        if(index>=count){fail();return Demand(Mode::Hold);}
        const Step &step=route[index];
        if(now-stepAt>=step.maxMs){fail();return Demand(Mode::Hold);}
        if(o.trusted){
            eventPending=false;
            if(!clearPending){clearPending=true;clearAt=now;}
            if(now-clearAt>=100)armed=true;
        }else clearPending=false;
        if(armed&&(o.wide||o.split)){
            Event e=o.wide?Event::Wide:Event::Split;
            if(!eventPending||pending!=e){eventPending=true;pending=e;eventAt=now;}
            if(now-eventAt>=30){
                armed=false;eventPending=false;clearPending=false;
                if(e!=step.trigger||now-stepAt<step.minMs){fail();return Demand(Mode::Hold);}
                at=now;confirm=false;departed=false;
                switch(step.action){
                    case Action::Left:direction=-1;phase=Phase::Turning;break;
                    case Action::Right:direction=1;phase=Phase::Turning;break;
                    case Action::Straight:phase=Phase::Crossing;break;
                    case Action::Lift:phase=Phase::Waiting;return Demand(Mode::Hold);
                    case Action::Finish:phase=Phase::Finished;return Demand(Mode::Hold);
                }
                return phase==Phase::Turning?Demand(Mode::Turn,direction):Demand(Mode::Straight,0,45);
            }
        }else eventPending=false;
        return Demand();
    }
};
} // namespace layered
