# AGENTS.md — 小书童·百宝箱分发仓 Project Agent 入口

## Authority order

1. Owner's latest explicit release/distribution decision.
2. Live GitHub Release assets and verified size/hash/signing evidence.
3. `apps/*-version.json` plus referenced `apps/icons/*` assets — canonical per-app catalog metadata.
4. `versions.json` — committed generated projection consumed by Baibaoxiang; it must equal `scripts/catalog.py` output.
5. `README.md` distribution rules.
6. Chat recollection or model memory.

## Repository role

This repository is a distribution metadata/release index, not an application source repository. APK binaries belong in GitHub Releases; Git tracks version metadata and catalog assets only.

## Fresh-session recovery

1. Read this file and `README.md` (including its 上海 APK 镜像运行边界、续期与 COS Gate); revalidate snapshot dates and current resource state.
2. Live-fetch `main`, open PRs, the relevant per-app manifest, and referenced GitHub Release.
3. Check for another active release writer/PR before touching the same app or `versions.json`.
4. Verify release asset state, size, SHA-256, version/signing provenance as applicable.
5. Run `python scripts/catalog.py check` and `python scripts/catalog.py verify-releases`.
6. Edit the per-app manifest/icon only; do not hand-edit `versions.json`.
7. Run `python scripts/catalog.py generate`, then rerun `check` and the applicable release Gate.
8. After metadata merge, run `python scripts/catalog.py purge-verify` before claiming the catalog is live.
9. Use physical-device/client verification when the change affects user-visible discovery/install behavior.
10. After any public main catalog mutation and purge-verify, use the existing README Shanghai catalog mirror procedure; validate origin bytes/hash/updatedAt. Do not claim the Shanghai copy is canonical or fresh if synchronization was not verified. A mirror HOLD does not erase an independently verified GitHub catalog state.

All branch/head/release/CDN/device facts are staleable and must be revalidated live before mutation or completion claims.

## Release mutation protocol

- Release asset first, catalog metadata second.
- `apps/*-version.json` is the app-level source of truth.
- `iconFile` points to a canonical 192×192 PNG under `apps/icons/`; the generator embeds it as the existing data-URI protocol expected by Baibaoxiang.
- `catalogOrder` controls stable display order.
- `catalogUpdatedAt` is the app manifest's last catalog mutation time; root `updatedAt` is generated as the newest value.
- `versions.json` is generated and committed because deployed Baibaoxiang clients consume it directly.
- After merge, jsDelivr `@main/versions.json` must be purged and re-read; a GitHub merge alone is not CDN PASS.

## CI / execution

The repository must not consume GitHub-hosted minutes merely for catalog validation. Reuse an authorized self-hosted runner if one is actually available to this repository; otherwise run the same deterministic scripts through the authorized Project Agent/local execution path. Do not register a new runner merely for this metadata repository.

## Hard stops

- 上海独立下载域名、免费证书与 CloudBase 套餐的到期/费用、Range=206、COS 原生直连约束以 `README.md` 的上海镜像节为唯一仓内操作提示；GitHub Issue/PR 回执为历史验收证据，不是未来额度或网络状态保证。
- 未经 Owner 单独批准不得切换 canonical 下载、改当前 `dl` DNS、放宽底层 COS ACL、购买或开启计费资源；新镜像必须经完整制品校验与客户端 Gate。

Owner input is required for changing release/signing identity, deleting or replacing published release assets, redirecting users to a materially different distribution channel, or publishing a production release outside approved scope.

## Evidence integrity

A metadata edit or merged PR is not RELEASE_PASS. Release asset existence, expected package/version, size/hash/signing evidence, generated-catalog consistency, CDN readback, and applicable client/device verification are separate Gates.

## Continuity design

Existing GitHub Releases, per-app manifests, generated `versions.json`, this file and `README.md` already carry the repository's current-state/authority responsibilities; do not create a parallel `PROJECT_STATE.md` merely for format consistency.
