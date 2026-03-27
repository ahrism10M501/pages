// sidebar.js — shared sidebar: panel toggle, navigation, outside-click close
(function () {
  // 패널 토글 버튼 (data-panel 속성 있음)
  document.querySelectorAll('.sidebar-btn[data-panel]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var panelId = 'panel-' + btn.dataset.panel;
      var panel = document.getElementById(panelId);
      if (!panel) return;
      var isOpen = panel.classList.contains('open');
      document.querySelectorAll('.sidebar-panel').forEach(function (p) {
        p.classList.remove('open');
      });
      if (!isOpen) panel.classList.add('open');
    });
  });

  // 이동 버튼 (data-href 속성 있음)
  document.querySelectorAll('.sidebar-btn[data-href]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      window.location.href = btn.dataset.href;
    });
  });

  // 사이드바 외부 클릭 시 패널 닫기
  document.addEventListener('click', function (e) {
    if (!e.target.closest('#sidebar')) {
      document.querySelectorAll('.sidebar-panel').forEach(function (p) {
        p.classList.remove('open');
      });
    }
  });
})();
