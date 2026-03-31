// ============================================================
//  BINTANG & PARTIKEL
// ============================================================
const cv = document.getElementById('starCanvas');
const cx = cv.getContext('2d');
let stars = [];

function resizeCv() {
  cv.width  = window.innerWidth;
  cv.height = window.innerHeight;
}

function makeStars() {
  stars = Array.from({ length: 220 }, () => ({
    x: Math.random() * cv.width,
    y: Math.random() * cv.height,
    r: Math.random() * 1.4 + .3,
    a: Math.random(),
    spd: Math.random() * .008 + .002,
    dir: Math.random() > .5 ? 1 : -1
  }));
}

let shooters = [];
function addShooter() {
  shooters.push({
    x: Math.random() * cv.width * .65,
    y: Math.random() * cv.height * .35,
    len: Math.random() * 90 + 40,
    spd: Math.random() * 7 + 4,
    a: 1
  });
}

function drawAll() {
  cx.clearRect(0, 0, cv.width, cv.height);
  stars.forEach(s => {
    s.a += s.spd * s.dir;
    if (s.a >= 1 || s.a <= .08) s.dir *= -1;
    cx.beginPath();
    cx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
    cx.fillStyle = `rgba(255,220,240,${s.a})`;
    cx.fill();
  });
  shooters = shooters.filter(s => s.a > 0);
  shooters.forEach(s => {
    const ang = Math.PI / 4;
    cx.beginPath();
    cx.moveTo(s.x, s.y);
    cx.lineTo(s.x - Math.cos(ang) * s.len, s.y - Math.sin(ang) * s.len);
    const g = cx.createLinearGradient(s.x, s.y, s.x - Math.cos(ang) * s.len, s.y - Math.sin(ang) * s.len);
    g.addColorStop(0, `rgba(255,200,220,${s.a})`);
    g.addColorStop(1, 'transparent');
    cx.strokeStyle = g; cx.lineWidth = 1.8; cx.stroke();
    s.x += Math.cos(ang) * s.spd; s.y += Math.sin(ang) * s.spd; s.a -= .022;
  });
  requestAnimationFrame(drawAll);
}

window.addEventListener('resize', () => { resizeCv(); makeStars(); });
resizeCv(); makeStars(); drawAll();
setInterval(addShooter, 3800);

// ============================================================
//  HATI TERBANG
// ============================================================
const HEARTS = ['💕','❤️','🩷','💗','💖','✨','🌸'];
function spawnHeart() {
  const el = document.createElement('div');
  el.className = 'fheart';
  el.textContent = HEARTS[Math.floor(Math.random() * HEARTS.length)];
  el.style.left = Math.random() * 100 + '%';
  el.style.animationDuration = (Math.random() * 10 + 8) + 's';
  el.style.animationDelay   = (Math.random() * 4) + 's';
  el.style.fontSize = (Math.random() * 1.4 + .7) + 'rem';
  document.getElementById('heartsWrap').appendChild(el);
  setTimeout(() => el.remove(), 22000);
}
setInterval(spawnHeart, 1800);

// ============================================================
//  NAVIGASI HALAMAN
// ============================================================
let cur = 'splash';

function goTo(id) {
  const from = document.getElementById(cur);
  const to   = document.getElementById(id);
  from.classList.add('exit');
  setTimeout(() => {
    from.classList.remove('active', 'exit');
    to.classList.add('active');
    cur = id;
    if (id === 'timeline') initTimeline();
    if (id === 'puzzle')   initPuzzle();
    if (id === 'cardgame') initCardGame();
    if (id === 'gallery')  initGallery();
  }, 680);
}

// Splash → Intro otomatis
setTimeout(() => goTo('intro'), 3000);

// ============================================================
//  COUNTER
// ============================================================
function updateCounter() {
  const ms   = Date.now() - CFG.startDate;
  const days = Math.floor(ms / 86400000);
  const hrs  = Math.floor(ms / 3600000);
  const dEl  = document.getElementById('cntDays');
  const hEl  = document.getElementById('cntHours');
  if (dEl) dEl.textContent = days.toLocaleString('id-ID');
  if (hEl) hEl.textContent = hrs.toLocaleString('id-ID');
}
updateCounter();

