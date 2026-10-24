# Historical firmware

`three_sensor_baseline` is the simple three-center-sensor PWM100 experiment last
uploaded before this repository was prepared. It includes editable XML and its
official CAGEBOT Arduino export. Its old F-table is superseded for the new
controller, but the file remains available for controlled rollback/comparison.

`five_sensor_before_change.xml` is the exact preceding five-sensor source backup,
SHA-256 `11f89913c1034821dd37e775a2dce42873e840f77e71c214ef2f50167a8d47bb`.

Neither baseline is qualified for the full race. Original exports may require
CAGEBOT's Motoshare NeoPixel library. No original vendor library is bundled.
Binary flash/EEPROM backups remain local; do not assume these XML files reproduce
any unrelated teammate modifications made to a car.
