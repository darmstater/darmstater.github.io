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
