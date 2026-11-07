#include "../firmware/layered_car/controller.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "layered_arduino/Arduino.h"
static uint32_t mockTime=0;static bool buttonLow=true;static int pwm[20]={0};
void pinMode(uint8_t,uint8_t){}
void digitalWrite(uint8_t,uint8_t){}
void analogWrite(uint8_t pin,int value){pwm[pin]=value;}
int digitalRead(uint8_t){return buttonLow?LOW:HIGH;}
int analogRead(uint8_t pin){return pin==A3?35:500;}
uint32_t millis(){return mockTime;}
#include "../firmware/layered_car/layered_car.ino"
using namespace layered;
static const uint16_t center[]={500,500,35,500,500};
static const uint16_t left[]={500,130,35,500,500};
static const uint16_t right[]={500,500,35,130,500};
static const uint16_t wide[]={35,35,35,35,35};
static const uint16_t split[]={500,35,500,35,500};
static const uint16_t absent[]={500,500,500,500,500};
static const uint16_t outer[]={35,500,500,500,35};
static Observation good(){Observation o;o.trusted=o.centered=true;return o;}
static Observation broad(){Observation o;o.wide=true;return o;}
static void feed(Controller &c,uint32_t a,uint32_t b,const uint16_t *adc){
    for(uint32_t t=a;t<=b;t+=5)c.tick(t,adc);
}
void pd(){Controller l,r;feed(l,0,200,left);feed(r,0,200,right);
    Wheels a=l.tick(205,left),b=r.tick(205,right);
    assert(a.left<a.right&&b.left>b.right&&a.left==b.right&&a.right==b.left);}
void dynamic_pd(){Controller l,r;feed(l,0,100,center);feed(r,0,100,center);
    for(uint32_t t=105;t<=400;t+=5){
        Wheels a=l.tick(t,t<200?left:right),b=r.tick(t,t<200?right:left);
        assert(a.left==b.right&&a.right==b.left);
    }}
void adapter(){setup();for(mockTime=0;mockTime<=100;mockTime+=5)loop();
    assert(!running&&pwm[5]==0&&pwm[6]==0); // held at boot cannot start
    buttonLow=false;for(;mockTime<=140;mockTime+=5)loop();
    buttonLow=true;for(;mockTime<=230;mockTime+=5)loop();
    assert(running&&!stopped&&pwm[5]>0&&pwm[6]>0);
    buttonLow=false;for(;mockTime<=270;mockTime+=5)loop();
    buttonLow=true;for(;mockTime<=310;mockTime+=5)loop();
    assert(stopped&&pwm[5]==0&&pwm[6]==0);
    buttonLow=false;for(;mockTime<=350;mockTime+=5)loop();
    buttonLow=true;for(;mockTime<=400;mockTime+=5)loop();
    assert(stopped&&pwm[5]==0&&pwm[6]==0);
}
void partial(){const uint16_t gray[]={500,500,200,500,500};Controller c;feed(c,0,200,gray);
    assert(c.fault==Fault::None&&c.tick(205,gray).left>0);}
void bounded(){Config cfg;cfg.base=cfg.ceiling=230;Controller c(cfg);feed(c,0,500,right);
    Wheels w=c.tick(505,right);assert(w.left<=230&&w.right<=230&&w.left>=0&&w.right>=0);}
void blips(){Controller c;feed(c,0,100,center);
    for(uint32_t t=105;t<=1005;t+=5)c.tick(t,t%100==0?center:absent);
    assert(c.fault==Fault::Signal&&c.tick(1010,center).left==0);}
void uncertainty(){const uint16_t *inputs[]={wide,split,outer,absent};
    for(const uint16_t *adc:inputs){Controller c;feed(c,0,900,adc);assert(c.fault==Fault::Signal);}}
void recover(){Controller c;feed(c,0,100,center);feed(c,105,145,absent);feed(c,150,300,center);
    assert(c.fault==Fault::None&&c.tick(305,center).left>0);}
void timing(){Controller c;c.tick(0,center);assert(c.tick(51,center).left==0&&c.fault==Fault::Timing);}
void rollover(){Controller c;for(uint32_t i=0;i<=200;i+=5)c.tick(0xfffffff0U+i,center);
    assert(c.fault==Fault::None);}
void stop(){Controller c;feed(c,0,100,center);assert(c.tick(105,center,true).left==0);
    assert(c.tick(110,center).right==0&&c.fault==Fault::ManualStop);}
void invalid(){Config cfg;cfg.line[2]=cfg.background[2];Controller c(cfg);
    assert(c.tick(0,center).left==0&&c.fault==Fault::Configuration);
    Step s[]={ {Event::Wide,Action::Lift,200,100} };Controller d(Config::field(),s,1);
    assert(d.tick(0,center).left==0&&d.fault==Fault::Configuration);}
