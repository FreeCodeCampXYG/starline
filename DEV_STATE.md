# DEV_STATE

更新时间：2026-11-01

## 机器人 3D 设计演示

- 用户明确以提供的白色机器人图作为外观约束，圆润白壳、黑色笑脸、胸前摄像头和短手臂均需保留；飞碟图只是询问 3D 代码演示的例子。
- 当前先完善讲解演示，用户时间有限，不想安装学习切片软件或立即打印。新增 v2 入口 `outputs/story-companion-design-v2/打开故事搭子设计演示.html`；初版在 `outputs/story-companion-reference-3d/` 保留。
- v2 包括四组配色/自定义机身与眼睛色、整机、拆解、真实机壳三段剖切、内部占位、虚拟摆盘、逐层几何截面与自动播放、原图对照、PNG 导出。轮廓用连续曲线和平滑放样，补充材质、接缝、胸前固定耳和手臂套筒；仍未达到原图逐细节一致。
- Edge 桌面与 390 px 布局、六视图、四套不同颜色、自定义色、原图开关、PNG、截面播放/离开停止及离线无网络请求检查通过。剖切时验证闭合和体积守恒；随包为 GLB/3MF 外观预览和生成源码。3MF 不是 `.gcode.3mf` 机器路径，未在 Bambu Studio 切片、试装或打印，内部和背面均保留示意状态。
- 生成代码：`tools/robot_companion_design_v2.py`、`tools/robot_companion_design_v2.html`，复用 `tools/robot_reference_demo_3d.py` 的几何基础函数；Python 环境在 `outputs/robot-companion-3d/.venv/`。
- 早期 `outputs/robot-companion-3d/` 外观偏方且部分孔位只是视觉占位，已标记为停用草稿。后续需先核对外观，再测电子模块并设计真实固定、声道与拆装结构。

## 故事搭子播放器当前状态（2026-10-31）

