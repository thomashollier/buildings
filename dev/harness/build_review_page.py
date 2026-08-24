#!/usr/bin/env python3
"""
build_review_page.py

Reads dev/reference/meta/*.json (one per reference-photo family) and emits
dev/reference/review.html: a single self-contained, offline-usable HTML page
the operator uses to select which reference photographs become the
ground-truth set for VLM checking of generated procedural-Paris-building
output.

Run:  python3 dev/harness/build_review_page.py

Regenerate this page any time the corpus (images/meta) changes.
"""

import json
import glob
import os
import html
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF_DIR = os.path.join(REPO_ROOT, "dev", "reference")
META_DIR = os.path.join(REF_DIR, "meta")
OUT_PATH = os.path.join(REF_DIR, "review.html")

# Family display order + one-line "evidence for" note, matched to the brief.
FAMILY_INFO = {
    "restauration": (
        "Restauration & Louis-Philippe (1820–1848)",
        "Pre-Haussmann envelope: flat incised refends, thin lozenge/palmette ironwork, plaster over rubble.",
    ),
    "second-empire": (
        "Second Empire haussmannien, canonical (1853–1870)",
        "THE reference case: 45° comble, bossage socle, balcon filant at 2nd and 5th floors, strict block unity.",
    ),
    "se-elevation": (
        "Second Empire — measured elevations & drawings",
        "Evidence for exact proportions and construction geometry: Daly's plates give dimensioned facade elevations, not photographs.",
    ),
    "daly-1864": (
        "César Daly 1864 — measured plates, maisons à loyer",
        "The corpus's only source that supports MEASUREMENT rather than qualitative comparison: scale-barred elevations and dimensioned details/plans, by daly_class (Première/Deuxième/Troisième), for the maisons-à-loyer typology.",
    ),
    "se-facade": (
        "Second Empire — full frontal facades",
        "Evidence for whole-building composition and block unity: complete facades, straight-on, from period and modern photos.",
    ),
    "se-ironwork": (
        "Second Empire — ironwork & balcon filant",
        "Evidence for the continuous cast/wrought-iron balcony railing pattern at the 2nd and 5th floor string courses.",
    ),
    "se-socle": (
        "Second Empire — socle, bossage & refends",
        "Evidence for the rusticated ground-floor/mezzanine base: bossage coursing, refend joints, and their relation to the porte cochère.",
    ),
    "se-surround": (
        "Second Empire — window surrounds, keystones & consoles",
        "Evidence for period-correct window-opening dressing: keystones, console brackets, and pediments without later over-elaboration.",
    ),
    "se-comble": (
        "Second Empire — the 45° comble, dormers & zinc",
        "Evidence for the canonical straight 45° mansard plane, its dormer forms, and zinc roofing — the discontinuity baseline before Belle Époque.",
    ),
    "se-cornice": (
        "Second Empire — cornices, modillions & string courses",
        "Evidence for the main cornice profile, modillion spacing, and the horizontal string courses that tie the block facade together.",
    ),
    "se-entrance": (
        "Second Empire — portes cochères & entrances",
        "Evidence for entrance scale and dressing: carriage-door portes cochères and pedestrian entries, seen in context with adjacent shopfronts.",
    ),
    "third-republic": (
        "Early Third Republic (1870–1884)",
        "Mascarons becoming common; richening window pediments; still the 45° comble.",
    ),
    "belle-epoque": (
        "Belle Époque, post-1884 decree (1884–1902)",
        "THE discontinuity test: arc comble replaces the 45° plane, taller and more elaborate, iron cresting, varied dormers.",
    ),
    "post-1902": (
        "Post-1902 (Bonnier) & Art Nouveau",
        "Projections may now carry above the cornice; Guimard whiplash ironwork; Sauvage rue Vavin.",
    ),
    "corner": (
        "Corner buildings",
        "Angle, chamfer, rotonde — the corner is a THIRD SHORT FACADE with its own rhythm, not a module type.",
    ),
    "class-range": (
        "Class range — modest faubourg vs grand boulevard",
        "The absolute/proportional split: the door barely changes while bays, windows and cornice grow.",
    ),
    "ground-floor": (
        "Ground floor — shopfronts, cafés, portes cochères",
        "Fastest-turning feature family; carries the observation-date idea; the carriage door is the ruler for absolute scale.",
    ),
}

