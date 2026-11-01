# 故事搭子 · 灵机控制面板

此工程生成灵机平台“04 控制面板”上传的 H5 插件 ZIP。当前目标是用户确认沿用的 **PID 11910**。硬件固件和产品密钥继续由设备固件管理，面板不包含产品密钥。

## 使用与上传

1. 平台进入 **PID 11910** 的产品；先前截图中的 11913 是另一个产品，不能混用。
2. 进入“04 控制面板”→“上传控制面板”，选择 `../outputs/story-companion-panel/故事搭子_PID11910_播放器与3D展示_v4.zip`。
3. 更新记录可填“播放器、主题与3D外观展示”；插件版本填比已发布版本更大的整数，若已发布版本为 3 则填 4。
4. 上传后按平台界面执行发布。官方快速上手文档明确说明插件发布后才生效；本地打包不代表已经发布。
5. 从灵机小程序或 App 绑定并打开 PID 11910 下的设备。H5 需要宿主提供设备身份和访问授权，直接在电脑浏览器打开只会显示等待连接。

手机已实际加载第一版面板并拿到 PID11910 / DID100000817，用户报告设备听懂并回复过一次；持续对话还不稳定。控制面板与平台智能体配置分别管理，设备联网、绑定、语音会话与音乐播放需要分别验收。

## 2.1 日常使用与设计

最终字号统一为页头22px、分组17px、曲目15px、辅助12px，减轻字重并保留至少44px触控区；浏览器检查三主题的实际计算字号。三主题预览以390px CSS宽度、3倍设备像素比输出，避免低分辨率截图被放大后误判UI清晰度。

打开已绑定设备后直接载入分类和曲目，点曲目即可播放；底部固定暂停/继续、上首/下首、停止和队列。搜索当前分类，切分类不改变当前队列；有失败会保留队列，不重复提交。顺序、列表循环、单曲循环、随机通过底栏模式按钮切换；自动切歌依赖匹配的自然结束回报，页面需要保持打开，不采用歌曲时长定时假装完成。

界面使用 Vant4 组件和一致的主题角色，主页面只展示内容和必要反馈。介绍/排障文字移出主流程，PID/DID与版本折叠到设备信息。主题为暖雾紫、夜幕、苔绿；使用 Material HCT 色阶算法生成角色，默认暖米背景、柔雾紫操作色、暖杏/苔绿矢量封面，避免逐按钮挑色。更改基色可运行 `node scripts/generate-themes.mjs` 生成 `src/themes.json`；算法是开发依赖，不进入运行包。

23项交互/布局/身份等检查，加基础对比度和三主题单实例预览两项，共25项浏览器模拟通过；三套主题15组基础文字/操作色对比度最低5.99:1。这不是完整WCAG或弱视临床评估。`player-*-fixture.png` 为虚构曲目的视觉预览，不是云平台或扬声器验收证据。

同一块ESP32-S3已经更新应用段，保留Wi-Fi。真机串口验证暂停state3、继续state2、停止idle及对应事件成功；VB701N流控GPIO38仍持续忙，实际歌曲出声与平台状态转发/自动循环仍待验。见 `../outputs/story-companion-player-firmware/README.md`。设备页新增“3D 外观与打印”入口，弹层内嵌自包含 3D 演示，并提供 3MF 下载；不依赖设备在线状态，也不需要重新烧录。