// ============================================================
//  TIMELINE
// ============================================================
function initTimeline() {
  document.querySelectorAll('.tl-item').forEach((el, i) => {
    setTimeout(() => el.classList.add('vis'), i * 220);
  });
}

// ============================================================
//  PUZZLE SYSTEM
// ============================================================
let pIdx = 0;
let slotData = {};

function initPuzzle() { pIdx = 0; renderPuzzle(); }

function updateProg() {
  document.getElementById('progFill').style.width = (pIdx / CFG.puzzles.length * 100) + '%';
}

function renderPuzzle() {
  updateProg();
  const p   = CFG.puzzles[pIdx];
  const box = document.getElementById('puzzleBox');

  if (p.type === 'riddle') {
    box.innerHTML = `
      <div class="pcard">
        <div class="pnum">${p.num}</div>
        <div style="font-size:3rem;margin:.5rem 0">${p.emoji}</div>
        <div class="pq">"${p.q}"</div>
        <input class="pinput" id="pInput" placeholder="Jawaban kamu..."
          onkeydown="if(event.key==='Enter')checkRiddle()" autocomplete="off">
        <div class="phint" id="phint"></div>
        <div style="display:flex;gap:.7rem;margin-top:1rem;justify-content:center;flex-wrap:wrap">
          <button class="btn" style="margin-top:0" onclick="checkRiddle()">Jawab! ✓</button>
          <button class="btn btn-ghost" style="margin-top:0" onclick="showHint()">Petunjuk 💭</button>
        </div>
      </div>`;
  }

  else if (p.type === 'choice') {
    const opts = p.opts.map((o, i) =>
      `<button class="cbtn" onclick="checkChoice(${i})">${o}</button>`).join('');
    box.innerHTML = `
      <div class="pcard">
        <div class="pnum">${p.num}</div>
        <div style="font-size:3rem;margin:.5rem 0">${p.emoji}</div>
        <div class="pq">"${p.q}"</div>
        <div class="choices">${opts}</div>
        <div class="phint" id="phint"></div>
      </div>`;
  }

  else if (p.type === 'scramble') {
    slotData = {};
    const letters = p.word.split('');
    const shuffled = [...letters].sort(() => Math.random() - .5);

    const slotsHTML   = letters.map((_, i) =>
      `<div class="aslot" id="slot${i}" onclick="removeFromSlot(${i})"></div>`).join('');
    const lettersHTML = shuffled.map((l, i) =>
      `<div class="sletter" id="sl${i}" onclick="addToSlot(${i},'${l}')">${l}</div>`).join('');

    box.innerHTML = `
      <div class="pcard">
        <div class="pnum">${p.num}</div>
        <div style="font-size:3rem;margin:.5rem 0">${p.emoji}</div>
        <div class="pq">"${p.q}"</div>
        <div class="answer-slots">${slotsHTML}</div>
        <div class="scramble-wrap">${lettersHTML}</div>
        <div class="phint" id="phint"></div>
        <div style="display:flex;gap:.7rem;margin-top:1rem;justify-content:center;flex-wrap:wrap">
          <button class="btn" style="margin-top:0" onclick="checkScramble()">Jawab! ✓</button>
          <button class="btn btn-ghost" style="margin-top:0" onclick="clearScramble()">Reset 🔄</button>
          <button class="btn btn-ghost" style="margin-top:0" onclick="showHint()">Petunjuk 💭</button>
        </div>
      </div>`;
  }
}

function showHint() {
  const h = document.getElementById('phint');
  if (h) { h.textContent = CFG.puzzles[pIdx].hint || ''; h.style.opacity = '1'; }
}

function checkRiddle() {
  const inp = document.getElementById('pInput');
  const ua  = inp.value.trim().toLowerCase();
  const ca  = CFG.puzzles[pIdx].ans.toLowerCase();
  if (ua === ca) { inp.classList.add('ok'); setTimeout(nextPuzzle, 750); }
  else {
    inp.classList.add('wrong');
    setTimeout(() => inp.classList.remove('wrong'), 500);
    const h = document.getElementById('phint');
    h.textContent = 'Hmm, bukan itu... coba lagi! 🤔';
    h.style.color = '#ff6b6b';
  }
}

