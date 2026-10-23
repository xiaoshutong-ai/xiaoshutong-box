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

`sourceCommit`、`preferredApkUrl` 等字段按应用需要保留。大陆安装页可使用可选字段 `preferredInstallPageUrl`；它是浏览器安装入口，不得冒充可做 APK SHA-256 校验的 `apkUrl` / `preferredApkUrl`。

根 `versions.json.updatedAt` 自动取所有 manifest 中最新的 `catalogUpdatedAt`。

## 公开展示与内部保留

- `apps/*-version.json` 中可选的 `publicVisible` 默认为 `true`；严格布尔值 `false` 表示内部应用，`scripts/catalog.py` 在生成公开 `versions.json` 时省略它。
- 内部应用的 manifest、既有 APK 签名、SHA-256、GitHub Release 仍保留并参加 `verify-releases`，不影响已安装包；公开目录不再提供它的下载或更新卡片。
- 这只是**目录隐藏**，不是 GitHub Release 访问控制：历史公开 APK 链接仍可访问。内部人员通过各应用私有仓库中的更新指引下载同签名包并由 Android 系统确认安装。
- 生成目录、CDN 缓存回读和客户端展示分别验证；不得把主线 JSON 更新当成真机已隐藏。

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


## 上海 APK 镜像：运行边界与后续验收（2026-10-22 快照）

