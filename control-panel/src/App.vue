<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Button, ConfigProvider, Empty, Icon, Loading, Popup, Progress, Search, Slider, Tab, Tabs } from "vant";
import PlayerIcon from "./components/PlayerIcon.vue";
import CoverArt from "./components/CoverArt.vue";
import { canControl, panel, PRODUCT_PID, refreshDevice, setVolume } from "./bridge";
import { fetchConversation } from "./api";
import { canRead, control, cycleMode, library, loadLibrary, playTrack, player, selectCategory, step, togglePlayback, visibleTracks } from "./player";
import { colorTokens, modeLabels, preferences, type Skin } from "./preferences";
import palettes from "./themes.json";

const activePage = ref("music");
const showQueue = ref(false);
const showTheme = ref(false);
const show3d = ref(false);
const volume = ref(30);
const records = ref<any[]>([]);
const historyBusy = ref(false);
const historyLoaded = ref(false);
const notice = ref("");
watch(() => panel.identityEpoch, () => { records.value = []; historyLoaded.value = false; historyBusy.value = false; notice.value = ""; });
const theme = computed(() => preferences.skin === "dark" ? "dark" : "light");
const themeVars = computed(() => ({
  primaryColor: colorTokens.value.accent,
  buttonPrimaryColor: colorTokens.value["on-accent"], radiusLg: "20px"
}));
const onlineLabel = computed(() => panel.online === true ? "设备在线" : panel.online === false ? "设备离线" : "状态待返回");
const modeIcon = computed(() => preferences.mode === "shuffle" ? "shuffle" : preferences.mode === "repeat-one" ? "repeat-one" : "repeat");
const duration = (seconds = 0) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
const progress = computed(() => player.current?.durationSeconds ? Math.min(100, panel.playbackPosition / player.current.durationSeconds * 100) : 0);
const playbackLabel = computed(() => {
  if (player.error) return "播放未成功，请重试";
  if (player.busy) return "正在准备…";
  if (player.notice) return player.notice;
  if (!player.current) return "选择喜欢的内容";
  if (panel.playbackStatus === "error") return "播放未成功，请重试";
  if (panel.playbackStatus === "playing") return "正在播放";
  if (panel.playbackStatus === "paused") return "已暂停";
  if (player.intent === "stopped") return "已停止";
  return "等待设备响应…";
});
const skinOptions: {key: Skin; name: string; detail: string}[] = [
  {key:"light",name:"暖雾紫",detail:"温暖的陪伴"}, {key:"dark",name:"夜幕",detail:"安静的夜色"}, {key:"forest",name:"苔绿",detail:"自然的呼吸"}
];
async function applyVolume() { notice.value = ""; try { await setVolume(volume.value); } catch (error) { notice.value = error instanceof Error ? error.message : "音量下发失败"; } }
async function readHistory() {
  if (historyBusy.value) return;
  historyBusy.value = true; notice.value = "";
  const epoch = panel.identityEpoch;
  try { records.value = await fetchConversation(); historyLoaded.value = true; }
  catch (error) { if (epoch === panel.identityEpoch) notice.value = error instanceof Error ? error.message : "读取失败"; }
  finally { if (epoch === panel.identityEpoch) historyBusy.value = false; }
}
function refresh() { try { refreshDevice(); } catch (error) { notice.value = error instanceof Error ? error.message : "刷新失败"; } }
</script>

