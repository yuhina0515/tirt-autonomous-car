#pragma once
#include <stdint.h>
#define TIRT_CONTINUOUS_CANDIDATE 1
#define TIRT_MISSION_PREFIX 1

// Experimental ADC/time-only core. Endpoints are provisional, not measured.
// No pose, route station, gate, mechanism feedback, heap or vendor dependency.
namespace tirt {
struct Settings {
    static constexpr int16_t base = 180, curveReduction = 30;
    static constexpr int16_t kp = 60, kd = 3, correction = 80, ceiling = 230;
    static constexpr uint16_t lineAdc = 35, backgroundAdc = 500;
    static constexpr uint32_t predictionMs = 60, lossMs = 800, broadMs = 300;
    static constexpr uint32_t liftWaitMs = 31000, maximumLapMs = 360000;
    // Zero deliberately leaves lift unarmed until an observable mission prefix
    // has been established. Broad paint alone cannot identify a lift.
    static constexpr uint8_t missionWordCount = 0;
};
enum class Motion : uint8_t { Follow, Search, Gap };
enum class Lift : uint8_t { Before, Waiting, Exiting, Done };
enum class Fault : uint8_t { None, SignalDeadline, BroadDeadline, TickGap, RunDeadline, MissionAmbiguous };
struct Wheels {
    int16_t left, right;
    Wheels(int16_t l=0,int16_t r=0):left(l),right(r){}
};
struct State {
    uint8_t f=0;
    Fault fault=Fault::None;
    Motion motion=Motion::Follow;
    Lift lift=Lift::Before;
    bool lapDone=false,recovery=false,probe=false,splitActive=false;
    int8_t direction=0,captureSide=0;
    int16_t straightPwm=0,position=0,confidence=0;
    uint16_t events=0;
    uint32_t uncertainMs=0;
    uint8_t missionPhase=0;
    bool markerArmed=false;
    uint16_t eventSerial=0;
    uint8_t eventCode=0,missionCandidates=0,missionStep=0;
    bool missionAmbiguous=false;
};

class Controller {
public:
    const State &state()const{return s;}
    Wheels output()const{return wheels;}
    void reset(){s=State{};wheels=Wheels{};started=false;initialized=false;lost=false;broad=false;uncertain=false;validPending=false;eventPending=false;eventLatched=false;narrowPending=false;derivative=0;lastRaw=0;lastCorrection=0;turnMean=0;turnCandidate=turnLatched=lastToken=0;turnPending=turnClear=lossExpanded=false;cornerActive=cornerEpisode=cornerHintPending=exitConfirmed=false;cornerHint=0;for(uint8_t h=0;h<4;++h)phases[h]=h<Settings::missionWordCount?1:0;missionStatus();}
    bool blue()const{return s.fault!=Fault::None||s.lift==Lift::Waiting||s.motion!=Motion::Follow;}
    Wheels tick(uint32_t now,const uint16_t adc[5]) {
        uint32_t dt=started?now-lastAt:5;
        if(!started){started=true;beganAt=now;}
        lastAt=now;
        s.f=(adc[1]<70?8:0)|(adc[2]<70?4:0)|(adc[3]<70?2:0);
        if(dt>50)fail(Fault::TickGap);
        if(now-beganAt>=Settings::maximumLapMs)fail(Fault::RunDeadline);
        if(s.fault!=Fault::None)return stop();
        if(dt==0)return wheels;
        int16_t w[5];
        for(uint8_t i=0;i<5;++i)w[i]=bound((int32_t(Settings::backgroundAdc)-adc[i])*1000/(Settings::backgroundAdc-Settings::lineAdc),0,1000);
        const int16_t fullThreshold=eventPending?500:750;
        const bool full=w[0]>fullThreshold&&w[1]>fullThreshold&&w[2]>fullThreshold&&w[3]>fullThreshold&&w[4]>fullThreshold;
        const bool wide=w[1]>650&&w[2]>650&&w[3]>650;
        const bool narrow=w[2]>600&&w[1]<350&&w[3]<350;
        const bool split=w[1]>600&&w[3]>600&&w[2]<350;
        s.splitActive=split;
        observeEvent(now,full,narrow);
        if(s.fault!=Fault::None)return stop();
        if(s.lift==Lift::Waiting){
            if(now-liftAt>=Settings::liftWaitMs){s.lift=Lift::Exiting;exitAt=now;}
            return stop();
        }
        if(s.lift==Lift::Exiting){
            if(now-exitAt>=1500){fail(Fault::SignalDeadline);return stop();}
            if(narrow){if(!exitConfirmed){exitConfirmed=true;exitLineAt=now;}if(now-exitLineAt>=100){s.lift=Lift::Done;s.missionPhase=4;}}
            else exitConfirmed=false;
        }
        int32_t sum=0,numerator=0;
        // Inner three supply normal tracking. Outer sensors extend capture only
        // as the inner peak fades, rather than turning a distant branch into error.
        int16_t peak=w[1]>w[2]?w[1]:w[2];if(w[3]>peak)peak=w[3];
        for(uint8_t i=1;i<4;++i){int32_t q=int32_t(w[i])*w[i]/1000;sum+=q;numerator+=int32_t(int8_t(i)-2)*1000*q;}
        if(peak<650){
            const int32_t gain=650-peak;
            int32_t left=int32_t(w[0])*w[0]/1000*gain/650;
            int32_t right=int32_t(w[4])*w[4]/1000*gain/650;
            sum+=left+right;numerator+=2000*(right-left);
        }
        s.confidence=peak;
        const bool visible=sum>=160&&!split;
        const int16_t raw=visible?bound(numerator/sum,-2000,2000):lastRaw;
        if(visible&&!wide){s.position=raw;observeTurn(now,raw,dt);if(s.fault!=Fault::None)return stop();}
        const int8_t hint=w[0]>750&&w[1]>650&&w[2]>600&&w[3]<350&&w[4]<350?-1:
                          w[4]>750&&w[3]>650&&w[2]>600&&w[1]<350&&w[0]<350?1:0;
        // After the lift, preview slows translation before binary side bits
        // mature. It never supplies confidence or a mission/direction token.
        const bool preview=s.lift==Lift::Done&&w[2]>600&&
            ((w[0]>400&&w[1]>350&&w[3]<350&&w[4]<350)||
             (w[4]>400&&w[3]>350&&w[1]<350&&w[0]<350));
        if(s.lift==Lift::Done&&hint){
            if(!cornerHintPending||cornerHint!=hint){cornerHintPending=true;cornerHint=hint;cornerHintAt=now;}
            if(!cornerEpisode&&now-cornerHintAt>=10&&s.direction==hint){cornerActive=cornerEpisode=true;cornerAt=now;}
        }else cornerHintPending=false;
        const bool confident=visible&&!wide&&peak>=600&&(!cornerEpisode||narrow);
        if(!confident){
            if(!uncertain){uncertain=true;uncertainAt=now;}
            validPending=false;
        }else if(uncertain){
            if(!validPending){validPending=true;validAt=now;}
            if(now-validAt>=20){uncertain=false;validPending=false;cornerEpisode=cornerActive=false;}
        }
        s.uncertainMs=uncertain?now-uncertainAt:0;
        if(s.uncertainMs>=Settings::lossMs){fail(Fault::SignalDeadline);return stop();}
        s.recovery=cornerEpisode;
        if(cornerActive){
            // Stop the open-loop pivot on the first central/overshoot evidence.
            // The shared timer is still renewed only by20ms of narrow line.
            // Continuing to pivot during confirmation can rotate past it.
            const bool crossed=narrow||(visible&&!wide&&peak>=600&&
                (s.direction<0?raw>150:raw<-150));
            if(now-cornerAt>=650||crossed)cornerActive=false;
            else{initialized=false;derivative=0;s.motion=Motion::Search;return drive(s.direction<0?-100:180,s.direction<0?180:-100,dt,true);}
        }
        if(wide){
            turnPending=turnClear=false;
            if(!broad){broad=true;broadAt=now;}
            if(now-broadAt>=Settings::broadMs){fail(Fault::BroadDeadline);return stop();}
            derivative=0;initialized=false;
            const int16_t u=s.uncertainMs<Settings::predictionMs?lastCorrection:0;
            return drive(Settings::base+u,Settings::base-u,dt);
        }
        broad=false;
        if(!visible){
            turnPending=turnClear=false;
            if(!lost){lost=true;lostAt=now;lossExpanded=false;}
            if(!lossExpanded&&now-lostAt>=25){
                lossExpanded=true;
                for(uint8_t h=0;h<Settings::missionWordCount;++h)phases[h]|=phases[h]<<1;
                missionStatus();
            }
            s.motion=Motion::Search;
            initialized=false;derivative=0;
            if(s.uncertainMs<Settings::predictionMs)return drive(Settings::base+lastCorrection,Settings::base-lastCorrection,dt);
            if(s.direction==0)return drive(70,70,dt);
            const int16_t turn=s.direction;
            return drive(turn>0?230:100,turn>0?100:230,dt);
        }
        lost=false;s.motion=Motion::Follow;
        if(!initialized){lastRaw=raw;derivative=0;initialized=true;}
        int32_t instantaneous=int32_t(raw-lastRaw)*1000/int32_t(dt);
        derivative+=(instantaneous-derivative)*int32_t(dt)/int32_t(25+dt);lastRaw=raw;
        if(raw>150)s.direction=1;else if(raw<-150)s.direction=-1;
        int16_t u=bound((int32_t(Settings::kp)*raw+Settings::kd*derivative)/1000,-Settings::correction,Settings::correction);
        int32_t bend=absolute(raw)+3*absolute(derivative)/100;
        int16_t base=Settings::base-Settings::curveReduction*bound(bend,0,1000)/1000;
        if(preview&&base>100)base=100;
        if(cornerEpisode&&base>85)base=85;
        if(s.lift==Lift::Exiting)base=100;
        lastCorrection=u;s.straightPwm=base;
        return drive(base+u,base-u,dt,cornerEpisode);
    }
private:
    State s;
    Wheels wheels;
    bool started=false,initialized=false,lost=false,broad=false,uncertain=false,validPending=false,eventPending=false,eventLatched=false,narrowPending=false;
    uint32_t beganAt=0,lastAt=0,lostAt=0,broadAt=0,eventAt=0,narrowAt=0,liftAt=0,exitAt=0;
    uint32_t uncertainAt=0,validAt=0;
    int32_t derivative=0;
    int16_t lastRaw=0,lastCorrection=0;
    int32_t turnMean=0;
    int8_t turnCandidate=0,turnLatched=0;
    uint8_t lastToken=0;
    bool turnPending=false,turnClear=false,lossExpanded=false;
    uint32_t turnAt=0,turnClearAt=0,phases[4]={0,0,0,0};
    bool cornerActive=false,cornerEpisode=false,cornerHintPending=false,exitConfirmed=false;
    int8_t cornerHint=0;
    uint32_t cornerAt=0,cornerHintAt=0,exitLineAt=0;
    static uint8_t wordAt(uint8_t hypothesis,uint8_t at){
        // MISSION_TABLE_BEGIN
        (void)hypothesis;(void)at;return 0;
        // MISSION_TABLE_END
    }
    static int32_t absolute(int32_t x){return x<0?-x:x;}
    static int16_t bound(int32_t x,int16_t lo,int16_t hi){return x<lo?lo:x>hi?hi:int16_t(x);}
    void fail(Fault f){if(s.fault==Fault::None)s.fault=f;}
    Wheels stop(){wheels=Wheels{};return wheels;}
    Wheels drive(int16_t left,int16_t right,uint32_t dt,bool rapid=false){
        const int16_t slew=bound(int32_t(dt)*(rapid?4:2),1,100);
        left=bound(left,-Settings::ceiling,Settings::ceiling);right=bound(right,-Settings::ceiling,Settings::ceiling);
        wheels.left+=bound(left-wheels.left,-slew,slew);wheels.right+=bound(right-wheels.right,-slew,slew);
        return wheels;
    }
    void observeEvent(uint32_t now,bool full,bool narrow){
        if(full&&!eventLatched){if(!eventPending){eventPending=true;eventAt=now;}}
        else if(!full&&eventPending){
            if(now-eventAt>=25){
                ++s.events;eventLatched=true;
                emit(1,now);turnLatched=turnCandidate=0;turnPending=false;
            }
            eventPending=false;
        }
        if(narrow){if(!narrowPending){narrowPending=true;narrowAt=now;}if(now-narrowAt>=80)eventLatched=false;}
        else narrowPending=false;
    }
    void observeTurn(uint32_t now,int16_t raw,uint32_t dt){
        turnMean+=(int32_t(raw)-turnMean)*int32_t(dt)/int32_t(100+dt);
        if(absolute(turnMean)<120){
            if(!turnClear){turnClear=true;turnClearAt=now;}
            if(now-turnClearAt>=300)turnLatched=0;
        }else turnClear=false;
        const int8_t sign=turnMean<-250?-1:turnMean>250?1:0;
        if(sign&&sign!=turnLatched){
            if(!turnPending||turnCandidate!=sign){turnPending=true;turnCandidate=sign;turnAt=now;}
            if(now-turnAt>=150){
                const uint8_t token=sign<0?2:3;
                if(lastToken!=token)emit(token,now);
                turnLatched=sign;turnPending=false;
            }
        }else turnPending=false;
    }
    void missionStatus(){
        s.missionCandidates=0;s.missionStep=31;s.markerArmed=false;
        bool any=false,allLift=true;
        uint16_t count=0;
        for(uint8_t h=0;h<Settings::missionWordCount;++h){
            if(phases[h])s.missionCandidates|=uint8_t(1)<<h;
            for(uint8_t p=0;p<31;++p)if(phases[h]&(uint32_t(1)<<p)){
                any=true;++count;if(p<s.missionStep)s.missionStep=p;
                if(wordAt(h,p)!=4)allLift=false;
            }
        }
        if(!any)s.missionStep=0;
        s.missionAmbiguous=count>1;
        if(s.lift==Lift::Before){s.markerArmed=any&&allLift;s.missionPhase=Settings::missionWordCount?(any?1:5):0;}
    }
    void emit(uint8_t code,uint32_t now){
        lastToken=code;s.eventCode=code;++s.eventSerial;
        if(s.lift!=Lift::Before||Settings::missionWordCount==0)return;
        bool lift=false,ordinary=false;
        for(uint8_t h=0;h<Settings::missionWordCount;++h){
            uint32_t next=0;
            for(uint8_t p=0;p<30;++p)if(phases[h]&(uint32_t(1)<<p)){
                const uint8_t expected=wordAt(h,p);
                if(expected==code||(expected==4&&code==1)){
                    next|=uint32_t(1)<<(p+1);
                    if(expected==4)lift=true;else ordinary=true;
                }
            }
            phases[h]=next;
        }
        missionStatus();
        if(lift&&ordinary){s.missionAmbiguous=true;fail(Fault::MissionAmbiguous);}
        else if(lift){
            s.markerArmed=true;s.lift=Lift::Waiting;liftAt=now;s.missionPhase=3;
            uncertain=lost=broad=validPending=false;initialized=false;
            derivative=0;lastCorrection=0;s.uncertainMs=0;
        }
    }
};
} // namespace tirt
