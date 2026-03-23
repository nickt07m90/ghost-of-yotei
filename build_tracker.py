import re
import json

GAME_NAME = 'Ghost of Yotei'
GAME_SLUG = 'ghostOfYotei'

ACHIEVEMENT_KEYWORDS = [
    'trophy', 'achievement', 'platinum', 'gold', 'silver', 'bronze',
    'unlock', 'missable', 'point of no return', 'missables'
]

def is_achievement_line(text):
    lower = text.lower()
    return any(kw in lower for kw in ACHIEVEMENT_KEYWORDS)

def split_into_chunks(text, min_size=350, max_size=500):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current = ''
    for sentence in sentences:
        if not sentence.strip():
            continue
        test = (current + ' ' + sentence).strip() if current else sentence
        if len(test) <= max_size:
            current = test
        else:
            if current:
                chunks.append(current.strip())
            if len(sentence) > max_size:
                chunks.append(sentence.strip())
                current = ''
            else:
                current = sentence
    if current.strip():
        chunks.append(current.strip())
    if not chunks:
        return [text.strip()]
    return chunks

def parse_walkthrough(filepath):
    sections = []
    current_section = None
    current_text_lines = []

    def flush_section():
        if current_section is not None:
            raw_text = ' '.join(current_text_lines).strip()
            raw_text = re.sub(r'\s+', ' ', raw_text)
            if raw_text:
                raw_chunks = split_into_chunks(raw_text)
            else:
                raw_chunks = []
            chunks = []
            for c in raw_chunks:
                chunks.append({
                    'text': c,
                    'achievement': is_achievement_line(c)
                })
            sections.append({
                'title': current_section,
                'chunks': chunks
            })

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line_stripped = line.rstrip('\n')
            if line_stripped.startswith('SECTION:'):
                flush_section()
                current_section = line_stripped[len('SECTION:'):].strip()
                current_text_lines = []
            else:
                current_text_lines.append(line_stripped)

    flush_section()
    return sections

def build_html(sections):
    sections_json = json.dumps(sections, ensure_ascii=False)

    html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Yotei Tracker">