- 最新任务定位：用户明确当前为研究原型，尚未确定最终产品方向；优先连续语音、真实播放/切歌/停止和工具结果的可靠反馈，缺少健康资料时如实说明。摄像头尚未插且用途未定，暂不接入；播放器页面为辅助界面，此前桌面/坐姿方案仍为未确认候选。
- 用户目标：面向终端用户的完整播放器，苹果式排版；不喜欢鲜红和单调蓝灰。最终使用Material HCT语义色阶生成暖米/柔雾紫主界面，暖杏/苔绿SVG封面，主题为暖雾紫/夜幕/苔绿。去掉介绍横幅与重复引导，设备ID/版本折叠到设置；灯光暂不加入，后续按真实反馈需要决定。
- 主功能：分类自动载入/当前分类搜索、播放/暂停/继续/停止、上首/下首、完整队列、顺序/单曲/列表循环/随机、皮肤/模式记忆。保留设备音量与对话记录；未知在线状态可尝试、明确离线或身份不匹配禁写。自然结束回报与停止/错误分开，自动续播只在页面可见并收到匹配完成事件时执行。
- 最新网页：outputs/story-companion-panel/故事搭子_PID11910_播放器与主题_v3.zip，154462 bytes，SHA256 992E712D50E0DEAC8108BC2C27C2A5B9653DAAC6C6C1016CD5825E76EBA2BB8D。页面2.0，平台版本需递增（旧2填3）。生产构建与25项浏览器模拟通过；15组基础对比度最低5.99:1，非完整WCAG/医学评估。三主题截图为测试数据预览。
- 当前硬件：PID11910/DID100000817；COM5 ESP32-S3尾号B5:8C，2026-11-01 仅更新0x20000应用段，Hash verify通过，Wi-Fi/NVS保留。当前镜像3215392 bytes、SHA256 `36A053E088EAC23AD0668640CB341ACCEC2010562BFAB20D02CCFE1760B9096F`，IDF5.4.1/基线89020f5e，约22%分区余量；启动后 `voice status cloud=1 started=0 state=ready`。
- 固件：新增player/pause|resume|stop异步worker与player/report，修复迟到终态清理新任务、release busy丢句柄、VB701N暂停/继续ENOSYS；新增用户提供的4.64秒启动语音。根因已确认：VB701N 未声明物理 DRAIN，音频引擎之前在等待渲染队列前就返回 `-QM_ENOSYS`，Service 随即停止 worker，可能截断长启动音。引擎现等待所有已接受帧完成 UART 写操作后，再报告物理播放回执不支持；IDF构建及应用段 Hash verify通过，已刷COM5。日志确认 `local audio submitted frames=232; speaker completion is unconfirmed`，重启后云连接正常；扬声器实际听感仍待用户确认。GPIO38 busy 是传输限制线索，未猜改有效极性。修复包在`outputs/story-companion-player-firmware/灵机_PID11910_启动语音播放修复_应用升级_20261101.zip`。
- 用户指出此前反馈倾向不要改音频代码；当前应用已经包含共享 `qm_audio` Engine 改动并已刷写。后续暂停音频实现修改，只做日志、命令链路和硬件核对。
- 当前启动 PCM 峰值约 `-6.0 dBFS`、RMS 约 `-23.4 dBFS`，排除源文件全静音；音量日志为 15/硬件值4，但是否足够响尚无听感证据。当前驱动将 GPIO38 配为输入下拉，板卡 Skill 表格却标输出，主板原理图/实物映射缺失，方向与极性待核。COM5 本轮 2 秒被动读取没有新日志。
- Wi-Fi由wifi_cfg KV/NVS持久化，普通重启读取。2026-11-01 用户从家用 Wi-Fi 换到其他网络后，COM5监听确认设备持续断连且 `cloud=0`；清除旧配置后按用户指定的 `INTERCITYHACK-NB-PLAYER-2.4G` 重新配网，设备日志确认 `wifi got ip`、动态注册 DID `100000817`、MQTT 订阅成功和 `cloud connected`，只读 `voice status` 返回 `cloud=1 started=0 state=ready`。密码未写入状态文档或记忆。用户曾听懂回复一次为用户报告，日志捕获过Agora断开约8秒后恢复；连续对话根因仍待查。
- 配网回退修复：`apps/main/cloud/ljyd_provision.c` 新增连续 10 次 Wi-Fi 失败后自动清理旧配置并重启进入 BLE 的兜底，已包含于当前 COM5 应用镜像；10 次失败自动回 BLE 尚未做真机回归。
- `qm_audio` 新增无物理 DRAIN 时等待已接受渲染写入的回归用例。宿主测试链接被 Windows MinGW 缺少 `sys/select.h` 阻断，未实际运行；IDF 5.4.1 全量应用构建通过。
- 下一步：待下一次实际 `player/play` 下发时被动捕获 MQTT 分发、PCM URL 获取、音频事件和 UART 流控日志；核对音频板供电/排线、GPIO38 实际电平及音量。后续按用户偏好不改音频实现；另做 Wi-Fi 回退 HIL 和 Agora/ASR/TTS 验证。MQTT 应答和帧提交都不能代替真实听感。

## 故事搭子 3D 面板入口（2026-11-01）

- 控制面板设备页新增“3D 外观与打印”入口，使用自包含 Three.js 演示页和 3MF 下载文件；弹层不依赖设备在线状态，不需要重新烧录。
- 交付包：`outputs/story-companion-panel/故事搭子_PID11910_播放器与3D展示_v4.zip`，2,237,831 bytes，SHA-256 `ACCDDAC6A24D4743D7A2B507045F7F40952F893185AC0573C81A802486CF1A78`；面板内显示版本 2.1，平台插件建议填 4。
- 验证：Vite 生产构建和 ZIP 结构/大小校验通过；真实平台发布和手机 WebView 现场打开待用户侧确认。
## 海报最新状态（2026-10-31）