设计依据：[Material 色彩角色](https://m3.material.io/styles/color/roles)、[官方色彩算法库](https://github.com/material-foundation/material-color-utilities)、[Vant ConfigProvider](https://vant-ui.github.io/vant/#/zh-CN/config-provider)、[WCAG文字对比度](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)。

## 1.1 状态与播放修复

- 第一版将 `online===true` 作为按钮门禁，但实际宿主有时只提供 PID/DID、不提供在线字段，导致曲目可读而播放按钮一直灰色。现在身份匹配、页面连接正常且未收到明确离线时允许用户尝试下发；未知状态继续显示“在线状态未返回”。
- 同时主动查询 `getDeviceOnline`，兼容 `isOnline` / `onlineStatus` / `onlionStatus` 和对象、JSON 状态事件；业务 `status` 的未定义枚举不会猜作在线。SDK 的对象 `!!` 会误判 `{isOnline:false}`，在适配层修正，原 vendor 保持不动。
- 显示“正在提交”→“请求已提交、等待平台回报”→平台报告的播放/暂停/停止状态。资源编号不匹配的旧回报被忽略；HTTP 结果不能替代硬件声音。

## 已实现的调用

| 功能 | 来源与边界 |
| --- | --- |
| PID/DID、设备在线状态、刷新 | 复用 `aiToys.zip` 的 `xjiang-sdk`，只接收宿主真实设备信息；产品身份不匹配时禁用控制 |
| 音量 10..100 | 对齐当前固件 `iot_control_volume.h` 的 SIID=2、PIID=1，即 `prop.2.1`；等待设备属性回报才显示确认，12 秒无回报明确提示未确认 |
| 故事与音乐列表 | 采用模板 `/app/api/resouce/categories` 与 `/app/api/resouce/categories/detail`；显示当前产品已发布的资源 |
| 资源播放 | 采用模板 `/agent-merchant/api/resource/event`，发送 `playerReply/play` 资源事件；平台转发与设备声音仍需实机确认 |
| 最近 20 条对话 | 采用模板 `/app/ws/chatRecord/getConvoList`，只读取当前设备的记录；这不是文本聊天发送接口 |

物模型必须与设备固件一致。目前已核实固件音量为 `prop.2.1`，**尚未读取当前平台 PID11910 的在线物模型**；若面板能打开却无法控制，需先核对平台服务/属性编号。

## 开发与打包

要求 Node.js 18+ 和 PowerShell 7。

```powershell
npm ci --ignore-scripts
npm run build
npm run package
```

`npm run dev` 提供本地界面预览；`npm run preview` 查看生产构建。本地浏览器不模拟真实设备成功。默认构建使用模板的生产 API `https://api.ljyd.cn`；只有目标明确为平台测试环境时才使用 `npm run build:test`。

浏览器模拟验证要求 Node.js 22+、本机 Microsoft Edge，并在另一个终端先运行 `npm run preview`，随后执行 `npm run check:browser`。检查只使用虚构的设备和授权，不连接真实平台或硬件。`panel-preview-host-fixture.png` 是模拟宿主截图，不是实机成功证据。

ZIP 根目录直接包含 `index.html`、`MainPage.html`、`app.json`、`assets/`。保留模板 `app.json` 的 MainPage 入口，同时兼容小程序的 index 入口。打包不包含源码、原始模板、依赖目录、固件或环境凭据。

## 来源与验证

- 原始模板：`D:\MyPro\brainwave\aiToys.zip` 中的 `private-cloud-h5`。`vendor/xjiang-sdk`（1.0.0）与 `vendor/xjiang-ui`（1.1.0）逐文件提取自模板，保留原文；依赖版本取自模板 lockfile。
- 当前固件契约：`../ljyd_xjwb03_agent_public_developer/apps/main/lj_components/iot_control/ctrl/iot_control_volume.h`、`cloud/ljyd_method.c` 与 `playback/README_CN.md`。
- 官方文档：[快速上手：创建你的第一个产品](https://xjiangiot.yuque.com/afahpl/qrhct7/tlq4vfmwt4rw5nt8)。说明控制面板展示状态、执行控制、关联物模型，且插件发布后才生效。
- 新补充：[灵机WEB插件开发流程](https://xjiangiot.yuque.com/afahpl/qrhct7/olekex333e94vvxk)，说明标准面板源码下载、登录后选择小程序已绑定设备、物模型文件和内置 `plugin-generator` 技能及构建上传流程。
- 最新验证结论见 `DEV_STATE.md`。本地构建、宿主模拟与平台实机验收分别记录。

## Wi-Fi 与后续故障记录

- 固件 `qm_wifi_dev_set_config()` 把 Wi-Fi 配置同步保存到 `wifi_cfg` KV/NVS，正常重启会读取它；网页不保存 Wi-Fi 密码。
- 之前为恢复 BLE 扫描主动执行过一次 `provision clear`；这会删除旧 Wi-Fi 并重新广播。已有 Wi-Fi 时固件默认跳过 BLE，所以扫码失败不等于固件被烧坏。
- 手机打开面板后，COM5 已观察到 MQTT 心跳响应；这说明该时刻云连接通，但不单独证明 Agora 会话或音乐可用。
- 语音曾成功回复一次为用户报告。后续只读日志捕获 `running→error / agora disconnected`，约 8 秒后 `error→running / agora connected`。根因尚未确定，不以网页按钮修复宣称语音稳定问题已解决。
