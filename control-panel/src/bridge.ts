import { computed, reactive } from "vue";
import XJIotSDK from "xjiang-sdk";

export const PRODUCT_PID = 11910;
const VOLUME_PROPERTY = "prop.2.1";
const sdkConfig = {
  type: "wifi" as const,
  basicConfig: { defaultData: false },
  info: { displayName: "故事搭子" },
  data: { voice_Volume: { key: VOLUME_PROPERTY, value: null } }
};

type DeviceInfo = {
  pid?: number | string;
  did?: number | string;
  deviceName?: string;
  onlionStatus?: unknown;
  [key: string]: unknown;
};
type HostHeaders = Record<string, string>;

export const panel = reactive({
  info: {} as DeviceInfo,
  online: null as boolean | null,
  connected: false,
  reportedVolume: null as number | null,
  volumePending: false,
  volumeMessage: "尚未收到设备音量",
  playbackMessage: "",
  playbackResourceId: null as number | null,
  playbackRevision: 0,
  playbackStatus: "",
  playbackPosition: 0,
  hostMessage: "请从灵机小程序或 App 打开已绑定的设备",
  identityEpoch: 0
});

let sdk: XJIotSDK | null = null;
let finishVolume: ((error?: Error) => void) | null = null;
let volumeTarget: number | null = null;
let volumeTimer: ReturnType<typeof setTimeout> | undefined;
let headersPromise: Promise<HostHeaders> | null = null;
const hostWindow = window as any;
export const isMiniProgram = hostWindow.__wxjs_environment === "miniprogram" ||
  (hostWindow.__wxjs_environment === undefined && /MicroMessenger/i.test(navigator.userAgent));
const hasHost = isMiniProgram || typeof hostWindow.ReactNativeWebView?.postMessage === "function";

export const productMatches = computed(() => Number(panel.info.pid) === PRODUCT_PID);
export const canControl = computed(() => Boolean(
  // 实机宿主可能不回在线字段；未知状态允许用户尝试下发，明确离线及身份不匹配仍禁止控制。
  sdk && panel.connected && productMatches.value && panel.info.did && panel.online !== false
));

function asOnline(value: unknown, depth = 0): boolean | null {
  if (value === true || value === 1 || value === "1" || value === "true") return true;
  if (value === false || value === 0 || value === "0" || value === "false") return false;
  if (typeof value === "string") {
    const text = value.trim().toLowerCase();
    if (text === "online" || text === "true") return true;
    if (text === "offline" || text === "false") return false;
    if (depth < 3 && text.startsWith("{")) {
      try { return asOnline(JSON.parse(value), depth + 1); } catch { return null; }
    }
  }
  if (value && typeof value === "object" && depth < 3) {
    const record = value as Record<string, unknown>;
    // 只解释语义明确的在线字段，不把业务 status/code=0 或未定义枚举当作在线证据。
    for (const key of ["isOnline", "online", "onlineStatus", "onlionStatus"]) {
      if (key in record) {
        const result = asOnline(record[key], depth + 1);
        if (result !== null) return result;
      }
    }
    for (const key of ["device", "data", "params"]) {
      if (key in record) {
        const result = asOnline(record[key], depth + 1);
        if (result !== null) return result;
      }
    }
  }
  return null;
}

function applyOnline(value: unknown) {
  if (typeof value === "string" && value.trim().startsWith("{")) {
    try { value = JSON.parse(value); } catch { return; }
  }
  if (value && typeof value === "object") {
    const info = value as DeviceInfo;
    if (info.did !== undefined && String(info.did) !== String(panel.info.did)) return;
    if (info.pid !== undefined && Number(info.pid) !== PRODUCT_PID) return;
  }
  const online = asOnline(value);
  if (online !== null) panel.online = online;
}