function checkChoice(i) {
  const btns = document.querySelectorAll('.cbtn');
  btns.forEach(b => b.style.pointerEvents = 'none');
  const ci = CFG.puzzles[pIdx].correct;
  if (i === ci) { btns[i].classList.add('cok'); setTimeout(nextPuzzle, 900); }
  else {
    btns[i].classList.add('cwrong');
    btns[ci].classList.add('cok');
    setTimeout(nextPuzzle, 1600);
  }
}

function addToSlot(srcIdx, letter) {
  const slots = document.querySelectorAll('.aslot');
  const emptySlot = [...slots].find(s => !s.textContent.trim());
  if (!emptySlot) return;
  const slotId = parseInt(emptySlot.id.replace('slot',''));
  slotData[slotId] = { letter, srcIdx };
  emptySlot.textContent = letter;
  emptySlot.classList.add('filled');
  document.getElementById('sl' + srcIdx).classList.add('used');
}
function removeFromSlot(slotIdx) {
  const slot = document.getElementById('slot' + slotIdx);
  if (!slot.textContent.trim()) return;
  const d = slotData[slotIdx];
  if (d) {
    const src = document.getElementById('sl' + d.srcIdx);
    if (src) src.classList.remove('used');
    delete slotData[slotIdx];
  }
  slot.textContent = '';
  slot.classList.remove('filled');
}
function clearScramble() {
  slotData = {};
  document.querySelectorAll('.aslot').forEach(s => { s.textContent=''; s.classList.remove('filled'); });
  document.querySelectorAll('.sletter').forEach(s => s.classList.remove('used'));
}
function checkScramble() {
  const slots  = document.querySelectorAll('.aslot');
  const formed = [...slots].map(s => s.textContent.trim()).join('').toLowerCase();
  const target = CFG.puzzles[pIdx].word.toLowerCase();
  if (formed === target) {
    slots.forEach(s => s.style.borderColor = '#2ecc71');
    setTimeout(nextPuzzle, 800);
  } else {
    slots.forEach(s => { s.style.borderColor = '#ff4757'; });
    setTimeout(() => slots.forEach(s => s.style.borderColor = ''), 600);
    const h = document.getElementById('phint');
    h.textContent = 'Belum tepat... coba susun lagi! 🤔';
    h.style.color = '#ff6b6b';
  }
}

function nextPuzzle() {
  pIdx++;
  if (pIdx >= CFG.puzzles.length) {
    document.getElementById('progFill').style.width = '100%';
    document.getElementById('puzzleBox').innerHTML = `
      <div class="pcard" style="text-align:center">
        <div style="font-size:4rem;margin:1rem 0">🎉</div>
        <h3 style="color:var(--gold);font-style:italic">Luar Biasa!</h3>
        <p style="margin-top:.6rem">Kamu memang kenal aku luar dalam 💕</p>
        <button class="btn" onclick="goTo('cardgame')">Lanjut Mini Game! 🎴</button>
      </div>`;
  } else {
    slotData = {};
    renderPuzzle();
  }
}

// ============================================================
//  MEMORY CARD GAME
// ============================================================
let gs = {};

function initCardGame() {
  clearInterval(gs.timerRef);
  gs = { flipped: [], matched: 0, attempts: 0, locked: false, secs: 0, timerRef: null };
  document.getElementById('gAttempts').textContent = '0';
  document.getElementById('gMatched').textContent  = '0';
  document.getElementById('gTimer').textContent     = '0:00';
  document.getElementById('gameWin').style.display  = 'none';

  const emojis = CFG.cardEmojis;
  const deck   = [...emojis, ...emojis].sort(() => Math.random() - .5);
  const grid   = document.getElementById('cardGrid');
  grid.innerHTML = '';

  deck.forEach((em, i) => {
    const c = document.createElement('div');
    c.className = 'mcard';
    c.dataset.em = em;
    c.innerHTML = `<div class="mcard-inner">
      <div class="mcard-front">💕</div>
      <div class="mcard-back">${em}</div>
    </div>`;
    c.addEventListener('click', () => flipCard(c));
    grid.appendChild(c);
  });

  gs.timerRef = setInterval(() => {
    gs.secs++;
    const m = Math.floor(gs.secs / 60), s = gs.secs % 60;
    document.getElementById('gTimer').textContent = `${m}:${String(s).padStart(2,'0')}`;
  }, 1000);
}

