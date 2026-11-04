# Layered controller (experimental)

This is a separate redesign, not a replacement of the runnable `../native_car` rollback. The published Hina Web native download remains unchanged. No device upload or real-course qualification has occurred.

## Two responsibilities

- `motion.h`: per-channel ADC normalization, filtered observation, inner-three squared-intensity position, PD with elapsed-time derivative, PWM clamp/rise limit and one absolute uncertainty timer. Outer readings are normalized but do not choose a branch. Defaults are provisional ADC35/500, base140, ceiling180; they need physical calibration. These differ deliberately from rollback speeds100/150/190/230.
- `mission.h`: ordered, explicitly configured `Step {trigger, action, minMs, maxMs}` instructions. Wide/Split are observations, not named checkpoints. Actions are Straight, Left, Right, Lift and Finish. Missing/wrong/early/late events stop; no model pose, gate index, trained word or elapsed-time-only stage advancement is accepted.
- `controller.h`: orchestrates those layers and prioritizes stop, configuration, >50ms tick gaps, six-minute run limit and latched faults. Route storage must remain alive for the controller lifetime; use static/namespace-scope Step arrays.
- `layered_car.ino`: same D7/D5 and D4/D6 motor wiring and active-low D12 button with the board's existing external bias. Release then press starts; another debounced press latches stop until reset. A held-at-boot button cannot start. No NeoPixel or vendor dependency. PWM0 is not an active brake.

The default sketch has **no route** and is line practice only. It will not stop for a lift or determine a finish. Do not run it on a mechanism course as if it were configured for race tasks. Native has not been promoted/replaced. Open the whole `layered_car` folder in Arduino IDE; all three headers must stay beside the INO. Board: Nano ATmega328P (Old Bootloader).

## What was removed from the old policy

No first-wide=lift or post-lift-wide=finish assumption, 15-second finish eligibility heuristic, 180-second race timeout, 20ms split automatic fatal rule, repeatedly renewed loss fallback, straight-time speed stages, lift-dependent corner hack or source-trained junction words. An unresolved line observation predicts at low PWM for at most60ms then waits stopped; 800ms absolute uncertainty faults. Continuous trusted line30ms is required to recover, and expiry wins over a confirmation first observed at the deadline. A recognized mission maneuver has its own absolute800ms bound (lift exit1500ms).

Requested turns require a chosen-side trusted observation followed by central return30ms, not merely return of the original straight branch. This observable sequence is a hypothesis requiring physical calibration, not proof of selecting the geometrically correct branch. Ordinary curves use PD; V corners and shortcuts still require verified maneuver/clearance evidence. Shortcuts have no dedicated boundary detector in this version.

## Lift profiles

`Config::field()` retains the **23350ms** Xiangyi field setting on explicit user evidence (2026-11-05). It is intentional and time-only, not an implementation bug. It does not establish that the lift has settled.

`Config::race()` uses28850ms (upper stated27s+5% interval plus500ms provisional margin) **and requires `liftReady=true`** before exit. If readiness does not arrive within a further5000ms, it faults. The current adapter does not have a verified mechanism-ready sensor and always supplies false. Selecting this profile alone therefore cannot complete a lift; add verified hardware input or explicitly select/document a calibrated time-only policy. The margin is an engineering setting, not an official guarantee. Expiry takes precedence over readiness at the exact deadline.

A Lift step stops on the configured stable observation, not after its painted exit; physical sensor-to-axle distance, stopping distance and target placement remain unmeasured. Exit requires central return30ms within1500ms. Marker arming requires trusted clearance100ms before a stable Wide/Split30ms can trigger, so one long mark cannot consume several steps.

## Configure a route only after field verification

```cpp
// Illustrative contract only, NOT the official map or a deployment preset.
static const layered::Step route[] = {
    {layered::Event::Split, layered::Action::Left, 1000, 20000},
    {layered::Event::Wide, layered::Action::Lift, 1000, 30000},
    {layered::Event::Wide, layered::Action::Finish, 1000, 30000},
};
layered::Controller controller(layered::Config::field(), route, 3);
```

The route must include ordinary junctions too. Early/unexpected stable events fault instead of silently counting through them. Each window starts at run start or completion of the previous maneuver, excluding a preceding lift wait. Finish latches zero PWM at its configured stopping landmark; it is **not** an external finish-crossing detector. Use only a verified stop landmark beyond the official timing line, with sufficient car clearance. An exhausted route without Finish faults; it does not claim completion.

## Verification and next physical inputs

Run `py -3.11 -m unittest discover -s tests -v`. The layered tests compile the actual C++ cores/Arduino adapter once; no simulated alternate algorithm. CI also executes 32-bit C++ contracts. Compile via Arduino CLI for `arduino:avr:nano:cpu=atmega328old`; no third-party library is needed. There is no automatic upload.

`pwsh -File tools/Compile-Layered.ps1` builds practice, field-route and race-route configurations in fresh ignored output folders. The two route configurations are compilation fixtures only; they are not the official route. Final local validation:139tests pass,29new; Nano practice6074/157, field-route6110/187, race-route6032/209 Flash/globalRAM bytes. These are static sizes, not peak RAM or measured loop timing.

Before a race preset can be authored: verify ordered junction exits and distinguishable landmark signatures, shortcut boundary, the lift's actual readiness/period and stop position, finish clearance, per-channel ADC endpoints, sensor height and motor response. Existing inferred-course model runs and unknown route fields are retained; no new full-course sweep is used to fit this design to those traces. Software tests are component contracts, not completed race attempts.
