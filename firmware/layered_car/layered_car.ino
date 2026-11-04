// Independent experimental two-layer firmware. Native rollback is unchanged.
#include <Arduino.h>
#include "controller.h"

// Empty route = line practice. Do not infer lift/finish from broad paint alone.
// Configure verified Step entries here before attempting a course mission.
layered::Controller controller(layered::Config::field());

void writeWheels(layered::Wheels w) {
    w.left=layered::bound(w.left,-230,230);w.right=layered::bound(w.right,-230,230);
    digitalWrite(7,w.left<0?HIGH:LOW);analogWrite(5,w.left<0?-w.left:w.left);
    digitalWrite(4,w.right<0?LOW:HIGH);analogWrite(6,w.right<0?-w.right:w.right);
}
// Active-low D12, existing board external bias. Release then press to start;
// a second debounced press latches stop until reset/power cycle.
bool lastLow=false,released=false,running=false,stopped=false;
uint32_t changedAt=0;
void setup(){
    pinMode(12,INPUT);
    const uint8_t outputs[]={7,5,4,6};
    for(uint8_t pin:outputs)pinMode(pin,OUTPUT);
    for(uint8_t pin=A1;pin<=A5;++pin)pinMode(pin,INPUT);
    writeWheels(layered::Wheels());
    lastLow=digitalRead(12)==LOW;changedAt=millis();
}
void loop(){
    uint32_t now=millis();bool low=digitalRead(12)==LOW;
    if(low!=lastLow){lastLow=low;changedAt=now;}
    if(now-changedAt>=25){
        if(!low)released=true;
        else if(released){released=false;if(running)stopped=true;else running=true;}
    }
    if(!running||stopped){writeWheels(layered::Wheels());return;}
    uint16_t adc[5];for(uint8_t i=0;i<5;++i)adc[4-i]=analogRead(A1+i);
    writeWheels(controller.tick(now,adc));
}
