#!/usr/bin/env python3
"""Midnight Mikan — E2E test (Playwright, headless Chromium).

Run:
  uv run --with playwright python tests/e2e.py

Covers: title screen, start flow, keyboard movement + facing, mikan pickup,
HUD counters, watcher light/cower behavior (lit -> retreats, unlit -> hunts),
full collect -> gate -> win + best time, restart, caught jumpscare -> game over,
canvas rendering, zero JS errors.
"""
import asyncio
import json
import pathlib

from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent.parent
URL = (HERE / "index.html").as_uri()

results = {}
checks = []


def check(name: str, ok: bool, detail=""):
    checks.append((name, ok, detail))


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on(
            "console",
            lambda m: errors.append(f"console.{m.type}: {m.text}")
            if m.type == "error"
            else None,
        )

        await page.goto(URL)
        await page.wait_for_timeout(600)

        # 1. title screen
        check("title screen visible", await page.locator("#title").is_visible())
        results["h1"] = await page.text_content("#title h1")
        check("h1 = 真夜中のミカン", "真夜中のミカン" in (results["h1"] or ""), results["h1"])
        check("hud hidden on title", await page.locator("#hud").is_hidden())
        results["mikan_count"] = await page.evaluate("MM.mikans.length")
        check("8 mikans spawned", results["mikan_count"] == 8, str(results["mikan_count"]))
        check("state starts as title", await page.evaluate("MM.state") == "title")

        # 2. start
        await page.click("#startBtn")
        await page.wait_for_timeout(350)
        check("state -> play", await page.evaluate("MM.state") == "play")
        check("title hidden after start", await page.locator("#title").is_hidden())
        check("hud visible in play", await page.locator("#hud").is_visible())

        # 3. keyboard movement + facing
        x0 = await page.evaluate("MM.player.x")
        await page.keyboard.down("ArrowRight")
        await page.wait_for_timeout(600)
        await page.keyboard.up("ArrowRight")
        x1 = await page.evaluate("MM.player.x")
        check("ArrowRight moves player", x1 > x0 + 30, f"{x0:.0f} -> {x1:.0f}")
        face = await page.evaluate("MM.player.face")
        check("facing follows movement (right)", abs(face) < 0.6, str(face))
        y0 = await page.evaluate("MM.player.y")
        await page.keyboard.down("w")
        await page.wait_for_timeout(400)
        await page.keyboard.up("w")
        y1 = await page.evaluate("MM.player.y")
        check("W moves player up", y1 < y0 - 20, f"{y0:.0f} -> {y1:.0f}")

        # 4. mikan collection
        await page.evaluate("MM.player.x = MM.mikans[0].x; MM.player.y = MM.mikans[0].y")
        await page.wait_for_timeout(250)
        results["collected"] = await page.evaluate("MM.collected")
        check("mikan collected on touch", results["collected"] == 1, str(results["collected"]))
        results["hud_count"] = await page.text_content("#hudCount")
        check("hud count updates", results["hud_count"] == "1", results["hud_count"])
        check("mikan marked got", await page.evaluate("!!MM.mikans[0].got") is True)

        # 5. watcher behavior: lit -> cowers + backs away; unlit -> hunts
        await page.evaluate(
            "MM.player.face = 0; MM.watchers[0].active = true; "
            "MM.watchers[0].x = MM.player.x + 120; MM.watchers[0].y = MM.player.y"
        )
        await page.wait_for_timeout(250)
        check("watcher lit in front", await page.evaluate("MM.watchers[0].lit") is True)
        d0 = await page.evaluate("Math.hypot(MM.watchers[0].x - MM.player.x, MM.watchers[0].y - MM.player.y)")
        await page.wait_for_timeout(600)
        d1 = await page.evaluate("Math.hypot(MM.watchers[0].x - MM.player.x, MM.watchers[0].y - MM.player.y)")
        check("lit watcher backs away", d1 > d0 + 5, f"{d0:.0f} -> {d1:.0f}")
        await page.evaluate("MM.watchers[0].x = MM.player.x - 200; MM.watchers[0].y = MM.player.y")
        await page.wait_for_timeout(250)
        check("watcher behind not lit", await page.evaluate("MM.watchers[0].lit") is False)
        d2 = await page.evaluate("Math.hypot(MM.watchers[0].x - MM.player.x, MM.watchers[0].y - MM.player.y)")
        await page.wait_for_timeout(600)
        d3 = await page.evaluate("Math.hypot(MM.watchers[0].x - MM.player.x, MM.watchers[0].y - MM.player.y)")
        check("unlit watcher approaches", d3 < d2 - 20, f"{d2:.0f} -> {d3:.0f}")
        # park both watchers far away for the win sequence
        await page.evaluate(
            "MM.watchers.forEach(w => { w.x = 40; w.y = 40; });"
            "MM.watchers[1].active = false; MM.watchers[1].spawnDelay = 9999;"
        )

        # 6. collect all 8 -> gate -> win
        for _ in range(10):
            if await page.evaluate("MM.collected") >= 8:
                break
            await page.evaluate(
                "(()=>{const m = MM.mikans.find(m => !m.got); if (m) { MM.player.x = m.x; MM.player.y = m.y; }})()"
            )
            await page.wait_for_timeout(150)
        results["collected_all"] = await page.evaluate("MM.collected")
        check("all 8 collected", results["collected_all"] == 8, str(results["collected_all"]))
        # re-park watchers (they activate at 5 collected) then head for the gate
        await page.evaluate("MM.watchers.forEach(w => { w.x = 40; w.y = 940; })")
        await page.evaluate("MM.player.x = MM.gate.x; MM.player.y = MM.gate.y")
        await page.wait_for_timeout(350)
        check("state -> win at gate", await page.evaluate("MM.state") == "win")
        check("win screen visible", await page.locator("#win").is_visible())
        results["win_text"] = await page.text_content("#winResult")
        check("win result shows time", "クリアタイム" in (results["win_text"] or ""), results["win_text"])
        best = await page.evaluate("localStorage.getItem('midnight-mikan-best')")
        results["best"] = best
        check("best time saved", bool(best) and float(best) > 0, str(best))

        # 7. restart from win
        await page.click("#againBtn")
        await page.wait_for_timeout(350)
        check("restart -> play", await page.evaluate("MM.state") == "play")
        check("restart resets count", await page.evaluate("MM.collected") == 0)
        results["respawn"] = await page.evaluate("MM.mikans.filter(m => !m.got).length")
        check("restart respawns 8 mikans", results["respawn"] == 8, str(results["respawn"]))

        # 8. caught -> jumpscare -> game over
        await page.evaluate(
            "MM.watchers[0].active = true; MM.watchers[0].spawnDelay = 0;"
            "MM.watchers[0].x = MM.player.x + 20; MM.watchers[0].y = MM.player.y"
        )
        await page.wait_for_timeout(400)
        check("state -> caught", await page.evaluate("MM.state") == "caught")
        await page.wait_for_timeout(1400)
        check("over screen appears after scare", await page.locator("#over").is_visible())
        results["over_text"] = await page.text_content("#overResult")
        check("over result text", "集めたみかん" in (results["over_text"] or ""), results["over_text"])

        # 9. canvas rendering (sample the center — the scare face / world are centered)
        px = await page.evaluate(
            """() => { const c = document.getElementById('game');
                 const w = Math.min(240, c.width), h = Math.min(240, c.height);
                 const x0 = Math.floor((c.width - w) / 2), y0 = Math.floor((c.height - h) / 2);
                 const d = c.getContext('2d').getImageData(x0, y0, w, h).data;
                 let n = 0; for (let i = 0; i < d.length; i += 4) { if (d[i] > 8 || d[i+1] > 8 || d[i+2] > 8) n++; } return n; }"""
        )
        results["canvas_px"] = px
        check("canvas has rendered pixels", px > 100, str(px))

        # 10. no JS errors
        results["js_errors"] = errors
        check("no JS errors", len(errors) == 0, "; ".join(errors[:3]))

        await browser.close()

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print()
    passed = sum(1 for _, ok, _ in checks if ok)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if not ok else ""))
    print(f"\n{passed}/{len(checks)} passed")
    raise SystemExit(0 if passed == len(checks) else 1)


asyncio.run(main())
