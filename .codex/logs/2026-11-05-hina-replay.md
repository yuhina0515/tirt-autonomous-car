# Hina Web interactive replay

User authorized publishing interactive simulation to the existing TIRT project. Replaced obsolete October overview with a native React/canvas player and current control/qualification boundaries. Two verified known711 runs,50ms display sampling plus exact final frame; no new physics run. Export rejects trace hash mismatches. Assets follow existing /projects permission policy; no auth changes.

Validation:145 Python tests pass; isolated Docker Next16.4.3 production build passes. Browser verified phase8 jump115205ms,126005ms lift waiting/PWM0, reference end219320ms and layered end103305ms/fault lock. Desktop and narrow layouts inspected. Preview and production image identical sha256:25f156d1cc6c14fde6b3fec0a5e73ead756928209277aacd66347cfbbb4f514b. Production telemetry SHA256 d6eccd58fb50b19553c439bb07405222070a5e8065cacd611b7bc0b96a9fc803 matches local export.

Live URL https://hina-tw.ddns.net/projects/tirt requires existing authorized login. Anonymous HTTPS data returns401; browser routes to login. Authenticated live browser inspection was unavailable, so deployed image/assets were checked directly and UI tested with the identical isolated preview image. Do not claim authenticated HTTPS download verification.

Source /srv/docker/hina-web/app/projects/tirt/{page.tsx,Replay.tsx,Replay.module.css}; generated assets public/projects/tirt/replay-20261105. Stage/backup /srv/docker/hina-web-tirt-preview-20261105, original page original-project.tsx.bak. Rollback image hina-web-hina-web:pre-tirt-replay-20261105. Existing server dirty files preserved; no firmware/download changes. Copy only tracked web/hina-tirt sources for future updates; exporter command in its README. Preview localhost3315 retained for review.
