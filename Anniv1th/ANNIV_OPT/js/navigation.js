// ============================================================
//  NAVIGASI HALAMAN + PAGINATION
// ============================================================
const PAGES = ['intro', 'timeline', 'puzzle', 'cardgame', 'gallery', 'finale'];
const PAGE_META = {
  intro:    { icon: '✨', label: 'Intro' },
  timeline: { icon: '🗺️', label: 'Perjalanan' },
  puzzle:   { icon: '🧩', label: 'Teka-teki' },
  cardgame: { icon: '🎴', label: 'Mini Game' },
  gallery:  { icon: '📸', label: 'Galeri' },
  finale:   { icon: '💌', label: 'Surprise' },
};

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
    updatePagination();
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
let timelineRead = false;

function initTimeline() {
  timelineRead = false;
  document.querySelectorAll('.tl-item').forEach((el, i) => {
    setTimeout(() => el.classList.add('vis'), i * 220);
  });

  const wrap = document.getElementById('tlWrap');
  if (!wrap) return;

  function onTlScroll() {
    if (timelineRead) return;
    const nearBottom = wrap.scrollTop + wrap.clientHeight >= wrap.scrollHeight - 40;
    if (nearBottom) {
      timelineRead = true;
      updatePagination();
      wrap.removeEventListener('scroll', onTlScroll);
    }
  }
  wrap.addEventListener('scroll', onTlScroll);
}

// ============================================================
//  PAGINATION
// ============================================================
function buildPagination() {
  const dotsContainer = document.getElementById('pagDots');
  const prevBtn       = document.getElementById('pagPrev');
  const nextBtn       = document.getElementById('pagNext');

  dotsContainer.innerHTML = '';

  PAGES.forEach(pageId => {
    const meta = PAGE_META[pageId];
    const dot  = document.createElement('button');
    dot.className    = 'pag-dot';
    dot.dataset.page = pageId;
    dot.dataset.label = meta.icon + ' ' + meta.label;
    dot.setAttribute('aria-label', meta.label);
    dot.addEventListener('click', () => goTo(pageId));
    dotsContainer.appendChild(dot);
  });

  prevBtn.addEventListener('click', pagBack);
  nextBtn.addEventListener('click', pagForward);

  updatePagination();
}

function updatePagination() {
  const pagination = document.getElementById('pagination');
  const label      = document.getElementById('pagLabel');
  const prevBtn    = document.getElementById('pagPrev');
  const nextBtn    = document.getElementById('pagNext');

  // Hide on splash, show on all other pages
  if (cur === 'splash') {
    pagination.classList.add('hidden');
    return;
  }
  pagination.classList.remove('hidden');

  // Update dots
  const dots = document.querySelectorAll('.pag-dot');
  dots.forEach(dot => {
    if (dot.dataset.page === cur) {
      dot.classList.add('active');
    } else {
      dot.classList.remove('active');
    }
  });

  // Update label
  const meta = PAGE_META[cur];
  if (meta && label) {
    label.textContent = meta.icon + ' ' + meta.label;
  }

  // Update arrow disabled state
  const idx = PAGES.indexOf(cur);
  if (prevBtn) prevBtn.disabled = (idx <= 0);
  const isLastPage   = idx >= PAGES.length - 1;
  const timelineLock = (cur === 'timeline' && !timelineRead);
  if (nextBtn) nextBtn.disabled = isLastPage || timelineLock;

  // Kasih hint visual kalau masih terkunci
  if (timelineLock) {
    nextBtn.title = 'Scroll dulu sampai bawah... 👇';
  } else {
    nextBtn.title = '';
  }
}

function pagBack() {
  const idx = PAGES.indexOf(cur);
  if (idx > 0) goTo(PAGES[idx - 1]);
}

function pagForward() {
  const idx = PAGES.indexOf(cur);
  if (idx < PAGES.length - 1) goTo(PAGES[idx + 1]);
}

buildPagination();
