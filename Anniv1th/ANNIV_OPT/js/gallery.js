// ============================================================
//  GALLERY — MASONRY GRID
// ============================================================
function initGallery() {
  const grid = document.getElementById('galGrid');
  grid.innerHTML = '';

  let lastMonth = '';

  CFG.gallery.forEach((item) => {
    // Month separator label
    if (item.month && item.month !== lastMonth) {
      lastMonth = item.month;
      const lbl = document.createElement('div');
      lbl.className = 'gal-month-label';
      lbl.textContent = item.month;
      grid.appendChild(lbl);
    }

    const d = document.createElement('div');
    d.className = 'gal-item' + (item.size ? ' ' + item.size : '');

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
        img.loading = 'lazy';
        d.appendChild(img);
      }
    } else {
      const ph = document.createElement('div');
      ph.className = 'gal-ph';
      ph.innerHTML = `${item.emoji || '📸'}<span>${item.cap}</span>`;
      d.appendChild(ph);
    }

    const ov = document.createElement('div');
    ov.className = 'gal-ov';
    ov.innerHTML = `<span class="gal-cap">${item.cap}</span>`;
    d.appendChild(ov);

    d.addEventListener('click', () => openLb(item));
    grid.appendChild(d);
  });
}

function openLb(item) {
  const lb    = document.getElementById('lightbox');
  const inner = document.getElementById('lbInner');
  document.getElementById('lbCap').textContent = item.cap;
  if (item.src) {
    if (item.type === 'video') {
      inner.innerHTML = `<video src="${item.src}" controls autoplay muted playsinline style="max-width:88vw;max-height:72vh;border-radius:12px;"></video>`;
    } else {
      inner.innerHTML = `<img src="${item.src}" alt="${item.cap}">`;
    }
  } else {
    inner.innerHTML = `<div class="lb-ph">${item.emoji || '📸'}<p>Tambah foto/video di js/config.js</p></div>`;
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
