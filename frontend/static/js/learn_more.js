const LearnMore = (() => {
  const TOTAL = 5;
  let current = 0;
  let particleAnim = null;
  let particles = [];

  // ── Particle system ──────────────────────────────────────
  function initParticles() {
    const canvas = document.getElementById('lm-canvas');
    const ctx = canvas.getContext('2d');

    function resize() {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    particles = Array.from({ length: 80 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 2.5 + 0.5,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      opacity: Math.random() * 0.5 + 0.1,
      hue: Math.random() < 0.6 ? 252 : 200,
    }));

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(124,111,224,${0.08 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${p.hue}, 70%, 70%, ${p.opacity})`;
        ctx.fill();
      });

      particleAnim = requestAnimationFrame(draw);
    }
    draw();
  }

  function stopParticles() {
    if (particleAnim) cancelAnimationFrame(particleAnim);
  }

  // ── Scene navigation ─────────────────────────────────────
  function goTo(index) {
    const scenes = document.querySelectorAll('.lm-scene');
    const dots = document.querySelectorAll('.lm-dot');

    const prev = scenes[current];
    prev.classList.add('lm-leaving');
    setTimeout(() => {
      prev.classList.remove('lm-active', 'lm-leaving');
    }, 350);

    current = index;
    dots.forEach((d, i) => d.classList.toggle('active', i === current));

    setTimeout(() => {
      scenes[current].classList.add('lm-active');
    }, 200);

    document.getElementById('lm-prev').disabled = current === 0;
    document.getElementById('lm-next').disabled = current === TOTAL - 1;
  }

  // ── Open / Close ─────────────────────────────────────────
  function open() {
    const overlay = document.getElementById('overlay-learn-more');
    overlay.classList.add('lm-visible');
    document.body.style.overflow = 'hidden';

    document.querySelectorAll('.lm-scene').forEach((s, i) => {
      s.classList.toggle('lm-active', i === 0);
    });
    current = 0;
    document.querySelectorAll('.lm-dot').forEach((d, i) => d.classList.toggle('active', i === 0));
    document.getElementById('lm-prev').disabled = true;
    document.getElementById('lm-next').disabled = false;

    initParticles();
  }

  function close() {
    const overlay = document.getElementById('overlay-learn-more');
    overlay.classList.remove('lm-visible');
    document.body.style.overflow = '';
    stopParticles();
  }

  // ── Init ──────────────────────────────────────────────────
  function init() {
    document.getElementById('lm-close-btn').addEventListener('click', close);

    document.getElementById('lm-next').addEventListener('click', () => {
      if (current < TOTAL - 1) goTo(current + 1);
    });
    document.getElementById('lm-prev').addEventListener('click', () => {
      if (current > 0) goTo(current - 1);
    });

    document.querySelectorAll('.lm-dot').forEach(dot => {
      dot.addEventListener('click', () => goTo(parseInt(dot.dataset.dot)));
    });

    document.getElementById('lm-cta-btn').addEventListener('click', () => {
      close();
      App.navigateTo('auth');
      UIAuth.init();
    });

    document.getElementById('overlay-learn-more').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) close();
    });

    document.addEventListener('keydown', (e) => {
      const overlay = document.getElementById('overlay-learn-more');
      if (!overlay.classList.contains('lm-visible')) return;
      if (e.key === 'ArrowRight' && current < TOTAL - 1) goTo(current + 1);
      if (e.key === 'ArrowLeft' && current > 0) goTo(current - 1);
      if (e.key === 'Escape') close();
    });
  }

  return { init, open, close };
})();