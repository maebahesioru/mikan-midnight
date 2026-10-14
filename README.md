# 真夜中のミカン — Midnight Mikan 🍊🔦

**A tiny top-down horror game for [Hack Club Scare](https://scare.hackclub.com/).**

真夜中のミカン園。誰もいないはずの畑に、みかんが8つだけ光っている。
集めて、門から出るんだ。……あなたは、ひとりじゃない。

*Midnight. An empty mikan orchard. Eight mikans glow in the dark. Gather them all and slip out the gate — but you are not alone.*

## How to play

Open `index.html` in a browser, or serve it:

```bash
python3 -m http.server 3966
```

- **Move**: Arrow keys / WASD / hold click-tap (touch supported)
- **Flashlight**: lights the direction you move — **when the light hits the watcher, it cowers and backs away**
- **Goal**: collect all **8 mikans**, then escape through the gate (it lights up once you have them all)
- Watch the heartbeat — it speeds up as *it* gets closer

## Features

- 🌑 Flashlight-only visibility (canvas composite darkness cone + mikan glows that shimmer in the dark)
- 👁 The Watcher — a shadow that hunts you; two of them by the end, and they drift straight through trees
- 💓 Procedural heartbeat audio that scales with danger, low drone, scare stinger, pickup chime — **zero audio files**
- 😱 Full-screen jumpscare when it catches you
- 🚪 Gate + clear-time + best time saved locally
- 🎨 Everything is procedural — terrain, trees, grain, vignette, faces. **Single HTML file, no assets, no dependencies**
- 📱 Touch + keyboard + pointer input

## Test

E2E suite (Playwright, headless Chromium) — 31 checks (movement, pickup, watcher light behavior, win/restart, jumpscare, rendering, zero JS errors):

```bash
uv run --with playwright python tests/e2e.py
```

## Notes

- The second watcher joins once you've collected 5 mikans — the last stretch is the loudest.
- The watcher is slower than you: you can run, but you can't run forever.
- Made for **Hack Club Scare** (Oct 2026). Tracked with Hackatime.
