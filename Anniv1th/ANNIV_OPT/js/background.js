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