static Demand enter(Mission &m,const Config &c,Action action){
    (void)action;m.reset(0);for(uint32_t t=0;t<=100;t+=5)m.tick(t,good(),c,false);
    Demand d;for(uint32_t t=105;t<=135;t+=5)d=m.tick(t,broad(),c,false);return d;
}
void directions(){for(int sign=-1;sign<=1;sign+=2){Step s[]={ {Event::Wide,sign<0?Action::Left:Action::Right,0,5000},{Event::Wide,Action::Finish,0,5000} };
    Mission m(s,2);Demand d=enter(m,Config::field(),s[0].action);
    assert(m.phase==Phase::Turning&&d.mode==Mode::Turn&&d.direction==sign);
    for(uint32_t t=140;t<=220;t+=5)m.tick(t,good(),Config::field(),false);
    assert(m.phase==Phase::Turning); // original centered branch is not completion
    Observation chosen=good();chosen.centered=false;chosen.position=sign*700;
    m.tick(225,chosen,Config::field(),false);
    for(uint32_t t=230;t<=270;t+=5)m.tick(t,good(),Config::field(),false);
    assert(m.index==1&&m.phase==Phase::Cruise);}}
void late_return(){Motion m;Config c;Observation none;
    m.tick(0,5,none,Demand(),c);m.tick(775,5,good(),Demand(),c);
    assert(m.tick(805,30,good(),Demand(),c).left==0&&m.fault);}
void derivative_sign(){Motion m;Config c;c.kp=0;c.kd=5;
    Observation o=good();for(uint32_t t=0;t<=400;t+=5)m.tick(t,5,o,Demand(),c);
    o.position=-100;Wheels w=m.tick(405,5,o,Demand(),c);assert(w.left<w.right);}
void ready_boundary(){Step s[]={ {Event::Wide,Action::Lift,0,5000} };Config c=Config::race();
    for(int delta=-1;delta<=1;++delta){Mission m(s,1);enter(m,c,Action::Lift);
        m.tick(135+c.liftWaitMs+5000+delta,good(),c,true);
        assert(m.phase==(delta<0?Phase::Exiting:Phase::Fault));}}
void invalid_routes(){Config c;Step bad[]={ {Event(3),Action::Left,0,100},
    {Event::Wide,Action(8),0,100},{Event::Wide,Action::Left,0,360001} };
    for(const Step &s:bad){Controller x(c,&s,1);assert(x.tick(0,center).left==0&&x.fault==Fault::Configuration);}
    Controller n(c,nullptr,1);assert(n.tick(0,center).left==0&&n.fault==Fault::Configuration);
    Step early[]={ {Event::Wide,Action::Finish,0,100},{Event::Wide,Action::Lift,0,100} };
    Controller x(c,early,2);assert(x.tick(0,center).left==0&&x.fault==Fault::Configuration);}
void mismatch(){Step s[]={ {Event::Split,Action::Right,0,5000} };Mission m(s,1);
    enter(m,Config::field(),Action::Right);assert(m.phase==Phase::Fault);}
void no_route(){Mission m;Config c;m.reset(0);for(uint32_t t=0;t<=200;t+=5)m.tick(t,broad(),c,false);
    assert(m.phase==Phase::Cruise&&m.index==0);}
void profiles(){assert(Config::field().liftWaitMs==23350);assert(Config::race().liftWaitMs==28850);
    for(int profile=0;profile<2;++profile){Config c=profile?Config::race():Config::field();
        Step s[]={ {Event::Wide,Action::Lift,0,5000},{Event::Wide,Action::Finish,0,5000} };Mission m(s,2);enter(m,c,Action::Lift);
        uint32_t end=135+c.liftWaitMs;
        assert(m.tick(end-1,good(),c,false).mode==Mode::Hold&&m.phase==Phase::Waiting);
        m.tick(end,good(),c,false);
        assert(m.phase==(profile?Phase::Waiting:Phase::Exiting));
        if(profile)m.tick(end+5,good(),c,true);
        assert(m.phase==Phase::Exiting);
        for(uint32_t t=end+10;t<=end+150;t+=5)m.tick(t,good(),c,true);
        assert(m.index==1&&m.phase==Phase::Cruise);
    }}
void lift_timeout(){Config c=Config::race();Step s[]={ {Event::Wide,Action::Lift,0,5000} };
    Mission m(s,1);enter(m,c,Action::Lift);m.tick(135+c.liftWaitMs+5000,good(),c,false);
    assert(m.phase==Phase::Fault);}