FAMILY_ORDER = list(FAMILY_INFO.keys())

QUALITY_RANK = {"good": 0, "partial": 1, "poor": 2}


def load_families():
    families = []
    for path in sorted(glob.glob(os.path.join(META_DIR, "*.json"))):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        fam = data.get("family")
        images = data.get("images", [])
        for im in images:
            im.setdefault("corner", None)
        families.append(
            {
                "family": fam,
                "saved": data.get("saved", len(images)),
                "images": images,
                "notes": data.get("notes", ""),
            }
        )
    # order per FAMILY_ORDER, then any leftovers alphabetically
    order_index = {f: i for i, f in enumerate(FAMILY_ORDER)}
    families.sort(key=lambda d: order_index.get(d["family"], 999))
    return families


def esc(s):
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def render_card(fam, im, idx):
    file_rel = im.get("file", "")
    title = im.get("title", "")
    year = im.get("year", "")
    klass = im.get("klass", "")
    street = im.get("street", "")
    shows = im.get("shows", "")
    quality = im.get("quality", "unknown")
    license_ = im.get("license", "")
    author = im.get("author", "")
    source_url = im.get("source_url", "")
    corner = im.get("corner", None)
    daly_class = im.get("daly_class", "")
    address = im.get("address", "")
    has_scale_bar = im.get("has_scale_bar", False)
    has_dimensions = im.get("has_dimensions", False)

    if not street and address:
        street = address

    meta_bits = []
    if year:
        meta_bits.append(esc(year))
    if klass:
        meta_bits.append(esc(klass))
    if daly_class:
        meta_bits.append(esc(daly_class))
    if corner is True:
        meta_bits.append("corner")
    meta_line = " · ".join(meta_bits)

    measure_badges = []
    if has_scale_bar:
        measure_badges.append('<span class="measure-badge">SCALE BAR</span>')
    if has_dimensions:
        measure_badges.append('<span class="measure-badge">DIMENSIONED</span>')
    measure_line = "".join(measure_badges)

    record = {
        "file": file_rel,
        "title": title,
        "source_url": source_url,
        "license": license_,
        "author": author,
        "year": year,
        "klass": klass,
        "corner": corner,
        "shows": shows,
        "street": street,
        "quality": quality,
        "family": fam,
        "daly_class": daly_class,
        "address": address,
    }
    record_json = esc(json.dumps(record, ensure_ascii=False))

    default_selected = "true" if quality == "good" else "false"

    return f'''
      <div class="card" data-file="{esc(file_rel)}" data-family="{esc(fam)}" data-quality="{esc(quality)}" data-record="{record_json}" data-default-selected="{default_selected}">
        <div class="thumb-wrap">
          <img class="thumb" src="{esc(file_rel)}" alt="{esc(title)}" loading="lazy" />
          <span class="quality-badge q-{esc(quality)}">{esc(quality)}</span>
          <label class="check-wrap" onclick="event.stopPropagation()">
            <input type="checkbox" class="card-check" />
          </label>
        </div>
        <div class="card-body">
          <div class="card-title">{esc(title)}</div>
          <div class="card-meta">{meta_line}</div>
          {f'<div class="card-street">{esc(street)}</div>' if street else ''}
          {f'<div class="measure-badges">{measure_line}</div>' if measure_line else ''}
          <div class="card-shows">{esc(shows)}</div>
          <div class="card-source">
            <span class="license">{esc(license_)}</span>{' · ' if license_ and author else ''}<span class="author">{esc(author)}</span>
            {f'<a href="{esc(source_url)}" target="_blank" rel="noopener" class="src-link" onclick="event.stopPropagation()">source ↗</a>' if source_url else ''}
          </div>
        </div>
      </div>'''


