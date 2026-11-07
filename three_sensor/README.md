# Three-center-sensor practice variant (2026-10-24)

Source: [../car.xml](../car.xml), editable CAGEBOT blocks. `three_sensor.ino` is
the official CAGEBOT Arduino export of that XML; edit the XML and export again.
Do not hand-edit only the Arduino file. This variant was uploaded on 2026-10-24 through COM7 and independently
read back successfully. It has not been drive-tested. The separate `race_v5` candidate is unchanged.

- Use only A4 (left), A3 (center), A2 (right) for decisions.
- Read all five raw ADCs for telemetry, then force decision values A1/A5 to 1023.
  The previous conditional outer filter is removed. At threshold 70, outer values
  cannot contribute to F, steering, noise decisions, or reset the loss counter.
- Restore pre-simulation-tuning settings: straight/outer-wheel PWM 100,
  inner-wheel floor 5, pivot PWM 95. TURN_KP remains 75, threshold remains 70.
  Pivot branches are unreachable with outer sensors disabled.
- Motor direction, start-button wait, serial 115200, and the existing loss-stop
  counter are retained. All five printed A-values are RAW values, not decisions.

F keeps the original bit positions: `8*A4_on + 4*A3_on + 2*A2_on`. No reindexing
to 0..7. For readings strictly below/above threshold:

| Active center sensors | F | Left PWM | Right PWM |
|---|---:|---:|---:|
| None | 0 | Retain previous command; stop on 41st lost iteration | Same |
| A2 | 2 | 100 | 25 |
| A3 | 4 | 100 | 100 |
| A3+A2 | 6 | 100 | 63 |
| A4 | 8 | 25 | 100 |
| A4+A2 without A3 | 10 | Retain previous command (existing noise rule) | Same |
| A4+A3 | 12 | 63 | 100 |
| A4+A3+A2 | 14 | 100 | 100 |

The existing exact-threshold comparisons are retained; steering conditions use
strict `<` and `>`. No physical sampling interval is asserted for loop counts.
Five-sensor intersection hold and outer-only 90-degree pivot no longer trigger.
This is a focused practice experiment, not a qualified race strategy.

## Verification

- Actual CAGEBOT parser and Arduino generator: import/export passed.
- Nano old-bootloader AVR compile using installed CAGEBOT Motoshare library:
  9040 bytes flash, 436 bytes RAM. Subsequently uploaded at explicit user request;
  independent readback verifies all 9040 programmed bytes. Bootloader/EEPROM unchanged.
- Native execution of that actual export: 3125 ADC combinations including 69/70/71
  prove outer-input invariance; eight center patterns and 41-loop loss stop pass.
  These are software checks, not on-car acceptance.

## Restore

The exact previous XML is [../examples/car_v4_pre_three_sensor_20261024.xml](../examples/car_v4_pre_three_sensor_20261024.xml),
SHA-256 `11f89913c1034821dd37e775a2dce42873e840f77e71c214ef2f50167a8d47bb`.
Open that backup in CAGEBOT to restore the previous five-sensor configuration.
The earlier verified original flash/EEPROM backup remains separate in project docs.