function flipCard(c) {
  if (gs.locked || c.classList.contains('flipped') || c.classList.contains('matched') || gs.flipped.length >= 2) return;
  c.classList.add('flipped');
  gs.flipped.push(c);
  if (gs.flipped.length === 2) {
    gs.attempts++;
    document.getElementById('gAttempts').textContent = gs.attempts;
    gs.locked = true;
    const [a, b] = gs.flipped;
    if (a.dataset.em === b.dataset.em) {
      a.classList.add('matched'); b.classList.add('matched');
      gs.matched++;
      document.getElementById('gMatched').textContent = gs.matched;
      gs.flipped = []; gs.locked = false;
      if (gs.matched === CFG.cardEmojis.length) {
        clearInterval(gs.timerRef);
        setTimeout(() => document.getElementById('gameWin').style.display = 'block', 600);
      }
    } else {
      setTimeout(() => {
        a.classList.remove('flipped'); b.classList.remove('flipped');
        gs.flipped = []; gs.locked = false;
      }, 1000);
    }
  }
}

// ============================================================
//  GALLERY
// ============================================================
function initGallery() {
  const grid = document.getElementById('galGrid');
  grid.innerHTML = '';
  CFG.gallery.forEach((item) => {
    const d = document.createElement('div');
    d.className = 'gal-item';
    const isVideo = item.type === 'video';
    if (item.src) {
      if (isVideo) {
        const vid = document.createElement('video');
        vid.src = item.src; vid.muted = true; vid.loop = true; vid.playsInline = true;
        vid.preload = 'metadata';
        d.appendChild(vid);
        const icon = document.createElement('span');
        icon.className = 'gal-vid-icon'; icon.textContent = '▶';
        d.appendChild(icon);
        d.addEventListener('mouseenter', () => vid.play().catch(() => {}));
        d.addEventListener('mouseleave', () => { vid.pause(); vid.currentTime = 0; });
      } else {
        const img = document.createElement('img');
        img.src = item.src; img.alt = item.cap;
        d.appendChild(img);
      }
    } else {
      const ph = document.createElement('div');
      ph.className = 'gal-ph';
      ph.innerHTML = `${item.emoji}<span>${item.cap}</span>`;
      d.appendChild(ph);
    }
    const ov = document.createElement('div');
    ov.className = 'gal-ov';
    ov.innerHTML = `<span class="gal-cap">${item.cap}</span>`;
    d.appendChild(ov);
    d.addEventListener('click', () => openLb(item));
    grid.appendChild(d);
  });

  document.getElementById('galPrev').onclick = () => {
    const w = grid.querySelector('.gal-item').offsetWidth + 11;
    grid.scrollBy({ left: -w * 3, behavior: 'smooth' });
  };
  document.getElementById('galNext').onclick = () => {
    const w = grid.querySelector('.gal-item').offsetWidth + 11;
    grid.scrollBy({ left: w * 3, behavior: 'smooth' });
  };
}

function openLb(item) {
  const lb    = document.getElementById('lightbox');
  const inner = document.getElementById('lbInner');
  document.getElementById('lbCap').textContent = item.cap;
  if (item.src) {
    if (item.type === 'video') {
      inner.innerHTML = `<video src="${item.src}" controls autoplay muted playsinline style="max-width:82vw;max-height:68vh;border-radius:14px;"></video>`;
    } else {
      inner.innerHTML = `<img src="${item.src}" alt="${item.cap}">`;
    }
  } else {
    inner.innerHTML = `<div class="lb-ph">${item.emoji}<p>Tambah foto/video di js/config.js</p></div>`;
  }
  lb.classList.add('open');
}
function closeLb() {
  const lb  = document.getElementById('lightbox');
  const vid = lb.querySelector('video');
  if (vid) { vid.pause(); }
  lb.classList.remove('open');
}
document.getElementById('lightbox').addEventListener('click', e => {
  if (e.target === document.getElementById('lightbox')) closeLb();
});

