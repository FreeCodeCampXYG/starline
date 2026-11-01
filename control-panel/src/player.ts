import { computed, reactive, watch } from "vue";
import { canControl, panel, productMatches } from "./bridge";
import { fetchCategories, fetchResources, requestResourceAction } from "./api";
import { modes, preferences } from "./preferences";

export type Track = { id: number; title: string; description?: string; durationSeconds?: number; icon?: string; categoryId?: number };
export type Category = { id: number; name: string; children?: Category[] };
export const library = reactive({
  categories: [] as Category[], tracks: [] as Track[], categoryId: 0,
  query: "", loading: false, categoriesLoading: false, error: "", loaded: false
});
export const player = reactive({
  queue: [] as Track[], current: null as Track | null, intent: "stopped", busy: false,
  notice: "", error: "", completionArmed: false
});
export const canRead = computed(() => Boolean(panel.connected && productMatches.value && panel.info.did));
export const visibleTracks = computed(() => {
  const query = library.query.trim().toLocaleLowerCase();
  return query ? library.tracks.filter(track => `${track.title} ${track.description || ""}`.toLocaleLowerCase().includes(query)) : library.tracks;
});
export const currentIndex = computed(() => player.queue.findIndex(track => track.id === player.current?.id));
let browseGeneration = 0;
const cache = new Map<number, Track[]>();

function validTracks(value: unknown): Track[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<number>();
  return value.filter(track => {
    const id = Number(track?.id);
    if (!Number.isSafeInteger(id) || id <= 0 || seen.has(id)) return false;
    seen.add(id); return true;
  }).map(track => ({ ...track, id: Number(track.id), title: String(track.title || "未命名曲目") }));
}

export async function selectCategory(categoryId: number) {
  const generation = ++browseGeneration;
  const epoch = panel.identityEpoch;
  library.categoryId = categoryId;
  library.error = "";
  library.loading = true;
  library.tracks = cache.get(categoryId) || [];
  try {
    const tracks = cache.get(categoryId) || validTracks(await fetchResources(categoryId));
    // 分类切换只接受最后一次结果；慢的旧分类请求不能覆盖用户当前选择或播放队列。
    if (generation !== browseGeneration || epoch !== panel.identityEpoch) return;
    cache.set(categoryId, tracks);
    library.tracks = tracks;
    library.loaded = true;
  } catch (error) {
    if (generation === browseGeneration && epoch === panel.identityEpoch) library.error = message(error);
  } finally {
    if (generation === browseGeneration && epoch === panel.identityEpoch) library.loading = false;
  }
}

export async function loadLibrary() {
  if (!canRead.value || library.categoriesLoading) return;
  const epoch = panel.identityEpoch;
  library.categoriesLoading = true; library.error = "";
  try {
    const flatten = (items: Category[]): Category[] => items.flatMap(item => Array.isArray(item.children) && item.children.length ? flatten(item.children) : [item]);
    const result = await fetchCategories();
    if (epoch !== panel.identityEpoch) return;
    cache.clear();
    library.categories = flatten(Array.isArray(result) ? result : []).filter(item => Number.isSafeInteger(Number(item.id)) && Number(item.id) > 0)
      .map(item => ({ ...item, id: Number(item.id) }));
    library.loaded = true;
    if (library.categories.length) await selectCategory(library.categories[0].id);
  } catch (error) {
    if (epoch === panel.identityEpoch) library.error = message(error);
  } finally {
    if (epoch === panel.identityEpoch) library.categoriesLoading = false;
  }
}

function message(error: unknown) { return error instanceof Error ? error.message : "操作失败，请重试"; }

