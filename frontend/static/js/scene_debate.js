// ══ SCENE_DEBATE.JS — Three.js 13-agent orbital scene (rich 3D v2) ══

const SceneDebate = (() => {
  let renderer, scene, camera, animFrameId;
  let agentMeshes = {}, agentGlows = {}, agentLabels = {};
  let particles = [];
  let beamLines = {};
  let time = 0;
  let mouseX = 0, mouseY = 0;

  // ── Spherical camera state (drag + scroll) ─────────────────
  let sph = { theta: 0.3, phi: 1.05, r: 520 };
  let drag = false, prev = { x: 0, y: 0 };

  // ── Agent definitions (13 agents, 3D Y offsets for depth) ──
  const AGENTS = [
    // Ring 0 — Center
    { id: 'orchestrator',    label: 'Orchestrator',    col: 0x63a0ff, em: 0x0a1840, r: 13, oR: 0,   oY: 0,    oS: 0,     ph: 0 },
    // Ring 1 — Inner
    { id: 'debater_a',       label: 'Debater A',       col: 0xff6b6b, em: 0x601010, r: 9,  oR: 80,  oY: 10,   oS: 0.32,  ph: 0 },
    { id: 'debater_b',       label: 'Debater B',       col: 0x6bffb8, em: 0x104030, r: 9,  oR: 80,  oY: -10,  oS: 0.32,  ph: Math.PI },
    // Ring 2 — Mid
    { id: 'judge',           label: 'Judge',           col: 0xffd76b, em: 0x604010, r: 10, oR: 140, oY: 0,    oS: -0.22, ph: 1.57 },
    { id: 'bias_detector',   label: 'Bias Detector',   col: 0xff9a3c, em: 0x602800, r: 8,  oR: 140, oY: 14,   oS: -0.22, ph: 2.09 + 0.1 },
    { id: 'devils_advocate', label: "Devil's Adv.",    col: 0xcc44ff, em: 0x400060, r: 8,  oR: 140, oY: -14,  oS: -0.22, ph: 4.19 },
    // Ring 3 — Outer
    { id: 'critic',          label: 'Critic',          col: 0xff4466, em: 0x601020, r: 7,  oR: 220, oY: 20,   oS: 0.15,  ph: 0 },
    { id: 'fact_checker',    label: 'Fact Checker',    col: 0x44ddff, em: 0x103050, r: 7,  oR: 220, oY: -8,   oS: 0.15,  ph: 1.05 },
    { id: 'memory_agent',    label: 'Memory',          col: 0x44ff88, em: 0x104020, r: 7,  oR: 220, oY: 12,   oS: 0.15,  ph: 2.09 },
    { id: 'summariser',      label: 'Summariser',      col: 0x88aaff, em: 0x201060, r: 6,  oR: 220, oY: -20,  oS: 0.15,  ph: 3.14 },
    { id: 'topic_decomposer',label: 'Decomposer',      col: 0xffaa44, em: 0x603010, r: 6,  oR: 220, oY: 5,    oS: 0.15,  ph: 4.19 },
    { id: 'audience_agent',  label: 'Audience',        col: 0xff88cc, em: 0x601040, r: 6,  oR: 220, oY: -15,  oS: 0.15,  ph: 5.24 },
    { id: 'meta_evaluator',  label: 'Meta Eval.',      col: 0xaaffee, em: 0x106040, r: 6,  oR: 260, oY: 8,    oS: 0.09,  ph: 0.52 },
  ];

  // Beam connections to draw static lines
  const BEAM_PAIRS = [
    ['orchestrator','debater_a'],['orchestrator','debater_b'],
    ['orchestrator','judge'],['debater_a','judge'],['debater_b','judge'],
    ['judge','critic'],['critic','orchestrator'],['memory_agent','orchestrator'],
    ['fact_checker','debater_a'],['fact_checker','debater_b'],['summariser','orchestrator'],
    ['bias_detector','judge'],['devils_advocate','judge'],
    ['topic_decomposer','orchestrator'],['audience_agent','orchestrator'],
    ['meta_evaluator','judge'],
  ];

  // ── Initialise ─────────────────────────────────────────────
  function init() {
    const canvas = document.getElementById('canvas-debate');
    if (!canvas) return;

    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(canvas.clientWidth || window.innerWidth, canvas.clientHeight || window.innerHeight);
    renderer.setClearColor(0x020408, 1);

    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera(52, (canvas.clientWidth || window.innerWidth) / (canvas.clientHeight || window.innerHeight), 0.1, 4000);
    camera.position.set(0, 100, 420);
    camera.lookAt(0, 0, 0);

    // ── Lighting ──
    scene.add(new THREE.AmbientLight(0xffffff, 0.2));
    const pl1 = new THREE.PointLight(0x63a0ff, 4, 800); scene.add(pl1);
    const pl2 = new THREE.PointLight(0xff6b6b, 2.5, 500); pl2.position.set(-200, -80, 120); scene.add(pl2);
    const pl3 = new THREE.PointLight(0x6bffb8, 2.5, 500); pl3.position.set(200, -80, -120); scene.add(pl3);
    const pl4 = new THREE.PointLight(0xc86bff, 1.8, 400); pl4.position.set(0, 200, 0); scene.add(pl4);

    // Store animated lights for later
    scene.userData.pl1 = pl1;
    scene.userData.pl4 = pl4;

    // ── Stars ──
    _buildStars(2500, 3500, 1.5, 0.55);
    _buildStars(600,  1800, 3.0, 0.30);
    _buildStars(100,   800, 6.0, 0.15);

    // ── Grid floor ──
    const gridGeo = new THREE.PlaneGeometry(900, 900, 30, 30);
    const gridMat = new THREE.MeshBasicMaterial({ color: 0x112244, wireframe: true, transparent: true, opacity: 0.10 });
    const gridMesh = new THREE.Mesh(gridGeo, gridMat);
    gridMesh.rotation.x = -Math.PI / 2;
    gridMesh.position.y = -120;
    scene.add(gridMesh);
    scene.userData.gridMesh = gridMesh;

    // ── Central core orb ──
    const coreGeo = new THREE.SphereGeometry(5, 32, 32);
    const coreMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.6 });
    const core = new THREE.Mesh(coreGeo, coreMat);
    scene.add(core);
    scene.userData.core = core;

    // Core shell rings
    [12, 22, 34].forEach((r, i) => {
      const g = new THREE.SphereGeometry(r, 32, 32);
      const m = new THREE.MeshBasicMaterial({ color: 0x63a0ff, wireframe: true, transparent: true, opacity: 0.04 - i * 0.01 });
      scene.add(new THREE.Mesh(g, m));
    });

    // ── Orbit rings ──
    _buildOrbitRings();

    // ── Agent orbs + glows + labels ──
    AGENTS.forEach(a => {
      // Main icosahedron
      const geo = new THREE.IcosahedronGeometry(a.r, 3);
      const mat = new THREE.MeshPhongMaterial({
        color: a.col,
        emissive: a.em,
        shininess: 140,
        transparent: true,
        opacity: 0.93,
      });
      const mesh = new THREE.Mesh(geo, mat);
      const r = a.oR;
      mesh.position.set(r * Math.cos(a.ph), a.oY, r * Math.sin(a.ph));
      mesh.userData = { agent: a, isPulsing: false, pulseTimer: 0 };
      scene.add(mesh);
      agentMeshes[a.id] = mesh;

      // Glow shell
      const gg = new THREE.SphereGeometry(a.r * 1.85, 16, 16);
      const gm = new THREE.MeshBasicMaterial({ color: a.col, transparent: true, opacity: 0.06, side: THREE.BackSide });
      const glow = new THREE.Mesh(gg, gm);
      scene.add(glow);
      agentGlows[a.id] = glow;

      // Floating canvas label
      const cv = document.createElement('canvas');
      cv.width = 256; cv.height = 56;
      const ctx2 = cv.getContext('2d');
      ctx2.font = '500 22px system-ui';
      ctx2.fillStyle = '#' + a.col.toString(16).padStart(6, '0');
      ctx2.textAlign = 'center';
      ctx2.fillText(a.label, 128, 38);
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({
        map: new THREE.CanvasTexture(cv),
        transparent: true,
        opacity: 0.80,
      }));
      sp.scale.set(55, 14, 1);
      scene.add(sp);
      agentLabels[a.id] = sp;
    });

    // ── Beams ──
    _buildBeams();

    // ── Input ──
    const el = renderer.domElement;
    el.addEventListener('mousedown', e => { drag = true; prev = { x: e.clientX, y: e.clientY }; });
    el.addEventListener('mouseup', () => drag = false);
    el.addEventListener('mousemove', e => {
      if (drag) {
        sph.theta -= (e.clientX - prev.x) * 0.005;
        sph.phi = Math.max(0.15, Math.min(Math.PI - 0.15, sph.phi + (e.clientY - prev.y) * 0.005));
        prev = { x: e.clientX, y: e.clientY };
      }
      mouseX = (e.clientX / window.innerWidth) - 0.5;
      mouseY = (e.clientY / window.innerHeight) - 0.5;
    });
    el.addEventListener('wheel', e => { sph.r = Math.max(150, Math.min(700, sph.r + e.deltaY * 0.3)); });
    el.addEventListener('touchstart', e => { if (e.touches.length === 1) { drag = true; prev = { x: e.touches[0].clientX, y: e.touches[0].clientY }; } });
    el.addEventListener('touchend', () => drag = false);
    el.addEventListener('touchmove', e => {
      if (!drag || e.touches.length !== 1) return;
      sph.theta -= (e.touches[0].clientX - prev.x) * 0.005;
      sph.phi = Math.max(0.15, Math.min(Math.PI - 0.15, sph.phi + (e.touches[0].clientY - prev.y) * 0.005));
      prev = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    });

    window.addEventListener('resize', _onResize);
    _animate();
  }

  // ── Stars helper ───────────────────────────────────────────
  function _buildStars(n, spread, size, opacity) {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(n * 3);
    for (let i = 0; i < n * 3; i++) pos[i] = (Math.random() - 0.5) * spread;
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    scene.add(new THREE.Points(geo, new THREE.PointsMaterial({ color: 0xffffff, size, transparent: true, opacity })));
  }

  // ── Orbit rings (tilted slightly for 3D feel) ─────────────
  function _buildOrbitRings() {
    const rings = [
      { r: 80,  y: 0,   col: 0xff6b6b, tilt: 0.06 },
      { r: 140, y: 0,   col: 0xffd76b, tilt: -0.05 },
      { r: 220, y: 0,   col: 0x44ddff, tilt: 0.08 },
      { r: 260, y: 0,   col: 0xaaffee, tilt: -0.04 },
    ];
    rings.forEach(({ r, y, col, tilt }) => {
      const pts = [];
      for (let i = 0; i <= 128; i++) {
        const a = (i / 128) * Math.PI * 2;
        pts.push(new THREE.Vector3(r * Math.cos(a), tilt * r * Math.sin(a), r * Math.sin(a)));
      }
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({ color: col, transparent: true, opacity: 0.10 });
      const line = new THREE.Line(geo, mat);
      line.position.y = y;
      scene.add(line);
    });
  }

  // ── Beam lines ─────────────────────────────────────────────
  function _buildBeams() {
    BEAM_PAIRS.forEach(([a, b]) => {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(6), 3));
      const mat = new THREE.LineBasicMaterial({ color: 0x334466, transparent: true, opacity: 0.15 });
      const line = new THREE.Line(geo, mat);
      scene.add(line);
      beamLines[a + '_' + b] = line;
    });
  }

  function _updateBeams() {
    Object.entries(beamLines).forEach(([key, line]) => {
      const [a, b] = key.split('_');
      const pa = agentMeshes[a]?.position;
      const pb = agentMeshes[b]?.position;
      if (!pa || !pb) return;
      const pos = line.geometry.attributes.position.array;
      pos[0] = pa.x; pos[1] = pa.y; pos[2] = pa.z;
      pos[3] = pb.x; pos[4] = pb.y; pos[5] = pb.z;
      line.geometry.attributes.position.needsUpdate = true;
    });
  }

  // ── Main loop ──────────────────────────────────────────────
  function _animate() {
    animFrameId = requestAnimationFrame(_animate);
    time += 0.007;

    // Move agents along orbits
    AGENTS.forEach(a => {
      const mesh = agentMeshes[a.id];
      const glow = agentGlows[a.id];
      const label = agentLabels[a.id];
      if (!mesh) return;

      if (a.oR > 0) {
        const ang = a.ph + time * a.oS;
        mesh.position.set(
          Math.cos(ang) * a.oR,
          a.oY + Math.sin(time * 0.6 + a.ph) * 5,
          Math.sin(ang) * a.oR
        );
      } else {
        mesh.position.set(0, Math.sin(time * 0.5) * 2.5, 0);
      }

      mesh.rotation.x = time * 0.35 + a.ph;
      mesh.rotation.y = time * 0.55 + a.ph * 0.7;

      // Active pulse override
      if (mesh.userData.isPulsing) {
        mesh.userData.pulseTimer -= 0.016;
        const activePulse = 1 + 0.5 * Math.abs(Math.sin(time * 8));
        mesh.scale.setScalar(activePulse);
        if (mesh.userData.pulseTimer <= 0) {
          mesh.userData.isPulsing = false;
          mesh.scale.setScalar(1);
        }
      }

      if (glow) {
        glow.position.copy(mesh.position);
        glow.material.opacity = 0.04 + Math.sin(time * 1.8 + a.ph) * 0.025;
      }
      if (label) {
        label.position.copy(mesh.position);
        label.position.y += a.r + 14;
      }
    });

    // Particles
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.t += p.speed;
      if (p.t >= 1) { scene.remove(p.pts); particles.splice(i, 1); continue; }

      const from = p.from.clone(), to = p.to.clone();
      const mid = from.clone().lerp(to, 0.5).add(new THREE.Vector3(p.offset * 40, 60 + Math.abs(p.offset) * 30, p.offset * 30));
      const pos = p.pts.geometry.attributes.position.array;
      const n = p.n;
      for (let j = 0; j < n; j++) {
        const jt = Math.max(0, Math.min(1, p.t - j * 0.032));
        const a2 = jt < 0.5 ? jt * 2 : 1;
        const b2 = jt < 0.5 ? 0 : (jt - 0.5) * 2;
        const pt = from.clone().lerp(mid, a2).lerp(to, b2);
        pt.x += (Math.random() - 0.5) * 1.0;
        pt.y += (Math.random() - 0.5) * 1.0;
        pt.z += (Math.random() - 0.5) * 1.0;
        pos[j * 3] = pt.x; pos[j * 3 + 1] = pt.y; pos[j * 3 + 2] = pt.z;
      }
      p.pts.geometry.attributes.position.needsUpdate = true;
      p.pts.material.opacity = Math.sin(p.t * Math.PI) * 0.95;
      p.pts.material.size = 2.5 + Math.sin(p.t * Math.PI) * 1.5;
    }

    _updateBeams();

    // Core pulse
    const core = scene.userData.core;
    if (core) {
      core.material.opacity = 0.4 + Math.sin(time * 3) * 0.25;
      core.scale.setScalar(1 + Math.sin(time * 2.5) * 0.12);
    }

    // Light animation
    const pl1 = scene.userData.pl1;
    if (pl1) pl1.position.set(Math.sin(time * 0.4) * 100, 160, Math.cos(time * 0.4) * 100);
    const pl4 = scene.userData.pl4;
    if (pl4) pl4.intensity = 1.5 + Math.sin(time * 2.2) * 0.7;

    // Grid breathe
    const gm = scene.userData.gridMesh;
    if (gm) gm.material.opacity = 0.07 + Math.sin(time * 0.3) * 0.03;

    // Camera orbit (spherical)
    const cx = Math.sin(sph.phi) * Math.cos(sph.theta) * sph.r;
    const cy = Math.cos(sph.phi) * sph.r;
    const cz = Math.sin(sph.phi) * Math.sin(sph.theta) * sph.r;
    camera.position.lerp(new THREE.Vector3(cx, cy, cz), 0.055);
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
  }

  // ── Public: pulse an agent ─────────────────────────────────
  function pulseAgent(agentId) {
    const mesh = agentMeshes[agentId];
    if (!mesh) return;
    mesh.userData.isPulsing = true;
    mesh.userData.pulseTimer = 2.0;
  }

  // ── Public: fire particle arc between two agents ───────────
  function fireParticle(fromId, toId) {
    const fromMesh = agentMeshes[fromId];
    const toMesh = agentMeshes[toId];
    if (!fromMesh || !toMesh) return;

    const n = 22;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));

    const col = AGENTS.find(a => a.id === fromId)?.col || 0xffffff;
    const mat = new THREE.PointsMaterial({ color: col, size: 3, transparent: true, opacity: 1 });
    const pts = new THREE.Points(geo, mat);
    scene.add(pts);

    particles.push({
      pts,
      from: fromMesh.position.clone(),
      to: toMesh.position.clone(),
      t: 0,
      speed: 0.012 + Math.random() * 0.008,
      n,
      offset: (Math.random() - 0.5) * 0.6,
    });
  }

  // ── Public: debate complete ────────────────────────────────
  function onDebateComplete() {
    pulseAgent('orchestrator');
    // Gentle slow-down — multiply orbital speeds in AGENTS
    AGENTS.forEach(a => { a.oS *= 0.15; });
  }

  // ── Resize ────────────────────────────────────────────────
  function _onResize() {
    if (!renderer) return;
    const w = window.innerWidth, h = window.innerHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }

  // ── Destroy ────────────────────────────────────────────────
  function destroy() {
    if (animFrameId) cancelAnimationFrame(animFrameId);
    window.removeEventListener('resize', _onResize);
    if (renderer) renderer.dispose();
    agentMeshes = {}; agentGlows = {}; agentLabels = {};
    particles = []; beamLines = {};
  }

  return { init, destroy, pulseAgent, fireParticle, onDebateComplete };
})();