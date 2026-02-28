async function loadIndex() {
  if (window.BIBLE_INDEX) return window.BIBLE_INDEX;
  // Fallback for HTTP hosting
  const res = await fetch('./bible_index.json')
    .catch(() => fetch('../bible_index.json'))
    .catch(() => fetch('/bible_index.json'));
  if (!res || !res.ok) throw new Error('Cannot load bible_index.json');
  return await res.json();
}

function esc(s){
  return (s||'').toString().replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function pad2(n){ return String(n).padStart(2,'0'); }

function getSiteBase() {
  // Returns the project base path ending with '/'
  // Works on GitHub Pages (/REPO/...), local servers, and file://
  const p = window.location.pathname || '';
  const i = p.indexOf('/books/');
  if (i >= 0) return p.slice(0, i+1); // keep trailing '/'
  // fallback: if we are on /index.html, base is folder path
  if (p.endsWith('/')) return p;
  return p.replace(/[^\/]*$/, ''); // strip filename
}

function chapterUrl(slug, ch2) {
  const base = getSiteBase();
  return `${base}books/${slug}/${ch2}/`;
}

function homeUrl() {
  const base = getSiteBase();
  return `${base}index.html`;
}

function parsePath() {
  // Expected: /books/<slug>/index.html OR /books/<slug>/<ch>/index.html
  const parts = window.location.pathname.split('/').filter(Boolean);
  const booksIdx = parts.indexOf('books');
  if (booksIdx === -1) return {type:'landing'};
  const slug = parts[booksIdx+1] || null;
  const maybeChapter = parts[booksIdx+2] || null;
  if (!slug) return {type:'landing'};
  if (!maybeChapter || maybeChapter === 'index.html') return {type:'book', slug};
  return {type:'chapter', slug, chapter: maybeChapter};
}

function relativeIndexPath() {
  const parts = window.location.pathname.split('/').filter(Boolean);
  // Determine how many levels deep to reach root
  // landing: 0, book: /books/<slug>/ => 2 deep, chapter: /books/<slug>/<ch>/ => 3 deep
  const booksIdx = parts.indexOf('books');
  if (booksIdx === -1) return './bible_index.json';
  const depth = parts.length; // includes file maybe
  // if last part is index.html, depth includes it; we want folder depth
  const isFile = parts[parts.length-1].includes('.');
  const folderDepth = isFile ? depth-1 : depth;
  // root is folderDepth levels up from current folder
  const up = Array(folderDepth).fill('..').join('/');
  return (up ? up + '/' : './') + 'bible_index.json';
}

function relativeAssetsPrefix() {
  const parts = window.location.pathname.split('/').filter(Boolean);
  const booksIdx = parts.indexOf('books');
  if (booksIdx === -1) return './assets';
  const isFile = parts[parts.length-1].includes('.');
  const folderDepth = isFile ? parts.length-1 : parts.length;
  const up = Array(folderDepth).fill('..').join('/');
  return (up ? up + '/' : './') + 'assets';
}

function buildTopNav(index, ctx) {
  const nav = document.getElementById('topnav');
  if (!nav) return;

  const books = index.books || [];
  const currentBook = books.find(b => b.slug === ctx.slug) || books[0];

  const bookOptions = books.map(b =>
    `<option value="${esc(b.slug)}" ${b.slug===currentBook.slug?'selected':''}>${esc(b.name)}</option>`
  ).join('');

  const chapterCount = currentBook?.chapters || 1;
  const currentChapter = ctx.chapter ? parseInt(ctx.chapter,10) : 1;
  const chapterOptions = Array.from({length: chapterCount}, (_,i)=>{
    const ch = i+1;
    const val = pad2(ch);
    return `<option value="${val}" ${ch===currentChapter?'selected':''}>Chapter ${ch}</option>`;
  }).join('');

  nav.innerHTML = `
    <div class="controls" style="position:static; margin-bottom:14px;">
      <a class="btn" href="${homeUrl()}">Home</a>
      <label class="small muted">Book
        <select id="bookSelect" class="btn" style="padding:8px 10px;">
          ${bookOptions}
        </select>
      </label>
      <label class="small muted">Chapter
        <select id="chapterSelect" class="btn" style="padding:8px 10px;">
          ${chapterOptions}
        </select>
      </label>
      <span class="tag">Nav</span>
    </div>
  `;

  const bookSel = document.getElementById('bookSelect');
  const chSel = document.getElementById('chapterSelect');

  const go = () => {
    const slug = bookSel.value;
    const ch = chSel.value; // already 2-digit
    window.location.href = chapterUrl(slug, ch);
  };

  bookSel.addEventListener('change', () => {
    // reset to chapter 01 when switching books
    const selected = books.find(b => b.slug === bookSel.value);
    const count = selected?.chapters || 1;
    chSel.innerHTML = Array.from({length: count}, (_,i)=>{
      const ch=i+1, val=pad2(ch);
      return `<option value="${val}">Chapter ${ch}</option>`;
    }).join('');
    go();
  });
  chSel.addEventListener('change', go);
}

async function renderLanding() {
  const idx = await loadIndex();
  const el = document.getElementById('books');
  if (!el) return;
  el.innerHTML = (idx.books||[]).map(b => `
    <div class="item">
      <a href="./books/${esc(b.slug)}/">${esc(b.name)}</a>
      <span class="tag">${esc(b.chapters)} chapters</span>
      <div class="muted small" style="margin-top:6px;">Slug: <span class="mono">${esc(b.slug)}</span></div>
    </div>
  `).join('');
}

async function renderBookTOC(slug) {
  const idx = await loadIndex();
  const book = (idx.books||[]).find(b => b.slug === slug);
  if (!book) {
    document.getElementById('bookTitle').textContent = 'Book not found';
    return;
  }
  document.getElementById('bookTitle').textContent = book.name;
  document.getElementById('bookMeta').textContent = `${book.chapters} chapters`;

  const list = document.getElementById('chapters');
  list.innerHTML = Array.from({length: book.chapters}, (_,i)=>{
    const ch=i+1;
    const folder=pad2(ch);
    return `<div class="item"><a href="./${folder}/">Chapter ${ch}</a> <span class="tag">${folder}</span></div>`;
  }).join('');

  buildTopNav(idx, {type:'book', slug});
}


function tokenizeHebrewToTokens(he, data, ref){
  const cleaned = (he||'').replace(/[׃]/g,'').trim();
  if (!cleaned) return [];
  const parts = cleaned.split(/\s+/g);
  const toks = [];
  let t = 1;
  parts.forEach(p=>{
    const subs = p.split('־').filter(Boolean);
    subs.forEach(sp=>{
      toks.push({
        id: `${(data.book_slug||'book')}.${String(data.chapter||1).padStart(2,'0')}.${String((ref||'1:1').split(':')[1]||1).padStart(2,'0')}.t${String(t++).padStart(3,'0')}`,
        surface: sp,
        lemma: '',
        root: '',
        pos: '',
        morph: '',
        features: {},
        gloss: ''
      });
    });
  });
  return toks;
}

function renderTokenInfo(tok){
  const el = document.getElementById('tokenInfo');
  if (!el) return;
  if (!tok) {
    el.innerHTML = '<div class="muted small">Click a Hebrew token to see lemma, root, morphology, and gloss.</div>';
    return;
  }
  const feat = tok.features ? Object.entries(tok.features).map(([k,v])=>`<div><span class="tag">${esc(k)}</span> <span class="mono">${esc(String(v))}</span></div>`).join('') : '';
  el.innerHTML = `
    <div class="item">
      <div style="display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; align-items:baseline;">
        <div><b dir="rtl" style="font-size:18px;">${esc(tok.surface||'')}</b> <span class="tag">${esc(tok.pos||'')}</span></div>
        <div class="mono small">${esc(tok.id||'')}</div>
      </div>
      <div class="muted small" style="margin-top:8px;">
        <div><span class="tag">lemma</span> <b dir="rtl">${esc(tok.lemma||'')}</b></div>
        <div style="margin-top:6px;"><span class="tag">root</span> <span class="mono">${esc(tok.root||'')}</span></div>
        <div style="margin-top:6px;"><span class="tag">morph</span> <span class="mono">${esc(tok.morph||'')}</span></div>
        <div style="margin-top:6px;"><span class="tag">gloss</span> <b>${esc(tok.gloss||'')}</b></div>
        ${feat ? `<div style="margin-top:8px;">${feat}</div>` : ''}
      </div>
    </div>
  `;
}

function wireTokenClicks(){
  renderTokenInfo(null);
  document.querySelectorAll('.hbTok').forEach(el=>{
    el.addEventListener('click', ()=>{
      const id = el.dataset.tok;
      const tok = window.__tokenIndex ? window.__tokenIndex.get(id) : null;
      renderTokenInfo(tok || {surface: el.textContent, id, pos:'', lemma:'', root:'', morph:'', gloss:''});
    });
  });
}

function tokenizeHebrew(he){
  const cleaned = (he||'').replace(/[׃]/g,'').trim();
  return cleaned ? cleaned.split(/\s+/g) : [];
}



function parseVerseNum(ref){
  // ref like "2:17"
  const m = String(ref||'').match(/:(\d+)/);
  return m ? parseInt(m[1],10) : null;
}

function verseRange(data){
  const nums = (data.verses||[]).map(v=>parseVerseNum(v.ref)).filter(n=>Number.isFinite(n));
  if (!nums.length) return null;
  const min = Math.min.apply(null, nums);
  const max = Math.max.apply(null, nums);
  return {min, max};
}

// --- Compatibility + normalization layer ---------------------------------
// Goal: accept older / ad-hoc chapter JSON shapes (e.g. {book:{name,slug}, verses:[{n,...}]})
// and normalize into Spec v1.2-ish shape expected by the renderer.
function normalizeChapterData(raw){
  const data = raw && typeof raw === 'object' ? JSON.parse(JSON.stringify(raw)) : {};

  // spec_version
  if (!data.spec_version) {
    if (typeof data.spec === 'string') data.spec_version = data.spec;
    else if (data.spec && typeof data.spec === 'object' && data.spec.version) data.spec_version = String(data.spec.version);
  }

  // book/name/slug
  if (data.book && typeof data.book === 'object') {
    if (!data.book_name && data.book.name) data.book_name = data.book.name;
    if (!data.book_slug && data.book.slug) data.book_slug = data.book.slug;
  }
  // Some inputs use book_name instead of book
  if (typeof data.book !== 'string') {
    if (typeof data.book_name === 'string') data.book = data.book_name;
    else if (data.book && typeof data.book === 'object' && typeof data.book.name === 'string') data.book = data.book.name;
  }
  if (!data.book_slug && data.book && typeof data.book === 'object' && data.book.slug) data.book_slug = data.book.slug;
  if (!data.book_slug && typeof data.book === 'string') {
    // best-effort slugify
    data.book_slug = String(data.book).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
  }

  // title
  if (!data.title || typeof data.title !== 'string') {
    const b = (typeof data.book === 'string' && data.book) ? data.book : 'Book';
    const ch = data.chapter || '';
    data.title = `${b} - Chapter ${ch}`.trim();
  }

  // verses: ensure ref exists; accept {n:1,...} as verse number.
  const chNum = data.chapter || (data.verses && data.verses[0] && data.verses[0].ref ? String(data.verses[0].ref).split(':')[0] : null);
  (data.verses||[]).forEach((v,i)=>{
    if (!v.ref) {
      const n = (v.n != null ? v.n : (i+1));
      v.ref = `${chNum || data.chapter || 1}:${n}`;
    }
    // normalize missing fields
    if (typeof v.en !== 'string') v.en = v.en == null ? '' : String(v.en);
    if (typeof v.tr !== 'string') v.tr = v.tr == null ? '' : String(v.tr);
    if (!Array.isArray(v.tokens)) v.tokens = [];
  });

  return data;
}

function formatChapterTitle(data){
  const book = (typeof data.book === 'string' ? data.book : (data.book_name || (data.book && data.book.name))) || 'Book';
  const ch = data.chapter || (String((data.verses||[{}])[0].ref||'').split(':')[0] || '');
  return `${book} - Chapter ${ch}`;
}

function getSubtitle(data){
  // Optional: provide in JSON as `subtitle` or `book_subtitle` or `book_hebrew`.
  return data.subtitle || data.book_subtitle || data.book_hebrew || data.book_he || '';
}

function buildBreadcrumb(data){
  const base = getSiteBase();
  const slug = data.book_slug || '';
  const bookName = (typeof data.book === 'string' ? data.book : (data.book_name || (data.book && data.book.name))) || 'Book';
  const ch = data.chapter || '';
  const home = `<a href="${homeUrl()}">Home</a>`;
  const book = slug ? `<a href="${base}books/${slug}/index.html">${esc(bookName)}</a>` : esc(bookName);
  const chap = `<span>Chapter ${esc(String(ch))}</span>`;
  return `${home} <span class="crumb-sep">›</span> ${book} <span class="crumb-sep">›</span> ${chap}`;
}

function renderErrorBox(err){
  try{
    const wrap = document.querySelector('main.wrap') || document.body;
    let box = document.getElementById('runtimeErrorBox');
    if (!box){
      box = document.createElement('div');
      box.id = 'runtimeErrorBox';
      box.className = 'card';
      box.style.border = '1px solid rgba(239,68,68,0.35)';
      box.style.background = 'rgba(239,68,68,0.06)';
      box.style.margin = '16px auto';
      box.style.maxWidth = '1100px';
      wrap.prepend(box);
    }
    box.innerHTML = `<div class="h2" style="margin-bottom:6px;">Renderer error</div>
      <div class="muted small">This page loaded, but a JavaScript error prevented rendering the chapter content.</div>
      <pre class="mono" style="white-space:pre-wrap; margin-top:10px;">${escapeHtml(String(err && err.stack ? err.stack : err))}</pre>`;
  }catch(_){}
}
function renderChapter(data) {
  try{
  const title = formatChapterTitle(data);
  document.getElementById('chapterTitle').textContent = title;
  // SEO title
  document.title = `${title} | Hebrew Bible`;

  // Breadcrumb
  const h1 = document.getElementById('chapterTitle');
  let bc = document.getElementById('chapterBreadcrumb');
  if (!bc) {
    bc = document.createElement('nav');
    bc.id = 'chapterBreadcrumb';
    bc.className = 'breadcrumb';
    h1.parentNode.insertBefore(bc, h1);
  }
  bc.innerHTML = buildBreadcrumb(data);

  // Subtitle + verse range
  const sub = getSubtitle(data);
  const vr = verseRange(data);
  const vrText = vr ? `verses ${vr.min}–${vr.max}` : '';
  let meta = document.getElementById('chapterMeta');
  if (!meta) {
    meta = document.createElement('div');
    meta.id = 'chapterMeta';
    meta.className = 'chapter-meta';
    h1.parentNode.insertBefore(meta, h1.nextSibling);
  }
  meta.innerHTML = [
    sub ? `<div class="subtitle">${escapeHtml(sub)}</div>` : ``,
    vrText ? `<div class="muted small">${escapeHtml(vrText)}</div>` : ``
  ].join('');

  

  const tokenIndex = new Map();
  (data.verses||[]).forEach(v => (v.tokens||[]).forEach(t => tokenIndex.set(t.id, t)));
  window.__tokenIndex = tokenIndex;

  const versesEl = document.getElementById('verses');
  if (!versesEl) throw new Error('Missing #verses container in index.html template');
  versesEl.innerHTML = (data.verses||[]).map(v=>{
    const tokens = v.tokens && v.tokens.length ? v.tokens : tokenizeHebrewToTokens(v.he, data, v.ref);
    const hebSpans = tokens.map(t => {
      const id = t.id || '';
      const surface = t.surface || '';
      return `<span class="hbTok" data-tok="${esc(id)}" title="Click for parsing">${esc(surface)}</span>`;
    }).join(' ');

    const interlinear = tokens.map(t => `
      <div class="il-row">
        <div class="il-he"><span class="hbTok" data-tok="${esc(t.id||'')}">${esc(t.surface||'')}</span></div>
        <div class="il-en">
          <div><span class="tag">${esc(t.pos||'')}</span> <span class="mono">${esc(t.morph||'')}</span></div>
          <div class="muted small" style="margin-top:4px;"><b>${esc(t.gloss||'')}</b> <span class="muted">${esc(t.lemma||'')}</span> <span class="muted">${esc(t.root?('· '+t.root):'')}</span></div>
        </div>
      </div>
    `).join('');

    return `
      <div class="verse" data-ref="${esc(v.ref)}" data-he="${esc(v.he)}" data-en="${esc(v.en)}" data-tr="${esc(v.tr)}">
        <div class="vref">
          <b>${esc(v.ref)}</b>
          <span class="tag">Text</span>
          <span class="spacer"></span>
          <button class="btn small" onclick="speakVerse('${esc(v.ref)}')">Play</button>
        </div>
        <div class="he heBlock" dir="rtl" style="user-select:text;">${hebSpans}</div>
        <div class="en enBlock">${esc(v.en)}</div>
        <div class="tr trBlock">${esc(v.tr)}</div>
        <div class="interlinear ilBlock">
          <div class="muted small" style="margin-bottom:8px;">Interlinear (v1.1): token · POS/morph · gloss · lemma/root. Click a token anywhere to see details.</div>
          ${interlinear}
        </div>
      </div>
    `;
  }).join('');

  // Help panels
  const g = document.getElementById('grammar');
  if (g) g.innerHTML = (data.grammar||[]).map(n=>`
    <div class="item" style="margin-bottom:10px;">
      <div><b>${esc(n.title)}</b> <span class="tag">${esc(n.id)}</span></div>
      <div class="muted small" style="margin-top:6px;">${esc(n.body)}</div>
    </div>
  `).join('');

  const l = document.getElementById('lexicon');
  if (l) l.innerHTML = (data.lexicon||[]).map(x=>`
    <div class="item" style="margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; align-items:baseline;">
        <div class="lex-lemma"><b dir="rtl">${esc(x.lemma)}</b> <span class="muted">(${esc(x.pos)})</span></div>
        <div class="lex-gloss" style="color:var(--good); font-weight:600;">${esc(x.gloss)}</div>
      </div>
      <div class="muted small" style="margin-top:6px;">
        <div><span class="tag">root</span> <span class="mono">${esc(x.root)}</span></div>
        <div style="margin-top:6px;">${esc(x.notes||'')}</div>
      </div>
    </div>
  `).join('');

  const e = document.getElementById('exercises');
  if (e) e.innerHTML = (data.exercises||[]).map((x,i)=>`
    <details>
      <summary>Exercise ${i+1}</summary>
      <div class="muted" style="margin-top:10px;"><b>Q:</b> ${esc(x.q)}</div>
      <div class="muted" style="margin-top:10px;"><b>A:</b> ${esc(x.a)}</div>
    </details>
  `).join('');

  // Token click handler
  wireTokenClicks();
}


let showHeb = true, showEng = true, showIL = false;
let ttsRate = 0.90;

function applyToggles(){
  document.querySelectorAll('.heBlock').forEach(el => el.style.display = showHeb ? 'block':'none');
  document.querySelectorAll('.enBlock').forEach(el => el.style.display = showEng ? 'block':'none');
  document.querySelectorAll('.trBlock').forEach(el => el.style.display = showEng ? 'block':'none');
  document.querySelectorAll('.ilBlock').forEach(el => el.style.display = showIL ? 'block':'none');
  }catch(err){
    renderErrorBox(err);
  }

}

function setActive(btn, active){ btn.classList.toggle('active', active); }

function setupControls(){
  const toggleHeb = document.getElementById('toggleHeb');
  const toggleEng = document.getElementById('toggleEng');
  const toggleIL = document.getElementById('toggleInterlinear');
  const search = document.getElementById('search');
  const rateEl = document.getElementById('ttsRate');
  const rateLabel = document.getElementById('ttsRateLabel');

  toggleHeb?.addEventListener('click', (ev)=>{ showHeb=!showHeb; setActive(ev.target, showHeb); applyToggles(); });
  toggleEng?.addEventListener('click', (ev)=>{ showEng=!showEng; setActive(ev.target, showEng); applyToggles(); });
  toggleIL?.addEventListener('click', (ev)=>{ showIL=!showIL; setActive(ev.target, showIL); applyToggles(); });

  search?.addEventListener('input', (ev)=>{
    const q=(ev.target.value||'').toLowerCase();
    document.querySelectorAll('.verse').forEach(v=>{
      const extra = (v.querySelectorAll('.hbTok') ? Array.from(v.querySelectorAll('.hbTok')).map(x=>x.textContent).join(' ') : '');
      const hay=(v.dataset.ref+' '+v.dataset.he+' '+v.dataset.en+' '+v.dataset.tr+' '+extra).toLowerCase();
      v.style.display = hay.includes(q) ? 'block':'none';
    });
  });

  if (rateEl && rateLabel){
    ttsRate = parseFloat(rateEl.value);
    rateLabel.textContent = `${ttsRate.toFixed(2)}×`;
    rateEl.addEventListener('input', ()=>{
      ttsRate = parseFloat(rateEl.value);
      rateLabel.textContent = `${ttsRate.toFixed(2)}×`;
    });
  }
}

function speakVerse(ref){
  try{
    const data = window.__chapterData;
    const v = (data?.verses||[]).find(x => x.ref === ref);
    if (!v) return;
    const u = new SpeechSynthesisUtterance((v.he||'').replace(/[׃]/g,''));
    u.lang = 'he-IL';
    u.rate = ttsRate;
    u.pitch = 1.0;
    u.volume = 1.0;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  } catch(e){
    alert('TTS not available in this browser/device.');
  }
}
window.speakVerse = speakVerse;

async function renderChapterPage(slug, chapter) {
  // Load chapter data first (so we can normalize and recover missing book metadata)
  let data = window.__chapterData;
  if (!data) {
    const res = await fetch('./data.json');
    if (!res.ok) throw new Error('Cannot load data.json in this chapter folder. If you opened via file://, use data.js.');
    data = await res.json();
    window.__chapterData = data;
  }

  data = normalizeChapterData(data);
  window.__chapterData = data;

  // Load index and ensure current book exists (best-effort)
  const idx = await loadIndex();
  idx.books = idx.books || [];
  const curSlug = data.book_slug || slug;
  const curName = (typeof data.book === 'string' ? data.book : (data.book_name || (data.book && data.book.name))) || curSlug;
  if (!idx.books.find(b => b.slug === curSlug)) {
    idx.books.push({
      name: curName,
      slug: curSlug,
      chapters: data.book_chapters || data.chapters || data.chapter || 1,
      abbr: (curName||'').split(/\s+/)[0] || curSlug
    });
    // stable-ish ordering: keep existing order, append unknown books last
  }

  buildTopNav(idx, {type:'chapter', slug: curSlug, chapter});

  renderChapter(data);
  setupControls();
  applyToggles();

  // Prev/Next links
  const book = (idx.books||[]).find(b => b.slug === curSlug);
  const chNum = parseInt(chapter,10);
  const prev = document.getElementById('prevNext');
  if (book && prev){
    const prevCh = chNum > 1 ? pad2(chNum-1) : null;
    const nextCh = chNum < book.chapters ? pad2(chNum+1) : null;
    prev.innerHTML = `
      <a class="btn" href="${prevCh ? `../${prevCh}/` : '#'}" ${prevCh ? '' : 'style="opacity:.4; pointer-events:none;"'}>← Prev</a>
      <a class="btn" href="../">Book TOC</a>
      <a class="btn" href="${nextCh ? `../${nextCh}/` : '#'}" ${nextCh ? '' : 'style="opacity:.4; pointer-events:none;"'}>Next →</a>
    `;
  }
}

(async function main(){
  const ctx = parsePath();
  const page = document.body.dataset.page || ctx.type;
  if (page === 'landing'){
    await renderLanding();
    return;
  }
  if (page === 'book'){
    // Prefer URL-derived slug to avoid manual edits in copied templates
    await renderBookTOC(ctx.slug || document.body.dataset.slug);
    return;
  }
  if (page === 'chapter'){
    // Prefer URL-derived slug/chapter to avoid manual edits in copied templates
    await renderChapterPage(ctx.slug || document.body.dataset.slug, ctx.chapter || document.body.dataset.chapter);
    return;
  }
})();
