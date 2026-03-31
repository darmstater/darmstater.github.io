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
