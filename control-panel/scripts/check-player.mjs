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
      const categoryDelay=route.endsWith('/detail')?window.__categoryDelays?.[new URL(url).searchParams.get('categoryId')]:0;
      if(categoryDelay) await new Promise(resolve=>setTimeout(resolve,categoryDelay));
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
  await mkdir(output,{recursive:true});
  await until(async()=>{try{return(await fetch(`http://127.0.0.1:${debugPort}/json/version`)).ok;}catch{return false;}},"Edge启动",15000);
  const plain=await page();
  assert.equal(await plain.evaluate("document.querySelector('.main-play').disabled"),true);
  pass("无宿主时保持未连接，播放不可用");
  const client=await page({mode:"mini",online:null});
  await until(()=>client.evaluate("document.querySelectorAll('.track-list .track-row').length===3"),"自动载入曲目");
  assert.equal(await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/categories')).length"),1);
  assert.equal(await client.evaluate("document.body.innerText.includes('设备在线')"),false);
  pass("真实在线字段缺失仍自动载入分类与歌曲，无需点击读取");
  await client.evaluate("(()=>{const input=document.querySelector('.van-search input');input.value='月光';input.dispatchEvent(new Event('input',{bubbles:true}));})()");
  await until(()=>client.evaluate("document.querySelectorAll('.track-list .track-row').length===1"),"搜索曲目");
  assert.match(await client.evaluate("document.querySelector('.track-list').innerText"),/月光/);
  await client.evaluate("(()=>{const input=document.querySelector('.van-search input');input.value='';input.dispatchEvent(new Event('input',{bubbles:true}));})()");
  await until(()=>client.evaluate("document.querySelectorAll('.track-list .track-row').length===3"),"取消搜索");
  pass("搜索即时筛选当前分类，清空恢复曲目列表");
  await client.evaluate("document.querySelector('[data-track=\"42\"]').click();document.querySelector('[data-track=\"42\"]').click()");
  await until(()=>client.evaluate("!document.querySelector('.main-play').disabled && document.querySelector('.main-play').getAttribute('aria-label')==='暂停'"),"播放提交");
  assert.equal(await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).length"),1);
  assert.match(await client.evaluate("document.querySelector('.player-feedback').innerText"),/等待设备响应/);
  pass("一键播放并建立队列，重复点击只提交一次，成功提交不冒充已出声");
  await click(client,"document.querySelector('.main-play')");
  await until(()=>client.evaluate("document.querySelector('.main-play').getAttribute('aria-label')==='继续播放'"),"暂停");
  await click(client,"document.querySelector('.main-play')");
  await until(()=>client.evaluate("document.querySelector('.main-play').getAttribute('aria-label')==='暂停'"),"继续");
  const actions=await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).map(c=>c.body.receiveBody.subMethod)");
  assert.deepEqual(actions,["play","pause","resume"]);
  pass("播放/暂停/继续映射模板平台事件，控件切换符合操作意图");
  await click(client,"document.querySelector('[aria-label=\"下一首\"]')");
  await until(()=>client.evaluate("document.querySelector('.player-track strong').innerText==='月光里的小船' && !document.querySelector('.main-play').disabled"),"下一首");
  await click(client,"document.querySelector('[aria-label=\"上一首\"]')");
  await until(()=>client.evaluate("document.querySelector('.player-track strong').innerText==='小星星的旅行' && !document.querySelector('.main-play').disabled"),"上一首");
  pass("上一首/下一首按当前队列切换");
  await click(client,"document.querySelector('[aria-label=\"播放队列\"]')");
  await until(()=>client.evaluate("document.querySelector('.queue-sheet')?.innerText.includes('晚安，森林')"),"队列弹层");
  assert.equal(await client.evaluate("document.querySelectorAll('.queue-sheet .track-row').length"),3);
  await click(client,"document.querySelector('.queue-sheet .van-popup__close-icon')");
  await delay(350);
  pass("队列弹层显示完整队列，不因搜索而丢曲目");
  await client.evaluate("__deliver('player',{method:'playerReply',params:{resourceId:42,playStatus:'playing'}})");
  await delay(70);
  await client.evaluate("__deliver('player',{method:'playerReply',params:{resourceId:42,playStatus:'stopped',reason:'completed'}})");
  await until(()=>client.evaluate("document.querySelector('.player-track strong').innerText==='月光里的小船' && !document.querySelector('.main-play').disabled"),"自然结束续播");
  const beforeDuplicate=await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).length");
  await client.evaluate("__deliver('player',{method:'playerReply',params:{resourceId:42,playStatus:'stopped',reason:'completed'}})");
  await delay(150);
  assert.equal(await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).length"),beforeDuplicate);
  pass("自然结束回报驱动下一首，重复/旧资源完成回报不重复切歌");
  await click(client,"document.querySelector('.mode-button')");
  await click(client,"document.querySelector('.mode-button')");
  assert.equal(await client.evaluate("document.querySelector('.mode-button').getAttribute('aria-label')"),"单曲循环");
  await client.evaluate("__deliver('player',{method:'playerReply',params:{resourceId:43,playStatus:'playing'}})");
  await delay(70);
  await client.evaluate("__deliver('player',{method:'playerReply',params:{resourceId:43,playStatus:'finished'}})");
  await until(()=>client.evaluate(`__apiCalls.filter(c=>c.route.endsWith('/resource/event')).length>${beforeDuplicate}`),"单曲循环回报");
  assert.equal(await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).at(-1).body.receiveBody.params.resourceId"),43);
  await until(()=>client.evaluate("!document.querySelector('.main-play').disabled"),"循环提交完成");
  pass("单曲循环重复当前曲目，依赖真实结束回报而非时长计时");
  await click(client,"document.querySelector('[aria-label=\"停止播放\"]')");
  await until(()=>client.evaluate("document.querySelector('.main-play').getAttribute('aria-label')==='播放'"),"停止");
  assert.equal(await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).at(-1).body.receiveBody.subMethod"),"stop");
  const afterStop=await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).length");
  await client.evaluate("__deliver('player',{method:'playerReply',params:{resourceId:43,playStatus:'stopped',reason:'cancelled'}})");
  await delay(150);
  assert.equal(await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).length"),afterStop);
  pass("停止映射stop，用户停止不触发循环续播");
  await click(client,"document.querySelector('.mode-button')");
  await click(client,"document.querySelector('.mode-button')");
  await click(client,"document.querySelector('.mode-button')");
  assert.equal(await client.evaluate("document.querySelector('.mode-button').getAttribute('aria-label')"),"列表循环");
  await click(client,"document.querySelector('[data-track=\"44\"]')");
  await until(()=>client.evaluate("!document.querySelector('.main-play').disabled"),"末首播放");
  await client.evaluate("__deliver('player',{params:{resourceId:44,playStatus:'playing'}})");await delay(70);
  await client.evaluate("__deliver('player',{params:{resourceId:44,playStatus:'finished'}})");
  await until(()=>client.evaluate("document.querySelector('.player-track strong').innerText==='小星星的旅行' && !document.querySelector('.main-play').disabled"),"列表循环回到首首");
  pass("列表循环在末首自然结束后回到第一首");
  await click(client,"document.querySelector('.mode-button')");await click(client,"document.querySelector('.mode-button')");await click(client,"document.querySelector('.mode-button')");
  assert.equal(await client.evaluate("document.querySelector('.mode-button').getAttribute('aria-label')"),"顺序播放");
  await click(client,"document.querySelector('[data-track=\"44\"]')");
  await until(()=>client.evaluate("!document.querySelector('.main-play').disabled"),"末首重新播放");
  const orderEndCount=await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).length");
  await client.evaluate("__deliver('player',{params:{resourceId:44,playStatus:'playing'}})");await delay(70);
  await client.evaluate("__deliver('player',{params:{resourceId:44,playStatus:'finished'}})");await delay(150);
  assert.equal(await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).length"),orderEndCount);
  assert.match(await client.evaluate("document.querySelector('.player-feedback').innerText"),/队列已结束/);
  pass("顺序播放在末首结束后停下，不偷偷循环");
  await click(client,"document.querySelector('.mode-button')");await click(client,"document.querySelector('.mode-button')");await click(client,"document.querySelector('.mode-button')");
  assert.equal(await client.evaluate("document.querySelector('.mode-button').getAttribute('aria-label')"),"随机播放");
  await click(client,"document.querySelector('[aria-label=\"下一首\"]')");
  await until(()=>client.evaluate("!document.querySelector('.main-play').disabled"),"随机切歌");
  assert.notEqual(await client.evaluate("__apiCalls.filter(c=>c.route.endsWith('/resource/event')).at(-1).body.receiveBody.params.resourceId"),44);
  pass("随机切歌在多首队列中不会再次选中当前曲目");
  const currentBeforeFailure=await client.evaluate("document.querySelector('.player-track strong').innerText");
  await client.evaluate("__failApi=true");
  await click(client,"document.querySelector('[data-track=\"44\"]')");
  await until(()=>client.evaluate("document.querySelector('.player-feedback').innerText.includes('播放未成功')"),"播放失败");
  assert.equal(await client.evaluate("document.querySelector('.player-track strong').innerText"),currentBeforeFailure);
  await client.evaluate("__failApi=false;__categoryDelays={'3':250}");
  await client.evaluate("Array.from(document.querySelectorAll('.category-tabs [role=tab]')).find(e=>e.innerText==='轻音乐').click()");
  await delay(50);
  await client.evaluate("Array.from(document.querySelectorAll('.category-tabs [role=tab]')).find(e=>e.innerText==='睡前故事').click()");await delay(350);
  assert.match(await client.evaluate("document.querySelector('.track-list').innerText"),/小星星/);
  assert.doesNotMatch(await client.evaluate("document.querySelector('.track-list').innerText"),/午后/);
  assert.equal(await client.evaluate("document.querySelector('.queue-count').innerText"),"3");
  pass("播放失败保留旧队列，慢分类回包不覆盖新分类或当前播放队列");
  // 复核保存偏好：随机模式再切两次到单曲循环。
  await click(client,"document.querySelector('.mode-button')");await click(client,"document.querySelector('.mode-button')");await click(client,"document.querySelector('.mode-button')");
  await click(client,"document.querySelector('[aria-label=\"切换皮肤\"]')");
  await delay(350);
  await click(client,"document.querySelector('[data-skin-choice=\"dark\"]')");
  assert.equal(await client.evaluate("document.documentElement.dataset.skin"),"dark");
  await click(client,"document.querySelector('.theme-sheet .van-popup__close-icon')");
  await delay(350);
  const darkCapture=await client.send("Page.captureScreenshot",{format:"png",captureBeyondViewport:false});
  await writeFile(path.join(output,"player-dark-fixture.png"),Buffer.from(darkCapture.data,"base64"));
  await client.send("Page.reload");
  await until(()=>client.evaluate("document.querySelectorAll('.track-list .track-row').length===3"),"重开页面");
  assert.equal(await client.evaluate("document.documentElement.dataset.skin"),"dark");
  assert.equal(await client.evaluate("document.querySelector('.mode-button').getAttribute('aria-label')"),"单曲循环");
  pass("皮肤与播放模式在重开后保留，不持久化设备授权或队列");
  await click(client,"document.querySelector('[aria-label=\"切换皮肤\"]')");await delay(350);
  await click(client,"document.querySelector('[data-skin-choice=\"forest\"]')");
  await click(client,"document.querySelector('.theme-sheet .van-popup__close-icon')");await delay(350);
  for(const width of [320,390,900]){
    await client.send("Emulation.setDeviceMetricsOverride",{width,height:844,deviceScaleFactor:1,mobile:width<700});
    await delay(120);
    assert.equal(await client.evaluate("document.documentElement.scrollWidth<=window.innerWidth+1"),true,`水平溢出${width}`);
  }
  pass("320px、390px与桌面宽度均无横向溢出");
  await client.send("Emulation.setDeviceMetricsOverride",{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await delay(150);
  const forestCapture=await client.send("Page.captureScreenshot",{format:"png",captureBeyondViewport:false});
  await writeFile(path.join(output,"player-forest-fixture.png"),Buffer.from(forestCapture.data,"base64"));
  await click(client,"document.querySelector('[aria-label=\"切换皮肤\"]')");await delay(350);
  await click(client,"document.querySelector('[data-skin-choice=\"light\"]')");
  await click(client,"document.querySelector('.theme-sheet .van-popup__close-icon')");await delay(350);
  const lightCapture=await client.send("Page.captureScreenshot",{format:"png",captureBeyondViewport:false});
  await writeFile(path.join(output,"player-light-fixture.png"),Buffer.from(lightCapture.data,"base64"));
  pass("三套主题复用同一组件布局，截图已保存供视觉复核");
  await client.evaluate("document.querySelector('.track-list .track-row:last-child').scrollIntoView({block:'center'})");await delay(150);
  assert.equal(await client.evaluate("document.querySelector('.track-list .track-row:last-child').getBoundingClientRect().bottom<=document.querySelector('.player-bar').getBoundingClientRect().top"),true);
  pass("曲目列表最后一首可滚动到固定播放器上方，不被底栏遮住");
  await client.evaluate("__deliver('onDeviceOnline',{isOnline:false})");
  await until(()=>client.evaluate("document.querySelector('.main-play').disabled"),"明确离线");
  pass("明确离线时所有硬件写入控件禁用");
  const mismatch=await page({mode:"rn",pid:11913});
  await until(()=>mismatch.evaluate("document.body.innerText.includes('请先在小程序中打开已绑定的设备')"),"身份不匹配");
  assert.equal(await mismatch.evaluate("__apiCalls.length"),0);
  pass("错误PID不请求资源或发送控制");
  const noAuth=await page({mode:"rn",auth:false});
  await until(()=>noAuth.evaluate("document.body.innerText.includes('没有提供平台访问授权')"),"无授权");
  assert.equal(await noAuth.evaluate("__apiCalls.length"),0);
  pass("缺少宿主授权显示可重试错误，不向平台发业务请求");
  const rnPlayer=await page({mode:"rn"});
  await until(()=>rnPlayer.evaluate("document.querySelectorAll('.track-list .track-row').length===3"),"RN自动资源读取");
  await click(rnPlayer,"document.querySelector('[data-track=\"42\"]')");
  await until(()=>rnPlayer.evaluate("!document.querySelector('.main-play').disabled"),"RN播放请求");
  await rnPlayer.evaluate("__deliver('player',{params:{resourceId:42,playStatus:'playing',positionMs:3000}})");
  await until(()=>rnPlayer.evaluate("document.querySelector('.player-feedback').innerText==='正在播放'"),"RN播放状态");
  pass("RN原生player回调也可确认状态与进度，保留小程序契约");
  const contrastChecks=[];
  const luminance=hex=>{const h=hex.replace('#','');const full=h.length===3?h.split('').map(c=>c+c).join(''):h;const rgb=[0,2,4].map(i=>parseInt(full.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];};
  for(const skin of ['light','dark','forest']){
    await click(rnPlayer,"document.querySelector('[aria-label=\"切换皮肤\"]')");await delay(320);
    await click(rnPlayer,`document.querySelector('[data-skin-choice="${skin}"]')`);
    const colors=await rnPlayer.evaluate("(()=>{const s=getComputedStyle(document.documentElement);return Object.fromEntries(['--text','--muted','--accent','--on-accent','--app-bg','--surface'].map(key=>[key,s.getPropertyValue(key).trim()]));})()");
    for(const [fg,bg] of [['--text','--app-bg'],['--muted','--app-bg'],['--muted','--surface'],['--accent','--app-bg'],['--on-accent','--accent']]){
      const a=luminance(colors[fg]),b=luminance(colors[bg]),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
      assert.ok(ratio>=4.5,`${skin} ${fg}/${bg} 对比度 ${ratio}`);
      contrastChecks.push({skin,foreground:fg,background:bg,ratio:Number(ratio.toFixed(2))});
    }
    await click(rnPlayer,"document.querySelector('.theme-sheet .van-popup__close-icon')");await delay(320);
  }
  await writeFile(path.join(output,'theme-contrast-check.json'),JSON.stringify({scope:'三主题基础文字/辅助文字/操作色token，非完整WCAG或临床评估',checks:contrastChecks},null,2)+'\n','utf8');
  pass("三主题15组文字与操作色对比度均不少于4.5:1，不以高饱和度代替可读性");
  for(const skin of ['light','dark','forest']){
    const preview=await page({mode:'mini',online:true});
    await preview.send('Page.bringToFront');
    await preview.send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:3,mobile:true});
    await until(()=>preview.evaluate("document.querySelectorAll('.track-list .track-row').length===3"),'预览载入');
    await click(preview,"document.querySelector('[data-track=\"42\"]')");
    await until(()=>preview.evaluate("!document.querySelector('.main-play').disabled"),'预览播放请求');
    await preview.evaluate("__deliver('player',{params:{resourceId:42,playStatus:'playing'}})");
    await click(preview,"document.querySelector('[aria-label=\"切换皮肤\"]')");await delay(350);
    await click(preview,`document.querySelector('[data-skin-choice="${skin}"]')`);
    await click(preview,"document.querySelector('.theme-sheet .van-popup__close-icon')");await delay(550);
    assert.equal(await preview.evaluate("document.querySelectorAll('.app-header').length"),1);
    assert.deepEqual(await preview.evaluate("[getComputedStyle(document.querySelector('.brand strong')).fontSize,getComputedStyle(document.querySelector('.section-heading h2')).fontSize,getComputedStyle(document.querySelector('.track-info strong')).fontSize]"),['22px','17px','15px']);
    assert.equal(await preview.evaluate("document.body.innerText.includes('平台回报') || document.body.innerText.includes('PID')"),false);
    const shot=await preview.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    await writeFile(path.join(output,`player-${skin}-fixture.png`),Buffer.from(shot.data,'base64'));
  }
  pass('三主题实际预览单实例渲染，主界面无PID/平台回报等开发用语');
  for(const session of sessions)assert.deepEqual(session.errors,[]);
  pass("全部生产页面无未处理JavaScript异常");
  await writeFile(path.join(output,"browser-check-player.json"),JSON.stringify({checkedAt:new Date().toISOString(),scope:"生产构建+虚构RN/小程序宿主；不代表平台/硬件实测",checks,passed:checks.length,errors:0},null,2)+"\n","utf8");
} finally {for(const session of sessions)session.close();browser.kill();}
