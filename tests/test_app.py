#!/usr/bin/env python3
"""
Automatische browsertest voor Dactylo Supreme (index.html).

Eenmalig installeren (in WSL, vanuit de repo):
    python3 -m venv .venv
    source .venv/bin/activate
    pip install playwright
    python -m playwright install --with-deps chromium

Draaien:
    source .venv/bin/activate
    python3 -m http.server 8765 >/dev/null 2>&1 &
    python3 tests/test_app.py                      # of met een andere URL als argument
    kill %1                                        # server stoppen

Screenshots komen in /tmp/dactylo-shots (pas aan met DACTYLO_SHOTS).
De test is generiek: hij doorloopt alle lessen die in index.html staan,
dus hij groeit vanzelf mee met nieuwe modules.
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DACTYLO_URL", "http://localhost:8765/index.html")
SHOTS = os.environ.get("DACTYLO_SHOTS", "/tmp/dactylo-shots")
CHROME = os.environ.get("CHROME_PATH")  # optioneel: pad naar een eigen Chromium
STORAGE_KEY = "dactylo-be-azerty"
os.makedirs(SHOTS, exist_ok=True)

failures = []


def check(cond, msg):
    if cond:
        print("ok  :", msg)
    else:
        failures.append(msg)
        print("FAIL:", msg)


# Typt tekst zoals een echt toetsenbord: eerst een keydown op het document, daarna een
# input-event in het verborgen tekstveld #catch (zo komen tekens in de app binnen).
# '\n' wordt Enter en '\t' wordt Tab: die gaan enkel via keydown.
TYPE_JS = """async ([text, delay]) => {
  for (const ch of text) {
    const key = ch === '\\n' ? 'Enter' : ch === '\\t' ? 'Tab' : ch;
    document.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
    const field = document.getElementById('catch');
    if (key.length === 1 && field) field.dispatchEvent(new InputEvent('input', { inputType: 'insertText', data: ch, bubbles: true }));
    if (delay) await new Promise(r => setTimeout(r, delay));
  }
}"""

# Een teken met een dode toets, zoals de browser het aanlevert: keydown 'Dead', compositie-events
# en input-events. Chrome stuurt het laatste input-event vóór compositionend; 'safari' bootst een
# input-event ná compositionend na, 'webkit' een insertFromComposition ervoor. Welke volgorde
# Safari echt gebruikt, is nog niet op de Mac bevestigd: de app moet ze alle drie aankunnen.
# Geeft terug hoeveel posities, aanslagen en fouten erbij kwamen (verwacht: 1, 1, 0).
COMPOSE_JS = """(order) => {
  const R = window.__dactylo.run();
  const field = document.getElementById('catch');
  const ch = R.text[R.pos];
  const before = [R.pos, R.keystrokes, R.errors];
  const comp = (type, data) => field.dispatchEvent(new CompositionEvent(type, { data, bubbles: true }));
  const inp = (inputType, data, isComposing) => field.dispatchEvent(new InputEvent('input', { inputType, data, isComposing, bubbles: true }));
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Dead', bubbles: true, cancelable: true }));
  comp('compositionstart', '');
  inp('insertCompositionText', '^', true);
  document.dispatchEvent(new KeyboardEvent('keydown', { key: ch, isComposing: true, bubbles: true, cancelable: true }));
  if (order === 'chrome') { inp('insertCompositionText', ch, true); comp('compositionend', ch); }
  else if (order === 'webkit') { inp('insertFromComposition', ch, false); comp('compositionend', ch); }
  else { comp('compositionend', ch); inp('insertFromComposition', ch, false); }
  return [R.pos - before[0], R.keystrokes - before[1], R.errors - before[2]];
}"""

# Toegelaten tekens per les. Gebruikt window.__dactylo.allowed(id) als de app die aanbiedt,
# anders de gekende letters plus spatie (zo werkt versie 0.1.x).
ALLOWED_JS = """(id) => {
  const d = window.__dactylo;
  return d.allowed ? Array.from(d.allowed(id)) : d.known[id].concat([' ']);
}"""

# Opslag zoals versie 0.1.0 die schreef. Elke nieuwe versie moet dit nog kunnen lezen.
V010_STATE = {
    "schema": 1,
    "created": 1791450000000,
    "settings": {"name": "Test", "layout": "auto", "errorMode": "block", "help": "auto", "theme": "auto"},
    "lessons": {
        "m1-houding": {"passed": True, "bestAcc": 100, "bestApm": 80, "attempts": 1},
        "m1-vingers": {"passed": True, "bestAcc": 98.5, "bestApm": 90, "attempts": 2},
    },
    "sessions": [{"t": 1791450000000, "l": "m1-houding", "x": 2, "k": "test", "apm": 80, "acc": 100, "n": 110, "e": 0, "ms": 82000}],
    "keys": {"f": {"h": 120, "e": 3}, "j": {"h": 118, "e": 1}},
    "days": {"2026-10-08": 600000},
    "totalMs": 600000,
    "baseline": None,
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        js_errors, failed_requests = [], []
        page.on("console", lambda m: js_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: js_errors.append("PAGEERROR " + str(e)))
        page.on("requestfailed", lambda r: failed_requests.append(r.url))

        def typ(text, delay=0):
            page.evaluate(TYPE_JS, [text, delay])

        def run_text():
            return page.evaluate("() => window.__dactylo.run() ? window.__dactylo.run().text : null")

        def record(lesson_id):
            return page.evaluate("(id) => window.__dactylo.state().lessons[id] || null", lesson_id)

        def play_lesson(lesson_id, fail_test=False, delay=0):
            page.goto(URL + "#/les/" + lesson_id)
            page.wait_for_selector("[data-act=start]")
            page.keyboard.press("Enter")
            n = page.evaluate("() => window.__dactylo.flow().plan.length")
            for i in range(n):
                page.wait_for_selector("#strip")
                text = run_text()
                last = i == n - 1
                if fail_test and last:
                    # om de twee tekens eerst een verkeerde toets: ongeveer 67% nauwkeurig
                    for idx, ch in enumerate(text):
                        if idx % 2 == 0:
                            typ("q" if ch != "q" else "m")
                        typ(ch)
                else:
                    typ(text, delay if i == 1 else 0)
                page.wait_for_selector(".result")
                if not last:
                    page.keyboard.press("Enter")
            return record(lesson_id)

        # 1. Upgrade: opslag van versie 0.1.0 moet blijven werken
        page.goto(URL)
        page.evaluate("([k, v]) => { localStorage.clear(); localStorage.setItem(k, v); }", [STORAGE_KEY, json.dumps(V010_STATE)])
        page.reload()
        page.wait_for_selector(".hero")
        st = page.evaluate("() => window.__dactylo.state()")
        check(st["lessons"].get("m1-houding", {}).get("passed") and st["lessons"].get("m1-vingers", {}).get("passed"),
              "upgrade: geslaagde lessen uit versie 0.1.0 blijven geslaagd")
        check(st["settings"]["name"] == "Test" and st["keys"]["f"]["h"] == 120, "upgrade: instellingen en toetsstatistieken blijven bewaard")
        check(page.evaluate("() => localStorage.getItem('%s') !== null" % STORAGE_KEY), f"opslag staat nog onder '{STORAGE_KEY}'")

        # 1b. Een geslaagde les blijft open, ook als de les ervoor (nog) niet geslaagd is
        only_later = dict(V010_STATE, lessons={"m2-sl": {"passed": True, "bestAcc": 99, "bestApm": 100, "attempts": 1}})
        page.evaluate("([k, v]) => localStorage.setItem(k, v)", [STORAGE_KEY, json.dumps(only_later)])
        page.reload()
        page.wait_for_selector(".hero")
        page.goto(URL + "#/les/m2-sl")
        page.wait_for_timeout(300)
        check(page.evaluate("() => location.hash") == "#/les/m2-sl" and page.query_selector("[data-act=start]") is not None,
              "een geslaagde les blijft open, ook als de vorige les niet geslaagd is")
        page.goto(URL)
        page.evaluate("() => localStorage.clear()")
        page.reload()
        page.wait_for_selector(".hero")

        # 2. Leerplan
        info = page.evaluate("""() => {
          const d = window.__dactylo;
          const ids = d.lessons.map(l => l.id);
          return {
            version: d.version,
            modules: d.modules.length,
            planned: d.modules.reduce((a, m) => a + m.planned, 0),
            built: d.modules.filter(m => m.lessons.length).map(m => [m.nr, m.lessons.length, m.planned]),
            ids: ids,
            unique: new Set(ids).size === ids.length
          };
        }""")
        print("versie", info["version"], "-", len(info["ids"]), "lessen gebouwd")
        check(info["modules"] == 13, f"13 modules ({info['modules']})")
        check(info["planned"] == 126, f"126 lessen gepland ({info['planned']})")
        for nr, have, planned in info["built"]:
            check(have == planned, f"module {nr}: {have} van {planned} lessen gebouwd")
        check(info["unique"], "alle les-ids uniek")

        # 2b. Hulp van het toetsenbord volgens het leerplan (CLAUDE.md): modules 4-9 nieuwe lessen
        # 'full' en de andere 'hint', modules 10-11 'hint', modules 12-13 'none'
        helps = page.evaluate("() => window.__dactylo.lessons.map(l => [l.id, l.module.nr, l.type, l.help])")
        def want_help(nr, typ_):
            if 4 <= nr <= 9: return "full" if typ_ == "new" else "hint"
            if nr in (10, 11): return "hint"
            if nr >= 12: return "none"
            return None
        wrong_help = [f"{i}={h}" for i, nr, typ_, h in helps if want_help(nr, typ_) not in (None, h)]
        check(not wrong_help, f"hulpniveau per les volgens het leerplan {wrong_help[:5]}")

        # 3. Oefenteksten: enkel toegelaten tekens, redelijke lengte, nieuwe toetsen aanwezig
        gen = page.evaluate("""() => {
          const d = window.__dactylo;
          const problems = []; let count = 0;
          for (const l of d.lessons) {
            if (l.type === 'baseline') continue;
            const allowed = new Set(d.allowed ? d.allowed(l.id) : d.known[l.id].concat([' ']));
            const plan = d.planFor(l);
            for (let seed = 1; seed <= 100; seed++) {
              plan.forEach((ex, i) => {
                const t = ex.make(d.makeCtx(l, seed * 31 + i)).replace(/ +/g, ' ').trim();
                count++;
                if (t.length < 30) problems.push(l.id + ' #' + i + ' te kort (' + t.length + ')');
                if (t.length > 2500) problems.push(l.id + ' #' + i + ' te lang (' + t.length + ')');
                for (const ch of t) if (!allowed.has(ch)) { problems.push(l.id + ' #' + i + ' bevat ' + JSON.stringify(ch)); break; }
                if (/(^|\s)Ij[a-z]/.test(t)) problems.push(l.id + ' #' + i + ' schrijft Ij in plaats van IJ');
                const sp = t.match(/.{0,8}( [,;:!?.)]|\( |[,;!?][A-Za-z\u00c0-\u00ff]).{0,8}/);
                if (sp) problems.push(l.id + ' #' + i + ' spatie rond leesteken: ' + JSON.stringify(sp[0]));
                if ((t.match(/\(/g) || []).length !== (t.match(/\)/g) || []).length || (t.match(/"/g) || []).length % 2)
                  problems.push(l.id + ' #' + i + ' haakjes of aanhalingstekens niet in paren');
                if (/[,;:]$/.test(t)) problems.push(l.id + ' #' + i + ' eindigt op een komma, puntkomma of dubbele punt');
                if (/[,;:] [A-Z][a-z]+ [a-z]/.test(t) && /[,;:] (De|Het|Een|Ik|We|Zij|Hij|Mijn|Er|Op|In) /.test(t))
                  problems.push(l.id + ' #' + i + ' zin met hoofdletter na een komma: ' + JSON.stringify((t.match(/.{0,10}[,;:] (De|Het|Een|Ik|We|Zij|Hij|Mijn|Er|Op|In) .{0,10}/) || [''])[0]));
                if (l.type === 'new' && ex.name === 'Nieuwe toetsen')
                  for (const k of (l.add || '')) if (k !== ' ' && !t.includes(k)) problems.push(l.id + ' mist nieuwe toets ' + k);
              });
            }
          }
          return { count, n: problems.length, sample: problems.slice(0, 8) };
        }""")
        check(gen["n"] == 0, f"{gen['count']} oefenteksten gecontroleerd, {gen['n']} problemen {gen['sample']}")

        # 3a. Slottoetsen oefenen echt de nieuwe tekens: bij lessen die hoofdletters, leestekens,
        # cijfers of tekens oefenen (geen kleine letters in de focus) gemiddeld minstens 5 focustekens
        # per 100 tekens, en elke slottoets minstens 3.
        dens = page.evaluate("""() => {
          const d = window.__dactylo, low = [], out = [];
          for (const l of d.lessons) {
            const f = (l.add || l.focus || '');
            if (!f || l.src || !['new', 'practice', 'review', 'moduletest'].includes(l.type)) continue;
            if ([...f].some(ch => /[a-zéèçàùêâôëïöü]/.test(ch))) continue;
            const fs = new Set(f), plan = d.planFor(l), ex = plan[plan.length - 1];
            let sum = 0, len = 0, min = 1e9;
            for (let seed = 1; seed <= 100; seed++) {
              const t = ex.make(d.makeCtx(l, seed * 31 + plan.length - 1));
              const n = [...t].filter(ch => fs.has(ch)).length;
              sum += n; len += t.length; min = Math.min(min, n);
            }
            const per100 = 100 * sum / len, need = 5;
            low.push([l.id, Math.round(per100 * 10) / 10]);
            if (per100 < need || min < 3) out.push(l.id + ' ' + per100.toFixed(1) + '/100, min ' + min);
          }
          low.sort((a, b) => a[1] - b[1]);
          return { out, lowest: low.slice(0, 3) };
        }""")
        check(not dens["out"], f"slottoetsen oefenen de nieuwe tekens (laagste: {dens['lowest']}) {dens['out'][:4]}")

        # 3b. Zinnenlessen tonen echte zinnen, geen terugval op losse woorden en lettercombinaties
        no_sent = page.evaluate("""() => {
          const d = window.__dactylo, out = [];
          const norm = s => s.toLowerCase().replace(/[.?!]/g, '').replace(/\\s+/g, ' ').trim();
          const all = d.sentences.map(norm).filter(s => s.split(' ').length >= 3);
          for (const l of d.lessons.filter(l => l.type === 'sentences')) {
            const ex = d.planFor(l).find(e => e.name === 'Zinnetjes' || e.name === 'Korte zinnen');
            if (!ex) continue;
            // Kent de les hoofdletters, dan moet een zin in haar echte vorm voorkomen (met hoofdletter).
            const ok = new Set(d.allowed(l.id));
            const forms = d.sentences.map(s => ok.has('.') || !s.endsWith('.') ? s : s.slice(0, -1))
              .filter(s => s.split(' ').length >= 3 && [...s].every(ch => ok.has(ch)));
            for (let seed = 1; seed <= 5; seed++) {
              const raw = ex.make(d.makeCtx(l, seed)).replace(/ +/g, ' ').trim();
              const good = forms.length ? forms.some(s => raw.includes(s)) : all.some(s => norm(raw).includes(s));
              if (!good) { out.push(l.id + ' #' + seed); break; }
            }
          }
          return out;
        }""")
        check(not no_sent, f"zinnenlessen tonen echte zinnen {no_sent[:5]}")

        page.screenshot(path=f"{SHOTS}/home.png")

        # 3b. Dode toetsen: een teken uit een compositie telt precies één keer, in beide volgordes
        page.goto(URL + "#/les/m1-houding")
        page.wait_for_selector("[data-act=start]")
        page.keyboard.press("Enter")
        page.wait_for_selector("#strip")
        for order in ("chrome", "safari", "webkit"):
            got = page.evaluate(COMPOSE_JS, order)
            check(got == [1, 1, 0], f"compositie ({order}-volgorde) telt één keer: positie, aanslagen, fouten = {got}")
        page.keyboard.press("Escape")
        page.goto(URL + "#/lessen")
        page.wait_for_selector(".hero")

        # 4. Alle lessen doorlopen, in volgorde. De eerste les van het type 'new' zakt eerst bewust.
        lessons = page.evaluate("() => window.__dactylo.lessons.map(l => ({ id: l.id, type: l.type }))")
        first_new = next((l["id"] for l in lessons if l["type"] == "new"), None)
        for idx, l in enumerate(lessons):
            if l["id"] == first_new:
                rec = play_lesson(l["id"], fail_test=True)
                check(rec and not rec["passed"], f"{l['id']}: gezakt bij veel fouten ({rec and rec.get('attempts')} poging)")
                if idx + 1 < len(lessons):
                    page.goto(URL + "#/les/" + lessons[idx + 1]["id"])
                    page.wait_for_timeout(300)
                    check(page.evaluate("() => location.hash") in ("#/lessen", "#/", ""), f"{lessons[idx + 1]['id']} blijft op slot")
                rec = play_lesson(l["id"], delay=40)
                check(rec and rec["passed"] and rec["attempts"] == 2, f"{l['id']}: geslaagd bij tweede poging")
                apm = page.evaluate("() => window.__dactylo.state().sessions.filter(s => s.x === 1).slice(-1)[0].apm")
                check(500 <= apm <= 2500, f"snelheidsmeting klopt ongeveer bij 40 ms per toets (~1500 verwacht, kreeg {apm})")
            else:
                rec = play_lesson(l["id"])
                check(rec and rec["passed"], f"{l['id']}: geslaagd")
            if l["id"] == "m1-beginmeting":
                base = page.evaluate("() => window.__dactylo.state().baseline")
                check(base is not None and base["acc"] == 100, "beginmeting bewaard")

        # 4a. Hoofdletters: de intro toont de juiste Shift als nieuwe toets, de hint toont de letter
        # en de Shift van de andere hand, en met Caps Lock aan telt een aanslag niet.
        ids = [l["id"] for l in lessons]
        for lid, shift, side in (("m5-shift-links", "k_lshift", "linker"), ("m5-shift-rechts", "k_rshift", "rechter")):
            if lid not in ids:
                continue
            other = "k_rshift" if shift == "k_lshift" else "k_lshift"
            page.goto(URL + "#/les/" + lid)
            page.wait_for_selector("[data-act=start]")
            isnew = page.evaluate("() => Array.from(document.querySelectorAll('.key.is-new')).map(k => k.dataset.k)")
            check(shift in isnew and other not in isnew, f"{lid}: de intro toont de {side}-Shift als nieuwe toets")
            page.keyboard.press("Enter")
            page.wait_for_selector("#strip")
            typ(run_text())
            page.wait_for_selector(".result")
            page.keyboard.press("Enter")
            page.wait_for_selector("#strip")
            text = run_text()
            cap = next(i for i, ch in enumerate(text) if ch.isupper())
            typ(text[:cap])
            hint = page.evaluate("""() => ({ keys: Array.from(document.querySelectorAll('.key.is-next')).map(k => k.dataset.k).sort(),
              label: document.getElementById('finger-label').textContent })""")
            check(hint["keys"] == sorted(["k_" + text[cap].lower(), shift]) and f"met de {side}-Shift" in hint["label"],
                  f"{lid}: de hint voor {text[cap]} toont de letter en de {side}-Shift ({hint['label']})")
            before = page.evaluate("() => window.__dactylo.run().pos")
            page.evaluate("""(ch) => {
              document.dispatchEvent(new KeyboardEvent('keydown', { key: ch, bubbles: true, cancelable: true, modifierCapsLock: true }));
              const f = document.getElementById('catch');
              if (f) f.dispatchEvent(new InputEvent('input', { inputType: 'insertText', data: ch, bubbles: true }));
            }""", text[cap])
            after = page.evaluate("() => [window.__dactylo.run().pos, !document.getElementById('caps').hidden]")
            check(after == [before, True], f"{lid}: met Caps Lock aan telt een aanslag niet en verschijnt de melding ({after})")
            page.keyboard.press("Escape")

        # 4e. Dode toetsen in de lessen van module 6, met echte compositie-events van Chromium (CDP)
        ids = [l["id"] for l in lessons]
        if "m6-trema" in ids:
            def state():
                return page.evaluate("() => { const R = window.__dactylo.run(); return [R.pos, R.keystrokes, R.errors]; }")
            def dead(shift=False):
                page.evaluate("(s) => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Dead', shiftKey: s, bubbles: true, cancelable: true }))", shift)
            def next_keys():
                return page.evaluate("() => Array.from(document.querySelectorAll('#kb-area .key.is-next')).map(k => k.dataset.k).sort()")
            def open_new_keys(lid):
                # Opent de oefening 'Nieuwe toetsen' en typt tot het eerste teken met een dode toets.
                page.goto(URL + "#/les/" + lid)
                page.wait_for_selector("[data-act=start]")
                page.keyboard.press("Enter")
                page.wait_for_selector("#strip")
                typ(run_text())
                page.wait_for_selector(".result")
                page.keyboard.press("Enter")
                page.wait_for_selector("#strip")
                text = run_text()
                i = next(k for k, ch in enumerate(text) if ch in "êâôëïöü")
                typ(text[:i])
                return text[i]
            cdp = page.context.new_cdp_session(page)

            # Een afgewerkte compositie (^ en dan de letter) telt één keer.
            target = open_new_keys("m6-circ")
            before = state()
            dead()
            cdp.send("Input.imeSetComposition", {"text": "^", "selectionStart": 1, "selectionEnd": 1})
            cdp.send("Input.insertText", {"text": target})
            check([a - b for a, b in zip(state(), before)] == [1, 1, 0], f"dode toets met echte compositie-events: {target} telt één keer")

            # Een geannuleerde dode toets (lege compositie) laat geen hint voor de letter alleen hangen.
            dead()
            cdp.send("Input.imeSetComposition", {"text": "^", "selectionStart": 1, "selectionEnd": 1})
            cdp.send("Input.imeSetComposition", {"text": "", "selectionStart": 0, "selectionEnd": 0})
            check(page.evaluate("() => window.__dactylo.run().dead") is False, "een geannuleerde dode toets zet de hint terug")
            page.keyboard.press("Escape")

            # ^ en dan een letter die er niet mee samengaat ('^r') telt als één fout.
            target = open_new_keys("m6-circ")
            before = state()
            dead()
            cdp.send("Input.imeSetComposition", {"text": "^", "selectionStart": 1, "selectionEnd": 1})
            cdp.send("Input.insertText", {"text": "^r"})
            check([a - b for a, b in zip(state(), before)] == [0, 1, 1], "dode toets met een verkeerde letter telt als één fout")
            page.keyboard.press("Escape")

            # Hint voor een trema: eerst Shift + ^ en de letter; ^ zonder Shift kort de hint niet in.
            target = open_new_keys("m6-trema")
            letter = {"ë": "k_e", "ï": "k_i", "ö": "k_o", "ü": "k_u", "ê": "k_e", "â": "k_a", "ô": "k_o"}[target]
            full = next_keys()
            label = page.evaluate("() => document.getElementById('finger-label').textContent")
            dead(False)
            after_plain = next_keys()
            dead(True)
            after_shift = next_keys()
            check(full == sorted(["k_circ", "k_lshift", letter]) and after_plain == full and after_shift == [letter]
                  and "linker-Shift" in label,
                  f"hint voor {target}: Shift + ^ en de letter, na ¨ enkel de letter ({full} / {after_plain} / {after_shift})")
            page.keyboard.press("Escape")

            # Na een klik in de marge van de pagina gaat de focus terug naar het tekstveld.
            page.goto(URL + "#/les/m1-houding")
            page.wait_for_selector("[data-act=start]")
            page.keyboard.press("Enter")
            page.wait_for_selector("#strip")
            page.mouse.click(5, 450)
            page.wait_for_timeout(50)
            check(page.evaluate("() => document.activeElement && document.activeElement.id") == "catch",
                  "na een klik buiten de tekst gaat de focus terug naar het tekstveld")
            page.keyboard.press("Escape")

        # 4f. Leestekens: slimme aanhalingstekens (zoals Safari ze kan sturen) tellen als ' en ",
        # en de hint bij punt en vraagteken toont de toets met de linker-Shift.
        def open_until(lid, chars):
            # Opent de oefening 'Nieuwe toetsen' en typt tot het eerste teken uit chars.
            page.goto(URL + "#/les/" + lid)
            page.wait_for_selector("[data-act=start]")
            page.keyboard.press("Enter")
            page.wait_for_selector("#strip")
            typ(run_text())
            page.wait_for_selector(".result")
            page.keyboard.press("Enter")
            page.wait_for_selector("#strip")
            text = run_text()
            i = next(k for k, ch in enumerate(text) if ch in chars)
            typ(text[:i])
            return text[i]
        def counts():
            return page.evaluate("() => { const R = window.__dactylo.run(); return [R.pos, R.keystrokes, R.errors]; }")
        if "m7-aanhaling" in ids:
            target = open_until("m7-aanhaling", "'\"")
            curly = "\u2019" if target == "'" else "\u201d"
            before = counts()
            page.evaluate("(ch) => document.getElementById('catch').dispatchEvent(new InputEvent('input', { inputType: 'insertText', data: ch, bubbles: true }))", curly)
            check([a - b for a, b in zip(counts(), before)] == [1, 1, 0], f"slim aanhalingsteken {curly} telt als {target}")
            page.keyboard.press("Escape")
        if "m7-punt" in ids:
            target = open_until("m7-punt", ".?")
            hint = page.evaluate("""() => ({ keys: Array.from(document.querySelectorAll('#kb-area .key.is-next')).map(k => k.dataset.k).sort(),
              label: document.getElementById('finger-label').textContent })""")
            want = sorted(["k_semi" if target == "." else "k_comma", "k_lshift"])
            check(hint["keys"] == want and "met de linker-Shift" in hint["label"],
                  f"hint voor {target}: de toets met de linker-Shift ({hint['keys']}, {hint['label']})")
            page.keyboard.press("Escape")

        # 5. Toetsstatistieken bevatten enkel tekens die in de lessen voorkomen (beginmeting telt niet mee)
        last_id = lessons[-1]["id"]
        allowed_last = set(page.evaluate(ALLOWED_JS, last_id))
        keys_seen = set(page.evaluate("() => Object.keys(window.__dactylo.state().keys)"))
        check(keys_seen <= allowed_last, f"toetsstatistieken enkel voor geoefende tekens (extra: {sorted(keys_seen - allowed_last)})")

        # 6. Herladen: voortgang blijft
        page.goto(URL + "#/lessen")
        page.reload()
        page.wait_for_selector(".hero")
        n_passed = page.evaluate("() => Object.values(window.__dactylo.state().lessons).filter(r => r.passed).length")
        check(n_passed == len(lessons), f"na herladen nog {n_passed} van {len(lessons)} lessen geslaagd")
        page.screenshot(path=f"{SHOTS}/home_done.png", full_page=True)

        # 7. Back-up: export, import, en een back-up van een nieuwere versie weigeren
        exported = page.evaluate("() => window.__dactylo.exportJSON()")
        ok = page.evaluate("(txt) => { localStorage.clear(); return window.__dactylo.importJSON(txt, true); }", exported)
        n_after = page.evaluate("(k) => Object.keys(JSON.parse(localStorage.getItem(k)).lessons).length", STORAGE_KEY)
        check(ok and n_after >= len(lessons), f"back-up terugzetten werkt ({n_after} lessen)")
        bad = page.evaluate("() => window.__dactylo.importJSON(JSON.stringify({ schema: 999, lessons: {} }), true)")
        check(bad is False, "back-up van een nieuwere versie wordt geweigerd")

        # 8. Toetsenbord op het scherm: Mac- en Windows-variant
        page.goto(URL + "#/instellingen")
        page.wait_for_selector("#set-layout")
        page.select_option("#set-layout", "win")
        win_top = page.evaluate("() => window.__dactylo.layout()[0][0].base")
        page.select_option("#set-layout", "mac")
        mac_top = page.evaluate("() => window.__dactylo.layout()[0][0].base")
        check(win_top == "\u00b2" and mac_top != "\u00b2", f"Windows- en Mac-indeling verschillen (win: {win_top}, mac: {mac_top})")
        page.select_option("#set-layout", "auto")

        # 9. Typscherm past op een MacBook (Safari toont ongeveer 1440 x 790), ook bij de langste
        # oefeningen: de opwarming van de laatste nieuwe les, de slottoets van de laatste zinnenles
        # en de toets van de laatste moduletoets.
        page.set_viewport_size({"width": 1440, "height": 790})
        def last_of(typ_):
            return next((l["id"] for l in reversed(lessons) if l["type"] == typ_), None)
        targets = [(last_of("new"), 0), (last_of("sentences"), -1), (last_of("moduletest"), -1)]
        for lid, idx in [x for x in targets if x[0]]:
            page.goto(URL + "#/les/" + lid)
            page.wait_for_selector("[data-act=start]")
            page.keyboard.press("Enter")
            n = page.evaluate("() => window.__dactylo.flow().plan.length")
            stop = idx % n
            for i in range(stop):
                page.wait_for_selector("#strip")
                typ(run_text())
                page.wait_for_selector(".result")
                page.keyboard.press("Enter")
            page.wait_for_selector("#strip")
            typ(run_text()[:4], 30)
            bottom = page.evaluate("() => { const el = document.getElementById('finger-label'); return el ? el.getBoundingClientRect().bottom : 0; }")
            check(0 < bottom <= 790, f"typscherm past op een MacBook bij {lid}, oefening {stop + 1} (onderkant op {bottom:.0f}px van 790)")
            if idx != 0:
                # Na een paar regels schuift het venster mee: geen teken mag half zichtbaar zijn.
                typ(run_text()[4:len(run_text()) // 2])
                half = page.evaluate("""() => {
                  const box = document.getElementById('strip-lines').getBoundingClientRect();
                  return Array.from(document.querySelectorAll('#strip-lines .ch')).filter(el => {
                    const r = el.getBoundingClientRect();
                    return r.height && r.top < box.bottom && r.bottom > box.top && (r.top < box.top - 0.5 || r.bottom > box.bottom + 0.5);
                  }).length;
                }""")
                check(half == 0, f"geen half zichtbare regels in het typvenster bij {lid} ({half} tekens half zichtbaar)")
            page.screenshot(path=f"{SHOTS}/typing_macbook.png" if idx == 0 else f"{SHOTS}/typing_macbook_{lid}.png")
            page.keyboard.press("Escape")
        page.set_viewport_size({"width": 1280, "height": 900})

        # 10. Voortgang en donker thema renderen
        page.goto(URL + "#/voortgang")
        page.wait_for_selector(".chart")
        page.screenshot(path=f"{SHOTS}/progress.png", full_page=True)
        page.emulate_media(color_scheme="dark")
        page.goto(URL + "#/lessen")
        page.wait_for_selector(".hero")
        page.screenshot(path=f"{SHOTS}/home_dark.png")

        # 11. Geen fouten (lettertypes van Google mogen falen zonder internet)
        other = [u for u in failed_requests if "fonts.googleapis.com" not in u and "fonts.gstatic.com" not in u]
        errs = [e for e in js_errors if "Failed to load resource" not in e]
        check(not other, f"geen mislukte verzoeken behalve lettertypes {other[:3]}")
        check(not errs, f"geen JavaScript-fouten {errs[:3]}")
        browser.close()

    print()
    print("RESULTAAT:", "ALLES OK" if not failures else f"{len(failures)} problemen")
    print("Screenshots:", SHOTS)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
