# Telemetry contract

115200 module/controller UART, CSV numeric records, no heap String building.
Host Bluetooth virtual COM 9600 worked in earlier tests; that host setting is
independent of the configured module UART. USB uses host 115200.

Wire columns are fixed, with no startup header dependency:

`millis,tick,dt,rawA5,rawA4,rawA3,rawA2,rawA1,mask,state,reason,position,accepted_position,contrast,left_pwm,right_pwm,rejected,timing_faults`

- `millis`, `tick`, cumulative counters are unsigned 32-bit device values.
- `dt` is elapsed device time before that control tick, not host arrival spacing.
- Raw order is A5..A1, each 0..1023. Outer values are logged but ignored by control.
- `mask` uses original bit positions 8/4/2 after filtering/hysteresis. It is not
  a direct threshold of the raw value displayed in the same record.
- Position units: A4=-1000, A3=0, A2=1000; calibrated strengths give intermediate positions.
- `position` is the latest valid candidate; when reason is invalid, it may be stale.
  `accepted_position` is the last trusted value, not a pose or steering angle.
- `contrast` is max-minus-min filtered strength across the center three, 0..1000.
- PWM is commanded duty, not measured wheel speed. Commands are forward-only.
- `rejected` counts unaccepted control ticks in acquisition/uncertainty, not text characters.
- Capture uses 20 ms scheduling/logging; track targets 10 ms control with 50 ms
  log snapshots by default. UART blocking and hardware execution may cause gaps;
  configured periods are targets, not measured real-time guarantees.
- The collector adds `host_ms,label`. Labels reflect when the host handled a
  buffered record; they are not synchronized device event timestamps.

| State | Meaning |
|---:|---|
| 0 | WAIT / unarmed |
| 1 | ACQUIRE, motors off except bounded straight departure on full white in lap mode |
| 2 | TRACK, continuous PD steering |
| 3 | UNCERTAIN, frozen recovery budget; edge search, centered gap, wide crossing or last curvature |
| 4 | STOP, button, run limit or finish candidate; requires a new press |
| 5 | FAULT, timing or uncertainty/acquisition deadline; requires a new press |
| 6 | CAPTURE, motors always off |

| Reason | Meaning |
|---:|---|
| 0 | Accepted / normal |
| 1 | No line, or uncertainty watchdog expired |
| 2 | All center sensors active / wide observation |
| 3 | Split observation A4+A2 without A3 |
| 4 | Abrupt jump awaiting confirmation |
| 5 | Configuration not armed |
| 6 | Tick gap exceeds configured maximum |
| 7 | Physical button stop |
| 8 | Candidate not yet continuously confirmed |
| 9 | Initial acquisition timeout |
| 10 | Run time limit reached |
| 11 | Insufficient center contrast |
| 12 | Full-white start departure |
| 13 | Finish candidate latched; not proof of a completed lap |
| 14 | Edge-directed search with inner wheel unpowered |
| 15 | Centered gap, slow straight motion |
| 16 | Wide crossing, slow straight motion |

Fault/stop commands drop PWM immediately; no automatic recovery or reverse pivot.
The next start requires a debounced release and press. A held button at boot does
not start. A receiver exiting or a lost Bluetooth connection does NOT stop the
car: it is autonomous, without a host heartbeat protocol. Use its physical button
or power switch. Do not depend on Bluetooth for emergency stopping.

Raw `.bin` preserves all received bytes. The collector validates field count,
records malformed/tail counts in its JSON receipt, and never transmits payload.
Offline analysis also checks ranges, duplicate/reset clocks and wrap. Device tick
differences include intentionally unlogged ticks, not solely packet loss.
