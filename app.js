// Fetch posts.json from a relative path and return parsed array
async function fetchPosts(jsonPath) {
  const res = await fetch(jsonPath);
  if (!res.ok) return [];
  return res.json();
}

// Render a list of posts into a container element
// Each post: { slug, title, date, tags, summary }
// postsBasePath: relative path prefix to posts/ directory
function renderPostList(posts, container, postsBasePath) {
  container.innerHTML = '';
  posts.forEach(post => {
    const item = document.createElement('a');
    item.href = `${postsBasePath}${post.slug}/`;
    item.className = 'post-item';
    item.style.textDecoration = 'none';
    item.style.display = 'block';
    item.innerHTML = `
      <h3>${post.title}</h3>
      <div class="post-meta">
        ${post.date}
        ${post.tags.map(t => `<span class="tag">${t}</span>`).join(' ')}
      </div>
      ${post.summary ? `<p style="color:#777;font-size:0.85rem;margin-top:0.3rem">${post.summary}</p>` : ''}
    `;
    container.appendChild(item);
  });
}

// Extract slug from current URL path
// e.g., /repo/posts/my-post/ → "my-post"
// e.g., /repo/posts/my-post/index.html → "my-post"
function getSlugFromURL() {
  const path = window.location.pathname.replace(/\/index\.html$/, '').replace(/\/$/, '');
  const parts = path.split('/');
  return parts[parts.length - 1];
}
