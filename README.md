# 小书童·百宝箱 更新分发

小书童全家桶的公开更新索引与安装包分发仓库。

- `versions.json` —— 百宝箱 App 启动时读取的全家桶版本单
- `apps/*-version.json` —— 各应用的独立更新版本单
- GitHub Releases —— 正式 APK 与校验文件（SHA-256）的唯一发布位置
- `apps/` —— 仅保存版本元数据，不保存 APK 二进制

发布原则：Git 管理元数据，APK 等二进制制品通过 GitHub Releases 分发；不得再把 `apps/*.apk` 提交到 `main`。

仅用于分发，不含应用源代码。

> 由小书童发布流程维护；发布新版时先上传并校验 Release asset，再更新版本单。
