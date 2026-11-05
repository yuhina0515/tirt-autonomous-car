# Hina Web TIRT project integration

These three source files deploy together into `/srv/docker/hina-web/app/projects/tirt/`. They replace the obsolete October project overview and embed a native React/canvas replay (no iframe). The existing `/tirt` parameter sandbox is a separate legacy model and remains unchanged.

Generate telemetry from the frozen November5 runs:

```powershell
py -3.11 tools/export_hina_replay.py --output build-output/hina-web-20261105/public/projects/tirt/replay-20261105
```

Copy the generated directory into Hina Web `public/projects/tirt/`. Assets share the existing `/projects` TIRT permission policy. Only whitelisted numeric telemetry, public course artwork and scenario analysis are exported; no firmware binaries, secrets or machine-local paths. Display samples are50ms with the exact final frame retained; scoring remains from the original full trace. Both data and source are tied to the known2026110711 runs, not a new simulation or unseen validation.

Player: two case tabs, play/pause/restart,0.25..16x speed,1s stepping, timestamp seek, phase jumps, route/source toggles,100..200% map zoom, current ordered gates, ADC, PWM, height/tilt and final result. Unreached phase jumps are disabled. Layered bridge lacks detailed mission telemetry, so it is not fabricated in the UI. Playback is explicitly labelled as precomputed, not a browser C++ solver.

Build against the live Next/React lockfile in an isolated preview first, verify desktop/mobile UI and live HTTPS assets after deployment. Back up the original project source and running image. Promote only the reviewed image and copy task-scoped source/assets; preserve unrelated dirty server files, existing auth policy, downloads, firmware and legacy simulator.