本节记录**已执行的结果与明确未通过的 Gate**，不是永久状态；每次改分发地址、签名、DNS 或付费资源前必须重新回读腾讯云控制台、GitHub Release、实际客户端与网络。详细证据：[上海自定义域名验收](https://github.com/xiaoshutong-ai/xiaoshutong-box/pull/27#issuecomment-6341207407)及[Note9 Range 复测](https://github.com/xiaoshutong-ai/xiaoshutong-box/pull/27#issuecomment-6341236418)。

### 当前已交付的候选镜像

- 上海现有 CloudBase 静态托管（`ap-shanghai`，`DIRECT`），公开 HTTPS 域名为 `https://dl.xiaoshutongai.com`，仅开放 `/releases` 路由；未接入额外 CDN/EdgeOne，也不代表生产下载主链已切流。
- 试点镜像：`/releases/baibaoxiang/1.16.1/baibaoxiang-1.16.1.apk`（173,193 bytes，SHA-256 `2dfe985bdc8e3da91b0608894538d4d2698dc3404b09e505e55d0be878aa8173`）；`/releases/fuzipartner/0.2.4/fuzipartner-0.2.4.apk`（95,119,421 bytes，SHA-256 `ae7197b83d5ae22aeead5b6ac75cbad9f10b3ab9ccb9ca58cea0d6b27830d00f`）。镜像是已发布 GitHub Release 的**同一 APK 字节**，不是第二份签名或独立版本。
- 2026-10-22 Note9 / Android 12 的系统 `curl` 在 Wi-Fi 下完整下载并在手机本地核验：两款均 HTTP 200、SHA-256 PASS（观察到约 1.47 秒和 26.47 秒）；测试 APK 已清理，**未安装**。这不等同于百宝箱内部 Android DownloadManager 或全国运营商下载合格。
- **未通过：** 在 Windows 和 Note9 上对上述镜像请求 `Range: bytes=0-1023`，均得到 HTTP **200**、无 `Content-Range`，而非 **206 Partial Content**。即使响应包含 `Accept-Ranges: bytes`，也不得宣称支持断点续传。大 APK 下载中断可能从头重新传输；当前镜像为受控试点/备用候选，不是自动预备首选源。

### 免费上海目录镜像：同步与防止过期（2026-10-23 新增）

**职责**：GitHub main 的 versions.json 始终是唯一权威公开目录；上海现有 CloudBase DIRECT 只存放一份相同字节的被动镜像，供百宝箱 1.16.3/code20 源码候选的 Java 网络故障回退。固定访问地址：https://dl.xiaoshutongai.com/releases/catalog/versions.json（同路由只有版本目录及 SHA256SUMS.txt）。没有购买 COS/CDN、增加域名、改变 GitHub Releases、正式 apkUrl 或分发事实源。

2026-10-23 可重复验收快照：公开目录 8 款、552263 字节，SHA-256 **21dfafd5d4b2024517c410eca9c5f9b10aab9b5eb6df4119dcf74ce6d0f6b631**，updatedAt **2026-10-23T00:27:34Z**。从官方 main 读出后上传至现有上海 CloudBase；Windows HTTPS 完整 GET、Note9 系统 curl 完整 GET+sha256sum 以及 Note9 Android Java 原生 HTTP 请求均返回 200，前两种全量哈希与官方一致。Note9 Java 对 jsDelivr / GitHub Raw 的 SocketException 解释了第三源用途，但不等于 1.16.3 真机 App 验收。当前已安装 Note9 仍为 1.16.2/code19；公开 Release 仍为 1.16.1/code18。

**今后每次正式目录更新**须按以下操作：

1. 先通过仓库原有 manifest→generate→check→verify-releases→PR/review→merge→purge-verify Gate。GitHub main 最新目录和 Release 仍是唯一权威。
2. 从合入后的 GitHub main 重新取完整版本目录字节，核对 SHA-256、公开数量、隐藏应用排除、根 updatedAt、精确 HEAD；本节旧哈希/数量只是历史快照。
3. 仅在现有免费额度和权限仍合格时，把核实后的完整 versions.json 和对应 SHA256SUMS.txt 上传到既有 commercial-cloudbase-d0a54cf5801 / ap-shanghai 静态托管目录 releases/catalog/。复用现有 CLI 命令 tcb hosting deploy，参数包含 releases/catalog、-e commercial-cloudbase-d0a54cf5801、--region ap-shanghai、--verify、--concurrency 1。临时目录必须只含两份已核实的公开文件。禁止新收费资源、通配桶权限或改 dl DNS。
4. 从公开 HTTPS 重新 GET 上海镜像，比较完整响应 SHA 与官方 main、根 updatedAt 以及 HTTP200；用户可见变更时抽测真实 Android Java。未通过标记上海目录镜像 STALE/NOT_VERIFIED，不得把它当最新版本。GitHub 已通过的独立正式 Gate 不因镜像卡住被伪造或抹掉。
5. 新版 Android 客户端须拒绝 updatedAt 早于当前可靠私有缓存或签名 APK 内置种子的目录，不允许较旧的上海镜像覆写“上次最新”缓存；内置快照仅供展示，离线不创建 APK 下载任务。

不授权新的 APK 签名、再次 Note9 覆盖安装、改变公开下载源或发布新版本。原上海 Range/206 限制、成本与两项到期提醒仍在下文。

### COS 原生下载的独立候选（尚未开通／切流）

- 2026-10-22 只读检查现有 CloudBase 的上海静态存储与普通存储两类底层资源：**外部存储未启用**；从现有 COS 默认端点对已知试点对象执行 HEAD / 小范围读取均返回 **403**，无法证明这些底层桶可直接公开下载，也没有取得 206 验收。**不要为了测试把整个桶、已有身份文件或其他项目对象改成公共读。**
- 腾讯云 [COS GET Object](https://cloud.tencent.com/document/api/436/7753) 官方支持单段 `Range` 返回 **206 + Content-Range**；这是产品能力，不是本项目已经实测通过的结果。
- 腾讯云 [2024 年起的存储桶域名限制](https://cloud.tencent.com/document/product/436/96243)：新桶经**默认 COS 域名**公网下载 `.apk` / `.ipa` 会遭遇 `403 DownloadForbidden`。需先配置受控自定义源站 HTTPS 域名，参考[自定义源站域名](https://cloud.tencent.com/document/product/436/36638)；不必天然购买 CDN，但 COS 直连也有公网下行流量、请求和容量等[费用](https://cloud.tencent.com/document/product/436/53863)。
- 如需要验证独立 COS：先只读核对现有桶的对象归属、ACL、域名绑定与计费归属；不满足则提出**单独低预算试点**与回退方案，待 Owner 另批后使用新的测试子域名和小范围授权。**不得直接改 `dl.xiaoshutongai.com` 现有 CNAME 或增开付费桶/CDN。**

### 两个到期日与免费证书续期

- `dl.xiaoshutongai.com` 的现有腾讯云免费单域 DV 证书于 **2027-01-20 18:59:59（北京时间）**到期。腾讯云[免费证书续期流程](https://cloud.tencent.com/document/product/400/61353)确认**重新申请免费证书本身不收费**；通常到期前 30 天（约 **2026-12-21**）才开放快捷续期。续期是**签发新证书**，必须再次完成域名验证、更新 CloudBase 绑定并以真实 HTTPS 链路复验，不能只看“申请成功”。
- **免费重新签发 ≠ 自动续期/自动部署**。截至本快照未证明该域名已配置免费自动轮换；证书托管、自动续费或收费套餐是另外的产品，不能在未核价和授权时启用。建议到期前 30 / 14 / 7 天检查证书状态、域名验证 TXT、证书部署、链路有效期和失败回退。
- 当前上海 CloudBase **体验套餐**到期时间为 **2027-03-24 23:59:59（北京时间）**；既有记录中自动续费和超额使用均关闭。**SSL 免费 ≠ CloudBase 套餐续期免费**。在此日期前核实套餐费用、资源用量/流量预算及替代承载，未经批准不得续费或打开超额计费。

### 将上海设为首选源前的必过 Gate

1. Release 仍是唯一权威 APK 原件，`apps/*-version.json` 的 canonical `apkUrl`、`sizeBytes`、`sha256`、包名、版本、固定 APK 签名证书与历史版本不得被镜像覆盖。下载页 `preferredInstallPageUrl` 不等于可校验的 APK 直链。
2. 候选 HTTPS 自定义域名必须通过证书主机名/有效期、公网可达、APK 全量哈希和**真正 `206 + Content-Range`**、断线续传/重试/断流，以及用户网络实测；如必须不支持续传，需 Owner 另行明确接受风险并在客户端验证安全的重下合同。
3. Android 客户端目前未把上海域名放入 `isAllowedApkUrl`/`isAllowedExternalUrl` 白名单；**只添加 `preferredApkUrl` 不会生效**。必须另起明确批准的客户端 PR，限制精确域名/路径、校验 SHA-256 / size / package / version / 内置 signer pin / 已装更新签名连续性，保留仅非计费网络、系统安装确认与有界 GitHub 官方源回退。
4. 客户端源码、现有 self-hosted CI、独立审查及 Note9/K40 实际 **DownloadManager** 下载与失败回退验收全部通过后，才能修改 mirror 元数据并按 `generate → check → verify-releases → PR → purge-verify → 真机回读` 上线。
5. 回退优先撤销可选 `preferredApkUrl` 并重新生成/校验/合入/清缓存；不要删除或覆盖已发布 Release 资产，不修改已安装应用的数据/签名，禁止在没有验证时变更线上 `dl` 的 DNS 目标。

## CI / Runner

本仓的校验逻辑已经封装为可重复脚本。若仓库实际分配了现有 self-hosted runner，可直接把这些命令接入薄 workflow；不得为了这类轻量 JSON 检查新增 runner，也不应消耗 GitHub-hosted runner 配额。

发布原则：Git 管理元数据；APK 等二进制制品通过 GitHub Releases 分发；不得把 `apps/*.apk` 提交到 `main`。
