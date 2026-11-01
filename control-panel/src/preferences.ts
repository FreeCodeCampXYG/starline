import { computed, reactive, watch } from "vue";
import palettes from "./themes.json";

export type Skin = "light" | "dark" | "forest";
export type PlayMode = "order" | "repeat-all" | "repeat-one" | "shuffle";
const key = "story-companion-player-preferences-v1";
const skins: Skin[] = ["light", "dark", "forest"];
export const modes: PlayMode[] = ["order", "repeat-all", "repeat-one", "shuffle"];
export const modeLabels: Record<PlayMode, string> = {
  order: "顺序播放", "repeat-all": "列表循环", "repeat-one": "单曲循环", shuffle: "随机播放"
};
let saved: any = {};
try { saved = JSON.parse(localStorage.getItem(key) || "{}"); } catch { /* 禁止存储时使用本次会话偏好。 */ }
export const preferences = reactive({
  skin: (skins.includes(saved?.skin) ? saved.skin : "light") as Skin,
  mode: (modes.includes(saved?.mode) ? saved.mode : "order") as PlayMode
});
export const colorTokens = computed(() => palettes[preferences.skin]);
watch(() => ({ skin: preferences.skin, mode: preferences.mode }), value => {
  document.documentElement.dataset.skin = value.skin;
  // 所有组件与自绘区域共用同一语义色板；内联变量覆盖旧样式默认值，避免主题局部漏色。
  for (const [role, color] of Object.entries(palettes[value.skin])) {
    document.documentElement.style.setProperty(`--${role}`, color);
  }
  // 仅持久化皮肤与播放模式，不混入设备身份、授权、Wi-Fi 或播放队列。
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* 失败仍保留当前界面设置。 */ }
}, { immediate: true });