- 用户更换 API 后，按 `gpt-image-2-5-api` 技能指定 Sunburst/high，携带机器人、头像、构图参考和真实主板四张参考图，两次编辑请求均成功，未再出现 HTTP 403。
- 产物位于 `outputs/gpt-image-2.5/`：`story-companion-api-retry-20261031.png` 与 `story-companion-api-resolution-check-20261031.png`，均已打开检查；请求分别为 1664×3744、1536×3456，实际均为 836×1881、4:9。已无损封装同文件名前缀的 `-80x180cm.pdf`，均为单页 800×1800 mm、RGB、无额外出血；尺寸、原图像素一致性和渲染外观检查通过，清晰度未提升。
- 当前是两张产品概念预览，按 800×1800 mm 输出仅约 26.5 PPI，尚未达到高精度印刷目标；下一步需取得更高分辨率主视觉并矢量排字。详情见 `outputs/gpt-image-2.5/README-20261031.md`。旧接口 403 原因未知，不认定内容违规或必然缺少编辑权限。

## 当前目标

围绕灵机 ESP32-S3 组合开发板 SDK、所给模块资料和飞书配件说明，建立可复用的板级硬件 Skill、初学者开发说明书和飞书分析文档。

## 已完成

- 获取 Gitee `master` 提交 `89020f5e04bf777ae1672b8f3d320bc6e0ef3e0c`；有效仓库位于 `ljyd_xjwb03_agent_public_developer/`，使用 `blob:none` 浅 partial clone；构建所需路径已稀疏检出，对象包约 244.53 MiB，Git 工作树干净。
- 创建全局 Skill `C:\Users\xiaoy\.skills-manager\skills\ljyd-xjwb03-board-cy`，并创建 `C:\Users\xiaoy\.codex\skills\ljyd-xjwb03-board-cy` junction；包含证据规则、项目结构、固件引脚/复用、外设原理、排障、来源地图和触发评测。
- 创建 `硬件开发说明书/`，包含项目身份、硬件原理、模块原理、作品开发路线、坑点、证据缺口和可上传飞书的图文版。
- 飞书《灵机一动硬件黑客松》由 revision 7 更新到 revision 11；回读含 21 个标题块和 8 个图片块，身份、电平、安全和 registry 离线验证说明均存在。
- 项目 IDF 5.4.1 的 S3 工具安装在 `%USERPROFILE%\.espressif`，Python 环境为 `idf5.4_py3.12_env`；原有 `C:\Espressif` 的 IDF 5.5.5 未改动。
- `esp-idf/export.ps1` 激活后 `idf.py build` 成功，生成 `apps/build/vb701n.bin`（3,116,912 bytes），最小应用分区约 25% 余量，flash_args 含 6 个镜像。
- 已将该既有构建（ESP-IDF 5.4.1，commit `89020f5e`）打包为 `灵机VB701N_ESP32-S3_本地烧录包_89020f5e.zip`（SHA-256 `90c73716e6842139102f98c86f7abe97e6cb0e8bf4a0cf5fa2006e4bab5e6dbf`）；首次编译发生于 2026-10-26，本轮未重编译或烧录。`D:\MyPro\easyinput-flasher\build\bin\easyinput-flasher.exe` 已增加本地 ESP32-S3 manifest ZIP 导入与逐段回读验证。
- 新增 [本地固件烧录说明](硬件开发说明书/08_本地固件烧录.md)，包含包路径、六段地址、导入和手动板型核对要求。
- HTTP/HTTPS 代理在本进程指向不可达本机端口时，Component Manager 报 registry 不可达但仍解析本地/缓存组件；`idf.py reconfigure` 和增量 build 成功。该模拟没有关闭整机网络。
- `D:\MyPro\brainwave` 本身没有 Git 元数据；Git 状态只针对其下的 SDK partial clone。

## 关键结论

- SDK/手册称主板 `XJWB03-DevKIT-V1`，主板照片/配件说明称 `LJWB76-DevKIT-V1`；音频模块也有 KIT/Core 名称差异，映射尚未确认。
- 主板完整原理图、BOM、Gerber 和装配修订未提供；GPIO 表只作为当前固件声明，不是物理走线合同。
- README/手册与当前 `qm_config.h`、`partitions.csv` 有配置差异；以指定提交的实际配置文件为当前 build 输入参考。
- 公开 README 有明文云端密钥风险；未在任何新文档复制，需维护者核验轮换。

## 验证与限制