def render_family_section(fam_data):
    fam = fam_data["family"]
    title, evidence = FAMILY_INFO.get(fam, (fam, ""))
    images = fam_data["images"]
    cards = "\n".join(render_card(fam, im, i) for i, im in enumerate(images))
    return f'''
    <section class="family" id="fam-{esc(fam)}" data-family="{esc(fam)}">
      <div class="family-header">
        <h2>{esc(title)} <span class="fam-count" data-fam-count="{esc(fam)}">0/{len(images)}</span></h2>
        <p class="fam-evidence">{esc(evidence)}</p>
        <div class="fam-controls">
          <button class="btn small" data-fam-action="all" data-fam="{esc(fam)}">select all</button>
          <button class="btn small" data-fam-action="none" data-fam="{esc(fam)}">select none</button>
        </div>
      </div>
      <div class="grid">
        {cards}
      </div>
    </section>'''


def build_html(families):
    total = sum(len(f["images"]) for f in families)
    family_sections = "\n".join(render_family_section(f) for f in families)
    family_pills = "\n".join(
        f'<option value="{esc(f["family"])}">{esc(FAMILY_INFO.get(f["family"], (f["family"],""))[0])}</option>'
        for f in families
    )

    return TEMPLATE.format(
        total=total,
        family_sections=family_sections,
        family_pills=family_pills,
    )


