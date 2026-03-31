// ============================================================
//  BACKGROUND MUSIC
// ============================================================
const bgMusic     = document.getElementById('bgMusic');
const musicBtn    = document.getElementById('musicBtn');
const musicPrompt = document.getElementById('musicPrompt');

bgMusic.src    = 'asset/sound/A Thousand Years \u2013 Piano Cover \uff5c Christina Perri (Sheet Music) [_TNwN92mw6E].webm';
bgMusic.loop   = true;
bgMusic.volume = 0.45;

let musicStarted = false;

function startMusic() {
  if (musicStarted) return;
  bgMusic.play().then(() => {
    musicStarted = true;
    musicBtn.classList.add('playing');
    musicBtn.classList.remove('muted');
    dismissPrompt();
  }).catch(() => {});
}

function dismissPrompt() {
  musicPrompt.classList.add('hidden');
  setTimeout(() => { musicPrompt.style.display = 'none'; }, 600);
}

function toggleMusic() {
  if (!musicStarted) { startMusic(); return; }
  if (bgMusic.paused) {
    bgMusic.play();
    musicBtn.classList.add('playing');
    musicBtn.classList.remove('muted');
  } else {
    bgMusic.pause();
    musicBtn.classList.remove('playing');
    musicBtn.classList.add('muted');
  }
}

musicPrompt.addEventListener('click', startMusic);
musicBtn.addEventListener('click', toggleMusic);