// ============================================================
//  FINALE — AMPLOP & SURAT
// ============================================================
function openEnv() {
  const flap   = document.getElementById('envFlap');
  const letter = document.getElementById('letterBox');
  const hint   = document.getElementById('envHint');
  const wrap   = document.getElementById('envWrap');
  const btns   = document.getElementById('finBtns');
  if (flap.classList.contains('open')) return;

  flap.classList.add('open');
  hint.style.display = 'none';

  setTimeout(() => {
    wrap.style.display = 'none';
    letter.classList.add('show');
    btns.style.display = 'flex';
    boom();
  }, 1100);
}

// ============================================================
//  QR CODE
// ============================================================
let qrInstance = null;

const HEART_SVG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23FF6B9D' d='M12 21.593c-5.63-5.539-11-10.297-11-14.402 0-3.791 3.068-5.191 5.281-5.191 1.312 0 4.151.501 5.719 4.457 1.59-3.968 4.464-4.447 5.726-4.447 2.54 0 5.274 1.621 5.274 5.181 0 4.069-5.136 8.625-11 14.402z'/%3E%3C/svg%3E";

function buildQr(url) {
  return new QRCodeStyling({
    width: 230,
    height: 230,
    type: "canvas",
    data: url,
    image: HEART_SVG,
    dotsOptions: {
      type: "rounded",
      gradient: {
        type: "radial",
        rotation: 0,
        colorStops: [
          { offset: 0, color: "#FFD166" },
          { offset: 1, color: "#C084FC" }
        ]
      }
    },
    backgroundOptions: { color: "#07071a" },
    imageOptions: { crossOrigin: "anonymous", margin: 5, imageSize: 0.35 },
    cornersSquareOptions: { type: "extra-rounded", color: "#FF6B9D" },
    cornersDotOptions:   { type: "dot",           color: "#FFD166" }
  });
}

function openQr() {
  const url = window.location.href;
  const inp = document.getElementById('qrUrlInp');
  inp.placeholder = url;

  const canvas = document.getElementById('qrCanvas');
  canvas.innerHTML = '';

  qrInstance = buildQr(url);
  qrInstance.append(canvas);

  document.getElementById('qrModal').classList.add('open');
}

function updateQr() {
  const inp = document.getElementById('qrUrlInp');
  const url = inp.value.trim() || window.location.href;
  const canvas = document.getElementById('qrCanvas');
  canvas.innerHTML = '';
  qrInstance = buildQr(url);
  qrInstance.append(canvas);
}

function closeQr() {
  document.getElementById('qrModal').classList.remove('open');
}

document.getElementById('qrModal').addEventListener('click', e => {
  if (e.target === document.getElementById('qrModal')) closeQr();
});

// ============================================================
//  CONFETTI
// ============================================================
const COLORS = ['#FFD166','#FF6B9D','#C084FC','#60A5FA','#34D399','#F87171','#FBCFE8'];
function boom() {
  for (let i = 0; i < 90; i++) {
    setTimeout(() => {
      const p = document.createElement('div');
      p.className = 'cpiece';
      p.style.left    = Math.random() * 100 + 'vw';
      p.style.background = COLORS[Math.floor(Math.random() * COLORS.length)];
      p.style.width   = (Math.random() * 11 + 5) + 'px';
      p.style.height  = (Math.random() * 6 + 3) + 'px';
      p.style.borderRadius = Math.random() > .5 ? '50%' : '2px';
      p.style.animationDuration = (Math.random() * 2.5 + 2) + 's';
      p.style.animationDelay    = (Math.random() * .4) + 's';
      document.body.appendChild(p);
      setTimeout(() => p.remove(), 5500);
    }, i * 28);
  }
}
