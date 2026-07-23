// ══ SCENE_DEBATE.JS — Three.js 13-agent orbital scene ══

const SceneDebate = (() => {
  let renderer, scene, camera, animFrameId;
  let agentMeshes = {};
  let particles = [];
  let mouseX = 0, mouseY = 0;

  // ── Agent definitions ──────────────────────────────────────
  const AGENTS = [
    // Ring 1 — Center
    { id: 'orchestrator',    label: 'Orchestrator',    color: 0xffffff, ring: 0, angle: 0 },
    // Ring 2 — Inner
    { id: 'debater_a',       label: 'Debater A',       color: 0x4fc3f7, ring: 1, angle: 0 },
    { id: 'debater_b',       label: 'Debater B',       color: 0xff6b9d, ring: 1, angle: Math.PI },
    // Ring 3 — Mid
    { id: 'judge',           label: 'Judge',           color: 0xffd700, ring: 2, angle: 0 },
    { id: 'bias_detector',   label: 'Bias Detector',   color: 0xff9a3c, ring: 2, angle: Math.PI * 2/3 },
    { id: 'devils_advocate', label: "Devil's Advocate", color: 0xcc44ff, ring: 2, angle: Math.PI * 4/3 },
    // Ring 4 — Outer
    { id: 'critic',          label: 'Critic',          color: 0xff4466, ring: 3, angle: 0 },
    { id: 'fact_checker',    label: 'Fact Checker',    color: 0x44ddff, ring: 3, angle: Math.PI * 2/6 },
    { id: 'memory_agent',    label: 'Memory',          color: 0x44ff88, ring: 3, angle: Math.PI * 4/6 },
    { id: 'summariser',      label: 'Summariser',      color: 0x88aaff, ring: 3, angle: Math.PI * 6/6 },
    { id: 'topic_decomposer',label: 'Decomposer',      color: 0xffaa44, ring: 3, angle: Math.PI * 8/6 },
    { id: 'audience_agent',  label: 'Audience',        color: 0xff88cc, ring: 3, angle: Math.PI * 10/6 },
    { id: 'meta_evaluator',  label: 'Meta Evaluator',  color: 0xaaffee, ring: 3, angle: Math.PI * 12/6 },
  ];

  const RING_RADII = [0, 80, 160, 260];
  const ORBIT_SPEEDS = [0, 0.0003, 0.0002, 0.00015];

  function init() {
    const canvas = document.getElementById('canvas-debate');
    if (!canvas) return;

    // ── Renderer ──────────────────────────────────────────────
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000008, 1);

    // ── Scene + Camera ────────────────────────────────────────
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 2000);
    camera.position.set(0, 80, 420);
    camera.lookAt(0, 0, 0);

    scene.fog = new THREE.FogExp2(0x000008, 0.0012);

    // ── Stars ─────────────────────────────────────────────────
    _buildStars();

    // ── Orbit rings ───────────────────────────────────────────
    _buildOrbitRings();

    // ── Agent orbs ────────────────────────────────────────────
    AGENTS.forEach(agent => {
      const radius = agent.id === 'orchestrator' ? 10 : 7;
      const geo = new THREE.SphereGeometry(radius, 16, 16);
      const mat = new THREE.MeshBasicMaterial({ color: agent.color });
      const mesh = new THREE.Mesh(geo, mat);

      // Set initial position
      const r = RING_RADII[agent.ring];
      mesh.position.set(
        r * Math.cos(agent.angle),
        0,
        r * Math.sin(agent.angle),
      );

      mesh.userData = {
        agent,
        baseAngle: agent.angle,
        currentAngle: agent.angle,
        pulseOffset: Math.random() * Math.PI * 2,
        isPulsing: false,
        pulseTimer: 0,
      };

      scene.add(mesh);
      agentMeshes[agent.id] = mesh;
    });

    // ── Events ────────────────────────────────────────────────
    window.addEventListener('resize', _onResize);
    window.addEventListener('mousemove', _onMouseMove);

    _animate();
  }

  function _buildStars() {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(400 * 3);
    for (let i = 0; i < 400; i++) {
      pos[i * 3]     = (Math.random() - 0.5) * 2000;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 2000;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 2000;
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    scene.add(new THREE.Points(geo, new THREE.PointsMaterial({
      color: 0xffffff, size: 1, transparent: true, opacity: 0.4
    })));
  }

  function _buildOrbitRings() {
    [1, 2, 3].forEach(ring => {
      const r = RING_RADII[ring];
      const points = [];
      for (let i = 0; i <= 128; i++) {
        const a = (i / 128) * Math.PI * 2;
        points.push(new THREE.Vector3(r * Math.cos(a), 0, r * Math.sin(a)));
      }
      const geo = new THREE.BufferGeometry().setFromPoints(points);
      const mat = new THREE.LineBasicMaterial({
        color: 0x6c63ff,
        transparent: true,
        opacity: 0.12,
      });
      scene.add(new THREE.Line(geo, mat));
    });
  }

  function _animate() {
    animFrameId = requestAnimationFrame(_animate);
    const t = Date.now() * 0.001;

    // Orbit agents
    AGENTS.forEach(agent => {
      if (agent.ring === 0) return;
      const mesh = agentMeshes[agent.id];
      if (!mesh) return;

      mesh.userData.currentAngle += ORBIT_SPEEDS[agent.ring];
      const r = RING_RADII[agent.ring];
      const a = mesh.userData.currentAngle;
      mesh.position.set(r * Math.cos(a), 0, r * Math.sin(a));

      // Idle pulse
      const idle = 1 + 0.08 * Math.sin(t * 1.2 + mesh.userData.pulseOffset);

      // Active pulse
      if (mesh.userData.isPulsing) {
        mesh.userData.pulseTimer -= 0.016;
        const activePulse = 1 + 0.4 * Math.abs(Math.sin(t * 6));
        mesh.scale.setScalar(activePulse);
        if (mesh.userData.pulseTimer <= 0) {
          mesh.userData.isPulsing = false;
        }
      } else {
        mesh.scale.setScalar(idle);
      }
    });

    // Animate particles
    particles = particles.filter(p => {
      p.progress += p.speed;
      if (p.progress >= 1) {
        scene.remove(p.mesh);
        return false;
      }
      p.mesh.position.lerpVectors(p.from, p.to, p.progress);
      p.mesh.material.opacity = Math.sin(p.progress * Math.PI);
      return true;
    });

    // Camera
    camera.position.x += (mouseX * 60 - camera.position.x) * 0.02;
    camera.position.y += (-mouseY * 40 + 80 - camera.position.y) * 0.02;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
  }

  // ── Pulse an agent orb ─────────────────────────────────────
  function pulseAgent(agentId) {
    const mesh = agentMeshes[agentId];
    if (!mesh) return;
    mesh.userData.isPulsing = true;
    mesh.userData.pulseTimer = 2.0;
  }

  // ── Fire a particle arc between two agents ─────────────────
  function fireParticle(fromId, toId) {
    const fromMesh = agentMeshes[fromId];
    const toMesh   = agentMeshes[toId];
    if (!fromMesh || !toMesh) return;

    const geo = new THREE.SphereGeometry(2, 6, 6);
    const mat = new THREE.MeshBasicMaterial({
      color: fromMesh.material.color,
      transparent: true,
      opacity: 1,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(fromMesh.position);
    scene.add(mesh);

    particles.push({
      mesh,
      from: fromMesh.position.clone(),
      to: toMesh.position.clone(),
      progress: 0,
      speed: 0.015,
    });
  }

  // ── Debate complete animation ──────────────────────────────
  function onDebateComplete() {
    // Slow down all orbit speeds
    ORBIT_SPEEDS[1] *= 0.1;
    ORBIT_SPEEDS[2] *= 0.1;
    ORBIT_SPEEDS[3] *= 0.1;

    // Pulse orchestrator
    pulseAgent('orchestrator');
  }

  function _onResize() {
    if (!renderer) return;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  function _onMouseMove(e) {
    mouseX = (e.clientX / window.innerWidth) - 0.5;
    mouseY = (e.clientY / window.innerHeight) - 0.5;
  }

  function destroy() {
    if (animFrameId) cancelAnimationFrame(animFrameId);
    window.removeEventListener('resize', _onResize);
    window.removeEventListener('mousemove', _onMouseMove);
    if (renderer) renderer.dispose();
    agentMeshes = {};
    particles = [];
  }

  return { init, destroy, pulseAgent, fireParticle, onDebateComplete };
})();