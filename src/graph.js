(() => {
  const data = document.getElementById('graph-data');
  if (!data) return;
  const root = document.currentScript.dataset.root;
  const { nodes, edges } = JSON.parse(data.textContent);
  if (!nodes.length) return;
  const byId = new Map(nodes.map(node => [node.id, node]));
  const positions = new Map();
  const buttons = new Map();
  const lines = [];
  const stage = document.getElementById('graph-stage');
  const explorer = document.getElementById('graph-explorer');
  const records = document.getElementById('graph-records');
  const preferredView = matchMedia('(max-width: 700px)').matches ? 'list' : 'graph';
  let selected, view;

  // shortcut: circular layout suits small archives; use a layout engine when node labels overlap.
  for (const kind of ['post', 'twinkle']) {
    const group = nodes.filter(node => node.kind === kind);
    group.forEach((node, index) => {
      const angle = 2 * Math.PI * index / group.length - Math.PI / 2;
      const x = (kind === 'post' ? 290 : 740) + (group.length > 1 ? 170 * Math.cos(angle) : 0);
      const y = 300 + (group.length > 1 ? 170 * Math.sin(angle) : 0);
      positions.set(node.id, { x, y });
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'graph-node ' + kind;
      button.style.left = x / 10 + '%';
      button.style.top = y / 5.6 + '%';
      button.setAttribute('aria-label', (kind === 'post' ? '글: ' : 'Twinkle: ') + node.title);
      button.setAttribute('aria-pressed', 'false');
      const mark = document.createElement('span');
      mark.className = 'node-mark';
      mark.setAttribute('aria-hidden', 'true');
      mark.textContent = kind === 'post' ? '●' : '✦';
      const label = document.createElement('span');
      label.className = 'node-label';
      label.textContent = node.title;
      button.append(mark, label);
      button.addEventListener('click', () => select(node.id));
      stage.appendChild(button);
      buttons.set(node.id, button);
    });
  }
  edges.forEach(edge => {
    const source = positions.get(edge.source), target = positions.get(edge.target);
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    // The marker sits above the node's fixed two-line label.
    for (const [key, value] of Object.entries({ x1: source.x, y1: source.y - 21.5, x2: target.x, y2: target.y - 21.5 })) {
      line.setAttribute(key, value);
    }
    line.classList.add('graph-edge');
    if (edge.manual) line.classList.add('manual');
    document.getElementById('graph-lines').appendChild(line);
    lines.push({ edge, line });
  });

  function updateURL() {
    const url = new URL(location.href);
    url.searchParams.set('node', selected);
    url.searchParams.set('view', view);
    if (url.href !== location.href) history.pushState(null, '', url);
  }

  function select(id, update = true) {
    const node = byId.get(id);
    if (!node) return;
    selected = id;
    const connected = edges.filter(edge => edge.source === id || edge.target === id);
    const neighbors = new Set(connected.map(edge => edge.source === id ? edge.target : edge.source));
    buttons.forEach((button, buttonId) => {
      button.setAttribute('aria-pressed', String(buttonId === id));
      button.classList.toggle('connected', neighbors.has(buttonId));
      button.classList.toggle('dimmed', buttonId !== id && !neighbors.has(buttonId));
    });
    lines.forEach(({ edge, line }) => {
      line.classList.toggle('active', edge.source === id || edge.target === id);
    });
    document.getElementById('detail-kind').textContent = node.kind === 'post' ? '글' : 'Twinkle';
    const date = document.getElementById('detail-date');
    date.dateTime = node.date;
    date.textContent = new Intl.DateTimeFormat('ko-KR', { dateStyle: 'medium' }).format(new Date(node.date + 'T00:00:00'));
    document.getElementById('detail-title').textContent = node.title;
    document.getElementById('detail-summary').textContent = node.summary;
    document.getElementById('detail-tags').textContent = node.tags.join(' · ');
    const link = document.getElementById('detail-link');
    link.href = root + node.url;
    link.textContent = node.kind === 'post' ? '글 읽기' : 'Twinkle 읽기';
    const list = document.getElementById('graph-connections');
    list.replaceChildren();
    connected.forEach(edge => {
      const other = byId.get(edge.source === id ? edge.target : edge.source);
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = other.title;
      button.addEventListener('click', () => {
        select(other.id);
        document.getElementById('detail-title').focus();
      });
      const reason = document.createElement('span');
      reason.textContent = [edge.manual ? '직접 연결' : '', edge.tags.length ? '같은 태그: ' + edge.tags.join(', ') : ''].filter(Boolean).join(' / ');
      item.append(button, reason);
      list.appendChild(item);
    });
    document.getElementById('graph-isolated').hidden = connected.length !== 0;
    document.querySelectorAll('[data-select]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.select === id));
    });
    if (update) updateURL();
  }

  function setView(next, update = true) {
    view = next;
    document.getElementById('view-graph').setAttribute('aria-pressed', String(view === 'graph'));
    document.getElementById('view-list').setAttribute('aria-pressed', String(view === 'list'));
    document.querySelector('.graph-map').hidden = view !== 'graph';
    explorer.classList.toggle('list-view', view === 'list');
    records.hidden = view !== 'list';
    if (view === 'list') explorer.before(records);
    if (update) updateURL();
  }

  function readURL() {
    const params = new URLSearchParams(location.search);
    const first = nodes.find(node => edges.some(edge => edge.source === node.id || edge.target === node.id)) || nodes[0];
    select(byId.has(params.get('node')) ? params.get('node') : first.id, false);
    setView(['graph', 'list'].includes(params.get('view')) ? params.get('view') : preferredView, false);
  }

  document.getElementById('view-graph').addEventListener('click', () => setView('graph'));
  document.getElementById('view-list').addEventListener('click', () => setView('list'));
  document.querySelectorAll('[data-select]').forEach(button => {
    button.hidden = false;
    button.addEventListener('click', () => {
      select(button.dataset.select);
      const heading = document.getElementById('detail-title');
      heading.tabIndex = -1;
      heading.focus();
    });
  });
  addEventListener('popstate', readURL);
  readURL();
  document.getElementById('graph-tools').hidden = false;
  explorer.hidden = false;
})();
