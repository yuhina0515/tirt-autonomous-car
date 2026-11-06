#pragma once
// Write-only RUNNING telemetry. Protocol: docs/race-two-marker-2026-11-06/TELEMETRY.md
// Reports what the sketch already did; takes no host input and drives no motor pin.
#include <Arduino.h>
#include "controller.h"

namespace race_telemetry {
static const uint32_t kBaud = 115200;
static const uint32_t kPeriodUs = 20000;  // 50 Hz slots on the device clock.
static const uint8_t kSync0 = 0xA5, kSync1 = 0x5A, kVersion = 1, kFrameSize = 48;
static const uint8_t kFlagRunning = 1, kFlagStopped = 2, kFlagMaskStale = 4;
static_assert(kFrameSize <= 48, "telemetry frame must stay within 48 bytes");

namespace detail {
static bool armed = false;
static uint32_t nextDueUs = 0, maxLoopGapUs = 0;
static uint16_t sequence = 0, dropped = 0, maxScanUs = 0, scanCount = 0;

inline void put16(uint8_t* p, uint16_t v) {
    p[0] = uint8_t(v);
    p[1] = uint8_t(v >> 8);
}
inline void put32(uint8_t* p, uint32_t v) {
    p[0] = uint8_t(v);
    p[1] = uint8_t(v >> 8);
    p[2] = uint8_t(v >> 16);
    p[3] = uint8_t(v >> 24);
}
// CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, no final XOR.
inline uint16_t crc16(const uint8_t* data, uint8_t length) {
    uint16_t crc = 0xFFFF;
    for (uint8_t i = 0; i < length; i++) {
        uint8_t x = uint8_t(crc >> 8) ^ data[i];
        x ^= uint8_t(x >> 4);
        crc = uint16_t(crc << 8) ^ uint16_t(uint16_t(x) << 12) ^ uint16_t(uint16_t(x) << 5) ^ x;
    }
    return crc;
}
}  // namespace detail

inline void begin() {
    detail::armed = false;
    detail::nextDueUs = 0;
    detail::maxLoopGapUs = 0;
    detail::sequence = 0;
    detail::dropped = 0;
    detail::maxScanUs = 0;
    detail::scanCount = 0;
    Serial.begin(kBaud);
}

// Call once per loop, after the motor write. Worst/total timing accumulates across
// every scan since the last transmitted frame, including slots dropped on backpressure.
inline void emit(uint32_t scanStartUs, uint32_t loopGapUs, uint16_t scanUs, const uint16_t raw[5],
                 const race::Controller& controller, race::Wheels applied, bool running, bool stopped) {
    using namespace detail;
    if (loopGapUs > maxLoopGapUs) maxLoopGapUs = loopGapUs;
    if (scanUs > maxScanUs) maxScanUs = scanUs;
    if (scanCount != 0xFFFF) scanCount++;

    if (armed && int32_t(scanStartUs - nextDueUs) < 0) return;
    // A scan later than a whole period restarts the grid instead of bursting to catch up.
    nextDueUs = (armed && scanStartUs - nextDueUs < kPeriodUs) ? nextDueUs + kPeriodUs : scanStartUs + kPeriodUs;
    armed = true;

    if (Serial.availableForWrite() < int(kFrameSize)) {
        dropped++;
        return;
    }

    const race_motion::State& motion = controller.motionState();
    const bool maskStale = !running || stopped || controller.phase == race::Phase::Finished ||
                           controller.phase == race::Phase::Fault;
    uint8_t f[kFrameSize];
    f[0] = kSync0;
    f[1] = kSync1;
    f[2] = kVersion;
    f[3] = kFrameSize;
    put16(f + 4, sequence);
    put16(f + 6, dropped);
    put32(f + 8, scanStartUs);
    put32(f + 12, loopGapUs);
    put32(f + 16, maxLoopGapUs);
    put16(f + 20, scanUs);
    put16(f + 22, maxScanUs);
    put16(f + 24, scanCount);
    for (uint8_t i = 0; i < 5; i++) put16(f + 26 + 2 * i, raw[i]);
    put16(f + 36, uint16_t(applied.left));
    put16(f + 38, uint16_t(applied.right));
    f[40] = controller.mask();
    f[41] = uint8_t(controller.phase);
    f[42] = uint8_t(controller.fault);
    f[43] = controller.events();
    f[44] = uint8_t((running ? kFlagRunning : 0) | (stopped ? kFlagStopped : 0) | (maskStale ? kFlagMaskStale : 0));
    f[45] = uint8_t((uint8_t(motion.motion) & 0x0F) | (uint8_t(motion.fault) << 4));
    put16(f + 46, crc16(f, kFrameSize - 2));

    Serial.write(f, size_t(kFrameSize));
    sequence++;
    maxLoopGapUs = 0;
    maxScanUs = 0;
    scanCount = 0;
}
}  // namespace race_telemetry