- Yao `validate_skill.py`、`resource_boundary_check.py` 通过；触发评测 13 例，误触发/漏触发均为 0；初始加载估算 778 tokens。
- 本地说明书 Markdown 链接检查 31 项，0 个失效；飞书 revision 11 回读 21 个标题、8 张图片和离线验证补充均存在。
- IDF 5.4.1 应用于 2026-10-26 构建成功；registry 不可达模拟下 reconfigure/build 也成功。该日尚未烧录。
- 自定义烧录包已由 Python ZIP 校验和 EasyInput Flasher Go 导入集成检查；Wails Windows x64 构建成功。2026-10-31 在用户授权下对 COM5 实烧，fresh ROM 验出 ESP32-S3 rev0.2、尾号 B5:8C、JEDEC 16 MB，六段 esptool hash verification 均通过，未整片擦除。
- 写后串口 115200 两次采集 20 秒均为 0 字节，RTS 复位效果无法证明；其后 esptool 与当前 Flasher `Runner.Inspect` 的 NoReset ROM 探测均失败，最新错误为 `failed to sync with ESP bootloader after 3 attempts`。本次没有复位或写入；芯片/MAC 当前未读、应用/ROM 状态仍未知。当前未做功能/HIL；XJWB03/LJWB76 PCB 版次映射仍待确认。
- 2026-10-31 正常运行态串口监听收到设备持续 Wi-Fi 重连：`reason=1`（QUMI 枚举为未找到 AP），期间一次 `reason=6`（DHCP 超时）；未出现 `wifi got ip`、`cloud connecting` 或 `cloud connected`。电脑当前连接现场 WLAN `INTERCITYHACK-NB-PLAYER-2.4G`，本机 IPv4 为 `10.20.0.89`。因此当前不能下发 `player/play` 或验证 PCM 播放，需先重新配网。
- 2026-10-31 通过 COM5 发送 `provision clear` 成功；新增的 `provision set <ssid> <password>` 命令随后直接写入现场 Wi-Fi。设备取得 IP `10.20.0.168`，动态注册 HTTP 200，MQTT 连接成功并注册 `player` 下行方法，云连接链路已通过。
- 为绕过云平台控制，固件新增 `play_url <http://...pcm>` CLI；应用构建和 COM5 应用段写入/Hash verify 通过。电脑生成 2 秒 16 kHz 单声道 S16LE PCM，HTTP 服务监听 `0.0.0.0:18080`；设备已接受 `play_url`、进入 `tcp connect`，但 Windows Public 防火墙拒绝 18080 入站，Python HTTP 服务尚未收到设备请求，音频播放完成尚未确认。
- 2026-10-31 产品身份已切换到平台 PID `11910`；仅更新应用段并 Hash verify。重启后日志确认 `wifi got ip`、动态注册 DID `100000817`、`iot start ok`、`cloud connected`，说明设备已按新产品身份注册。最终包：`D:\MyPro\brainwave\灵机VB701N_ESP32-S3_PID11910_USB配网播放CLI烧录包_89020f5e.zip`，SHA-256 `BF809AF3F47B10C06CAF70BFF7EE1B6F49BB501FDEE4DE392680CBE8D6AE12C1`。
- 2026-10-31 新增 `volume <10..100>` CLI；构建成功，应用段 COM5 写入和 Hash verify 通过。设备回显 `hw vol=30`、`volume: set 30 and saved`，音量值写入 NVS。生成 232224-byte 原创旋律 PCM，设备请求电脑当前 IP `10.20.0.182:18080` 成功；HTTP 200 返回完整文件，设备日志有首音频帧和 VB701N TX，但播放时报告 flow-control pin 38 busy，完整旋律出声待用户听感确认。最终包 `D:\MyPro\brainwave\灵机VB701N_ESP32-S3_PID11910_音量与音乐测试CLI烧录包_89020f5e.zip`，SHA-256 `2D5DA7B9921C220CB98E61D37E42041954D91E7A7E5962B732B501C0E0235D0`。
- 截图根因复核：CH340 的 COM5 曾被 Flasher 误标为“下载模式”；通用串口现显示“模式待验身”，只有 ROM 同步成功才确认下载模式。用户按 BOOT + RESET 后被动监听确认 `DOWNLOAD(USB/UART0)`，正式 Flasher 关闭 DTR/RTS 后读到 ESP32-S3、MAC 尾号 B5:8C、Flash ID 0x4018、16 MB。新版 exe 已重建；应用功能/HID 仍待验证。
- 仓库 `dev.bat` 写死 `idf5.4_py3.14_env`，与实际安装的 `idf5.4_py3.12_env` 不一致；已验证的入口是 PowerShell `esp-idf/export.ps1`。
- Yao 统一 CLI 的 update-check 在当前 Windows Python 上因 `fcntl` 导入失败；独立结构、资源边界和触发评测脚本可运行。
- Skills Manager `adopt` 不接受 source 与目标相同的 manager 内目录；为保证 Codex 可加载，已按现有 EasyInput Skill 的目录方式创建并验证 junction。Skills Manager 数据库本身尚无该 Skill 记录。
- 首次完整浅克隆传输过慢而停止，现场保留为 `ljyd_xjwb03_agent_public_developer_incomplete-transfer/`；有效 partial clone 后续已检出当前应用构建所需源码、组件和模型，但仍不是完整 Git 历史。

