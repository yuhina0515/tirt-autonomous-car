# Final pre-practice audit and R3.1

Baseline a67eb06. Independent Claude Opus5.5 medium read-only audit and followup verified by modelUsage, no permission denials. Bare CLI attempt lacked auth context; normal configured CLI succeeded. Snapshot E:/Temp/tirt-audit-20261107-r3. Lead reproduced two white-override timing bugs: stale exit uncertain timer causes spurious stop after valid line returns, and interrupted narrow recovery incorrectly carries across white blips. Both regression cases failed before their fixes. Minimal two-location reset only; no speed/deadline tuning.

Fix review accepted; reviewer requested alternating-white/loss1500ms deadline test, added and run. Reviewer snapshot equals actual controller bytes. Added64 wait/exit matrices,1000 variable-dt histories and explicit priority cases. R3.1 Nano main8754/294,capture10690/491. No hardware acceptance or physical scan rate claim. Full report and original independent reviews under docs/prepractice-2026-11-07. Existing main/capture R3 HTTPS hashes verified before replacement listing. New R3.1 uses fresh versioned paths, old artifacts retained.

Final195 tests passed in42.671s after followup deadline regression. Opus followup accepted both changes; no further control changes.

Published R3.1 two versioned INOs with HTTPS hash verification. Hina download/project live HTML includes both links. Preview and production image87f1a7faa279f1bc6e74267fb144dfea865b421496e445156edc72daa6b54e45 match; source hashes checked before promotion. Backup /srv/docker/hina-web-backups/two-marker-r3-1-20261107 and image hina-web-rollback:pre-two-marker-r3-1-20261107. Only two website source files changed; no visual browser pass for text/link-only update.
