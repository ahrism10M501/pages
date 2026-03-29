// page-fold.js — scroll-based fold transition between pages
(function () {
  var PAGE = parseInt(document.body.dataset.page, 10);

  // 각 페이지의 이전/다음 URL (현재 위치 기준 상대경로)
  var DEFS = [
    { prev: null,         next: './blog/'    },  // 0: Home
    { prev: '../',        next: '../github/' },  // 1: Blog
    { prev: '../blog/',   next: null         },  // 2: GitHub
  ];
  var def = DEFS[PAGE];
  if (!def) return;

  var el = document.getElementById('page-content');
  if (!el) return;

  var THRESHOLD  = 120;  // 이 이상 당겨야 전환
  var RESISTANCE = 0.35; // 당기는 시각적 반응 비율

  var pullAccum  = 0;
  var pulling    = false; // 현재 overscroll 중인지
  var triggered  = false; // 전환 실행됐는지
  var wheelTimer = null;

  // 스크롤 위치 캐싱 — passive 리스너에서 업데이트하여 wheel 핸들러에서 DOM 읽기 없애기
  var cachedScrollY = window.scrollY;
  var cachedScrollH = document.documentElement.scrollHeight;
  var cachedInnerH  = window.innerHeight;

  window.addEventListener('scroll', function () {
    cachedScrollY = window.scrollY;
    cachedScrollH = document.documentElement.scrollHeight;
  }, { passive: true });
  window.addEventListener('resize', function () {
    cachedInnerH  = window.innerHeight;
    cachedScrollH = document.documentElement.scrollHeight;
  }, { passive: true });

  // ── 상태 초기화 (당기다가 놓으면 복귀) ────────────────
  function resetPull() {
    pullAccum = 0;
    pulling   = false;
    triggered = false;
    el.style.transition = 'transform 0.35s cubic-bezier(0.34,1.56,0.64,1), opacity 0.3s ease';
    el.style.transform  = '';
    el.style.opacity    = '';
    document.documentElement.style.overflow = '';
  }

  // ── 당기는 중 시각 피드백 ─────────────────────────────
  function applyPull(ratio, direction) {
    var r = Math.min(ratio, 1);
    el.style.transition = 'none';
    if (direction === 'next') {
      // 아래로 당김: 현재 페이지가 위로 살짝 접히기 시작
      var deg  = r * -20;
      var fade = 1 - r * 0.4;
      el.style.transform  = 'perspective(900px) rotateX(' + deg + 'deg) translateY(' + (-r * 12) + 'px)';
      el.style.opacity    = fade;
    } else {
      // 위로 당김: 현재 페이지가 아래로 살짝 밀림
      el.style.transform = 'translateY(' + (r * 30) + 'px)';
    }
  }

  // ── 전환 실행 ─────────────────────────────────────────
  function trigger(direction) {
    if (triggered) return;
    triggered = true;
    var href = direction === 'next' ? def.next : def.prev;
    if (!href) { triggered = false; return; }

    var exitDirection = direction === 'next' ? 'forward' : 'backward';

    // exit 애니메이션
    el.style.transition = 'transform 0.5s cubic-bezier(0.4,0,0.2,1), opacity 0.5s ease';
    if (exitDirection === 'forward') {
      el.style.transform = 'perspective(900px) rotateX(-90deg) translateY(-55px)';
      el.style.opacity   = '0';
    } else {
      el.style.transform = 'translateY(100%)';
    }
    document.documentElement.style.overflow = 'hidden';

    setTimeout(function () {
      try { sessionStorage.setItem('nav-direction', exitDirection); } catch (e) {}
      window.location.href = href;
    }, 520);
  }

  // ── 스크롤 하단/상단 판별 (캐시 사용) ────────────────
  function atBottom() { return cachedScrollY + cachedInnerH >= cachedScrollH - 4; }
  function atTop()    { return cachedScrollY <= 2; }

  // ── Wheel ────────────────────────────────────────────
  // passive: true — e.preventDefault() 불필요 (overscroll 시 이미 스크롤 끝이라 추가 이동 없음,
  //                 CSS overscroll-behavior-y:contain 이 bounce 방지)
  window.addEventListener('wheel', function (e) {
    if (triggered) return;

    // 다음 페이지로 (하단 overscroll)
    if (def.next && atBottom() && e.deltaY > 0) {
      pullAccum += e.deltaY;
      pulling = true;
      applyPull(pullAccum / THRESHOLD * RESISTANCE, 'next');
      if (pullAccum >= THRESHOLD) { trigger('next'); return; }
      clearTimeout(wheelTimer);
      wheelTimer = setTimeout(resetPull, 350);
      return;
    }

    // 이전 페이지로 (상단 overscroll)
    if (def.prev && atTop() && e.deltaY < 0) {
      pullAccum += Math.abs(e.deltaY);
      pulling = true;
      applyPull(pullAccum / THRESHOLD * RESISTANCE, 'prev');
      if (pullAccum >= THRESHOLD) { trigger('prev'); return; }
      clearTimeout(wheelTimer);
      wheelTimer = setTimeout(resetPull, 350);
      return;
    }

    // 일반 스크롤 중엔 pull 리셋
    if (pulling) resetPull();
  }, { passive: true });

  // ── Touch ────────────────────────────────────────────
  var tStartY = 0;
  var tLastY  = 0;

  window.addEventListener('touchstart', function (e) {
    tStartY = tLastY = e.touches[0].clientY;
  }, { passive: true });

  window.addEventListener('touchmove', function (e) {
    if (triggered) return;
    var dy    = tLastY - e.touches[0].clientY; // 양수 = 아래로 스크롤
    tLastY    = e.touches[0].clientY;

    if (def.next && atBottom() && dy > 0) {
      pullAccum += dy * 1.5;
      pulling = true;
      applyPull(pullAccum / THRESHOLD * RESISTANCE, 'next');
      if (pullAccum >= THRESHOLD) trigger('next');
      return;
    }

    if (def.prev && atTop() && dy < 0) {
      pullAccum += Math.abs(dy) * 1.5;
      pulling = true;
      applyPull(pullAccum / THRESHOLD * RESISTANCE, 'prev');
      if (pullAccum >= THRESHOLD) trigger('prev');
      return;
    }

    if (pulling) resetPull();
  }, { passive: true });

  window.addEventListener('touchend', function () {
    if (!triggered) resetPull();
  }, { passive: true });

})();
