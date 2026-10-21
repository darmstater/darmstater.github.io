/* ===================================================
   ALBERT PORTFOLIO — SCRIPT.JS
   =================================================== */

// ===== NAVBAR SCROLL EFFECT =====
const navbar    = document.getElementById('navbar');
const navLinks  = document.getElementById('nav-links');
const hamburger = document.getElementById('hamburger');
const navClose  = document.getElementById('nav-close');
const navLinkItems = document.querySelectorAll('.nav-link');

window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
    updateActiveLink();
    toggleScrollTop();
});

// ===== MOBILE MENU =====
hamburger.addEventListener('click', () => navLinks.classList.add('open'));
navClose.addEventListener('click',  () => navLinks.classList.remove('open'));

navLinkItems.forEach(link => {
    link.addEventListener('click', () => navLinks.classList.remove('open'));
});

// ===== ACTIVE NAV LINK ON SCROLL =====
function updateActiveLink() {
    const sections = document.querySelectorAll('section[id]');
    sections.forEach(section => {
        const top    = section.offsetTop - 120;
        const bottom = top + section.offsetHeight;
        const id     = section.getAttribute('id');
        const link   = document.querySelector(`.nav-link[href="#${id}"]`);
        if (link && window.scrollY >= top && window.scrollY < bottom) {
            navLinkItems.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        }
    });
}

// ===== TYPING EFFECT =====
const roles = [
    'Full-stack Developer',
    '.NET Developer',
    'ASP.NET MVC & C#',
    'SQL Server Engineer',
    'Application Support Developer',
    'Problem Solver',
];

let roleIndex  = 0;
let charIndex  = 0;
let isDeleting = false;
const typingEl = document.getElementById('typing-text');

function type() {
    const current = roles[roleIndex];

    if (isDeleting) {
        typingEl.textContent = current.substring(0, charIndex - 1);
        charIndex--;
    } else {
        typingEl.textContent = current.substring(0, charIndex + 1);
        charIndex++;
    }

    let delay = isDeleting ? 55 : 95;

    if (!isDeleting && charIndex === current.length) {
        delay = 2200;
        isDeleting = true;
    } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        roleIndex = (roleIndex + 1) % roles.length;
        delay = 400;
    }

    setTimeout(type, delay);
}

type();

// ===== TABS (ABOUT SECTION) =====
function openTab(e, tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active-tab'));
    document.querySelectorAll('.tab-content').forEach(pane => pane.classList.remove('active'));
    e.currentTarget.classList.add('active-tab');
    const pane = document.getElementById(tabName);
    pane.classList.add('active');
    pane.scrollTop = 0;
    updateTabFade(pane);
}

// Show a bottom fade while the tab pane still has content below the fold
function updateTabFade(pane) {
    const more = pane.scrollHeight - pane.clientHeight - pane.scrollTop > 8;
    pane.classList.toggle('has-more', more);
}

document.querySelectorAll('.tab-content').forEach(pane => {
    pane.addEventListener('scroll', () => updateTabFade(pane));
});
window.addEventListener('load',   () => document.querySelectorAll('.tab-content.active').forEach(updateTabFade));
window.addEventListener('resize', () => document.querySelectorAll('.tab-content.active').forEach(updateTabFade));

// ===== SCROLL REVEAL =====
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            revealObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

// ===== SCROLL TO TOP =====
const scrollTopBtn = document.getElementById('scroll-top');

function toggleScrollTop() {
    scrollTopBtn.classList.toggle('visible', window.scrollY > 450);
}

scrollTopBtn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});