## 下一步

1. 请硬件负责人确认 XJWB03/LJWB76 与 LJX40 KIT/Core 的板卡版本映射，并提供主板原理图/BOM/装配版本。
2. 对照实物核实相机 24 MHz、舵机型号/脉宽、振动模块有效电平和 WS2812 数据电平。
3. 由仓库维护者处理公开 README 的云端密钥轮换和历史暴露审查。
4. 若现场要求严格断网验收，在隔离网络条件下再跑一次增量构建。
5. 请硬件负责人确认板名映射、主板原理图和外设参数；密钥轮换、烧录/HIL 另行授权并验证。
6. 用户使用电源开关完全断电再上电后，重新采 COM5 启动日志并观察板上功能；不把当前无串口字节写成固件未启动。

## 市场调研与公开用户反馈（2026-10-26；渠道补查 2026-10-27）

- 调研报告：`灵机一动市场调研_2026-10-26.md`。结论区分小匠物联的 B2B IoT 业务与灵机一动 Agent 平台；GDPS 现场“灵机一动”黑客松与 INTERCITY HACK 宁波站赛道分别核实，后者是灵机一动冠名赞助，不是整场活动主办。
- 独立交付 `Anker黑客松与跨平台用户痛点调研_2026-10-27.md`，覆盖活动目的/赛制、获奖原型、财报口径、B站互动、录音豆体验与官方 GitHub issue；OntoCare 指标已按团队仓库更正为原型评测口径。主报告第 7 节链接至专题报告。
- GDPS 报道称近百人参加，采用 7 天工作坊、线上开发、线下真机快闪、不设固定赛道并投票排名；公开作品方向包含儿童情绪选择+机器狗动作回应和“最后10米找车位”想法，后者未确认完成原型。报道提及控制指令连接失败后靠查文档解决。
- 2026-03 公开生态招募公告计划招募 100 位开发者、5 家服务商，提供魔盒、平台内测、案例曝光和合作推荐；可支持开发者/服务商生态拓展推断，实际报名、活跃和商务转化未公开。
- Anker 对照补查：2026 年公开资料至少找到两种不同目的的黑客松式活动：8 月 MKT 设计校招挑战（依据第三方招聘聚合页，原始公告待核）与 9–10 月公司称“首届”的 AI 硬件挑战赛，不代表同一赛制已办多届。后者赛后记录 1800+ 报名、33 队/116 人现场；“举手豆”“驿站追迹”“电小鱼”和 OntoCare 对应录音、安防、储能、售后。组织者称赛题来自内部场景、SDK开放和真实 VOC；创造者社区/API/MCP/平台是计划，不等于已上线或商业转化。
- 项目指标边界：OntoCare 公开仓库将 83.8%→98.6%界定为 74 个核心任务单轮硬断言通过率，基础资料含 63 条脱敏工单；不是生产客服解决率。安克 2025 年报总营收 305.14 亿元，充电储能/智能创新/智能影音三大类分别占 50.47%/27.11%/22.39%；不可拆分为 SOLIX 或录音豆单品营收。
- 跨平台痛点：B站安克黑客松复盘约 1.77 万播放、3400 赞、14评；两条热评质疑 prompt/算法真实含量，属小样本观众信号。录音豆高互动 B站比较视频有 20.4 万播放/144评、12.6万/59评等，但详情/评论正文未读，不能从标题推断正负。
- GitHub 信号：AnkerInnovations 官方 SDK Demo 的 issue 报中国区双击 Marker 无效、SDK/固件兼容和 app_id/key/license 获取不清；其中 Marker 功能与“举手豆”交互直接相关，单条未复现报告。Anker 官方 SOLIX HA 集成 issue 中，Solarbank 3 本地 Modbus请求 18评/24 reactions 且以 not planned 关闭；Max AC 断网 issue 67评仍 open、E5000 同类 issue 43评。技术社区集中反映本地/离线控制、旧型号支持和能源调度问题，不代表全体零售用户。
- 录音豆线索：定价 ¥899；媒体 2026-01 报道引用京东计数称销量破千，京东类目多 SKU 评论数有 48、79、1000+ 等差异，不可合并。第三方淘宝聚合有少量正评；一条买家帖抱怨额度/后续成本。独立评测另指出专有词准确度、磁吸夹持、Web回听/搜索等摩擦；低频用户月转写 148/226 分钟则反馈免费额度够用。官方权益为绑定后 6 个月每月额外 1200 分钟/25 篇纪要，免费额度另叠加。
- Anker 飞书获奖清单/赛后文字记录由当前授权账号读取，但对权限设置的查询返回 permission_denied，未认证为匿名公开文档；录音豆媒体/京东/聚合评论计数也不构成完整销量或口碑样本。
- 渠道补查：LINKY 官网目录列出 G01 Ultra（4G 双向通话版，型号 G01 ultra）¥558，另列鸿蒙版 ¥468；这是品牌目录/询价信息，不是交易量证据。京东可见 LINKY 物联款商品编号 10209363374974，当前类目显示 0+ 评论；另一个泛型号页面快照出现 80 人评价，商品版本和计数口径不一致，评论正文未能读取。
- 公开反馈边界：找到 2023 LINKY G01 旧款的独立体验问题，但不是灵机平台/2026 G01 Ultra 的买家评论；当前 G01 Ultra 的买家评论正文和销量仍未核实。Gitee `xj-open` 组织页及公开 SDK 仓库是代码托管/问题跟踪入口，不是独立论坛；仓库 API 为 0 issue、5 watchers、0 star、0 fork，组织联系字段无可用邮箱。淘宝/闲鱼/1688/小红书公开索引未发现可归因条目，平台站内内容未知。Feishu CLI 可读到赛题/手册，但匿名 HTTP 访问跳转登录、共享文档权限查询被拒绝，未将其标为公开文档。
- 通用 Skill：`C:\Users\xiaoy\.skills-manager\skills\company-market-intel`；新增跨平台社媒/视频/GitHub 用户痛点参考、互动快照与匿名化/访问阻断规则；Codex junction 指向 manager 源。
- 验证：Yao `validate_skill.py`、`resource_boundary_check.py` 通过；20 条触发/负向/近邻用例 0 误触发、0 漏触发，入口加载估算 938 tokens。Yao 统一 update-check 仍受 Windows Python 缺 `fcntl` 阻断，本轮未运行全套 Skill OS 发布门禁。
- 遗留：灵机 GDPS 仍缺最终作品清单、评审明细、匿名用户调查、平台激活/留存及赛后合作转化；京东物联款与 G01 Ultra SKU 映射、真实成交/售后和评论正文待核。Anker 参赛原型是否量产、活动转化和录音豆累计销量未独立验证。X 搜索跳登录、YouTube 返回429，未获取评论正文；B站高互动产品视频只得搜索元数据。GitHub/HA issue 以技术用户为主，不能外推全体消费者。
- 下一步：取得灵机活动方赛后指标；向 LINKY/灵机确认 SKU 与成交售后；访谈开发者、品牌方和终端用户。设计活动时可参照 Anker 的真实产品 SDK、授权脱敏数据和明确评分/赛后承接，但须按灵机现有平台能力另行验证。

