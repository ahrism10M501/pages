// home-graph.js — home page graph: init, random node pulse, pull-to-expand, zoom presets.
// Reads data URLs from current script's dataset:
//   data-graph, data-posts, data-twinkles, data-posts-base
//
// Required globals: cytoscape, fetchGraph, fetchPosts, renderPostList, initGraph

(function () {
  const ds = document.currentScript ? document.currentScript.dataset : {};
  const GRAPH_URL = ds.graph;
  const POSTS_URL = ds.posts;
  const TWINKLES_URL = ds.twinkles;
  const POSTS_BASE = ds.postsBase || '../posts/';

  startPullToExpand();
  startZoomPresets();
  startGraph();

  async function startGraph() {
    const graphData = await fetchGraph(GRAPH_URL);
    const posts = await fetchPosts(POSTS_URL);
    const twinkles = await fetch(TWINKLES_URL)
      .then(r => r.ok ? r.json() : [])
      .catch(() => []);

    const hasGraph = graphData && graphData.nodes.length > 1;
    if (!hasGraph) {
      document.getElementById('graph-container').style.display = 'none';
      document.getElementById('graph-fallback').style.display = '';
      renderPostList(posts, document.getElementById('posts-container'), POSTS_BASE);
      return;
    }

    const cy = initGraph(document.getElementById('graph-container'), graphData, {
      onNodeClick: slug => { window.location.href = POSTS_BASE + slug + '/'; },
      userZoomingEnabled: false,
      twinkles,
    });
    window.__indexCy = cy;
    startPulse(cy);
  }

  function startPulse(cy) {
    const SCALE = 1.7, GROW_MS = 500, HOLD_MS = 13000, SHRINK_MS = 500;
    const INTERVAL_MS = GROW_MS + HOLD_MS;
    const origSizes = {};
    cy.one('layoutstop', () => {
      cy.nodes().forEach(node => {
        origSizes[node.id()] = {
          w: parseFloat(node.style('width')),
          h: parseFloat(node.style('height')),
        };
      });
      pulse();
    });
    setInterval(pulse, INTERVAL_MS);

    function pulse() {
      if (!Object.keys(origSizes).length) return;
      const nodes = cy.nodes().toArray();
      const count = 2 + Math.floor(Math.random() * 2);
      const picks = nodes.slice().sort(() => Math.random() - 0.5).slice(0, Math.min(count, nodes.length));
      picks.forEach(node => {
        const orig = origSizes[node.id()];
        if (!orig) return;
        node.animate(
          { style: { width: orig.w * SCALE, height: orig.h * SCALE } },
          { duration: GROW_MS, easing: 'ease-in-out-quad', complete: () => {
            setTimeout(() => {
              node.animate(
                { style: { width: orig.w, height: orig.h } },
                { duration: SHRINK_MS, easing: 'ease-in-out-quad' }
              );
            }, HOLD_MS);
          }}
        );
      });
    }
  }

  function startPullToExpand() {
    const gc = document.getElementById('graph-container');
    if (!gc) return;
    const SNAP_THRESHOLD = 80;
    const DEFAULT_VH = window.innerWidth <= 640 ? 40 : 45;
    const EXPANDED_VH = 100;
    const EASE = '0.35s cubic-bezier(0.34, 1.56, 0.64, 1)';
    let expanded = false, startY = 0, dragActive = false;
    const isMobile = () => window.innerWidth <= 640;
    const baseH = () => DEFAULT_VH / 100 * window.innerHeight;
    const setHPx = px => { gc.style.transition = 'none'; gc.style.height = px + 'px'; };
    const snapTo = vh => { gc.style.transition = 'height ' + EASE; gc.style.height = vh + 'vh'; };
    const snapExpand = () => { expanded = true; snapTo(EXPANDED_VH); document.getElementById('post-graph').classList.add('expanded'); };
    const snapCollapse = () => { expanded = false; snapTo(DEFAULT_VH); document.getElementById('post-graph').classList.remove('expanded'); };

    const back = document.getElementById('graph-back-btn');
    if (back) back.addEventListener('click', () => { snapCollapse(); window.scrollTo({ top: 0, behavior: 'smooth' }); });

    document.addEventListener('touchstart', e => {
      if (window.scrollY > 2 && !expanded) return;
      startY = e.touches[0].clientY;
      dragActive = true;
    }, { passive: true });

    document.addEventListener('touchmove', e => {
      if (!dragActive) return;
      const delta = e.touches[0].clientY - startY;
      if (delta <= 0 && !expanded) { dragActive = false; return; }
      if (!expanded) setHPx(baseH() + delta * 0.4);
    }, { passive: true });

    document.addEventListener('touchend', e => {
      if (!dragActive) return;
      dragActive = false;
      if (!expanded) {
        if (gc.offsetHeight - baseH() > SNAP_THRESHOLD) snapExpand();
        else snapCollapse();
      } else if (!isMobile()) {
        if (e.changedTouches[0].clientY - startY < -SNAP_THRESHOLD) snapCollapse();
      }
    }, { passive: true });

    document.addEventListener('scroll', () => {
      if (expanded && window.scrollY > 10 && !isMobile()) snapCollapse();
    }, { passive: true });

    let wheelAccum = 0, wheelTimer = null;
    document.addEventListener('wheel', e => {
      if (e.deltaY > 0 && window.scrollY < 2 && expanded) { snapCollapse(); return; }
      if (e.deltaY < 0 && window.scrollY < 2 && !expanded) {
        wheelAccum += Math.abs(e.deltaY);
        setHPx(baseH() + wheelAccum * 0.4);
        if (wheelAccum > SNAP_THRESHOLD) {
          snapExpand();
          wheelAccum = 0;
          clearTimeout(wheelTimer);
          return;
        }
        clearTimeout(wheelTimer);
        wheelTimer = setTimeout(() => { wheelAccum = 0; if (!expanded) snapCollapse(); }, 400);
      }
    }, { passive: true });
  }

  function startZoomPresets() {
    const buttons = document.querySelectorAll('.zoom-preset');
    if (!buttons.length) return;
    let baseZoom = null;
    const center = () => {
      const cy = window.__indexCy;
      if (!cy) return null;
      return { x: cy.container().offsetWidth / 2, y: cy.container().offsetHeight / 2 };
    };
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        const cy = window.__indexCy;
        if (!cy) return;
        if (baseZoom === null) baseZoom = cy.zoom();
        cy.zoom({ level: baseZoom * parseFloat(btn.dataset.zoom), renderedPosition: center() });
        buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  }
})();