TEMPLATE = r"""<title>Reference Selection Review</title>
<style>
:root {{
  --bg: #f5f5f3;
  --bg-elevated: #ffffff;
  --bg-sunken: #ececea;
  --text: #1a1a18;
  --text-dim: #5c5c58;
  --text-faint: #8a8a85;
  --border: #d8d8d4;
  --border-strong: #b8b8b3;
  --accent: #1d6fd6;
  --accent-tint: #e3edfb;
  --accent-text: #0d4fa3;
  --good: #2f8f4e;
  --good-bg: #e5f3e9;
  --partial: #b8860b;
  --partial-bg: #f8f0dc;
  --poor: #c0392b;
  --poor-bg: #fbe6e3;
  --shadow: 0 1px 2px rgba(0,0,0,0.06), 0 1px 8px rgba(0,0,0,0.04);
  --radius: 8px;
  --sticky-h: auto;
}}

@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #17181a;
    --bg-elevated: #202225;
    --bg-sunken: #131415;
    --text: #eaeaea;
    --text-dim: #a8a8a4;
    --text-faint: #777773;
    --border: #35363a;
    --border-strong: #48494e;
    --accent: #5b9dee;
    --accent-tint: #1c2c40;
    --accent-text: #8cbdf5;
    --good: #4fbf74;
    --good-bg: #143620;
    --partial: #d9a53a;
    --partial-bg: #3a2f10;
    --poor: #e0685a;
    --poor-bg: #3a1512;
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 1px 8px rgba(0,0,0,0.25);
  }}
}}

* {{ box-sizing: border-box; }}

html, body {{
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  overflow-x: hidden;
  max-width: 100vw;
}}

a {{ color: var(--accent-text); }}

.intro {{
  max-width: 980px;
  margin: 0 auto;
  padding: 20px 20px 4px;
}}

.intro h1 {{
  font-size: 1.5rem;
  margin: 0 0 8px;
}}

.limits {{
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: var(--radius);
  padding: 12px 16px;
  font-size: 0.92rem;
  line-height: 1.5;
  color: var(--text-dim);
}}

.limits strong {{ color: var(--text); }}

.header {{
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow);
  padding: 10px 20px;
}}

.header-row {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  max-width: 1400px;
  margin: 0 auto;
}}

.count-badge {{
  font-weight: 600;
  font-size: 0.95rem;
  padding: 6px 12px;
  background: var(--accent-tint);
  color: var(--accent-text);
  border-radius: 999px;
  white-space: nowrap;
}}

.btn {{
  background: var(--bg-sunken);
  color: var(--text);
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  padding: 7px 12px;
  font-size: 0.85rem;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
}}

.btn:hover {{ background: var(--border); }}
.btn.small {{ padding: 4px 9px; font-size: 0.78rem; }}
.btn.primary {{
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  font-weight: 600;
}}
.btn.primary:hover {{ filter: brightness(1.08); }}

.sep {{
  width: 1px;
  align-self: stretch;
  background: var(--border);
  margin: 0 2px;
}}

select, .filter-select {{
  background: var(--bg-sunken);
  color: var(--text);
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 0.85rem;
  font-family: inherit;
}}

.header-note {{
  font-size: 0.78rem;
  color: var(--text-faint);
  width: 100%;
  padding-top: 2px;
}}

.toggle-label {{
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.85rem;
  color: var(--text-dim);
  cursor: pointer;
  white-space: nowrap;
}}

main {{
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px 20px 60px;
}}

.family {{
  margin-top: 34px;
}}

.family-header h2 {{
  font-size: 1.15rem;
  margin: 0 0 2px;
  display: flex;
  align-items: baseline;
  gap: 10px;
}}

.fam-count {{
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent-text);
  background: var(--accent-tint);
  padding: 2px 9px;
  border-radius: 999px;
}}

.fam-evidence {{
  margin: 0 0 8px;
  color: var(--text-dim);
  font-size: 0.86rem;
  max-width: 900px;
}}

.fam-controls {{
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}}

.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}}

.card {{
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: border-color 0.12s, background 0.12s;
  display: flex;
  flex-direction: column;
}}

.card.selected {{
  border-color: var(--accent);
  background: var(--accent-tint);
  box-shadow: 0 0 0 2px var(--accent);
}}

.card.hidden {{ display: none; }}

.thumb-wrap {{
  position: relative;
  height: 240px;
  background: var(--bg-sunken);
}}

.thumb {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}}

.quality-badge {{
  position: absolute;
  top: 8px;
  left: 8px;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 3px 7px;
  border-radius: 4px;
}}

.q-good {{ background: var(--good-bg); color: var(--good); }}
.q-partial {{ background: var(--partial-bg); color: var(--partial); }}
.q-poor {{ background: var(--poor-bg); color: var(--poor); }}

.check-wrap {{
  position: absolute;
  top: 8px;
  right: 8px;
  width: 26px;
  height: 26px;
  background: rgba(255,255,255,0.9);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow);
}}
@media (prefers-color-scheme: dark) {{
  .check-wrap {{ background: rgba(30,30,32,0.85); }}
}}

.card-check {{
  width: 17px;
  height: 17px;
  cursor: pointer;
  accent-color: var(--accent);
}}

.card-body {{
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}}

.card-title {{
  font-weight: 600;
  font-size: 0.88rem;
  line-height: 1.3;
}}

.card-meta {{
  font-size: 0.78rem;
  color: var(--text-dim);
  text-transform: capitalize;
}}

.card-street {{
  font-size: 0.76rem;
  color: var(--text-faint);
  line-height: 1.35;
}}

.measure-badges {{
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}}

.measure-badge {{
  font-size: 0.66rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--accent-tint);
  color: var(--accent-text);
}}

.card-shows {{
  font-size: 0.78rem;
  color: var(--text-dim);
  line-height: 1.4;
  margin-top: 2px;
}}

.card-source {{
  margin-top: auto;
  padding-top: 6px;
  font-size: 0.7rem;
  color: var(--text-faint);
  border-top: 1px solid var(--border);
  line-height: 1.4;
}}

.src-link {{
  display: inline-block;
  margin-left: 4px;
}}

/* Lightbox */
#lightbox {{
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.86);
  z-index: 200;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 30px;
}}
#lightbox.open {{ display: flex; }}

.lb-inner {{
  background: var(--bg-elevated);
  border-radius: 10px;
  max-width: min(1200px, 96vw);
  max-height: 94vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 10px 50px rgba(0,0,0,0.5);
}}

.lb-img-wrap {{
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
  flex: 1;
}}

.lb-img-wrap img {{
  max-width: 100%;
  max-height: 66vh;
  object-fit: contain;
  display: block;
}}

.lb-meta {{
  padding: 14px 20px;
  overflow-y: auto;
  border-top: 1px solid var(--border);
}}

.lb-title {{
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 4px;
}}

.lb-row {{
  font-size: 0.85rem;
  color: var(--text-dim);
  margin: 3px 0;
}}

.lb-shows {{
  margin: 8px 0;
  font-size: 0.9rem;
  line-height: 1.45;
}}

.lb-close {{
  position: absolute;
  top: 18px;
  right: 26px;
  background: rgba(0,0,0,0.5);
  color: #fff;
  border: none;
  border-radius: 50%;
  width: 38px;
  height: 38px;
  font-size: 1.3rem;
  cursor: pointer;
  z-index: 5;
}}

.lb-nav {{
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0,0,0,0.4);
  color: #fff;
  border: none;
  width: 46px;
  height: 70px;
  font-size: 1.6rem;
  cursor: pointer;
  border-radius: 6px;
}}
.lb-nav:hover {{ background: rgba(0,0,0,0.65); }}
.lb-prev {{ left: 14px; }}
.lb-next {{ right: 14px; }}

.lb-select-line {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}}

.toast {{
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--text);
  color: var(--bg);
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 0.85rem;
  z-index: 300;
  box-shadow: var(--shadow);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s;
}}
.toast.show {{ opacity: 1; }}

.save-note {{
  font-size: 0.78rem;
  color: var(--text-faint);
  margin-top: 4px;
}}

code {{
  background: var(--bg-sunken);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.85em;
}}
</style>

<div class="intro">
  <h1>Reference Selection Review</h1>
  <div class="limits">
    <strong>Two limits, kept in view while selecting:</strong> photographs support <strong>qualitative</strong>
    comparison reliably — proportion, ornament family, silhouette, rhythm — and support
    <strong>measurement</strong> not at all. And a visual check is a <strong>tripwire, not a passing grade</strong>:
    "that looks wrong" is strong evidence something is broken; "that looks right" is weak evidence anything is
    actually correct. Select images that give the clearest, least ambiguous read on the feature they are meant to
    evidence — not necessarily the prettiest photo.
  </div>
</div>

<div class="header">
  <div class="header-row">
    <span class="count-badge" id="countBadge">0 of {total} selected</span>
    <div class="sep"></div>
    <button class="btn" id="btnAll">Select all</button>
    <button class="btn" id="btnNone">Select none</button>
    <button class="btn" id="btnInvert">Invert</button>
    <div class="sep"></div>
    <label class="toggle-label"><input type="checkbox" id="filterGoodOnly" /> good only</label>
    <label class="toggle-label"><input type="checkbox" id="filterSelectedOnly" /> selected only</label>
    <div class="sep"></div>
    <button class="btn primary" id="btnDownload">Download selection.json</button>
    <button class="btn" id="btnCopy">Copy JSON to clipboard</button>
    <span class="header-note">Save the download as <code>dev/reference/selection.json</code> (overwrite if present). Your picks also persist automatically in this browser via localStorage.</span>
  </div>
</div>

<main>
{family_sections}
</main>

<div id="lightbox">
  <button class="lb-close" id="lbClose">×</button>
  <button class="lb-nav lb-prev" id="lbPrev">‹</button>
  <button class="lb-nav lb-next" id="lbNext">›</button>
  <div class="lb-inner">
    <div class="lb-img-wrap"><img id="lbImg" src="" alt="" /></div>
    <div class="lb-meta">
      <div class="lb-title" id="lbTitle"></div>
      <div class="lb-row" id="lbMeta1"></div>
      <div class="lb-row" id="lbMeta2"></div>
      <div class="lb-shows" id="lbShows"></div>
      <div class="lb-row" id="lbSource"></div>
      <div class="lb-select-line">
        <input type="checkbox" id="lbCheck" />
        <label for="lbCheck">selected for ground-truth set</label>
      </div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
(function() {{
  var STORAGE_KEY = 'refReviewSelection.v1';
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var lb = document.getElementById('lightbox');
  var lbImg = document.getElementById('lbImg');
  var lbTitle = document.getElementById('lbTitle');
  var lbMeta1 = document.getElementById('lbMeta1');
  var lbMeta2 = document.getElementById('lbMeta2');
  var lbShows = document.getElementById('lbShows');
  var lbSource = document.getElementById('lbSource');
  var lbCheck = document.getElementById('lbCheck');
  var currentLbIndex = -1;
  var visibleCards = cards.slice();

  function loadSelection() {{
    try {{
      var raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    }} catch (e) {{}}
    return null;
  }}

  function saveSelection() {{
    var sel = {{}};
    cards.forEach(function(c) {{
      sel[c.getAttribute('data-file')] = c.classList.contains('selected');
    }});
    try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(sel)); }} catch (e) {{}}
  }}

  function initSelection() {{
    var stored = loadSelection();
    cards.forEach(function(c) {{
      var file = c.getAttribute('data-file');
      var selected;
      if (stored && Object.prototype.hasOwnProperty.call(stored, file)) {{
        selected = stored[file];
      }} else {{
        selected = c.getAttribute('data-default-selected') === 'true';
      }}
      setCardSelected(c, selected, false);
    }});
  }}

  function setCardSelected(card, selected, persist) {{
    card.classList.toggle('selected', selected);
    var cb = card.querySelector('.card-check');
    if (cb) cb.checked = selected;
    if (persist !== false) saveSelection();
  }}

  function updateCounts() {{
    var total = cards.length;
    var selectedCount = cards.filter(function(c) {{ return c.classList.contains('selected'); }}).length;
    document.getElementById('countBadge').textContent = selectedCount + ' of ' + total + ' selected';

    var famGroups = {{}};
    cards.forEach(function(c) {{
      var fam = c.getAttribute('data-family');
      famGroups[fam] = famGroups[fam] || {{ total: 0, sel: 0 }};
      famGroups[fam].total++;
      if (c.classList.contains('selected')) famGroups[fam].sel++;
    }});
    Object.keys(famGroups).forEach(function(fam) {{
      var el = document.querySelector('[data-fam-count="' + fam + '"]');
      if (el) el.textContent = famGroups[fam].sel + '/' + famGroups[fam].total;
    }});
  }}

  function toggleCard(card) {{
    setCardSelected(card, !card.classList.contains('selected'));
    updateCounts();
    if (lb.classList.contains('open')) {{
      var rec = getRecord(card);
      if (currentLbIndex >= 0 && visibleCards[currentLbIndex] === card) {{
        lbCheck.checked = card.classList.contains('selected');
      }}
    }}
  }}

  cards.forEach(function(card) {{
    card.addEventListener('click', function(e) {{
      toggleCard(card);
    }});
    var cb = card.querySelector('.card-check');
    cb.addEventListener('click', function(e) {{
      e.stopPropagation();
      toggleCard(card);
    }});
    var img = card.querySelector('.thumb');
    img.addEventListener('click', function(e) {{
      e.stopPropagation();
      openLightboxFor(card);
    }});
  }});

  document.getElementById('btnAll').addEventListener('click', function() {{
    getFilteredCards().forEach(function(c) {{ setCardSelected(c, true, false); }});
    saveSelection(); updateCounts();
  }});
  document.getElementById('btnNone').addEventListener('click', function() {{
    getFilteredCards().forEach(function(c) {{ setCardSelected(c, false, false); }});
    saveSelection(); updateCounts();
  }});
  document.getElementById('btnInvert').addEventListener('click', function() {{
    getFilteredCards().forEach(function(c) {{ setCardSelected(c, !c.classList.contains('selected'), false); }});
    saveSelection(); updateCounts();
  }});

  document.querySelectorAll('[data-fam-action]').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      var fam = btn.getAttribute('data-fam');
      var action = btn.getAttribute('data-fam-action');
      cards.filter(function(c) {{ return c.getAttribute('data-family') === fam && !c.classList.contains('hidden'); }})
        .forEach(function(c) {{ setCardSelected(c, action === 'all', false); }});
      saveSelection(); updateCounts();
    }});
  }});

  function getFilteredCards() {{
    return cards.filter(function(c) {{ return !c.classList.contains('hidden'); }});
  }}

  var filterGoodOnly = document.getElementById('filterGoodOnly');
  var filterSelectedOnly = document.getElementById('filterSelectedOnly');

  function applyFilters() {{
    cards.forEach(function(c) {{
      var show = true;
      if (filterGoodOnly.checked && c.getAttribute('data-quality') !== 'good') show = false;
      if (filterSelectedOnly.checked && !c.classList.contains('selected')) show = false;
      c.classList.toggle('hidden', !show);
    }});
    visibleCards = cards.filter(function(c) {{ return !c.classList.contains('hidden'); }});
  }}

  filterGoodOnly.addEventListener('change', applyFilters);
  filterSelectedOnly.addEventListener('change', applyFilters);

  function getRecord(card) {{
    return JSON.parse(card.getAttribute('data-record'));
  }}

  function buildSelectionPayload() {{
    var selected = cards.filter(function(c) {{ return c.classList.contains('selected'); }})
      .map(function(c) {{ return getRecord(c); }});
    return {{ generated_by: 'review.html', selected: selected }};
  }}

  function showToast(msg) {{
    var t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(function() {{ t.classList.remove('show'); }}, 2200);
  }}

  document.getElementById('btnDownload').addEventListener('click', function() {{
    var payload = buildSelectionPayload();
    var blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'selection.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function() {{ URL.revokeObjectURL(url); }}, 1000);
    showToast('Downloaded selection.json — save it to dev/reference/selection.json');
  }});

  document.getElementById('btnCopy').addEventListener('click', function() {{
    var payload = buildSelectionPayload();
    var text = JSON.stringify(payload, null, 2);
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(text).then(function() {{
        showToast('Copied JSON to clipboard (' + payload.selected.length + ' images)');
      }}, function() {{
        fallbackCopy(text);
      }});
    }} else {{
      fallbackCopy(text);
    }}
  }});

  function fallbackCopy(text) {{
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {{ document.execCommand('copy'); showToast('Copied JSON to clipboard'); }}
    catch (e) {{ showToast('Copy failed — use Download instead'); }}
    document.body.removeChild(ta);
  }}

  // Lightbox
  function openLightboxFor(card) {{
    visibleCards = getFilteredCards();
    var idx = visibleCards.indexOf(card);
    if (idx === -1) {{ visibleCards = cards.slice(); idx = visibleCards.indexOf(card); }}
    currentLbIndex = idx;
    renderLightbox();
    lb.classList.add('open');
  }}

  function renderLightbox() {{
    var card = visibleCards[currentLbIndex];
    if (!card) return;
    var rec = getRecord(card);
    lbImg.src = rec.file;
    lbImg.alt = rec.title || '';
    lbTitle.textContent = rec.title || '';
    var bits = [];
    if (rec.year) bits.push('Year: ' + rec.year);
    if (rec.klass) bits.push('Class: ' + rec.klass);
    if (rec.corner === true) bits.push('Corner building');
    if (rec.quality) bits.push('Quality: ' + rec.quality);
    lbMeta1.textContent = bits.join('  ·  ');
    lbMeta2.textContent = rec.street || '';
    lbShows.textContent = rec.shows || '';
    var srcBits = [];
    if (rec.license) srcBits.push(rec.license);
    if (rec.author) srcBits.push(rec.author);
    lbSource.innerHTML = srcBits.join(' · ') + (rec.source_url ? ' — <a href="' + rec.source_url + '" target="_blank" rel="noopener">source ↗</a>' : '');
    lbCheck.checked = card.classList.contains('selected');
  }}

  lbCheck.addEventListener('change', function() {{
    var card = visibleCards[currentLbIndex];
    if (card) {{
      setCardSelected(card, lbCheck.checked);
      updateCounts();
    }}
  }});

  function closeLightbox() {{
    lb.classList.remove('open');
    currentLbIndex = -1;
  }}

  function lbStep(delta) {{
    if (!visibleCards.length) return;
    currentLbIndex = (currentLbIndex + delta + visibleCards.length) % visibleCards.length;
    renderLightbox();
  }}

  document.getElementById('lbClose').addEventListener('click', closeLightbox);
  document.getElementById('lbPrev').addEventListener('click', function() {{ lbStep(-1); }});
  document.getElementById('lbNext').addEventListener('click', function() {{ lbStep(1); }});
  lb.addEventListener('click', function(e) {{ if (e.target === lb) closeLightbox(); }});

  document.addEventListener('keydown', function(e) {{
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') closeLightbox();
    else if (e.key === 'ArrowLeft') lbStep(-1);
    else if (e.key === 'ArrowRight') lbStep(1);
  }});

  initSelection();
  applyFilters();
  updateCounts();
}})();
</script>
"""


def main():
    if not os.path.isdir(META_DIR):
        print(f"error: meta dir not found: {META_DIR}", file=sys.stderr)
        sys.exit(1)
    families = load_families()
    if not families:
        print("error: no family metadata JSON files found", file=sys.stderr)
        sys.exit(1)

    out_html = build_html(families)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(out_html)

    total = sum(len(f["images"]) for f in families)
    print(f"wrote {OUT_PATH}")
    print(f"total images: {total}")
    for f in families:
        print(f"  {f['family']}: {len(f['images'])}")


if __name__ == "__main__":
    main()