<meta name="theme-color" content="#1a0f0a">
<title>Ghost of Yotei Walkthrough Tracker</title>
<style>
  :root {
    --bg: #0e0905;
    --surface: #1a100a;
    --surface2: #231508;
    --border: #3a2210;
    --accent: #c8820a;
    --accent2: #e8a020;
    --gold: #d4a017;
    --gold-bg: #2a1f00;
    --gold-border: #a07010;
    --text: #e8d8c0;
    --text-muted: #907860;
    --text-dim: #604030;
    --green: #4a8a40;
    --green-bg: #0a1a08;
    --progress-bg: #2a1508;
    --progress-fill: #c8820a;
    --header-h: 80px;
    --safe-top: env(safe-area-inset-top, 0px);
    --safe-bottom: env(safe-area-inset-bottom, 0px);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif; }

  #header {
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 100;
    background: rgba(14,9,5,0.96);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding-top: max(var(--safe-top), 12px);
    padding-bottom: 10px;
    padding-left: 16px;
    padding-right: 16px;
  }
  #header-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  #header-title {
    font-size: 15px;
    font-weight: 700;
    color: var(--accent2);
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
  #header-pct {
    font-size: 14px;
    font-weight: 700;
    color: var(--accent);
    min-width: 40px;
    text-align: right;
  }
  #progress-bar-wrap {
    height: 5px;
    background: var(--progress-bg);
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 10px;
  }
  #progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    border-radius: 3px;
    transition: width 0.3s ease;
    width: 0%;
  }
  #btn-row {
    display: flex;
    gap: 7px;
  }
  .hdr-btn {
    flex: 1;
    padding: 7px 4px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
    transition: background 0.15s, color 0.15s;
  }
  .hdr-btn:active { background: var(--surface2); }
  .hdr-btn.resume-btn { background: var(--accent); color: #0e0905; border-color: var(--accent2); }
  .hdr-btn.resume-btn:active { background: var(--accent2); }
  .hdr-btn.reset-btn { color: #c05040; border-color: #5a1a10; }

  #content {
    padding-top: calc(var(--header-h) + max(var(--safe-top), 12px) + 20px);
    padding-bottom: calc(32px + var(--safe-bottom));
    padding-left: 12px;
    padding-right: 12px;
  }

  .section-block {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 12px;
    overflow: hidden;
  }
  .section-header {
    display: flex;
    align-items: center;
    padding: 13px 14px;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
    user-select: none;
    gap: 10px;
    background: var(--surface);
  }
  .section-header:active { background: var(--surface2); }
  .section-arrow {
    color: var(--text-muted);
    font-size: 11px;
    flex-shrink: 0;
    transition: transform 0.2s ease;
    display: inline-block;
  }
  .section-block.open .section-arrow { transform: rotate(90deg); }
  .section-title {
    flex: 1;
    font-size: 13px;
    font-weight: 700;
    color: var(--accent2);
    letter-spacing: 0.3px;
  }
  .section-counter {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    flex-shrink: 0;
    min-width: 44px;
    text-align: right;
  }
  .section-counter.done { color: var(--green); }
  .section-body {
    display: none;
    padding: 0 10px 10px;
  }
  .section-block.open .section-body { display: block; }

  .chunk-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 10px;
    border-radius: 8px;
    margin-bottom: 4px;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
    border-left: 3px solid transparent;
    background: var(--surface2);
    transition: background 0.15s;
  }
  .chunk-item:active { background: var(--border); }
  .chunk-item.achievement { border-left-color: var(--gold-border); background: var(--gold-bg); }
  .chunk-item.done { opacity: 0.45; }
  .chunk-item.highlight-pulse {
    animation: pulse-highlight 1.5s ease;
  }
  @keyframes pulse-highlight {
    0%   { background: var(--accent); color: #0e0905; }
    40%  { background: var(--accent); color: #0e0905; }
    100% { background: var(--surface2); color: var(--text); }
  }

  .chunk-checkbox {
    flex-shrink: 0;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 2px solid var(--text-dim);
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 1px;
    transition: background 0.15s, border-color 0.15s;
    font-size: 13px;
    color: transparent;
  }
  .chunk-item.done .chunk-checkbox {
    background: var(--green);
    border-color: var(--green);
    color: #fff;
  }
  .chunk-item.achievement .chunk-checkbox {
    border-color: var(--gold);
  }
  .chunk-item.achievement.done .chunk-checkbox {
    background: var(--gold);
    border-color: var(--gold);
    color: #0e0905;
  }

  .chunk-text {
    font-size: 14px;
    line-height: 1.55;
    color: var(--text);
    flex: 1;
  }
  .chunk-item.done .chunk-text { text-decoration: line-through; color: var(--text-dim); }
  .achievement-tag {
    display: inline-block;
    background: var(--gold);
    color: #0e0905;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.5px;
    border-radius: 4px;
    padding: 1px 5px;
    margin-bottom: 4px;
    text-transform: uppercase;
  }
</style>
</head>
<body>

<div id="header">
  <div id="header-top">
    <span id="header-title">Ghost of Yotei</span>
    <span id="header-pct">0%</span>
  </div>
  <div id="progress-bar-wrap"><div id="progress-bar"></div></div>
  <div id="btn-row">
    <button class="hdr-btn resume-btn" onclick="resumeWalkthrough()">Resume</button>
    <button class="hdr-btn" onclick="expandAll()">Expand All</button>
    <button class="hdr-btn" onclick="collapseAll()">Collapse All</button>
    <button class="hdr-btn reset-btn" onclick="confirmReset()">Reset</button>
  </div>
</div>

<div id="content"></div>

<script>
var GAME_SLUG = ''' + repr(GAME_SLUG) + ''';
var STORAGE_KEY = GAME_SLUG + 'TrackerData';

var SECTIONS = ''' + sections_json + ''';

var checkedState = {};

function loadState() {
  try {
    var raw = localStorage.getItem(STORAGE_KEY);
    if (raw) checkedState = JSON.parse(raw);
  } catch(e) { checkedState = {}; }
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(checkedState));
  } catch(e) {}
}

function chunkId(si, ci) { return 's' + si + 'c' + ci; }

function isChecked(si, ci) { return !!checkedState[chunkId(si, ci)]; }

function setChecked(si, ci, val) {
  checkedState[chunkId(si, ci)] = val;
  saveState();
  updateChunkUI(si, ci);
  updateSectionCounter(si);
  updateOverallProgress();
}

function totalChunks() {
  var t = 0;
  for (var i = 0; i < SECTIONS.length; i++) t += SECTIONS[i].chunks.length;
  return t;
}

function totalChecked() {
  var t = 0;
  for (var i = 0; i < SECTIONS.length; i++) {
    for (var j = 0; j < SECTIONS[i].chunks.length; j++) {
      if (isChecked(i, j)) t++;
    }
  }
  return t;
}

function sectionChecked(si) {
  var t = 0;
  for (var j = 0; j < SECTIONS[si].chunks.length; j++) {
    if (isChecked(si, j)) t++;
  }
  return t;
}

