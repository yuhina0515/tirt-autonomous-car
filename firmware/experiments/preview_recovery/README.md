# Rejected preview/reacquisition experiment

This archived ADC/time-only variant is **not adopted**. Maintained native_car and
the prior candidate_car are unchanged. Two known diagnostic seeds still fail;
one loses support and the other regresses from194 to192 ordered gates.

The experiment caps post-lift preview base PWM at100, ends a fixed pivot on the
first narrow/opposite-inner observation, and caps unconfirmed reacquisition base
at85. It forbids retriggering the pivot inside one uncertainty episode. The800ms
deadline and20ms narrow confirmation remain unchanged. Four mirrored/negative
functional regressions pass, which does not imply complete-course benefit.

Use `simulation/preview_recovery_mission.json` only with this archived source.
Its five training prefixes were revalidated using regenerated physical ADC and
identical actual-core command/state/event replay. Do not apply that profile to
another source or treat the known diagnostic seeds as unseen validation.

See `docs/PREVIEW_RECOVERY_2026-11-03.zh-TW.md` for outcomes, frozen evidence paths
and reproduction. Profiled Nano old-bootloader build:9226 bytes Flash/226 global
RAM; no upload, hardware operation, official acceptance or onboard finish-stop.