function applyPlayback(value: any) {
  // 平台回报必须匹配本次选中的资源；过期资源的状态不能覆盖新一次播放请求。
  if (!value || Number(value.resourceId) !== panel.playbackResourceId) return;
  const labels: Record<string, string> = {
    playing: "平台回报：正在播放",
    paused: "平台回报：已暂停",
    stopped: "平台回报：播放已停止",
    completed: "曲目播放完成", ended: "曲目播放完成", finished: "曲目播放完成", error: "设备报告播放失败"
  };
  let state = value.playStatus;
  if (state === "stopped" && ["completed", "finished", "ended", "eof"].includes(value.reason)) state = "completed";
  if (typeof state === "string" && labels[state]) {
    panel.playbackStatus = state;
    const position = Number(value.positionSeconds ?? Number(value.positionMs ?? 0) / 1000);
    if (Number.isFinite(position) && position >= 0) panel.playbackPosition = position;
    panel.playbackRevision++;
    panel.playbackMessage = labels[state];
  }
}

function installHostCompatibility() {
  if (!sdk) return;
  if (isMiniProgram) {
    const api = sdk._weappApi;
    const original = api.onMessage.bind(api);
    api.onMessage = (message: any) => {
      if (["onDeviceOnline", "getDeviceOnline_reply", "reportDeviceStatus"].includes(message?.method)) {
        const value = message.params ?? message.data;
        applyOnline(value);
        // 模板把整个对象 !! 转为 true，会误读 {isOnline:false}；在线事件在适配层完成解析。
        if (message.method === "onDeviceOnline") return;
      }
      original(message);
    };
  } else {
    hostWindow.xj.onDeviceOnline = applyOnline;
    hostWindow.xj.getDeviceOnline_reply = applyOnline;
    hostWindow.xj.reportDeviceStatus = applyOnline;
    hostWindow.xj.player = (value: any) => applyPlayback(value?.params ?? value);
  }
}

function applyInfo(info: DeviceInfo) {
  // 身份变化会使正在等待的回执失效；保留面板草稿，禁止用另一台设备的回报确认旧请求。
  if ((info.did !== undefined && String(info.did) !== String(panel.info.did)) ||
    (info.pid !== undefined && String(info.pid) !== String(panel.info.pid))) {
    panel.identityEpoch++;
    panel.reportedVolume = null;
    panel.online = null;
    panel.playbackMessage = "";
    panel.playbackStatus = "";
    panel.playbackPosition = 0;
    panel.playbackResourceId = null;
    panel.playbackRevision++;
    finishVolume?.(new Error("设备已切换，请重新下发"));
    headersPromise = null;
  }
  Object.assign(panel.info, info);
  // 模板 SDK 初始连接值为 true，首次 WebSocket 打开可能不触发变更回调；实际收到身份时核对传输状态。
  panel.connected = isMiniProgram
    ? sdk?._weappApi?.ws?.ws?.readyState === WebSocket.OPEN
    : typeof hostWindow.ReactNativeWebView?.postMessage === "function";
  applyOnline(info);
  panel.hostMessage = productMatches.value
    ? "已获取设备身份"
    : `当前产品为 ${info.pid ?? "未知"}，请打开 PID ${PRODUCT_PID} 的设备`;
}

function sendHost(method: string, params?: unknown) {
  if (!sdk) throw new Error("尚未连接灵机设备页面");
  if (isMiniProgram) {
    sdk._weappApi.webSocketSend(method, params);
  } else {
    hostWindow.xj.msgToNative(method, params);
  }
}

export function requireDevice(control = false) {
  if (!sdk || !panel.connected || !panel.info.did) throw new Error("尚未获取设备，请先在小程序内绑定并打开设备");
  if (!productMatches.value) throw new Error(`产品不匹配：本面板用于 PID ${PRODUCT_PID}`);
  if (control && panel.online === false) throw new Error("设备已报告离线，请检查 Wi-Fi 后刷新");
}

export function refreshDevice() {
  if (!sdk) throw new Error(panel.hostMessage);
  sdk.device.getDeviceInfo?.();
  sdk.device.getSnapshot?.();
  void sdk.device.get?.(["voice_Volume"]);
  // 小程序与 RN 都主动查询；宿主未实现该查询时保留“状态未返回”，不把按钮永久锁死。
  sendHost("getDeviceOnline");
}

