# AGENTS.md — 小书童·百宝箱分发仓 Project Agent 入口

## Authority order

1. Owner's latest explicit release/distribution decision.
2. Live GitHub Release assets and verified hashes.
3. Current `versions.json` and `apps/*-version.json` metadata.
4. `README.md` distribution rules.
5. Chat recollection or model memory.

## Repository role

This repository is a distribution metadata/release index, not an application source repository. APK binaries belong in GitHub Releases; Git tracks version metadata only.

## Fresh-session recovery

1. Read this file and `README.md`.
2. Live-fetch `main`, open PRs and the relevant app version metadata.
3. Inspect the referenced GitHub Release asset and applicable checksum/signature/version evidence.
4. Check for an existing release writer/PR before editing metadata.
5. Update version metadata only after the intended release asset is verified.

## Hard stops

Owner input is required for changing release/signing identity, deleting or replacing published release assets, redirecting users to a materially different distribution channel, or publishing a production release outside approved scope.

## Evidence integrity

A version metadata edit is not RELEASE_PASS. Release asset existence, expected version and required integrity/signing evidence must be verified at the applicable release Gate.

## Continuity design

`versions.json`, `apps/*-version.json` and GitHub Releases already carry current-state responsibilities; do not create a parallel `PROJECT_STATE.md` merely for format consistency.