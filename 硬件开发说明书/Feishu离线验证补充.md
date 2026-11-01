## 后续离线依赖验证（2026-10-26）

为模拟现场组件 registry 不可达，在一次 PowerShell 进程内把 HTTP/HTTPS 代理临时指向不可达的本机端口；没有改系统代理。Component Manager 提示 registry 无法连接并跳过依赖更新检查，仍解析出 16 个本地/缓存组件；`idf.py reconfigure` 与增量 `idf.py build` 均成功，固件和分区余量与首次构建一致。

这证明当前仓库已检出的组件、`apps/dependencies.lock` 和 IDF 工具缓存可在 registry 不可达时完成项目构建。测试没有关闭整机网络，因此不等同于全链路物理断网验收；本次也没有烧录。
