#include "../firmware/candidate_car/controller.h"
#include <assert.h>
#include <stdio.h>

int main(){
    tirt::Controller c;
    const uint16_t center[]={500,500,35,500,500};
    const uint16_t grayLeft[]={500,130,35,500,500};
    const uint16_t grayRight[]={500,500,35,130,500};
    const uint16_t partial[]={500,500,200,500,500};
    const uint16_t full[]={35,35,35,35,35};
    const uint16_t absent[]={500,500,500,500,500};
    for(uint32_t ms=0;ms<=200;ms+=5)c.tick(ms,grayLeft);
    assert(c.state().f==4&&c.output().left<c.output().right);
    c.reset();for(uint32_t ms=0;ms<=200;ms+=5)c.tick(ms,grayRight);
    assert(c.output().left>c.output().right);
    c.reset();for(uint32_t ms=0;ms<=200;ms+=5)c.tick(ms,partial);
    assert(c.state().f==0&&c.state().motion==tirt::Motion::Follow);
    assert(c.output().left>0&&c.output().right>0);
    c.reset();for(uint32_t ms=0;ms<=100;ms+=5)c.tick(ms,center);
    for(uint32_t ms=105;ms<=150;ms+=5)c.tick(ms,full);
    c.tick(155,center);
    assert(c.state().events==1&&c.state().lift==tirt::Lift::Before);
    c.reset();c.tick(0,center);
    // Isolated 5ms blips cannot renew an800ms uncertainty episode.
    for(uint32_t ms=5;ms<805;ms+=5)c.tick(ms,ms%100==0?center:absent);
    c.tick(805,absent);
    assert(c.state().fault==tirt::Fault::SignalDeadline);
    const uint16_t split[]={500,35,500,35,500};
    c.reset();for(uint32_t ms=0;ms<=800;ms+=5)c.tick(ms,split);
    assert(c.state().fault==tirt::Fault::SignalDeadline&&c.state().splitActive);
    assert(c.output().left==0&&c.output().right==0);
    const uint16_t outerOnly[]={35,500,500,500,35};
    c.reset();for(uint32_t ms=0;ms<=800;ms+=5)c.tick(ms,outerOnly);
    assert(c.state().fault==tirt::Fault::SignalDeadline);
    c.reset();c.tick(0xfffffff0U,center);c.tick(0x10U,center);
    assert(c.state().fault==tirt::Fault::None);
    printf("PASS candidate continuous core\n");
}
