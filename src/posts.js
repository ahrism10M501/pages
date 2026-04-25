// posts.js — post list fetching, rendering, search, and tag filtering.
// Required globals: formatPostDate (utils.js)

async function fetchPosts(jsonPath) {
  try {
    const res = await fetch(jsonPath);
    return res.ok ? res.json() : [];
  } catch {
    return [];
  }
}

async function fetchGraph(jsonPath) {
  try {
    const res = await fetch(jsonPath);
    return res.ok ? res.json() : null;
  } catch {
    return null;
  }
}

// Render a list of posts into a container. Each post: { slug, title, date, tags, summary }
function renderPostList(posts, container, postsBasePath) {
  container.innerHTML = '';
  posts.forEach(post => {
    const item = document.createElement('a');
    item.href = `${postsBasePath}${post.slug}/`;
    item.className = 'post-item';
    item.innerHTML = `
      <div class="post-item-row">
        <h3>${post.title}</h3>
        <span class="post-date-inline">${formatPostDate(post.date)}</span>
      </div>
      <div class="post-meta" style="margin-top:0.25rem">
        ${post.tags.map(t => `<span class="tag">${t}</span>`).join(' ')}
      </div>
      ${post.summary ? `<p style="color:#666;font-size:0.85rem;margin-top:0.3rem;margin-bottom:0">${post.summary}</p>` : ''}
    `;
    container.appendChild(item);
  });
}

// Extract slug from current URL: /repo/posts/my-post/ → "my-post"
function getSlugFromURL() {
  const path = window.location.pathname.replace(/\/index\.html$/, '').replace(/\/$/, '');
  const parts = path.split('/');
  return decodeURIComponent(parts[parts.length - 1]);
}

// Search nodes by query. mode: "text" (default) or "tfidf". Returns matching node IDs.
function searchPosts(nodes, query, mode) {
  if (!query || !query.trim()) return nodes.map(n => n.id);
  const q = query.trim().toLowerCase();

  if (mode === 'tfidf') {
    const queryWords = q.split(/\s+/);
    const scored = nodes.map(node => {
      const tfidf = node.tfidf || {};
      let score = 0;
      for (const word of queryWords) {
        for (const [keyword, value] of Object.entries(tfidf)) {
          if (keyword.includes(word) || word.includes(keyword)) score += value;
        }
      }
      return { id: node.id, score };
    });
    return scored.filter(s => s.score > 0)
      .sort((a, b) => b.score - a.score)
      .map(s => s.id);
  }

  return nodes.filter(n =>
    (n.title && n.title.toLowerCase().includes(q)) ||
    (n.summary && n.summary.toLowerCase().includes(q))
  ).map(n => n.id);
}

// Filter nodes by active tags (OR). Returns matching node IDs.
function filterByTags(nodes, activeTags) {
  if (!activeTags || activeTags.length === 0) return nodes.map(n => n.id);
  return nodes.filter(n => n.tags && n.tags.some(t => activeTags.includes(t))).map(n => n.id);
}