void exit_timeout(){Config c=Config::field();Step s[]={ {Event::Wide,Action::Lift,0,5000} };
    Mission m(s,1);enter(m,c,Action::Lift);uint32_t end=135+c.liftWaitMs;
    m.tick(end,broad(),c,false);m.tick(end+1500,broad(),c,false);assert(m.phase==Phase::Fault);}
void finish(){Step s[]={ {Event::Wide,Action::Finish,0,5000} };Mission m(s,1);
    Demand d=enter(m,Config::field(),Action::Finish);assert(m.phase==Phase::Finished&&d.mode==Mode::Hold);
    assert(m.tick(50000,good(),Config::field(),false).mode==Mode::Hold&&m.phase==Phase::Finished);}
void rearm(){Step s[]={ {Event::Wide,Action::Straight,0,5000},{Event::Wide,Action::Finish,0,5000} };
    Mission m(s,2);Config c;enter(m,c,Action::Straight);
    for(uint32_t t=140;t<=200;t+=5)m.tick(t,good(),c,false);
    assert(m.index==1);for(uint32_t t=205;t<=250;t+=5)m.tick(t,broad(),c,false);
    assert(m.phase==Phase::Cruise); // no 100ms trusted clearance since first event
    for(uint32_t t=255;t<=355;t+=5)m.tick(t,good(),c,false);
    for(uint32_t t=360;t<=390;t+=5)m.tick(t,broad(),c,false);
    assert(m.phase==Phase::Finished);}
void windows(){Step s[]={ {Event::Wide,Action::Lift,500,1000} };Config c;Mission early(s,1);
    enter(early,c,Action::Lift);assert(early.phase==Phase::Fault);
    Mission late(s,1);late.reset(0);late.tick(1000,good(),c,false);assert(late.phase==Phase::Fault);}
void turn_timeout(){Step s[]={ {Event::Wide,Action::Left,0,5000} };Mission m(s,1);Config c;
    enter(m,c,Action::Left);m.tick(935,broad(),c,false);assert(m.phase==Phase::Fault);}
void six_minutes(){Config cfg;cfg.runMs=200;Controller c(cfg);feed(c,0,200,center);
    assert(c.fault==Fault::RunLimit);assert(Config::field().runMs==360000);}
void complete_path(){Step s[]={ {Event::Wide,Action::Lift,0,1000},{Event::Wide,Action::Finish,0,5000} };
    Config cfg;cfg.liftWaitMs=200;Controller c(cfg,s,2);
    feed(c,0,150,center);feed(c,155,215,wide);assert(c.phase()==Phase::Waiting);
    feed(c,220,425,wide);assert(c.phase()==Phase::Exiting);
    feed(c,430,650,center);assert(c.phase()==Phase::Cruise&&c.step()==1&&c.fault==Fault::None);
    feed(c,655,720,wide);assert(c.phase()==Phase::Finished&&c.tick(725,center).left==0);}
void mission_rollover(){Step s[]={ {Event::Wide,Action::Lift,0,5000} };Config c;Mission m(s,1);
    uint32_t start=0xffffff00U;m.reset(start);
    for(uint32_t i=0;i<=100;i+=5)m.tick(start+i,good(),c,false);
    for(uint32_t i=105;i<=135;i+=5)m.tick(start+i,broad(),c,false);
    m.tick(start+135+c.liftWaitMs,good(),c,false);assert(m.phase==Phase::Exiting);}
struct Test {const char *name;void (*run)();};
static const Test tests[]={
    {"pd",pd},{"dynamic_pd",dynamic_pd},{"adapter",adapter},{"partial",partial},{"bounded",bounded},{"blips",blips},{"uncertainty",uncertainty},
    {"recover",recover},{"timing",timing},{"rollover",rollover},{"stop",stop},{"invalid",invalid},
    {"directions",directions},{"mismatch",mismatch},{"no_route",no_route},{"profiles",profiles},
    {"lift_timeout",lift_timeout},{"exit_timeout",exit_timeout},{"finish",finish},{"rearm",rearm},
    {"windows",windows},{"turn_timeout",turn_timeout},{"six_minutes",six_minutes},
    {"complete_path",complete_path},{"mission_rollover",mission_rollover}
    ,{"late_return",late_return},{"derivative_sign",derivative_sign},{"ready_boundary",ready_boundary},{"invalid_routes",invalid_routes}
};
int main(int argc,char **argv){int ran=0;for(const Test &t:tests)if(argc==1||!strcmp(argv[1],t.name)){
    t.run();printf("PASS %s\n",t.name);++ran;}return ran?0:2;}
