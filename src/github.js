// github.js — GitHub repos listing for /github/ page
(function () {
  var CACHE_TTL = 5 * 60 * 1000;

  var LANG_COLORS = {
    Python: '#3572A5', JavaScript: '#f1e05a', TypeScript: '#3178c6',
    'C++': '#f34b7d', C: '#555555', Java: '#b07219', HTML: '#e34c26',
    CSS: '#563d7c', Rust: '#dea584', Go: '#00ADD8', Shell: '#89e051',
    'Jupyter Notebook': '#DA5B0B', Kotlin: '#A97BFF', Swift: '#F05138', Ruby: '#701516'
  };

  function relativeDate(dateStr) {
    var sec = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
    if (sec < 60) return '방금';
    var min = Math.floor(sec / 60);
    if (min < 60) return min + '분 전';
    var hr = Math.floor(min / 60);
    if (hr < 24) return hr + '시간 전';
    var day = Math.floor(hr / 24);
    if (day < 30) return day + '일 전';
    var month = Math.floor(day / 30);
    if (month < 12) return month + '개월 전';
    return Math.floor(month / 12) + '년 전';
  }

  function getCached(key) {
    try {
      var raw = sessionStorage.getItem(key);
      if (!raw) return null;
      var obj = JSON.parse(raw);
      if (Date.now() - obj.ts > CACHE_TTL) {
        sessionStorage.removeItem(key);
        return null;
      }
      return obj.data;
    } catch (e) { return null; }
  }

  function setCache(key, data) {
    try {
      sessionStorage.setItem(key, JSON.stringify({ ts: Date.now(), data: data }));
    } catch (e) {}
  }

  function fetchRepos(source) {
    var cacheKey = 'gh_repos_' + source.name;
    var cached = getCached(cacheKey);
    if (cached) return Promise.resolve(cached);

    var base = source.type === 'org'
      ? 'https://api.github.com/orgs/'
      : 'https://api.github.com/users/';
    var url = base + encodeURIComponent(source.name) + '/repos?sort=updated&per_page=100';

    return fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      })
      .then(function (repos) {
        setCache(cacheKey, repos);
        return repos;
      });
  }

  function renderRepoCard(repo) {
    var card = document.createElement('a');
    card.className = 'gh-repo-card';
    card.href = repo.html_url;
    card.target = '_blank';
    card.rel = 'noopener noreferrer';

    var name = document.createElement('div');
    name.className = 'gh-repo-name';
    name.textContent = repo.name;
    card.appendChild(name);

    if (repo.description) {
      var desc = document.createElement('div');
      desc.className = 'gh-repo-desc';
      desc.textContent = repo.description;
      card.appendChild(desc);
    }

    var meta = document.createElement('div');
    meta.className = 'gh-repo-meta';

    if (repo.language) {
      var lang = document.createElement('span');
      lang.className = 'gh-repo-lang';
      var dot = document.createElement('span');
      dot.className = 'gh-lang-dot';
      dot.style.background = LANG_COLORS[repo.language] || '#888';
      lang.appendChild(dot);
      lang.appendChild(document.createTextNode(repo.language));
      meta.appendChild(lang);
    }

    if (repo.stargazers_count > 0) {
      var stars = document.createElement('span');
      stars.className = 'gh-repo-stars';
      stars.textContent = '★ ' + repo.stargazers_count;
      meta.appendChild(stars);
    }

    if (repo.updated_at) {
      var date = document.createElement('span');
      date.className = 'gh-repo-date';
      date.textContent = relativeDate(repo.updated_at);
      meta.appendChild(date);
    }

    card.appendChild(meta);
    return card;
  }

  function renderSection(source, container) {
    var section = document.createElement('div');
    section.className = 'gh-source-section';

    var label = document.createElement('div');
    label.className = 'label';
    label.textContent = source.label || source.name;
    section.appendChild(label);

    container.appendChild(section);

    fetchRepos(source)
      .then(function (repos) {
        repos = repos.filter(function (r) { return !r.fork; });
        if (repos.length === 0) {
          var empty = document.createElement('p');
          empty.className = 'gh-empty';
          empty.textContent = '공개 리포지토리가 없습니다';
          section.appendChild(empty);
          return;
        }
        var scroll = document.createElement('div');
        scroll.className = 'gh-repo-scroll';
        scroll.style.setProperty('--gh-rows', source.rows || 1);
        repos.forEach(function (repo) {
          scroll.appendChild(renderRepoCard(repo));
        });
        section.appendChild(scroll);
      })
      .catch(function (err) {
        var errEl = document.createElement('p');
        errEl.className = 'gh-error';
        errEl.textContent = 'API 요청 실패 — 잠시 후 다시 시도해주세요 (' + err.message + ')';
        section.appendChild(errEl);
      });
  }

  var sourcesUrl = document.currentScript && document.currentScript.dataset.sources;
  if (!sourcesUrl) return;

  fetch(sourcesUrl)
    .then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    })
    .then(function (sources) {
      var container = document.getElementById('github-sources');
      sources.forEach(function (source) { renderSection(source, container); });
    })
    .catch(function (err) {
      document.getElementById('github-sources').innerHTML =
        '<p class="gh-error">소스 설정을 불러올 수 없습니다 (' + err.message + ')</p>';
    });
})();
