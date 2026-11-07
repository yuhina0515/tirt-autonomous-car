# Ordered-recovery experiment (not promoted)

This separate ADC/time-only variant improves two known model diagnostics but
still fails both. Under the corrected corner-progress judge it reaches198/209
gates twice, then leaves the road. Original candidate_car/recovery_mission,
maintained native_car, rollback and stable references are unchanged.

Only post-lift sharp-corner capture changes; normal preview speed is unchanged.
The entry hint freezes recovery direction. Center and chosen-side observations
must clear before a return on that side switches the fast pivot to soft capture.
Return can be outer or inner: this is not a complete outer->inner->center proof.
Opposite error can correct steering but cannot rewrite the frozen search side.
Central narrow-line confirmation still requires20ms. One800ms uncertainty timer
covers every phase; repeated hints cannot rearm it. Fixed pivot remains bounded
650ms. Provisional soft commands are15/105 mirrored when invisible, or base90
with correction limited45 when visible. No motor response is claimed measured.

The matching profile is `simulation/ordered_recovery_mission.json`. Five original
training prefixes were revalidated using physical ADC regeneration and exact
actual-core command/state/event replay. Known seeds711/714 are diagnostics, not
training or unseen validation. Reserved fresh seeds741..745 remain unexecuted.

Nano old-bootloader: unprofiled8360 Flash/191 global RAM; profiled9312/229. These
are static build sizes. No upload, hardware operation, official acceptance or
onboard finish-stop. See `docs/ORDERED_RECOVERY_2026-11-04.zh-TW.md` and the frozen
receipts for comparison under both the original and corrected model judges.
