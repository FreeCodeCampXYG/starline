import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const baseUrl = "http://127.0.0.1:18763/";
const debugPort = 18764;
const output = path.resolve("../outputs/story-companion-panel");
const profile = await mkdtemp(path.join(tmpdir(), "story-panel-browser-"));
const browser = spawn("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", [
  "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
  `--remote-debugging-port=${debugPort}`, `--user-data-dir=${profile}`, "about:blank"
], { windowsHide: true, stdio: "ignore" });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const checks = [];
const sessions = [];

async function until(fn, label, timeout = 9000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await fn()) return;
    await delay(70);
  }
  throw new Error(`等待超时：${label}`);
}

async function connect(url) {
  const ws = new WebSocket(url);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });
  let nextId = 0;
  const pending = new Map();
  const errors = [];
  ws.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (message.method === "Runtime.exceptionThrown") {
      errors.push(message.params.exceptionDetails.exception?.description || message.params.exceptionDetails.text);
    }
    if (pending.has(message.id)) {
      const { resolve, reject, timer } = pending.get(message.id);
      clearTimeout(timer);
      pending.delete(message.id);
      if (message.error) reject(new Error(message.error.message)); else resolve(message.result);
    }
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++nextId;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP 超时 ${method}`)); }, 10000);
    pending.set(id, { resolve, reject, timer });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return {
    send, errors,
    async evaluate(expression) {
      const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
      if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
      return result.result.value;
    },
    close() { ws.close(); }
  };
}

function fixture({ mode = "rn", pid = 11910, online = true, auth = true, onlineField = "onlionStatus" } = {}) {
  return `(() => {
    const mode=${JSON.stringify(mode)}, pid=${pid}, online=${JSON.stringify(online)}, onlineField=${JSON.stringify(onlineField)};
    window.__hostCalls=[]; window.__apiCalls=[]; window.__holdVolume=true;
    window.__failApi=false; window.__auth=${auth}; window.__responsesDelay=0; let currentVolume=30;
    let socket;
    const reply=(method,params,data) => {
      if(mode==='mini') socket.onmessage?.({data:JSON.stringify({method,params,data})});
      else window.dispatchEvent(new MessageEvent('message',{data:JSON.stringify({method,params,data})}));
    };
    window.__deliver=reply;
    const handle=(raw) => {
      const message=typeof raw==='string'?JSON.parse(raw):raw;
      window.__hostCalls.push(message);
      const {method,params}=message;
      if(method==='onPageInit') setTimeout(()=>{
        const info={pid,did:10001,deviceName:'故事搭子测试设备'};
        if(online!==null) info[onlineField]=online;
        if(mode==='mini') {
          reply('getDeviceInfo_reply',info);
          reply('getAttrs_reply',{'prop.2.1':currentVolume});
          reply('stringsInit',{code:'zh-CN'});
        } else {
          reply('initDevice',{info,data:{'prop.2.1':currentVolume}});
          reply('onLoad',{});
        }
        if(online!==null) reply('onDeviceOnline',online);
      },20);
      if(method==='deviceDataGet') setTimeout(()=>reply('onDeviceDataChange',{'prop.2.1':currentVolume}),10);
      if(method==='getDeviceOnline' && online!==null) setTimeout(()=>reply('onDeviceOnline',online),10);
      if(method==='getReqHeaders') setTimeout(()=>reply('getReqHeaders',window.__auth?{'Agent-Authorization':'fixture-only-authorization'}:{}),10);
      if(method==='deviceDataSet' && !window.__holdVolume) {
        const value=typeof params==='string'?JSON.parse(params):params;
        currentVolume=value.value;
        setTimeout(()=>reply('onDeviceDataChange',{'prop.2.1':currentVolume}),80);
      }
    };
    window.fetch=async(url,options={})=>{
      const route=new URL(url).pathname;
      window.__apiCalls.push({route,body:options.body?JSON.parse(options.body):null,
        authorized:new Headers(options.headers).get('Authorization')==='fixture-only-authorization'});
      if(window.__responsesDelay) await new Promise(resolve=>setTimeout(resolve,window.__responsesDelay));
      if(window.__failApi) return new Response(JSON.stringify({msg:'资源暂不可用',status:503}),{status:503});
      if(window.__playerBeforeResponse && route.endsWith('/resource/event')) {
        reply('player',{method:'playerReply',params:{resourceId:42,playStatus:'playing'}});
        await new Promise(resolve=>setTimeout(resolve,150));
      }
      const result=route.endsWith('/categories')?{success:true,data:[{id:1,name:'故事',children:[{id:2,name:'睡前故事',children:[]},{id:3,name:'轻音乐',children:[]}]}]}:
        route.endsWith('/detail')?{success:true,data:{resources:new URL(url).searchParams.get('categoryId')==='3'?[{id:45,title:'午后钢琴',durationSeconds:120}]:[{id:42,title:'小星星的旅行',description:'一段温柔的睡前故事',durationSeconds:95},{id:43,title:'月光里的小船',description:'慢慢听，慢慢入睡',durationSeconds:112},{id:44,title:'晚安，森林',description:'来自森林的一封信',durationSeconds:180}]}}:
        route.endsWith('/getConvoList')?{status:0,result:{records:[{id:2,role:'assistant',content:'小星星开始了旅行。'},{id:1,role:'user',content:'讲一个星星的故事。'}]}}:
        {status:0,ok:true};
      return new Response(JSON.stringify(result),{status:200,headers:{'Content-Type':'application/json'}});
    };
    if(mode==='mini') {
      window.__wxjs_environment='miniprogram';
      window.WebSocket=class {
        static OPEN=1; static CONNECTING=0; readyState=0;
        constructor(){socket=this;setTimeout(()=>{this.readyState=1;this.onopen?.({});setTimeout(()=>reply('keepAlive',null,{}),10);},10);}
        send(message){handle(message);}
        close(){this.readyState=3;}
      };
    } else window.ReactNativeWebView={postMessage:handle};
  })();`;
}

async function page(options) {
  const target = await fetch(`http://127.0.0.1:${debugPort}/json/new?about:blank`, { method: "PUT" }).then(r => r.json());
  const client = await connect(target.webSocketDebuggerUrl);
  sessions.push(client);
  await client.send("Runtime.enable");
  await client.send("Page.enable");
  await client.send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  if (options) await client.send("Page.addScriptToEvaluateOnNewDocument", { source: fixture(options) });
  await client.send("Page.navigate", { url: baseUrl + (options?.mode === "mini" ? "?token=fixture-only-connection" : "") });
  await until(() => client.evaluate("!!document.querySelector('.main-play')"), "面板渲染");
  return client;
}

