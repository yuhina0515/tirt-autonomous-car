#pragma once
#include <stdint.h>

// Pure control core: no Arduino, vendor libraries, allocation, or hardware I/O.
// Baseline: f3501be root car.ino. Preserve its policies, including limitations.
namespace tirt {
struct Settings {
    static constexpr int16_t straight = 230, curve = 174, pivotOuter = 150;
    static constexpr int16_t pivotInner = 114, capture = 100, gap = 45;
    static constexpr int16_t stage1 = 100, stage2 = 150, stage3 = 190, trimDelta = 30;
    static constexpr uint32_t stage2Ms = 200, stage3Ms = 500, stage4Ms = 900;
    static constexpr uint16_t line = 70, outerBackground = 120;
    static constexpr uint32_t searchMs = 800, searchMinMs = 30, captureMs = 15;
    static constexpr uint32_t dropoutMs = 60, directionMs = 250, centerMs = 80;
    static constexpr uint32_t directionConfirmMs = 15, outerConfirmMs = 20;
    static constexpr uint32_t outerMemoryMs = 120, probeMs = 80, overrideMs = 150;
    static constexpr uint32_t gapMs = 120, splitMs = 20, splitClearMs = 15;
    static constexpr uint32_t trimMs = 30, trimCenterMs = 30, departMs = 100;
    static constexpr uint32_t liftMarkerMs = 30, markerRearmMs = 100;
    static constexpr uint32_t liftWaitMs = 23350, liftExitMs = 1500;
    static constexpr uint32_t finishMs = 250, minimumLapMs = 15000, maximumLapMs = 180000;
    static constexpr bool lossStop = false, cornerWideStop = false;
};

enum class Motion : uint8_t { Follow, Search, Gap };
enum class Lift : uint8_t { Before, Waiting, Exiting, Done };
enum class Fault : uint8_t { None, SearchDeadline, CapturePattern, GapDeadline,
                             SplitPattern, LiftExitDeadline, RunDeadline, UnexpectedPattern };
struct Wheels {
    int16_t left, right;
    Wheels(int16_t l = 0, int16_t r = 0) : left(l), right(r) {}
};
struct State {
    Motion motion = Motion::Follow;
    Lift lift = Lift::Before;
    Fault fault = Fault::None;
    uint8_t f = 0;
    bool lapDone = false, lapReady = false, lapStarted = false;
    bool recovery = false, recoveryPending = false, splitPending = false;
    bool splitClearPending = false, splitActive = false, outerReady = false;
    bool probe = false, outerSource = false, departed = false, captureStarted = false;
    bool captureConfirm = false, captureGapPending = false, centerPending = false;
    bool gapConfirm = false, straightPending = false, trimPending = false;
    bool trimCenterPending = false, trimAllowed = false, trimSlow = false, warning = false;
    bool departPending = false, markerLatched = false, markerPending = false;
    bool markerClearPending = false, exitPending = false;
    int8_t direction = 0, candidate = 0, outerCandidate = 0, outerDirection = 0;
    int8_t captureSide = 0, gapDirection = 0, wideDirection = 0;
    int16_t straightPwm = 100;
    uint32_t recoveryAt = 0, splitAt = 0, splitClearAt = 0;
    uint32_t outerCandidateAt = 0, outerSeenAt = 0, probeAt = 0;
    uint32_t turnAt = 0, captureAt = 0, captureGapAt = 0;
    uint32_t candidateAt = 0, seenAt = 0, centerAt = 0;
    uint32_t gapAt = 0, gapDirectionAt = 0, gapCaptureAt = 0, wideDirectionAt = 0;
    uint32_t straightElapsed = 0, straightLastAt = 0, trimAt = 0, trimCenterAt = 0;
    uint32_t lapAt = 0, departAt = 0, markerAt = 0, markerElapsed = 0;
    uint32_t markerClearAt = 0, liftWaitAt = 0, liftExitAt = 0, liftLineAt = 0;
};

class Controller {
public:
    const State &state() const { return s; }
    Wheels output() const { return wheels; }
    void reset() { s = State{}; wheels = Wheels{}; }
    bool blue() const { return s.probe || failed() || s.lapDone || s.lift == Lift::Waiting; }
    Wheels tick(uint32_t now, const uint16_t adc[5]) {
        s.f = (adc[1] < Settings::line ? 8 : 0) |
              (adc[2] < Settings::line ? 4 : 0) | (adc[3] < Settings::line ? 2 : 0);
        updateRecovery(now);
        updateSplit(now);
        updateOuter(now, adc[0], adc[4]);
        updateStraight(now);
        updateLap(now);
        if (normalLift() && s.motion == Motion::Follow && !failed() && !s.lapDone)
            selectMotion(now);
        updateMarker(now);

        if (failed() || s.lapDone) drive(0, 0);
        else if (!normalLift()) controlLift(now);
        else if (s.splitActive || s.probe) drive(0, 0);
        else if (s.motion == Motion::Search) search(now);
        else if (s.motion == Motion::Gap) crossGap(now);
        else if (s.f == 14) {
            if (s.recovery) directional(s.wideDirection, age(now, s.wideDirectionAt) <= Settings::gapMs, 100, 50);
            else drive(Settings::gap, Settings::gap);
        } else follow();
        return wheels;
    }

private:
    State s;
    Wheels wheels;
    static uint32_t age(uint32_t now, uint32_t at) { return now - at; }
    bool failed() const { return s.fault != Fault::None; }
    bool narrow() const { return s.f == 2 || s.f == 4 || s.f == 6 || s.f == 8 || s.f == 12; }
    bool centeredShape() const { return s.f == 4 || s.f == 6 || s.f == 12; }
    bool normalLift() const { return s.lift == Lift::Before || s.lift == Lift::Done; }
    int8_t side() const { return s.f == 8 || s.f == 12 ? -1 : s.f == 2 || s.f == 6 ? 1 : 0; }
    void drive(int16_t left, int16_t right) { wheels.left = left; wheels.right = right; }
    void fail(Fault fault) { if (!failed()) s.fault = fault; drive(0, 0); }
    void consume() { s.candidate = 0; s.candidateAt = 0; }
    void directional(int8_t direction, bool fresh, int16_t outer, int16_t inner) {
        drive(fresh && direction == -1 ? inner : outer, fresh && direction == 1 ? inner : outer);
    }
    void capture(int16_t outer, int16_t single, int16_t adjacent) {
        const int16_t inner = s.f == 2 || s.f == 8 ? single : adjacent;
        directional(side(), true, outer, inner);
    }
    bool fallbackAllowed() const {
        return (!Settings::lossStop && s.f == 0) || (!Settings::cornerWideStop && s.f == 14);
    }
    void fallback(uint32_t now) {
        if (s.f == 14) { s.recovery = true; s.recoveryPending = false; }
        if (s.motion == Motion::Search && s.captureStarted) {
            s.gapDirection = s.captureSide; s.gapDirectionAt = now;
        } else if (s.outerReady) {
            s.gapDirection = s.outerDirection; s.gapDirectionAt = s.outerSeenAt;
        } else if (s.motion == Motion::Search && s.direction) {
            s.gapDirection = s.direction; s.gapDirectionAt = now;
        } else if (s.motion != Motion::Gap && s.direction && age(now, s.seenAt) <= Settings::directionMs) {
            s.gapDirection = s.direction; s.gapDirectionAt = s.seenAt;
        } else if (s.motion != Motion::Gap) s.gapDirection = 0;
        if (s.f == 14) { s.wideDirection = s.gapDirection; s.wideDirectionAt = s.gapDirectionAt; }
        s.direction = 0; consume(); s.probe = false; s.motion = Motion::Gap;
        s.gapAt = now; s.gapConfirm = false;
        directional(s.gapDirection, age(now, s.gapDirectionAt) <= Settings::gapMs, Settings::gap, 15);
    }
    void beginTurn(uint32_t now, int8_t direction, bool outer) {
        s.direction = direction; s.outerSource = outer; consume();
        s.motion = Motion::Search; s.turnAt = now; s.captureConfirm = false;
        s.probe = false; s.departed = false; s.captureStarted = false;
        s.captureGapPending = false; s.captureSide = direction;
    }
    void search(uint32_t now) {
        const uint32_t elapsed = age(now, s.turnAt);
        if (s.f == 0) s.departed = true;
        if (s.f == 14) s.recovery = true;
        if (!s.captureStarted && !s.outerSource && elapsed <= Settings::overrideMs && s.outerReady) {
            s.direction = s.outerDirection; s.outerSource = true;
            s.captureConfirm = false; s.captureSide = s.outerDirection;
        }
        const bool visible = centeredShape() || ((s.departed || s.captureStarted) &&
            ((s.f == 2 && (s.captureStarted || s.direction == 1)) ||
             (s.f == 8 && (s.captureStarted || s.direction == -1))));
        // Accept an already-confirmed capture at the deadline; a newly visible
        // or insufficiently confirmed line still cannot extend the search.
        if (elapsed >= Settings::searchMs && centeredShape() && s.captureConfirm &&
            age(s.captureAt, s.turnAt) <= Settings::searchMs - Settings::captureMs &&
            age(now, s.captureAt) >= Settings::captureMs) {
            s.captureSide = side(); s.motion = Motion::Follow; s.direction = 0;
            consume(); s.captureConfirm = false; capture(Settings::capture, 20, 50);
            return;
        }
        if (elapsed >= Settings::searchMs) {
            if (fallbackAllowed()) fallback(now);
            else { s.motion = Motion::Follow; fail(Fault::SearchDeadline); }
            return;
        }
        if (elapsed >= Settings::searchMinMs && visible) {
            // Dropout is a continuous absence interval, not time since the first
            // dropout of this turn. Keep the independent absolute search limit.
            s.captureGapPending = false;
            s.captureStarted = true; s.captureSide = side();
            if (!s.captureConfirm) { s.captureConfirm = true; s.captureAt = now; }
        } else s.captureConfirm = false;
        if (centeredShape() && s.captureConfirm && age(now, s.captureAt) >= Settings::captureMs) {
            s.motion = Motion::Follow; s.direction = 0; consume(); s.captureConfirm = false;
            capture(Settings::capture, 20, 50);
        } else if (s.captureConfirm) capture(Settings::capture, 20, 50);
        else if (s.captureStarted) {
            if (s.f != 0 && s.f != 14) { s.motion = Motion::Follow; fail(Fault::CapturePattern); }
            else {
                if (!s.captureGapPending) { s.captureGapPending = true; s.captureGapAt = now; }
                if (age(now, s.captureGapAt) >= Settings::dropoutMs) {
                    if (fallbackAllowed()) fallback(now);
                    else { s.motion = Motion::Follow; fail(Fault::CapturePattern); }
                } else directional(s.captureSide, true, s.captureSide ? 60 : 45, 30);
            }
        } else if (s.f == 14) directional(s.direction, true, 100, 50);
        else drive(s.direction == -1 ? -Settings::pivotInner : Settings::pivotOuter,
                   s.direction == -1 ? Settings::pivotOuter : -Settings::pivotInner);
    }
    void crossGap(uint32_t now) {
        if (s.outerReady) { s.gapDirection = s.outerDirection; s.gapDirectionAt = s.outerSeenAt; }
        else if (side()) { s.gapDirection = side(); s.gapDirectionAt = now; }
        if (narrow()) {
            if (!s.gapConfirm) { s.gapConfirm = true; s.gapCaptureAt = now; }
            if (age(now, s.gapCaptureAt) >= Settings::captureMs) {
                s.motion = Motion::Follow; s.direction = 0; consume();
            }
        } else {
            s.gapConfirm = false;
            if (s.f == 14) {
                s.recovery = true; s.wideDirection = s.gapDirection; s.wideDirectionAt = s.gapDirectionAt;
                s.motion = Motion::Follow; s.direction = 0; consume();
            } else if (age(now, s.gapAt) >= Settings::gapMs) {
                if (fallbackAllowed()) fallback(now);
                else { s.motion = Motion::Follow; fail(Fault::GapDeadline); }
            }
        }
        if (!failed()) {
            if (side()) capture(Settings::gap, 20, 30);
            else if (s.f == 0) directional(s.gapDirection, age(now, s.gapDirectionAt) <= Settings::gapMs, Settings::gap, 15);
            else drive(Settings::gap, Settings::gap);
        }
    }
    void updateRecovery(uint32_t now) {
        if (!s.recovery) return;
        if (s.f == 4 && s.motion == Motion::Follow) {
            if (!s.recoveryPending) { s.recoveryPending = true; s.recoveryAt = now; }
            if (age(now, s.recoveryAt) >= Settings::centerMs) { s.recovery = false; s.recoveryPending = false; }
        } else s.recoveryPending = false;
    }
    void updateSplit(uint32_t now) {
        s.splitActive = false;
        if (normalLift() && s.motion != Motion::Gap && !failed() && !s.lapDone) {
            if (s.f == 10) {
                s.splitActive = true; s.splitClearPending = false;
                if (!s.splitPending) { s.splitPending = true; s.splitAt = now; }
                if (age(now, s.splitAt) >= Settings::splitMs) fail(Fault::SplitPattern);
            } else if (s.splitPending && narrow()) {
                if (!s.splitClearPending) { s.splitClearPending = true; s.splitClearAt = now; }
                if (age(now, s.splitClearAt) >= Settings::splitClearMs) s.splitPending = s.splitClearPending = false;
            } else s.splitClearPending = false;
        } else s.splitPending = s.splitClearPending = false;
    }
    void updateOuter(uint32_t now, uint16_t left, uint16_t right) {
        if (s.f != 0) s.probe = false;
        if (s.f == 0 || narrow()) {
            const int8_t direction = right < Settings::line && left >= Settings::outerBackground ? 1 :
                                     left < Settings::line && right >= Settings::outerBackground ? -1 : 0;
            if (direction) {
                if (s.outerCandidate != direction) { s.outerCandidate = direction; s.outerCandidateAt = now; }
                if (age(now, s.outerCandidateAt) >= Settings::outerConfirmMs) {
                    s.outerDirection = direction; s.outerSeenAt = now;
                }
            } else s.outerCandidate = 0;
            if (left < Settings::line && right < Settings::line) s.outerDirection = 0;
        } else { s.outerCandidate = 0; if (s.f != 14) s.outerDirection = 0; }
        s.outerReady = s.outerDirection && age(now, s.outerSeenAt) <= Settings::outerMemoryMs &&
                       (!s.outerCandidate || s.outerCandidate == s.outerDirection);
    }
    void resetStraight() {
        s.straightPending = false; s.straightElapsed = 0; s.straightPwm = Settings::stage1;
        s.trimPending = s.trimCenterPending = s.trimAllowed = s.trimSlow = false;
    }
    void updateStraight(uint32_t now) {
        uint32_t delta = age(now, s.straightLastAt); s.straightLastAt = now;
        s.trimAllowed = s.warning = false;
        if (s.outerReady || !normalLift() || s.motion != Motion::Follow || failed() || s.lapDone) { resetStraight(); return; }
        if (s.outerCandidate && centeredShape()) {
            s.warning = s.trimSlow = s.trimPending = true;
            s.trimCenterPending = false; s.trimAt = now - Settings::trimMs;
        } else if (s.f == 4) {
            if (!s.straightPending) { s.straightPending = true; s.straightElapsed = 0; delta = 0; s.straightPwm = Settings::stage1; }
            if (s.trimPending) {
                if (!s.trimCenterPending) { s.trimCenterPending = true; s.trimCenterAt = now; }
                if (age(now, s.trimCenterAt) >= Settings::trimCenterMs) s.trimPending = s.trimCenterPending = s.trimSlow = false;
            } else {
                s.straightElapsed += delta;
                s.straightPwm = s.straightElapsed >= Settings::stage4Ms ? Settings::straight :
                    s.straightElapsed >= Settings::stage3Ms ? Settings::stage3 :
                    s.straightElapsed >= Settings::stage2Ms ? Settings::stage2 : Settings::stage1;
            }
        } else if (s.f == 6 || s.f == 12) {
            if (!s.straightPending) resetStraight();
            else {
                if (!s.trimPending) { s.trimPending = true; s.trimAt = now; }
                s.trimCenterPending = false;
                s.trimAllowed = age(now, s.trimAt) < Settings::trimMs;
                if (!s.trimAllowed) s.trimSlow = true;
            }
        } else resetStraight();
    }
    void updateLap(uint32_t now) {
        if (!s.lapStarted) { s.lapStarted = true; s.lapAt = now; }
        if (age(now, s.lapAt) >= Settings::maximumLapMs) fail(Fault::RunDeadline);
        if (!s.lapReady) {
            if (narrow()) {
                if (!s.departPending) { s.departPending = true; s.departAt = now; }
                if (age(now, s.departAt) >= Settings::departMs) s.lapReady = true;
            } else s.departPending = false;
        }
    }
    void selectMotion(uint32_t now) {
        const int8_t direction = side();
        if (direction) {
            if (s.candidate != direction) { s.candidate = direction; s.candidateAt = now; }
            if (age(now, s.candidateAt) >= Settings::directionConfirmMs) { s.direction = direction; s.seenAt = now; }
        } else {
            if ((s.f == 0 || s.f == 14) && s.candidate && s.candidate != s.direction) s.direction = 0;
            s.candidate = 0;
        }
        if (s.f == 4) {
            if (!s.centerPending) { s.centerPending = true; s.centerAt = now; }
            if (age(now, s.centerAt) >= Settings::centerMs) s.direction = 0;
        } else s.centerPending = false;
        if (!s.recovery && s.f == 14) {
            if (s.outerReady) { s.wideDirection = s.outerDirection; s.wideDirectionAt = s.outerSeenAt; s.recovery = true; }
            else if (s.direction && age(now, s.seenAt) <= Settings::directionMs) {
                s.wideDirection = s.direction; s.wideDirectionAt = s.seenAt; s.recovery = true;
            }
        }
        if (s.f != 0) return;
        if (s.outerReady) beginTurn(now, s.outerDirection, true);
        else if (s.outerCandidate) {
            if (!s.probe) { s.probe = true; s.probeAt = now; }
            if (age(now, s.probeAt) >= Settings::probeMs) {
                if (fallbackAllowed()) fallback(now); else fail(Fault::GapDeadline);
            }
        } else if (s.probe) {
            if (fallbackAllowed()) fallback(now); else fail(Fault::GapDeadline);
        }
        else if (s.direction && age(now, s.seenAt) <= Settings::directionMs) beginTurn(now, s.direction, false);
        else { s.probe = false; s.motion = Motion::Gap; s.gapDirection = 0; s.gapDirectionAt = now; s.gapAt = now; s.gapConfirm = false; }
    }
    void updateMarker(uint32_t now) {
        if (s.lapReady && normalLift() && s.motion == Motion::Follow && !s.recovery &&
            !s.outerReady && !s.outerCandidate && !failed() && !s.lapDone) {
            if (s.f == 14) {
                if (!s.markerLatched) {
                    if (!s.markerPending) { s.markerPending = true; s.markerAt = now; }
                    s.markerElapsed = age(now, s.markerAt);
                }
            } else {
                if (s.markerPending && s.f == 4 && s.markerElapsed >= Settings::liftMarkerMs) {
                    s.markerLatched = true;
                    if (s.lift == Lift::Before) {
                        s.lift = Lift::Waiting; s.liftWaitAt = now; s.exitPending = false; s.direction = 0; consume();
                    } else if (age(now, s.lapAt) >= Settings::minimumLapMs && s.markerElapsed >= Settings::finishMs) s.lapDone = true;
                }
                s.markerPending = false;
            }
        } else s.markerPending = false;
        if (narrow()) {
            if (!s.markerClearPending) { s.markerClearPending = true; s.markerClearAt = now; }
            if (age(now, s.markerClearAt) >= Settings::markerRearmMs) s.markerLatched = false;
        } else s.markerClearPending = false;
    }
    void controlLift(uint32_t now) {
        if (s.lift == Lift::Waiting) {
            drive(0, 0);
            if (age(now, s.liftWaitAt) >= Settings::liftWaitMs) { s.lift = Lift::Exiting; s.liftExitAt = now; s.exitPending = false; }
        } else if (age(now, s.liftExitAt) >= Settings::liftExitMs) fail(Fault::LiftExitDeadline);
        else {
            if (narrow()) {
                if (!s.exitPending) { s.exitPending = true; s.liftLineAt = now; }
                if (age(now, s.liftLineAt) >= Settings::markerRearmMs) {
                    s.lift = Lift::Done; s.direction = 0; s.candidate = 0; s.centerPending = false;
                }
            } else s.exitPending = false;
            drive(Settings::gap, Settings::gap);
        }
    }
    void follow() {
        if (side()) {
            if ((s.f == 6 || s.f == 12) && s.trimAllowed) directional(side(), true, s.straightPwm, s.straightPwm - Settings::trimDelta);
            else capture(Settings::curve, 15, 87);
        } else if (s.f == 4) {
            const int16_t pwm = s.warning ? Settings::stage1 : s.trimSlow && s.straightPwm >= Settings::curve ? Settings::curve : s.straightPwm;
            drive(pwm, pwm);
        } else fail(Fault::UnexpectedPattern);
    }
};
} // namespace tirt
