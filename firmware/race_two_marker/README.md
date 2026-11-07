**2026-11-07 R3.2 practice setting:** first confirmed marker waits 20,000 ms. Earlier release timings below are historical. Verify the platform is stationary before departure.

# Two-marker practice candidate — 2026-11-07 R3.1

R3.1 additionally fixes uncertainty/recovery carry-over across full-white overrides. All speed/deadline settings remain R3 values. See docs/prepractice-2026-11-07.

R3 temporarily disables the R2 slow exit via `Config::useSlowExit=false`. Set true to restore R2 for field comparison. Marker lockout, clean-narrow100ms confirmation and1500ms exit deadline remain. On all-white after waiting, use native startup PWM100; otherwise run normal motion immediately. The retained R2 policy below only applies when the flag is true.

User-requested sequence: first confirmed five-white stops for27000ms, second confirmed five-white latches finish. Derived from the runnable native motion core with its legacy marker/lap calls disabled in an isolated copy. Native rollback is unchanged. It is not the low-pass-rate layered empty-route controller and has not passed a real full lap.

Open race_two_marker.ino with its three headers, or use the dependency-free single-file package. R2 historical Nano build:8670bytes Flash,293bytes globals. R3 build receipts are recorded separately. No NeoPixel/vendor library. Compile-only; no device upload performed.

ADC physical order A5,A4,A3,A2,A1. Each Schmitt state enters white at<70 and leaves at>=100; intermediate values retain state. These provisional per-sensor thresholds require morning verification. Motion and mission consume the same canonical bits.11111 stops immediately,30ms continuous confirmation counts. During27s wait no patterns can increment the counter. R2 exit uses a separate low-speed centroid follower (A4/A3/A2, PWM15..45) immediately, before mission rearm. Any continuous clean narrow line (00010/00100/00110/01000/01100, outer sensors black) for100ms within1500ms rearms; expiry wins. Initial no-line/wide patch advances45/45. After a narrow line, loss uses at most120ms direction memory then stops; split or renewed wide stops immediately. These uncertain observations reset rearm confirmation and never count another marker. Finished/fault remain stopped until reset. Total run360s; scheduling gap>100ms fails. Uncertain inner patterns have800ms budget, cleared only after30ms narrow recovery; inherited split20ms failure still applies outside exit.

D12 active-low with existing external bias: release then press25ms to start. A second debounced press latches stop. No remote start. Motor pins unchanged D7/D5left,D4/D6right. Zero PWM is not a guarantee of active mechanical braking.

Rules require physical finish crossing and mechanism completely settled. Two all-white events are a user-specified course hypothesis, not a guarantee in the PDF. Verify no additional broad patches qualify, the lift is stopped at departure, and the physical timer detects finish before the car stops. Full32pattern/state analysis and final-practice checklist are under docs/race-two-marker-2026-11-06.

Packaging: `py -3.11 tools/package_race_two_marker.py --output build-output/race-two-marker-release/race_two_marker/race_two_marker.ino`.
