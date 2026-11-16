// 宣傳片素材：用無頭 Chrome 拍詢價版的真實畫面（390×844，3 倍解析度），存到 promo\shots\
// 用法：先開本機伺服器（shengjia-site，5190），再 node promo\capture.mjs
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import { fileURLToPath } from "node:url";
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe", PORT = 9495;
const OUT = fileURLToPath(new URL("./shots", import.meta.url)), UDD = os.tmpdir() + "/promo-capture-prof";
const sleep = ms => new Promise(r => setTimeout(r, ms));
fs.mkdirSync(OUT, { recursive: true }); fs.rmSync(UDD, { recursive: true, force: true });
const proc = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${UDD}`, "--no-first-run", "--hide-scrollbars", "--disable-gpu", "about:blank"], { stdio: "ignore" });
let list; for (let i = 0; i < 60; i++) { try { list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); if (list.length) break; } catch {} await sleep(200); }
const ws = new WebSocket(list.find(t => t.type === "page").webSocketDebuggerUrl); await new Promise(r => ws.addEventListener("open", r));
let id = 0; const pend = new Map();
ws.addEventListener("message", e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result); pend.delete(m.id); } });
const send = (method, params = {}) => new Promise(res => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async x => (await send("Runtime.evaluate", { expression: x, awaitPromise: true, returnByValue: true })).result?.value;
const shot = async (name, full) => { await ev(`document.querySelector(".demo-bar").style.display="none";$("toast").classList.remove("show")`); await sleep(150); const p = { format: "png" }; if (full) { p.captureBeyondViewport = true; p.clip = { x: 0, y: 0, width: 390, height: full, scale: 1 }; } const r = await send("Page.captureScreenshot", p); fs.writeFileSync(`${OUT}/${name}.png`, Buffer.from(r.data, "base64")); };
await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 3, mobile: true });
await send("Page.navigate", { url: "http://localhost:5190/inquiry.html" }); await sleep(1500);
await ev(`localStorage.clear()`); await send("Page.reload"); await sleep(2500);
await ev(`document.querySelectorAll('.mq-track').forEach(t=>t.style.transform='translate3d(-60px,0,0)')`); await sleep(200);
await shot("01-home");
await ev(`setCat('壓縮機');window.scrollTo(0,document.getElementById('grid').getBoundingClientRect().top+scrollY-190)`); await sleep(800);
await shot("02-grid");
await ev(`nav('p-9')`); await sleep(1200); await shot("03-product");
await ev(`nav('models')`); await sleep(800); await ev(`$('mq').value='ZB26';drawModels();addModel('m:'+MODELS[0][1].find(r=>r[0].startsWith('ZB26'))[0])`); await sleep(1500); await shot("04-models");
await ev(`go('shop');add(1);add(2);cart['1']=2;renderHeader();openCart()`); await sleep(900); await shot("05-cart");
await ev(`openCheckout()`); await sleep(500); await ev(`$('cName').value='王老闆';document.querySelector('#checkoutBox form').requestSubmit()`); await sleep(900); await shot("06-line");
await ev(`closeModal('checkoutModal');nav('about')`); await sleep(900); await shot("07-about");
await ev(`localStorage.clear()`);
proc.kill(); await sleep(400); fs.rmSync(UDD, { recursive: true, force: true });
console.log(fs.readdirSync(OUT));
