# Experimental continuous-position controller

This separate ADC/time-only Arduino core is used for offline model experiments.
The maintained default remains `../native_car`; root rollback files are retained.
See `../../docs/CONTROL_RECOVERY_2026-11-03.zh-TW.md` for evidence and limitations.

The adapter uses the same pins and public NeoPixel library as native_car. The
core uses fixed-size state, continuous squared-strength line position, filtered
PD, PWM slew, and one absolute uncertainty deadline. ADC endpoints35/500 are
provisional assumptions. Outer sensors extend capture; separated inner peaks do
not renew confidence. PWM remains bounded to230. Zero PWM is modeled as coasting.

The unprofiled source deliberately has `missionWordCount = 0`: a broad white
observation alone cannot identify the lift. `tools/learn_course_mission.py` learns
literal event words from audited training poses and actual-core diagnostics.
`tools/run_course.py --candidate-profile simulation/recovery_mission.json` stages
a separate copy. Firmware never receives coordinates, ordered-gate progress or
mechanism state from the simulator. Profiles bind the complete core/adapter,
course and physical sensor model; source changes require new training or exact
regenerated ADC/core/state/command replay through all audited teacher targets.
Held-out seeds are rejected as training inputs.

Candidate stop conditions:

- Tick gap greater than50ms, elapsed run360s, continuous uncertainty800ms, or
  broad central-white interval300ms: latched fault.
- Mission hypotheses matching both an ordinary white event and the lift: latched
  ambiguity fault. A mismatched word refuses lift arming.
- Matched lift: stop31s, then require100ms narrow-line confirmation during exit;
  failure to exit within1500ms faults. No settled-position sensor is available.
- Qualified sharp corners after observed lift completion use turns bounded650ms per activation;
  the same800ms uncertainty episode remains active until confirmed recovery.

There is currently no onboard finish-stop detector: `lapDone` stays false. Full
model trials end only when the independent referee observes all ordered gates
and the finish crossing. Model completion therefore cannot establish finish
stopping, official geometry, calibrated dynamics or real-car acceptance. No
upload or motor operation was performed in this work.
