## 现场离线编译准备（2026-10-26）

本次已补齐 SDK 的主要构建依赖目录：`apps/`、`components/`、`apps/managed_components/`、`esp-idf/`、`qumios-dev/`、`tools/`、`idf_patches/` 和姿态识别模型。`components/` 主要是应用集成的第三方/平台组件，包含组件源码和部分预编译库；`apps/managed_components/` 是组件管理器依赖，例如 MPU6050、WS2812、相机、图像和音频组件。它们是应用构建依赖，不是烧录后的单个固件程序。

当前 SDK 锁定 ESP-IDF 5.4.1。机器原有 `C:\Espressif` 是 IDF 5.5.5 / Python 3.12 环境，本次保持未改动；另将 5.4.1 的 ESP32-S3 工具和 Python 3.12.7 环境安装在 `C:\Users\xiaoy\.espressif`，环境名为 `idf5.4_py3.12_env`。

已验证 PowerShell 构建方式：

```powershell
Set-Location 'D:\MyPro\brainwave\ljyd_xjwb03_agent_public_developer'
$env:IDF_TOOLS_PATH = "$env:USERPROFILE\.espressif"
. .\esp-idf\export.ps1
Set-Location .\apps
idf.py build
```

本机全量应用构建成功，生成 `vb701n.bin`（3,116,912 bytes）；应用分区约 25% 空间余量，`flash_args` 包含 6 个镜像，其中有 `0x810000` 的姿态模型。**没有执行烧录或设备操作。**

注意：仓库 `dev.bat` 固定查找 `idf5.4_py3.14_env`，和本机已准备的 3.12 环境不一致；本轮没有修改脚本，现场按上面的 PowerShell export 路径构建。后续 registry 不可达的代理模拟和增量构建结果见单独补充；整机物理断网尚未测试。
