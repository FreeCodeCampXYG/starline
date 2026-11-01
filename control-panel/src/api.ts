import { getHostHeaders, panel, requireDevice } from "./bridge";

const API_ORIGIN = import.meta.env.MODE === "test" ? "https://api-test.ljyd.cn" : "https://api.ljyd.cn";

async function request(path: string, method = "GET", body?: unknown) {
  requireDevice();
  const epoch = panel.identityEpoch;
  const nativeHeaders = await getHostHeaders();
  if (epoch !== panel.identityEpoch) throw new Error("设备已切换，请重试");
  // 沿用模板 requestAgent 的契约，优先采用宿主 Agent-Authorization；不嵌入产品密钥。
  const find = (name: string) => Object.entries(nativeHeaders).find(([key]) => key.toLowerCase() === name)?.[1];
  const authorization = find("agent-authorization") || find("authorization");
  if (!authorization) throw new Error("宿主没有提供平台访问授权，请重新登录小程序");
  const headers = new Headers(nativeHeaders);
  headers.delete("Agent-Authorization");
  headers.delete("App-Authorization");
  headers.set("Authorization", authorization);
  headers.set("Content-Type", "application/json");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(API_ORIGIN + path, {
      method, headers, signal: controller.signal,
      body: body === undefined ? undefined : JSON.stringify(body)
    });
    const result = await response.json();
    if (!response.ok || result.ok === false || result.success === false ||
      (result.status !== undefined && result.status !== 0) ||
      (result.code !== undefined && ![0, 200].includes(result.code))) {
      throw new Error(result.msg || result.message || `平台请求失败（${response.status}）`);
    }
    if (epoch !== panel.identityEpoch) throw new Error("设备已切换，本次结果已失效");
    return result;
  } catch (error) {
    if (controller.signal.aborted) throw new Error("平台请求超时，请稍后重试");
    throw error;
  } finally { clearTimeout(timeout); }
}

export async function fetchCategories() {
  const result = await request(`/app/api/resouce/categories?pid=${encodeURIComponent(panel.info.pid!)}`);
  return result.data ?? [];
}

export async function fetchResources(categoryId: number) {
  const result = await request(`/app/api/resouce/categories/detail?categoryId=${encodeURIComponent(categoryId)}&pid=${encodeURIComponent(panel.info.pid!)}`);
  return result.data?.resources ?? [];
}

export async function requestResourceAction(action: "play" | "pause" | "resume" | "stop", resourceId: number, title = "") {
  requireDevice(true);
  const actionLabels = { play: "播放", pause: "暂停", resume: "继续播放", stop: "停止" };
  if (!(action in actionLabels)) throw new Error("不支持的播放操作");
  const label = actionLabels[action];
  if (!Number.isSafeInteger(resourceId) || resourceId <= 0) throw new Error("资源编号无效，请重新读取列表");
  panel.playbackResourceId = resourceId;
  if (action === "play") { panel.playbackStatus = ""; panel.playbackPosition = 0; }
  panel.playbackMessage = `正在提交${title ? `《${title}》` : ""}${label}请求…`;
  const epoch = panel.identityEpoch;
  const revision = panel.playbackRevision;
  // 模板通过设备上行资源事件请求平台再下发 player/play；HTTP 成功只表示请求提交，不等于已出声。
  try {
    const result = await request("/agent-merchant/api/resource/event", "POST", {
      topicName: `/${panel.info.pid}/${panel.info.did}/device/up`,
      receiveBody: { method: "playerReply", subMethod: action, id: 6, code: 0, params: { resourceId } }
    });
    // 已到达的播放状态优先；慢 HTTP 响应不能把“播放中”回退为“等待回报”。
    if (epoch === panel.identityEpoch && revision === panel.playbackRevision) {
      panel.playbackMessage = `已提交${title ? `《${title}》` : ""}${label}请求，等待平台播放状态回报`;
    }
    return result;
  } catch (error) {
    if (epoch === panel.identityEpoch && revision === panel.playbackRevision) {
      panel.playbackMessage = error instanceof Error ? error.message : "播放请求失败，请重试";
    }
    throw error;
  }
}

export const requestResourcePlay = (resourceId: number, title = "") => requestResourceAction("play", resourceId, title);

export async function fetchConversation() {
  const result = await request("/app/ws/chatRecord/getConvoList", "POST", {
    did: Number(panel.info.did), beforeId: null, afterId: null, limit: 20
  });
  // 模板接口返回最近记录的倒序；只反转本次副本，不改写平台顺序或伪造对话。
  return [...(result.result?.records ?? [])].reverse();
}
