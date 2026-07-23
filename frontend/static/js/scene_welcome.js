// ══ WELCOME SCENE — Three.js Neural Network ══

const WelcomeScene = (() => {
  let renderer, scene, camera, animFrameId;
  let nodes = [], edges = [];
  let mouseX = 0, mouseY = 0;

  const NODE_COUNT = 80;
  const EDGE_DISTANCE = 120;
  const COLORS = [0x6c63ff, 0x4fc3f7, 0xff6b9d, 0xffd700, 0x69ff9a];

  function init() {
    const canvas = document.getElementById('canvas-welcome');
    if (!canvas) return;

    // ── Renderer ──────────────────────────────────────────────
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000008, 1);

    // ── Scene + Camera ────────────────────────────────────────
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
    camera.position.z = 400;

    // ── Fog ───────────────────────────────────────────────────
    scene.fog = new THREE.FogExp2(0x000008, 0.0018);

    // ── Nodes ─────────────────────────────────────────────────
    for (let i = 0; i < NODE_COUNT; i++) {
      const color = COLORS[Math.floor(Math.random() * COLORS.length)];
      const size = Math.random() * 3 + 1.5;

      const geo = new THREE.SphereGeometry(size, 8, 8);
      const mat = new THREE.MeshBasicMaterial({ color });
      const mesh = new THREE.Mesh(geo, mat);

      mesh.position.set(
        (Math.random() - 0.5) * 700,
        (Math.random() - 0.5) * 500,
        (Math.random() - 0.5) * 400,
      );

      // Velocity for floating animation
      mesh.userData.velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 0.08,
        (Math.random() - 0.5) * 0.08,
        (Math.random() - 0.5) * 0.04,
      );
      mesh.userData.color = color;
      mesh.userData.pulseOffset = Math.random() * Math.PI * 2;

      scene.add(mesh);
      nodes.push(mesh);
    }

    // ── Edges (lines between nearby nodes) ────────────────────
    _buildEdges();

    // ── Stars (background particles) ──────────────────────────
    _buildStars();

    // ── Events ────────────────────────────────────────────────
    window.addEventListener('resize', _onResize);
    window.addEventListener('mousemove', _onMouseMove);

    _animate();
  }

  function _buildEdges() {
    // Remove old edges
    edges.forEach(e => scene.remove(e));
    edges = [];

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dist = nodes[i].position.distanceTo(nodes[j].position);
        if (dist < EDGE_DISTANCE) {
          const opacity = 1 - dist / EDGE_DISTANCE;
          const geo = new THREE.BufferGeometry().setFromPoints([
            nodes[i].position,
            nodes[j].position,
          ]);
          const mat = new THREE.LineBasicMaterial({
            color: 0x6c63ff,
            transparent: true,
            opacity: opacity * 0.25,
          });
          const line = new THREE.Line(geo, mat);
          scene.add(line);
          edges.push(line);
        }
      }
    }
  }

  function _buildStars() {
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(300 * 3);
    for (let i = 0; i < 300; i++) {
      positions[i * 3]     = (Math.random() - 0.5) * 2000;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 2000;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 2000;
    }
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 1.2,
      transparent: true,
      opacity: 0.5,
    });
    scene.add(new THREE.Points(geo, mat));
  }

  function _animate() {
    animFrameId = requestAnimationFrame(_animate);
    const t = Date.now() * 0.001;

    // Move nodes
    nodes.forEach((node, i) => {
      node.position.add(node.userData.velocity);

      // Bounce off bounds
      ['x', 'y', 'z'].forEach(axis => {
        const limit = axis === 'z' ? 200 : axis === 'y' ? 250 : 350;
        if (Math.abs(node.position[axis]) > limit) {
          node.userData.velocity[axis] *= -1;
        }
      });

      // Pulse size
      const pulse = 1 + 0.15 * Math.sin(t * 1.5 + node.userData.pulseOffset);
      node.scale.setScalar(pulse);
    });

    // Rebuild edges every 60 frames (performance)
    if (Math.round(t * 60) % 60 === 0) {
      _buildEdges();
    }

    // Subtle camera drift following mouse
    camera.position.x += (mouseX * 30 - camera.position.x) * 0.02;
    camera.position.y += (-mouseY * 20 - camera.position.y) * 0.02;
    camera.lookAt(scene.position);

    renderer.render(scene, camera);
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
  }

  return { init, destroy };
})();