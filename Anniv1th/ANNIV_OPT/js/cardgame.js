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
      <div class="mcard-front">🖥️</div>
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
