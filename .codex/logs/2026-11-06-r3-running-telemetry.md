# R3 normal exit and running telemetry

User requests temporarily disabling dedicated slow exit, retaining restoration option for morning practice. Config.useSlowExit=false: after27s, all-white uses native startup100PWM, otherwise normal motion runs before marker rearm.100ms clean narrow/1500ms expiry remain. Repeated white cannot count during exit. Handoff does not reset active normal motion history. true restores R2. Tests cover both branches and continuity.

User explicitly clarified capture must drive normally, only adding data return. Claude CLI claude-opus-5-5, --effort medium implemented telemetry.h, decoder, protocol docs and tests. JSON modelUsage confirms requested model, zero permission denials. Lead integrated sketch/mocks/build packaging and reviewed code. Earlier motor-disabled design superseded. Lead fixed first-window peak accounting, incomplete-window mean_scan_hz and same-file decoder output rejection.

Telemetry:115200 USB,48-byte CRC16 binary at50Hz, buffer precheck/drop instead of blocking. Runs from same R3 source with TIRT_TELEMETRY. D12 starts/stops motors normally; no remote commands. Reports rawA5..A1, controller flags/phase/fault/events, applied PWM commands, scan/loop times, per-window maxima/count and dropped frames. Flags distinguish stale mask while stopped/faulted. USB opening may reset board; receiver must open before D12 start. No Bluetooth reconnect work.

Validation:194 tests passed in40.447s including actual C++ transmitter-to-Python decoder CRC/framing/backpressure, actual running adapter motor start/stop and retained R2 control. Nano Old Bootloader main8738Flash294globals; capture10678Flash491globals. Host simulated timings are not hardware measurements. Full hardware bandwidth/stable maximum unknown. ADC remains default128prescale125kHz; theoretical five conversions520us excludes overhead. See SCAN-RATE.md.

Versioned two INO files published under tirt-two-marker-20261106-r3; old downloads remain immutable. Website update and HTTPS receipts follow. No hardware flashing or driving claimed.