function updateOverallProgress() {
  var total = totalChunks();
  var done = totalChecked();
  var pct = total > 0 ? Math.round((done / total) * 100) : 0;
  document.getElementById('progress-bar').style.width = pct + '%';
  document.getElementById('header-pct').textContent = pct + '%';
}

function updateSectionCounter(si) {
  var el = document.getElementById('counter-' + si);
  if (!el) return;
  var total = SECTIONS[si].chunks.length;
  var done = sectionChecked(si);
  if (done === total && total > 0) {
    el.textContent = '\\u2713 ' + done + '/' + total;
    el.className = 'section-counter done';
  } else {
    el.textContent = done + '/' + total;
    el.className = 'section-counter';
  }
}

function updateChunkUI(si, ci) {
  var el = document.getElementById('chunk-' + si + '-' + ci);
  if (!el) return;
  var checked = isChecked(si, ci);
  var cb = el.querySelector('.chunk-checkbox');
  if (checked) {
    el.classList.add('done');
    if (cb) cb.textContent = '\\u2713';
  } else {
    el.classList.remove('done');
    if (cb) cb.textContent = '';
  }
}

function toggleChunk(si, ci) {
  setChecked(si, ci, !isChecked(si, ci));
}

function toggleSection(si) {
  var block = document.getElementById('section-block-' + si);
  if (block) block.classList.toggle('open');
}

function expandAll() {
  var blocks = document.querySelectorAll('.section-block');
  for (var i = 0; i < blocks.length; i++) blocks[i].classList.add('open');
}

function collapseAll() {
  var blocks = document.querySelectorAll('.section-block');
  for (var i = 0; i < blocks.length; i++) blocks[i].classList.remove('open');
}

function resumeWalkthrough() {
  for (var i = 0; i < SECTIONS.length; i++) {
    for (var j = 0; j < SECTIONS[i].chunks.length; j++) {
      if (!isChecked(i, j)) {
        var block = document.getElementById('section-block-' + i);
        if (block) block.classList.add('open');
        var el = document.getElementById('chunk-' + i + '-' + j);
        if (el) {
          setTimeout(function(elem) {
            elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            elem.classList.add('highlight-pulse');
            setTimeout(function() { elem.classList.remove('highlight-pulse'); }, 1600);
          }, 80, el);
        }
        return;
      }
    }
  }
  alert('All steps complete! Congratulations on completing Ghost of Yotei!');
}

function confirmReset() {
  if (window.confirm('Reset all progress? This cannot be undone.')) {
    checkedState = {};
    saveState();
    renderAll();
  }
}

function renderAll() {
  var content = document.getElementById('content');
  var html = '';
  for (var i = 0; i < SECTIONS.length; i++) {
    var sec = SECTIONS[i];
    html += '<div class="section-block" id="section-block-' + i + '">';
    html += '<div class="section-header" onclick="toggleSection(' + i + ')">';
    html += '<span class="section-arrow">&#9654;</span>';
    html += '<span class="section-title">' + escHtml(sec.title) + '</span>';
    html += '<span class="section-counter" id="counter-' + i + '">0/' + sec.chunks.length + '</span>';
    html += '</div>';
    html += '<div class="section-body">';
    for (var j = 0; j < sec.chunks.length; j++) {
      var chunk = sec.chunks[j];
      var achClass = chunk.achievement ? ' achievement' : '';
      html += '<div class="chunk-item' + achClass + '" id="chunk-' + i + '-' + j + '" onclick="toggleChunk(' + i + ',' + j + ')">';
      html += '<div class="chunk-checkbox"></div>';
      html += '<div class="chunk-text">';
      if (chunk.achievement) html += '<span class="achievement-tag">\\u26a0 Trophy / Achievement</span><br>';
      html += escHtml(chunk.text);
      html += '</div></div>';
    }
    html += '</div></div>';
  }
  content.innerHTML = html;
  for (var si = 0; si < SECTIONS.length; si++) {
    for (var ci = 0; ci < SECTIONS[si].chunks.length; ci++) {
      if (isChecked(si, ci)) updateChunkUI(si, ci);
    }
    updateSectionCounter(si);
  }
  updateOverallProgress();
}

function escHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

loadState();
renderAll();
</script>
</body>
</html>'''
    return html

def main():
    print('Parsing walkthrough.txt...')
    sections = parse_walkthrough('walkthrough.txt')
    total_chunks = sum(len(s['chunks']) for s in sections)
    print('Sections found: ' + str(len(sections)))
    print('Total chunks: ' + str(total_chunks))
    html = build_html(sections)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('index.html written successfully.')

if __name__ == '__main__':
    main()
