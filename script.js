/* =============================================
   NullSec — Landing Page Scripts
   ============================================= */

// Matrix Rain Effect (Katakana)
const canvas = document.getElementById('matrix-canvas');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

const chars = '01アカサタナハミレケXYZ#$%^&*';
const fontSize = 16;
let columns = Math.floor(canvas.width / fontSize);
let drops = Array(columns).fill(1);

function drawMatrix() {
    ctx.fillStyle = 'rgba(2, 4, 6, 0.12)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#00ffa3';
    ctx.font = `${fontSize}px monospace`;

    for (let i = 0; i < drops.length; i++) {
        const char = chars[Math.floor(Math.random() * chars.length)];
        ctx.fillText(char, i * fontSize, drops[i] * fontSize);

        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
            drops[i] = 0;
        }
        drops[i]++;
    }
}

setInterval(drawMatrix, 45);

// Card Hover Glow Effect
document.querySelectorAll('.command-card, .feature-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        card.style.setProperty('--mouse-x', `${x}px`);
        card.style.setProperty('--mouse-y', `${y}px`);
    });
});

// Typing Effect
const typingTexts = [
    'nullbot --osint check email@target.com',
    'echo "Encrypting communications..."',
    'shield encrypt --method AES-256',
    'dns lookup --type TXT target.local',
    './exploit.py --payload reverse_shell',
    'ssl audit --domain https://nullsec.local',
    'whois lookup --privacy on',
    'nmap -T4 -A -v nullsec.local'
];

let textIndex = 0;
let charIndex = 0;
let isDeleting = false;
const typingElement = document.getElementById('typing-text');

function typeEffect() {
    const currentText = typingTexts[textIndex];

    if (isDeleting) {
        typingElement.textContent = currentText.substring(0, charIndex - 1);
        charIndex--;
    } else {
        typingElement.textContent = currentText.substring(0, charIndex + 1);
        charIndex++;
    }

    let delay = isDeleting ? 40 : 80;

    if (!isDeleting && charIndex === currentText.length) {
        delay = 2500;
        isDeleting = true;
    } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        textIndex = (textIndex + 1) % typingTexts.length;
        delay = 800;
    }

    setTimeout(typeEffect, delay);
}

if (typingElement) typeEffect();

// Counter Animation
function animateCounters() {
    const counters = document.querySelectorAll('.stat-number');
    counters.forEach(counter => {
        const target = parseInt(counter.dataset.target);
        if (isNaN(target)) return;

        const duration = 2500;
        const increment = target / (duration / 16);
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = target;
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current);
            }
        }, 16);
    });
}

// Bot Command Filtering
const filterBtns = document.querySelectorAll('.filter-btn');
const commandCards = document.querySelectorAll('.command-card');

filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const filter = btn.dataset.filter;

        // Update active button
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Filter cards
        commandCards.forEach(card => {
            const category = card.dataset.category;
            if (filter === 'all' || category === filter) {
                card.style.display = 'block';
                setTimeout(() => card.style.opacity = '1', 10);
                setTimeout(() => card.style.transform = 'translateY(0) scale(1)', 10);
            } else {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px) scale(0.95)';
                setTimeout(() => card.style.display = 'none', 300);
            }
        });
    });
});

// Intersection Observer
const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            if (entry.target.classList.contains('hero-stats')) {
                animateCounters();
            }
        }
    });
}, observerOptions);

document.querySelectorAll('section, .feature-card, .command-card, .channel-category, .hero-stats').forEach(el => {
    observer.observe(el);
});

// Global Styles for reveals
const revealStyles = document.createElement('style');
revealStyles.innerHTML = `
    section, .feature-card, .command-card, .channel-category {
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
    }
    .visible {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
`;
document.head.appendChild(revealStyles);

// Navbar Scroll Effect
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Parallax Terminal
window.addEventListener('mousemove', (e) => {
    const terminal = document.querySelector('.terminal-window');
    if (!terminal) return;

    const xAxis = (window.innerWidth / 2 - e.pageX) / 40;
    const yAxis = (window.innerHeight / 2 - e.pageY) / 40;

    terminal.style.transform = `rotateY(${xAxis - 15}deg) rotateX(${yAxis + 5}deg)`;
});

console.log('%c🔒 NULLSEC COLLECTIVE BOOTED', 'color: #00ffa3; font-size: 28px; font-weight: 900; font-family: monospace;');
console.log('%cAccess granted. Operator active.', 'color: #00e0ff; font-size: 16px; font-family: monospace;');
