#include "../firmware/native_car/controller.h"
#include <assert.h>
#include <stdio.h>

static tirt::Wheels sample(tirt::Controller &c, uint32_t ms, uint8_t f) {
    const uint16_t adc[] = {500, uint16_t(f & 8 ? 35 : 500), uint16_t(f & 4 ? 35 : 500),
                            uint16_t(f & 2 ? 35 : 500), 500};
    return c.tick(ms, adc);
}
int main() {
    tirt::Controller c;
    assert(sample(c,0,4).left == 100);
    assert(sample(c,200,4).left == 150);
    assert(sample(c,500,4).left == 190);
    assert(sample(c,900,4).left == 230);
    c.reset(); sample(c,0,4); sample(c,100,4); sample(c,200,4);
    sample(c,205,0); assert(c.state().motion == tirt::Motion::Gap);
    sample(c,324,4); sample(c,325,4);
    assert(c.state().fault == tirt::Fault::None);
    sample(c,339,4); assert(c.state().motion == tirt::Motion::Follow);
    c.reset(); sample(c,0,8); sample(c,20,8);
    auto w=sample(c,25,0); assert(w.left == -114 && w.right == 150);
    sample(c,55,4); sample(c,70,4);
    assert(c.state().motion == tirt::Motion::Follow);
    c.reset(); sample(c,0,4); sample(c,100,4); sample(c,105,14); sample(c,140,14);
    w=sample(c,145,4); assert(c.state().lift == tirt::Lift::Waiting && w.left == 0);
    sample(c,23495,4); assert(c.state().lift == tirt::Lift::Exiting);
    sample(c,23500,4); sample(c,23600,4); assert(c.state().lift == tirt::Lift::Done);
    sample(c,23605,14); sample(c,23860,14); sample(c,23865,4); assert(c.state().lapDone);
    c.reset(); sample(c,0,10); w=sample(c,20,10);
    assert(c.state().fault == tirt::Fault::SplitPattern && w.left == 0 && w.right == 0);
    c.reset(); sample(c,0xffffff00U,4); w=sample(c,0x20U,4);
    assert(c.state().fault == tirt::Fault::None && w.left == 150);
    c.reset(); sample(c,5,4); sample(c,180005,4); assert(c.state().fault == tirt::Fault::RunDeadline);
    printf("PASS native core; state_bytes=%zu controller_bytes=%zu\n",sizeof(tirt::State),sizeof(tirt::Controller));
}