export async function setVolume(value: number) {
  requireDevice(true);
  // 固件的有效范围是 10..100；输入无效时不下发，保留用户当前选择。
  if (!Number.isInteger(value) || value < 10 || value > 100) throw new Error("音量必须为 10 至 100 的整数");
  if (panel.volumePending) throw new Error("正在等待设备回报，请稍候");
  if (value === panel.reportedVolume) {
    panel.volumeMessage = `设备当前音量已为 ${value}%`;
    return;
  }
  panel.volumePending = true;
  panel.volumeMessage = "已提交音量，等待设备回报…";
  volumeTarget = value;
  return new Promise<void>((resolve, reject) => {
    finishVolume = error => {
      clearTimeout(volumeTimer);
      finishVolume = null;
      panel.volumePending = false;
      volumeTarget = null;
      panel.volumeMessage = error ? error.message : `设备已回报音量 ${value}%`;
      if (error) reject(error); else resolve();
    };
    volumeTimer = setTimeout(() => finishVolume?.(new Error("尚未收到设备音量回报，请刷新核对；保留当前选择")), 12000);
    try {
      // SDK 的 device.set 会乐观回写 data，不能作为设备执行证据；使用模板原始宿主命令并等待真实上报。
      const payload = { key: VOLUME_PROPERTY, value };
      sendHost("deviceDataSet", isMiniProgram ? JSON.stringify(payload) : payload);
    } catch (error) {
      finishVolume?.(error instanceof Error ? error : new Error("音量下发失败"));
    }
  });
}

export function getHostHeaders(): Promise<HostHeaders> {
  requireDevice();
  if (headersPromise) return headersPromise;
  // 小程序与 RN 使用不同消息通道；授权只存在本次 Promise 内存中，不写文件或浏览器存储。
  const pending = new Promise<HostHeaders>((resolve, reject) => {
    const original = hostWindow.xj.getReqHeaders;
    const timer = setTimeout(() => finish(undefined, new Error("宿主未提供访问授权，请从小程序重新打开设备")), 8000);
    const finish = (headers?: HostHeaders, error?: Error) => {
      clearTimeout(timer);
      if (hostWindow.xj.getReqHeaders === callback) hostWindow.xj.getReqHeaders = original;
      if (error) reject(error); else resolve(headers ?? {});
    };
    const callback = (headers: HostHeaders) => {
      const normalized: HostHeaders = {};
      for (const [key, value] of Object.entries(headers ?? {})) {
        if (typeof value === "string" && !/[\r\n]/.test(key + value)) normalized[key] = value;
      }
      finish(normalized);
    };
    hostWindow.xj.getReqHeaders = callback;
    try { sendHost("getReqHeaders"); }
    catch { finish(undefined, new Error("无法向宿主请求授权")); }
  });
  headersPromise = pending;
  // 所有调用复用同一轮请求，完成后即释放；失败允许下一次重试，不永久缓存已失效的授权。
  void pending.then(() => { if (headersPromise === pending) headersPromise = null; }, () => {
    if (headersPromise === pending) headersPromise = null;
  });
  return pending;
}

if (hasHost && (!isMiniProgram || new URLSearchParams(location.search).has("token"))) {
  sdk = new XJIotSDK(sdkConfig);
  installHostCompatibility();
  panel.connected = !isMiniProgram;
  sdk.initProject({
    onDeviceInfoChange: applyInfo,
    onDeviceDataChange(data: Record<string, unknown>) {
      if (!productMatches.value) return;
      const value = data.voice_Volume;
      if (typeof value === "number" && Number.isInteger(value) && value >= 10 && value <= 100) {
        panel.reportedVolume = value;
        if (volumeTarget === value) finishVolume?.();
        else if (!panel.volumePending) panel.volumeMessage = `设备当前音量 ${value}%`;
      }
    },
    onPageConnectChange(connected: boolean) {
      panel.connected = connected;
      if (!connected) {
        panel.online = null;
        finishVolume?.(new Error("页面连接中断，请重新打开设备后核对音量"));
      }
    },
    onPageInit(init: any) {
      if (init.device?.did) applyInfo(init.device);
      applyOnline(init);
      if ("mediaPlayer" in init) applyPlayback(init.mediaPlayer);
    }
  });
  sdk.pageInit({ key: "STORY_COMPANION_PANEL", onLoad: refreshDevice });
  // Mini SDK 不转发 onLoad 回调；身份首次返回后同样主动拉取在线状态。
  if (isMiniProgram) sendHost("getDeviceOnline");
} else if (isMiniProgram) {
  panel.hostMessage = "缺少设备页面连接信息，请返回小程序后重新打开设备";
}
