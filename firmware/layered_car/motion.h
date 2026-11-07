#pragma once
#include <stdint.h>

namespace layered {
struct Wheels { int16_t left, right; Wheels(int16_t l=0,int16_t r=0):left(l),right(r){} };
struct Config {
    // Provisional endpoints, not a claim of field calibration; A5 -> A1.
    uint16_t line[5] = {35,35,35,35,35};
    uint16_t background[5] = {500,500,500,500,500};
    int16_t base=140, ceiling=180, kp=60, kd=1;
    uint32_t uncertaintyMs=800, runMs=360000, liftWaitMs=23350;
    bool requireLiftReady=false;
    static Config field() { return Config(); }
    static Config race() { Config c; c.liftWaitMs=28850; c.requireLiftReady=true; return c; }
    bool valid() const {
        if(base<1||base>ceiling||ceiling>230||kp<0||kp>150||kd<0||kd>10||
           uncertaintyMs<60||uncertaintyMs>2000||runMs==0||runMs>360000||
           liftWaitMs==0||liftWaitMs>60000) return false;
        for(uint8_t i=0;i<5;++i) {
            int32_t span=int32_t(background[i])-line[i];
            if(line[i]>1023||background[i]>1023||(span<100&&span>-100))return false;
        }
        return true;
    }
};
inline int16_t bound(int32_t v,int16_t lo,int16_t hi){return v<lo?lo:v>hi?hi:int16_t(v);}
struct Observation {
    int16_t position=0;
    bool trusted=false,centered=false,wide=false,split=false;
};
class Sensing {
    int16_t filtered[5]={0,0,0,0,0}; bool initialized=false;
public:
    void reset(){initialized=false;}
    Observation read(const uint16_t adc[5],const Config &c){
        Observation o; int32_t sum=0,weighted=0; int16_t peak=0,low=1000;
        for(uint8_t i=0;i<5;++i){
            int16_t n=bound((int32_t(adc[i])-c.background[i])*1000/
                (int32_t(c.line[i])-c.background[i]),0,1000);
            filtered[i]=initialized?(filtered[i]+3L*n)/4:n;
            if(i>=1&&i<=3){
                int32_t w=int32_t(filtered[i])*filtered[i]/1000;
                sum+=w;weighted+=w*(int8_t(i)-2)*1000L;
                if(filtered[i]>peak)peak=filtered[i];
                if(filtered[i]<low)low=filtered[i];
            }
        }
        initialized=true;
        o.wide=filtered[1]>=650&&filtered[2]>=650&&filtered[3]>=650;
        o.split=filtered[1]>=600&&filtered[3]>=600&&filtered[2]<350;
        o.trusted=peak>=600&&peak-low>=250&&!o.wide&&!o.split&&sum>0;
        o.centered=o.trusted&&filtered[2]>=600&&filtered[1]<350&&filtered[3]<350;
        if(sum)o.position=bound(weighted/sum,-1000,1000);
        return o;
    }
};
enum class Mode:uint8_t { Follow,Turn,Straight,Hold };
struct Demand { Mode mode;int8_t direction;int16_t speed;
    Demand(Mode m=Mode::Follow,int8_t d=0,int16_t v=45):mode(m),direction(d),speed(v){} };
class Motion {
    bool uncertain=false,recovering=false,history=false;
    uint32_t uncertainAt=0,recoverAt=0;
    int16_t previous=0,derivative=0,correction=0;
    Wheels wheels;
public:
    bool fault=false;
    void reset(){uncertain=recovering=history=fault=false;previous=derivative=correction=0;wheels=Wheels();}
    Wheels tick(uint32_t now,uint32_t dt,const Observation &o,const Demand &d,const Config &c){
        if(fault)return wheels=Wheels();
        if(d.mode!=Mode::Follow){
            uncertain=recovering=history=false;derivative=0;
            if(d.mode==Mode::Hold)return wheels=Wheels();
            if(d.mode==Mode::Turn)return wheels=Wheels(d.direction<0?-65:85,d.direction<0?85:-65);
            return wheels=Wheels(bound(d.speed,0,c.ceiling),bound(d.speed,0,c.ceiling));
        }
        // Expiry wins over a confirmation first observed at/after the deadline.
        if(uncertain&&now-uncertainAt>=c.uncertaintyMs){fault=true;return wheels=Wheels();}
        if(!o.trusted){
            if(!uncertain){uncertain=true;uncertainAt=now;}
            recovering=false;history=false;derivative=0;
        }else if(uncertain){
            if(!recovering){recovering=true;recoverAt=now;}
            if(now-recoverAt>=30){uncertain=false;recovering=false;}
        }
        if(uncertain){
            if(now-uncertainAt>=c.uncertaintyMs){fault=true;return wheels=Wheels();}
            // Short bounded prediction; stop while waiting for confirmed line.
            if(now-uncertainAt<60)return wheels=Wheels(bound(40+correction/4,0,c.ceiling),bound(40-correction/4,0,c.ceiling));
            return wheels=Wheels();
        }
        if(dt==0)return wheels;
        int16_t slope=history?bound((int32_t(o.position)-previous)*1000/int32_t(dt),-20000,20000):0;
        derivative=(3L*derivative+slope)/4; previous=o.position;history=true;
        correction=bound((int32_t(c.kp)*o.position+int32_t(c.kd)*derivative)/1000,-110,110);
        int16_t magnitude=o.position<0?-o.position:o.position;
        int16_t base=c.base-int32_t(c.base/3)*magnitude/1000;
        Wheels target(bound(base+correction,0,c.ceiling),bound(base-correction,0,c.ceiling));
        int16_t rise=bound(int32_t(dt)*600/1000,1,c.ceiling);
        wheels.left=target.left>wheels.left?bound(target.left,0,wheels.left+rise):target.left;
        wheels.right=target.right>wheels.right?bound(target.right,0,wheels.right+rise):target.right;
        return wheels;
    }
};
} // namespace layered
