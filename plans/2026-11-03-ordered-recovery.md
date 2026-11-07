# Ordered recovery experiment

Base: de1c0d4. Previous turn made progress by testing and rejecting a combined
preview/early-exit change; no whole-course improvement was established.

This experiment changes post-lift capture only, not preview speed, normal PD,
the physical model, mission observation semantics before the lift, referee,
800ms uncertainty deadline or20ms central confirmation. Source is isolated in
firmware/experiments/ordered_recovery. Maintained native_car, original
candidate_car/recovery_mission, root rollback and stable refs remain unchanged.

Hypothesis: a fixed pivot continues through returning line observations because
it ignores their order and lets transient opposite error overwrite recovery
direction. Freeze direction at the entry hint. Require the center and chosen
side to clear before a chosen-side return switches to softer capture. Continue
bounded feedback until central confirmation; wrong-side return alone cannot
clear uncertainty. The chosen-side return may be outer or inner; this is not a
claim of a fully verified outer->inner->center observation sequence.

Provisional capture commands: invisible soft search15/105 mirrored, visible
capture base90/correction45; no motor constants are claimed measured. Fixed pivot
still ends by650ms and all phases share800ms. Repeated hints cannot rearm the
episode. Four directed regressions cover entry-center aliasing, mirrored chosen
return, wrong-side sequence and direction freezing. Compile the actual Nano
target and revalidate all five original training prefixes before binding a
mission profile.

Diagnostic probes use known seeds2026110711 and2026110714, high-torque hypothesis,
240s cap, fresh output folders and unchanged legal checks. Compare against the
preserved original candidate, not just the rejected preview variant. Full ordered
gates, direction/layer, body/wheel coverage, mechanisms and finish all matter;
passing a local capture test or increasing gate count is not legal completion.
Keep every failure and audit actual-core commands plus regenerated sensor origin.

Fresh seeds2026110741..745 are reserved in
simulation/ordered_validation_seeds.json before diagnostic outcomes are read.
They remain unexecuted unless a frozen candidate justifies final validation.
Do not spend them on further tuning or combine prior-version successes. Official
geometry/calibration and real-car acceptance remain separate unmet requirements.

The learner CLI additionally gains stderr progress callbacks so later multi-minute
audits expose the current seed and completed prefix without changing its returned
JSON or audit criteria. Library calls are silent by default. No subagents, merge,
upload or hardware operation are part of this experiment.

Post-diagnosis deviation (2026-11-04): both frozen probes failed under the original
judge (194/209, wheel departure). Inspection found an incoming-tangent-only vertex
gate that never triggers for a legal rounded A-apex footprint. Preserve those
original results; use a uniform directed tangent bisector at vertices, with the
same width/height and positive crossing limits, for additional explicitly named
audits of both baseline and experiment. Nonvertex timing gates and independent
body/wheel/direction/layer/mechanism checks remain. Negative tests cover reverse,
distant cuts and wrong layers; exact reversals retain original semantics. This
corrects model progress, not official geometry or a vehicle failure. Never relabel
old receipts as if this judge had been predeclared or pool the two judge versions.
