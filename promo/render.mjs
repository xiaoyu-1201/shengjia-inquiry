// 宣傳片逐格輸出：node promo\render.mjs <beat秒> <輸出資料夾> [只截這些秒數,逗號分隔]
// 先開本機伺服器（shengjia-site，5190）。每格呼叫 seek(t) 再截圖，所以跟電腦快慢無關、每次結果一樣
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
const [beat = "0.4918", OUT = os.tmpdir() + "/promo-frames", only] = process.argv.slice(2);
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe", PORT = 9497, UDD = os.tmpdir() + "/promo-render-prof", FPS = 30;
const sleep = ms => new Promise(r => setTimeout(r, ms));
fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(OUT, { recursive: true }); fs.rmSync(UDD, { recursive: true, force: true });
const proc = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${UDD}`, "--no-first-run", "--hide-scrollbars", "--force-color-profile=srgb", "about:blank"], { stdio: "ignore" });
let list; for (let i = 0; i < 60; i++) { try { list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); if (list.length) break; } catch {} await sleep(200); }
const ws = new WebSocket(list.find(t => t.type === "page").webSocketDebuggerUrl); await new Promise(r => ws.addEventListener("open", r));
let id = 0; const pend = new Map(); const errs = [];
ws.addEventListener("message", e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result); pend.delete(m.id); } if (m.method === "Runtime.exceptionThrown") errs.push(m.params.exceptionDetails.exception?.description); });
const send = (method, params = {}) => new Promise(res => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async x => (await send("Runtime.evaluate", { expression: x, awaitPromise: true, returnByValue: true })).result?.value;
await send("Runtime.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1080, height: 1920, deviceScaleFactor: 1, mobile: false });
await send("Page.navigate", { url: `http://localhost:5190/promo/promo.html?beat=${beat}` }); await sleep(2000);
await ev("window.ready"); await sleep(500);
// 先把整支片從頭到尾跑一遍：網路字型是用到哪些字才下載哪些，沒先跑過，第一次出現的字會有幾格是空白
await ev(`(async()=>{for(let t=0;t<window.DURATION;t+=0.25){seek(t);await document.fonts.ready}seek(0)})()`); await sleep(1500); await ev("document.fonts.ready");
const dur = await ev("window.DURATION");
const times = only ? only.split(",").map(Number) : Array.from({ length: Math.ceil(dur * FPS) }, (_, i) => i / FPS);
let n = 0; const t0 = Date.now();
for (const t of times) {
  await ev(`seek(${t})`);
  const r = await send("Page.captureScreenshot", { format: "jpeg", quality: 92 });
  fs.writeFileSync(`${OUT}/${only ? "t" + t.toFixed(2) : String(n).padStart(5, "0")}.jpg`, Buffer.from(r.data, "base64")); n++;
  if (n % 150 === 0) console.log(n, "/", times.length, Math.round((Date.now() - t0) / 1000) + "s");
}
console.log("done", n, "frames", "dur", dur.toFixed(2), "errors", errs);
proc.kill(); await sleep(400); fs.rmSync(UDD, { recursive: true, force: true });
