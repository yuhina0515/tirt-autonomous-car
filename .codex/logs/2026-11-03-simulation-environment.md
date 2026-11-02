# Simulation environment and search boundary fix

User requested building the simulation environment, testing and fixes. Baseline00e0db0. Added configuration-driven14 routes/interference cases times3 plant profiles, baseline/current native compilation and84 closed-loop runs. Saves full JSON/CSV and standalone HTML replay. Rectangular paint/erase features are synthetic, not actual TAIWAN. Low battery, delay/grip, narrow/noisy line and opposite polarity are explicit assumptions/stress cases.

Directed test first failed: turn starts25ms, centered capture starts810ms, maturity825ms equals800ms search deadline; old code faults before accepting completed capture. Fixed only confirmation whose start plus15ms lies within the original search deadline. Unconfirmed or late-maturing observations still fault. Speeds, stop switches and root XML/INO unchanged. Portable C++ core assertions include positive and negative boundaries.

33 Python tests passed; Arduino Nano old-bootloader compile8772 Flash/203 global RAM. Full84-run result unchanged: each42-case version31 reached/6 fault/2 escape/3 timeout. Do not claim aggregate improvement or actual TAIWAN resolution. Preserve every failed case. Public plant remains uncalibrated.

Chrome headless checked84 case options, selection, seek and playback advancement without page errors; screenshot inspected. Latest source/bundle hashes, HEX digest and case outcomes in docs/simulations/2026-11-03-environment.json. E: native-simulation/index.html is the offline viewer; native-build contains current indexed application HEX, no upload. Runtime traces/dependencies remain ignored. Native/source mirror updated, rollback root files unchanged. Commit/push existing PR6, no merge/Release/hardware operation/memory write.
