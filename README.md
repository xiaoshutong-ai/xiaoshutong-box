# 小书童·百宝箱 更新分发

小书童全家桶的公开更新索引与安装包分发仓库。这里**不包含各应用源码**，只维护正式 Release 与分发元数据。

## 数据职责

- `apps/*-version.json` —— 各应用的 canonical（权威）版本元数据。
- `apps/icons/*.png` —— 版本单使用的 canonical 192×192 PNG 图标。
- `versions.json` —— 由 `scripts/catalog.py` 从各应用 manifest **确定性生成**的全家桶版本单；百宝箱 App 启动时读取它。
- GitHub Releases —— 正式 APK 与校验文件的唯一二进制发布位置。
- `scripts/catalog.py` —— 生成、完整性校验、Release 对账以及 jsDelivr purge/readback 工具。

不要手工维护 `versions.json` 中的单个应用对象；修改 `apps/*-version.json` 后重新生成。

## Manifest 关键字段

每个 `apps/*-version.json` 至少包含：

- `package` / `name` / `desc`
- `versionCode` / `versionName`
- `apkUrl` / `sha256` / `sizeBytes`
- `publishedAt` / `releaseTag`
- `changelog` / `minVersionCode`
- `iconFile`：相对于 `apps/` 的 192×192 PNG
- `catalogOrder`：统一版本单中的稳定顺序
- `catalogUpdatedAt`：该应用最近一次 catalog 元数据更新时间

`sourceCommit`、`preferredApkUrl` 等字段按应用需要保留。

根 `versions.json.updatedAt` 自动取所有 manifest 中最新的 `catalogUpdatedAt`。

## 本地/Agent Gate

以下命令仅使用 Python 标准库，不需要额外依赖：

```bash
python scripts/catalog.py check
python scripts/catalog.py verify-releases
```

- `check`：验证所有 manifest/schema/icon，并确认提交的 `versions.json` 与生成结果一致。
- `verify-releases`：实时读取 GitHub Releases，核对 draft/prerelease、asset URL、size、SHA-256 和发布时间。

修改 manifest/icon 后：

```bash
python scripts/catalog.py generate
python scripts/catalog.py check
python scripts/catalog.py verify-releases
```

## 发布顺序

1. 在应用源码仓完成构建、测试、签名与适用的设备验收。
2. 把**同一已验证 APK 字节**上传到本仓 GitHub Release，并校验 asset size/SHA-256。
3. 更新对应 `apps/*-version.json`；如展示图标变化，同步更新 `apps/icons/*`。
4. 更新该 manifest 的 `catalogUpdatedAt`。
5. 运行 `generate → check → verify-releases`。
6. 通过 PR 与要求的独立 review 后合入 `main`。
7. **合入后**执行：
   ```bash
   python scripts/catalog.py purge-verify
   ```
8. 对新增应用、下载链变化等用户可见变更，继续做百宝箱真机刷新/安装入口验收。

## jsDelivr 缓存

现有百宝箱客户端读取：

```text
https://cdn.jsdelivr.net/gh/xiaoshutong-ai/xiaoshutong-box@main/versions.json
```

`@main` 是可变引用，且 jsDelivr/Cloudflare 可能缓存旧内容。因此：

> GitHub `main` 已更新 ≠ 百宝箱已拿到新版本单。

`purge-verify` 会清理该精确路径并轮询回读，只有 CDN JSON 与当前生成 catalog 一致才返回 PASS。

## CI / Runner

本仓的校验逻辑已经封装为可重复脚本。若仓库实际分配了现有 self-hosted runner，可直接把这些命令接入薄 workflow；不得为了这类轻量 JSON 检查新增 runner，也不应消耗 GitHub-hosted runner 配额。

发布原则：Git 管理元数据；APK 等二进制制品通过 GitHub Releases 分发；不得把 `apps/*.apk` 提交到 `main`。
