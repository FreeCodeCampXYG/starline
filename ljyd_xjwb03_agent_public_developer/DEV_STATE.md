# DEV_STATE

更新：2026-11-01

- 目标：PID11910 故事搭子同时支持 Agora 实时对话和云端播放器；真实声音输出仍未验收。
- 当前设备：COM5 ESP32-S3 尾号 B5:8C。当前应用镜像 `apps/build/vb701n.bin` 为 3,215,392 bytes，SHA-256 `36A053E088EAC23AD0668640CB341ACCEC2010562BFAB20D02CCFE1760B9096F`；只更新 `0x20000` 应用段，Wi-Fi/NVS 保留。`voice status` 为 `cloud=1 started=0 state=ready`。
- 音频证据：CodeGraph 显示开机音在 `boot_sound.c` 直接申请本地 `qm_audio` 会话；MQTT `player/play` 走方法分发、播放器 worker 和 PCM URL，再申请同一音频服务。两者最终共用 QUMI Engine 与 VB701N UART/GPIO38 流控后端。
- 已知限制：VB701N 后端明确没有扬声器物理播放完成回执；旧 Engine 在待写帧处理前返回 `-QM_ENOSYS`。当前 Engine 等已接受帧和在途设备写入完成后才报告物理完成不可确认。新日志仅证明 232 帧已提交到设备接口；GPIO38 busy 仍出现，用户报告刷写重启后没有开机声音，实际声学输出仍未确认。启动 PCM 峰值 `-6.0 dBFS`、RMS `-23.4 dBFS`，不是静音数据；日志音量为 15、硬件值 4。
- 硬件资料冲突：当前 VB701N 驱动将 GPIO38 配为输入并启用下拉，代码按高电平判 busy；板卡 Skill 引脚表写成输出。主板原理图和实物修订映射缺失，方向/极性以实板核对前均待确认。COM5 本轮仅做 2 秒被动读取，没有新音频日志。
- 当前边界：用户指出此前反馈倾向不要修改音频代码。后续先只做日志、链路和硬件核对，暂停音频实现改动；不得猜改 GPIO38 流控极性。
- 其他状态：连续 10 次 Wi-Fi 失败后回退 BLE 的逻辑已包含在当前应用镜像，尚未做对应 HIL。IDF 5.4.1 应用构建及刷写 Hash verify 通过；新增 `qm_audio` 宿主回归测试未运行，Windows MinGW 缺少 `sys/select.h` 导致链接失败。
- 下一步：待下一次实际 `player/play` 下发时被动捕获 MQTT 分发、URL/PCM 获取、音频事件和 UART 流控日志；同时核对音频板供电、排线与 GPIO38 实际电平。不能用 MQTT 应答或帧提交日志代替听感验收。