function pass(name) { checks.push(name); console.log(`PASS ${name}`); }
async function click(client, expression) { await client.evaluate(`${expression}.click()`); await delay(60); }

try {
  await mkdir(output, { recursive: true });
  await until(async () => { try { return (await fetch(`http://127.0.0.1:${debugPort}/json/version`)).ok; } catch { return false; } }, "Edge 启动", 15000);
  const plain = await page();
  assert.equal(await plain.evaluate("document.querySelector('.primary').disabled"), true);
  assert.match(await plain.evaluate("document.body.innerText"), /请从灵机小程序或 App/);
  pass("普通浏览器保持未连接，不宣称设备在线");

  const rn = await page({ mode: "rn" });
  await until(() => rn.evaluate("!document.querySelector('.primary').disabled"), "RN 设备初始化");
  assert.match(await rn.evaluate("document.querySelector('.volume-value').innerText"), /30%/);
  pass("RN 宿主设备身份、在线状态和音量上报可显示");
  await rn.evaluate("(() => {const range=document.querySelector('#volume'); range.value='60'; range.dispatchEvent(new Event('input',{bubbles:true})); document.querySelector('.primary').click(); document.querySelector('.primary').click();})()");
  await delay(120);
  const volumeCalls = await rn.evaluate("__hostCalls.filter(c=>c.method==='deviceDataSet')");
  assert.equal(volumeCalls.length, 1);
  assert.deepEqual(volumeCalls[0].params, { key: "prop.2.1", value: 60 });
  assert.match(await rn.evaluate("document.querySelector('.feedback').innerText"), /等待设备回报/);
  assert.doesNotMatch(await rn.evaluate("document.querySelector('.volume-value').innerText"), /回报 60%/);
  pass("音量原始命令映射正确，重复点击只提交一次，无上报不误报执行成功");
  await rn.evaluate("__deliver('onDeviceDataChange',{'prop.2.1':60})");
  await until(() => rn.evaluate("document.querySelector('.feedback').innerText.includes('设备已回报音量 60%')"), "音量真实上报");
  pass("仅在真实属性事件到达后确认音量");

  await click(rn, "document.querySelectorAll('.tabs button')[1]");
  await click(rn, "document.querySelector('.card .secondary')");
  await until(() => rn.evaluate("document.querySelectorAll('.category-list button').length===1"), "资源分类");
  await click(rn, "document.querySelector('.category-list button')");
  await until(() => rn.evaluate("document.querySelectorAll('.resource-item').length===1"), "资源内容");
  await click(rn, "document.querySelector('.resource-item button')");
  const playback = await rn.evaluate("__apiCalls.find(c=>c.route.endsWith('/resource/event'))");
  assert.equal(playback.authorized, true);
  assert.equal(playback.body.topicName, "/11910/10001/device/up");
  assert.equal(playback.body.receiveBody.params.resourceId, 42);
  assert.equal(playback.body.receiveBody.method, "playerReply");
  assert.match(await rn.evaluate("document.querySelector('.playback-feedback').innerText"), /播放请求/);
  await rn.evaluate("__deliver('player',{method:'playerReply',params:{resourceId:42,playStatus:'playing'}})");
  pass("资源列表与播放使用宿主授权、当前 PID/DID 和模板事件契约");
  await rn.evaluate("__failApi=true");
  await click(rn, "document.querySelector('.card .secondary')");
  await until(() => rn.evaluate("document.querySelector('.notice')?.innerText.includes('资源暂不可用')"), "平台错误展示");
  assert.equal(await rn.evaluate("document.querySelectorAll('.resource-item').length"), 1);
  pass("平台错误可见，已加载内容保留");
  await rn.evaluate("__failApi=false");
  await click(rn, "document.querySelectorAll('.tabs button')[2]");
  await click(rn, "document.querySelector('.card .secondary')");
  await until(() => rn.evaluate("document.querySelectorAll('.conversation').length===2"), "对话记录");
  const history = await rn.evaluate("Array.from(document.querySelectorAll('.conversation p')).map(e=>e.innerText)");
  assert.deepEqual(history, ["讲一个星星的故事。", "小星星开始了旅行。"]);
  pass("对话记录保留模板倒序转正序契约，不伪造聊天发送");
  await click(rn, "document.querySelectorAll('.tabs button')[0]");
  const capture = await rn.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
  await writeFile(path.join(output, "panel-preview-host-fixture.png"), Buffer.from(capture.data, "base64"));

  const mismatch = await page({ mode: "rn", pid: 11913 });
  await until(() => mismatch.evaluate("document.body.innerText.includes('当前产品为 11913')"), "产品身份拦截");
  assert.equal(await mismatch.evaluate("document.querySelector('.primary').disabled"), true);
  assert.equal(await mismatch.evaluate("__hostCalls.filter(c=>c.method==='deviceDataSet').length"), 0);
  pass("PID11913 与 PID11910 不匹配时禁止写入");

  const offline = await page({ mode: "rn", online: false });
  await until(() => offline.evaluate("document.body.innerText.includes('设备离线')"), "离线状态");
  assert.equal(await offline.evaluate("document.querySelector('.primary').disabled"), true);
  pass("设备离线时禁止音量与播放写入");

  const mini = await page({ mode: "mini" });
  try {
    await until(() => mini.evaluate("!document.querySelector('.primary').disabled"), "小程序初始化");
  } catch (error) {
    throw new Error(JSON.stringify({ error: error.message, jsErrors: mini.errors,
      page: await mini.evaluate("document.body.innerText"),
      methods: await mini.evaluate("__hostCalls.map(call=>call.method)") }));
  }
  await click(mini, "document.querySelectorAll('.tabs button')[1]");
  await click(mini, "document.querySelector('.card .secondary')");
  await until(() => mini.evaluate("document.querySelectorAll('.category-list button').length===1"), "小程序授权通道");
  assert.equal(await mini.evaluate("__apiCalls[0].authorized"), true);
  pass("小程序 WebSocket 初始化和请求头通道均使用实际 SDK 实例");

  await click(mini, "document.querySelectorAll('.tabs button')[0]");
  await mini.evaluate("(() => {__holdVolume=false; const range=document.querySelector('#volume');range.value='55';range.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('.primary').click();})()");
  await until(() => mini.evaluate("document.querySelector('.feedback').innerText.includes('设备已回报音量 55%')"), "小程序音量回报");
  const miniVolume = await mini.evaluate("__hostCalls.find(c=>c.method==='deviceDataSet').params");
  assert.equal(typeof miniVolume, "string");
  assert.deepEqual(JSON.parse(miniVolume), { key: "prop.2.1", value: 55 });
  pass("小程序音量命令保留模板 JSON 字符串契约并等待设备回报");

  const unknown = await page({ mode: "mini", online: null });
  await until(() => unknown.evaluate("document.body.innerText.includes('产品 11910') && !document.querySelector('.primary').disabled"), "在线状态缺失的实机复现");
  assert.match(await unknown.evaluate("document.querySelector('.status-pill').innerText"), /在线状态未返回/);
  assert.equal(await unknown.evaluate("__hostCalls.some(call=>call.method==='getDeviceOnline')"), true);
  await click(unknown, "document.querySelectorAll('.tabs button')[1]");
  await click(unknown, "document.querySelector('.card .secondary')");
  await until(() => unknown.evaluate("document.querySelectorAll('.category-list button').length===1"), "状态未知时的分类列表");
  await click(unknown, "document.querySelector('.category-list button')");
  await until(() => unknown.evaluate("document.querySelectorAll('.resource-item').length===1"), "状态未知时的曲目列表");
  assert.equal(await unknown.evaluate("document.querySelector('.resource-item button').disabled"), false);
  await unknown.evaluate("document.querySelector('.resource-item button').click();document.querySelector('.resource-item button').click()");
  await until(() => unknown.evaluate("__apiCalls.filter(call=>call.route.endsWith('/resource/event')).length===1"), "状态未知时的播放提交");
  assert.match(await unknown.evaluate("document.querySelector('.playback-feedback').innerText"), /等待平台播放状态回报/);
  pass("复现无在线字段场景：不误标在线，曲目按钮可用，双击只发一次真实播放请求");
  await unknown.evaluate("__deliver('player',{method:'playerReply',params:{resourceId:999,playStatus:'playing'}})");
  await delay(100);
  assert.match(await unknown.evaluate("document.querySelector('.playback-feedback').innerText"), /等待平台播放状态回报/);
  await unknown.evaluate("__deliver('player',{method:'playerReply',params:{resourceId:42,playStatus:'playing'}})");
  await until(() => unknown.evaluate("document.querySelector('.playback-feedback').innerText.includes('平台回报：正在播放')"), "匹配资源的播放回报");
  pass("平台播放回报只更新匹配的资源，不把提交成功当作已播放");
  await unknown.evaluate("__playerBeforeResponse=true; document.querySelector('.resource-item button').click()");
  await until(() => unknown.evaluate("!document.querySelector('.resource-item button').disabled && document.querySelector('.playback-feedback').innerText.includes('平台回报：正在播放')"), "先到达的播放状态优先");
  pass("播放状态早于 HTTP 响应到达时不会回退为等待回报");
  await unknown.evaluate("__deliver('reportDeviceStatus',JSON.stringify({isOnline:false}))");
  await until(() => unknown.evaluate("document.querySelector('.resource-item button').disabled"), "字符串对象离线事件");
  assert.match(await unknown.evaluate("document.querySelector('.status-pill').innerText"), /设备离线/);
  await unknown.evaluate("__deliver('reportDeviceStatus',JSON.stringify({did:99999,isOnline:true}))");
  await delay(70);
  assert.equal(await unknown.evaluate("document.querySelector('.resource-item button').disabled"), true);
  await unknown.evaluate("__deliver('getDeviceOnline_reply',{isOnline:true})");
  await until(() => unknown.evaluate("!document.querySelector('.resource-item button').disabled"), "在线恢复事件");
  pass("对象或 JSON 离线事件禁写，其他设备状态不影响当前设备，明确在线后恢复");
  await unknown.evaluate("__deliver('onDeviceOnline',{isOnline:false})");
  await until(() => unknown.evaluate("document.querySelector('.resource-item button').disabled"), "小程序 false 对象");
  pass("修复模板把对象强转 true 的错误，{isOnline:false} 始终按离线处理");

  await mini.evaluate("(() => {__holdVolume=true; const range=document.querySelector('#volume');range.value='45';range.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('.primary').click();})()");
  await until(() => mini.evaluate("document.querySelector('.feedback').innerText.includes('尚未收到设备音量回报')"), "音量回报超时", 14000);
  assert.equal(await mini.evaluate("document.querySelector('#volume').value"), "45");
  assert.match(await mini.evaluate("document.querySelector('.volume-value').innerText"), /回报 55%/);
  pass("音量回报超时显示未确认，保留用户草稿与上次真实回报");

  const noAuth = await page({ mode: "rn", auth: false });
  await until(() => noAuth.evaluate("!document.querySelector('.primary').disabled"), "无授权设备初始化");
  await click(noAuth, "document.querySelectorAll('.tabs button')[1]");
  await click(noAuth, "document.querySelector('.card .secondary')");
  await until(() => noAuth.evaluate("document.querySelector('.notice')?.innerText.includes('没有提供平台访问授权')"), "缺少平台授权");
  assert.equal(await noAuth.evaluate("__apiCalls.length"), 0);
  pass("缺少宿主授权时不向平台发出业务请求");

  const alternate = await page({ mode: "rn", online: true, onlineField: "onlineStatus" });
  await until(() => alternate.evaluate("document.querySelector('.status-pill').innerText.includes('设备在线')"), "在线字段兼容");
  pass("设备信息 onlineStatus 别名兼容，未定义的 status 枚举不作为在线依据");

  await click(rn, "document.querySelectorAll('.tabs button')[0]");
  await rn.evaluate("(() => {const range=document.querySelector('#volume');range.value='70';range.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('.primary').click();})()");
  await delay(60);
  await rn.evaluate("__deliver('onDeviceInfoChange',{pid:11913,did:10002,deviceName:'另一台设备',onlionStatus:true});__deliver('onDeviceDataChange',{'prop.2.1':70});");
  await until(() => rn.evaluate("document.querySelector('.feedback').innerText.includes('设备已切换')"), "身份切换取消旧请求");
  assert.equal(await rn.evaluate("document.querySelector('.primary').disabled"), true);
  pass("切换产品或设备后，旧音量请求失效且禁止后续控制");

  for (const session of sessions) assert.deepEqual(session.errors, [], "页面存在未处理的 JavaScript 异常");
  pass("全部模拟页面无未处理 JavaScript 异常");
  await writeFile(path.join(output, "browser-check.json"), JSON.stringify({
    checkedAt: new Date().toISOString(), scope: "本地生产构建与模拟 RN/小程序宿主；未连接平台或真实硬件",
    checks, passed: checks.length, errors: 0
  }, null, 2) + "\n", "utf8");
} finally {
  for (const session of sessions) session.close();
  browser.kill();
}