export async function playTrack(track: Track, queue: Track[] = library.tracks) {
  if (player.busy || !canControl.value) return;
  const previous = { current: player.current, queue: player.queue, intent: player.intent, armed: player.completionArmed };
  const epoch = panel.identityEpoch;
  player.busy = true; player.error = ""; player.notice = "";
  player.current = track;
  player.queue = queue.some(item => item.id === track.id) ? [...queue] : [track];
  player.completionArmed = false;
  try {
    await requestResourceAction("play", track.id, track.title);
    if (epoch === panel.identityEpoch) player.intent = "playing";
  } catch (error) {
    if (epoch === panel.identityEpoch) {
      player.current = previous.current; player.queue = previous.queue;
      player.intent = previous.intent; player.completionArmed = previous.armed;
      player.error = message(error);
    }
  } finally { if (epoch === panel.identityEpoch) player.busy = false; }
}

export async function control(action: "pause" | "resume" | "stop") {
  if (!player.current || player.busy || !canControl.value) return;
  const epoch = panel.identityEpoch;
  const armed = player.completionArmed;
  player.busy = true; player.error = ""; player.notice = "";
  // 用户停止与暂停不触发自动续播；失败才恢复先前的结束监听。
  if (action !== "resume") player.completionArmed = false;
  try {
    await requestResourceAction(action, player.current.id, player.current.title);
    if (epoch === panel.identityEpoch) player.intent = action === "pause" ? "paused" : action === "stop" ? "stopped" : "playing";
  } catch (error) {
    if (epoch === panel.identityEpoch) { player.completionArmed = armed; player.error = message(error); }
  } finally { if (epoch === panel.identityEpoch) player.busy = false; }
}

export async function togglePlayback() {
  if (!player.current) {
    if (visibleTracks.value[0]) await playTrack(visibleTracks.value[0]);
  } else if (player.intent === "stopped") {
    await playTrack(player.current, player.queue);
  } else await control(player.intent === "paused" ? "resume" : "pause");
}

export async function step(direction: -1 | 1, automatic = false) {
  const queue = player.queue;
  if (!queue.length || player.busy) return;
  let index = currentIndex.value;
  if (preferences.mode === "shuffle" && queue.length > 1) {
    index = (index + 1 + Math.floor(Math.random() * (queue.length - 1))) % queue.length;
  } else if (!(automatic && preferences.mode === "repeat-one")) {
    index += direction;
    if (automatic && preferences.mode === "order" && index >= queue.length) {
      player.intent = "stopped"; player.notice = "播放队列已结束"; return;
    }
    index = (index + queue.length) % queue.length;
  }
  await playTrack(queue[Math.max(0, index)], queue);
}

export function cycleMode() { preferences.mode = modes[(modes.indexOf(preferences.mode) + 1) % modes.length]; }

watch(() => panel.playbackRevision, () => {
  if (!player.current || panel.playbackResourceId !== player.current.id) return;
  if (panel.playbackStatus === "playing") {
    player.intent = "playing"; player.completionArmed = true;
  } else if (panel.playbackStatus === "paused") {
    player.intent = "paused"; player.completionArmed = false;
  } else if (["completed", "ended", "finished"].includes(panel.playbackStatus)) {
    const canAdvance = player.completionArmed && !player.busy && canControl.value && document.visibilityState === "visible";
    // 一个播放周期只消费一次明确结束回报，不使用歌曲时长计时；停止/错误和重复回报不得触发切歌。
    player.completionArmed = false; player.intent = "stopped";
    if (canAdvance) void step(1, true);
  } else if (["stopped", "error"].includes(panel.playbackStatus)) {
    player.intent = "stopped"; player.completionArmed = false;
  }
});

watch(() => panel.identityEpoch, () => {
  browseGeneration++; cache.clear();
  Object.assign(library, { categories: [], tracks: [], categoryId: 0, query: "", loading: false, categoriesLoading: false, error: "", loaded: false });
  Object.assign(player, { queue: [], current: null, intent: "stopped", busy: false, notice: "", error: "", completionArmed: false });
});
watch([() => panel.identityEpoch, canRead], ([, ready]) => { if (ready && !library.loaded) void loadLibrary(); }, { immediate: true });