<template>
  <ConfigProvider :theme="theme" :theme-vars="themeVars">
    <main class="music-shell">
      <header class="app-header"><div class="brand"><span class="brand-icon"><PlayerIcon name="music" /></span><div><strong>故事搭子</strong></div></div><div class="header-actions"><button class="icon-button" aria-label="查看设备" @click="activePage='device'"><Icon name="setting-o" size="22" /></button><button class="icon-button theme-trigger" aria-label="切换皮肤" @click="showTheme=true"><Icon name="brush-o" size="23" /></button></div></header>
      <p v-if="!canRead" class="inline-message">请先在小程序中打开已绑定的设备。<button class="text-button" @click="activePage='device'">查看设备</button></p>
      <Tabs v-model:active="activePage" class="main-tabs" animated :border="false" background="transparent" color="var(--accent)">
        <Tab title="发现音乐" name="music">
          <Search v-model="library.query" shape="round" placeholder="搜索当前分类的歌曲或故事" background="transparent" aria-label="搜索歌曲或故事" />
          <div class="section-heading"><h2>听点喜欢的</h2><button class="text-button" aria-label="刷新内容" :disabled="library.categoriesLoading || !canRead" @click="loadLibrary"><Icon name="replay" /></button></div>
          <div v-if="library.categoriesLoading" class="loading-state"><Loading size="22">正在载入内容…</Loading></div>
          <Tabs v-if="library.categories.length" :active="library.categoryId" class="category-tabs" type="card" :border="false" color="var(--accent)" @change="selectCategory(Number($event))">
            <Tab v-for="category in library.categories" :key="category.id" :name="category.id" :title="category.name" />
          </Tabs>
          <div v-if="library.error" class="inline-message" role="alert">{{ library.error }}<button class="text-button" @click="library.categories.length ? selectCategory(library.categoryId) : loadLibrary()">重试</button></div>
          <div class="list-toolbar"><span>{{ visibleTracks.length }} 首{{ library.query ? '匹配内容' : '内容' }}</span><button class="text-button" :disabled="!visibleTracks.length || !canControl || player.busy" @click="playTrack(visibleTracks[0],visibleTracks)"><PlayerIcon name="play" />播放全部</button></div>
          <div v-if="library.loading && !library.tracks.length" class="loading-state"><Loading size="22">正在载入曲目…</Loading></div>
          <div class="track-list">
            <button v-for="(track,index) in visibleTracks" :key="track.id" class="track-row" :class="{current:player.current?.id===track.id}" :data-track="track.id" :disabled="!canControl || player.busy" @click="player.current?.id===track.id ? togglePlayback() : playTrack(track)">
              <span class="track-number">{{ player.current?.id===track.id ? '♫' : String(index+1).padStart(2,'0') }}</span><span class="track-cover"><CoverArt :variant="index" /></span><span class="track-info"><strong>{{ track.title }}</strong><small v-if="track.description">{{ track.description }}</small></span><span class="track-duration">{{ track.durationSeconds ? duration(track.durationSeconds) : '' }}</span><span class="row-play"><PlayerIcon :name="player.current?.id===track.id && player.intent==='playing' ? 'pause' : 'play'" /></span>
            </button>
          </div>
          <Empty v-if="!library.loading && !library.categoriesLoading && !library.error && !visibleTracks.length" :description="library.query ? '没有找到，换个关键词试试' : canRead ? '这个分类暂时没有内容' : '连接设备后，内容会自动出现'" image="search" />
        </Tab>
        <Tab title="设备" name="device"><section class="settings-card"><div class="section-heading"><h2>音量</h2><strong class="volume-number">{{volume}}<small>%</small></strong></div><Slider v-model="volume" :min="10" :max="100" :disabled="panel.volumePending" aria-label="设备音量" /><div class="range-labels"><span>轻声</span><span>响亮</span></div><Button class="volume-apply" round block type="primary" :disabled="!canControl" :loading="panel.volumePending" @click="applyVolume">应用音量</Button><p class="feedback">{{ panel.volumePending ? '正在调整…' : panel.reportedVolume !== null ? `当前音量 ${panel.reportedVolume}%` : '等待设备响应' }}</p></section><section class="settings-card"><h2>{{panel.info.deviceName || '我的设备'}}</h2><div class="details-row"><span>连接状态</span><strong>{{onlineLabel}}</strong></div><Button round block plain @click="refresh">刷新设备状态</Button><details class="device-details"><summary>设备信息</summary><div class="details-row"><span>产品</span><strong>{{panel.info.pid || PRODUCT_PID}}</strong></div><div class="details-row"><span>设备</span><strong>{{panel.info.did || '尚未连接'}}</strong></div><p>面板 2.1</p><p v-if="player.error">{{player.error}}</p></details></section><section class="settings-card showcase-card"><div class="showcase-copy"><span class="showcase-kicker">DESIGN STUDY</span><h2>3D 外观与打印</h2><p>旋转查看故事搭子的概念外观，并下载 3MF 打印文件。</p></div><Button round block type="primary" @click="show3d=true">打开 3D 演示</Button><a class="showcase-download" href="./story-companion-robot-v2.3mf" download>下载 3MF 打印文件</a></section></Tab>
        <Tab title="对话" name="records"><section class="settings-card"><h2>聊过的故事</h2><p>设备与智能体的最近 20 条对话。</p><Button round block type="primary" :disabled="!canRead" :loading="historyBusy" @click="readHistory">{{historyLoaded ? '刷新对话' : '查看对话记录'}}</Button><Empty v-if="historyLoaded && !records.length" description="还没有对话记录，试着和故事搭子说句话" /><article v-for="(item,index) in records" :key="item.id ?? index" class="conversation"><span>{{item.role==='user' || item.role===1 ? '你' : '故事搭子'}}</span><p>{{item.content}}</p></article></section></Tab>
      </Tabs>
      <p v-if="notice" class="inline-message" role="status">{{notice}}</p>
    </main>

    <aside class="player-bar" aria-label="播放器">
      <div class="player-track"><span class="now-cover"><CoverArt v-if="player.current" :variant="player.queue.findIndex(item=>item.id===player.current?.id)" /><PlayerIcon v-else name="music" /></span><div><strong>{{player.current?.title || '尚未播放'}}</strong><p class="player-feedback" aria-live="polite">{{playbackLabel}}</p></div><button class="icon-button" aria-label="播放队列" @click="showQueue=true"><PlayerIcon name="queue" /><span class="queue-count">{{player.queue.length}}</span></button></div>
      <Progress v-if="player.current && panel.playbackPosition>0" :percentage="progress" :show-pivot="false" stroke-width="2" color="var(--accent)" />
      <div class="transport"><button class="icon-button mode-button" :class="{selected:preferences.mode!=='order'}" :aria-label="modeLabels[preferences.mode]" @click="cycleMode"><PlayerIcon :name="modeIcon" /><small>{{modeLabels[preferences.mode]}}</small></button><button class="icon-button" aria-label="上一首" :disabled="!player.queue.length || player.busy || !canControl" @click="step(-1)"><PlayerIcon name="previous" /></button><button class="main-play" :aria-label="player.intent==='playing' ? '暂停' : player.intent==='paused' ? '继续播放' : '播放'" :disabled="(!player.current && !visibleTracks.length) || player.busy || !canControl" @click="togglePlayback"><Loading v-if="player.busy" size="23" color="currentColor" /><PlayerIcon v-else :name="player.intent==='playing' ? 'pause' : 'play'" /></button><button class="icon-button" aria-label="下一首" :disabled="!player.queue.length || player.busy || !canControl" @click="step(1)"><PlayerIcon name="next" /></button><button class="icon-button" aria-label="停止播放" :disabled="!player.current || player.busy || !canControl" @click="control('stop')"><PlayerIcon name="stop" /></button></div>
    </aside>

    <Popup v-model:show="showQueue" position="bottom" round closeable class="sheet queue-sheet" :style="{maxHeight:'75vh'}"><div class="sheet-heading"><h2>播放队列 <small>{{player.queue.length}}</small></h2><p>{{modeLabels[preferences.mode]}}</p></div><div class="queue-content"><button v-for="(track,index) in player.queue" :key="track.id" class="track-row" :class="{current:player.current?.id===track.id}" :disabled="!canControl || player.busy" @click="playTrack(track,player.queue)"><span class="track-number">{{index+1}}</span><span class="track-info"><strong>{{track.title}}</strong></span><PlayerIcon :name="player.current?.id===track.id && player.intent==='playing' ? 'pause' : 'play'" /></button><Empty v-if="!player.queue.length" description="队列为空" /></div><p class="queue-help">自动切歌需要保持此页面打开。</p></Popup>
    <Popup v-model:show="showTheme" position="bottom" round closeable class="sheet theme-sheet"><div class="sheet-heading"><h2>外观</h2></div><div class="skin-options"><button v-for="skin in skinOptions" :key="skin.key" :data-skin-choice="skin.key" :class="{chosen:preferences.skin===skin.key}" :aria-pressed="preferences.skin===skin.key" @click="preferences.skin=skin.key"><span class="skin-sample" :style="{background:palettes[skin.key]['app-bg']}"><i :style="{background:palettes[skin.key].accent}"></i><i :style="{background:palettes[skin.key].tint}"></i><i :style="{background:palettes[skin.key].line}"></i></span><strong>{{skin.name}}</strong></button></div></Popup>
    <Popup v-model:show="show3d" position="bottom" round closeable class="sheet model-sheet" :style="{height:'min(88vh,760px)'}"><div class="model-sheet-heading"><div><span class="showcase-kicker">DESIGN STUDY</span><h2>故事搭子 · 3D 外观</h2></div><a class="model-download" href="./story-companion-robot-v2.3mf" download>下载 3MF</a></div><iframe class="model-frame" title="故事搭子 3D 外观演示" src="./story-companion-3d.html"></iframe><p class="model-disclaimer">概念外观与结构演示，实际装配尺寸和打印适配性仍需实物测量确认。</p></Popup>
  </ConfigProvider>
</template>
