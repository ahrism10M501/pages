function escapeHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function renderMarkdown(source) {
  const math = [];
  let text = source.replace(/\$\$([\s\S]+?)\$\$/g, (_, value) => {
    math.push({ value, displayMode: true });
    return 'MATHPH' + (math.length - 1) + 'BLK';
  });
  text = text.replace(/\$([^\n$]+?)\$/g, (_, value) => {
    math.push({ value, displayMode: false });
    return 'MATHPH' + (math.length - 1) + 'INL';
  });
  return marked.parse(text).replace(/MATHPH(\d+)(BLK|INL)/g, (_, index) => {
    const item = math[+index];
    if (typeof katex === 'undefined') return escapeHtml(item.value);
    return katex.renderToString(item.value, { displayMode: item.displayMode, throwOnError: false });
  });
}

function renderNotebook(nb) {
  if (!Array.isArray(nb.cells)) throw new Error('Invalid notebook');
  const parts = [];
  let first = true;
  for (const cell of nb.cells) {
    let source = Array.isArray(cell.source) ? cell.source.join('') : (cell.source || '');
    if (!source.trim()) continue;
    if (first && cell.cell_type === 'markdown') source = stripFrontmatter(source);
    first = false;
    if (cell.cell_type === 'markdown') {
      parts.push('<div class="nb-cell nb-markdown">' + renderMarkdown(source) + '</div>');
    } else if (cell.cell_type === 'code') {
      let html = '<div class="nb-cell nb-code"><pre><code class="language-python">' + escapeHtml(source) + '</code></pre>';
      for (const output of cell.outputs || []) {
        const data = output.data || {};
        const text = value => Array.isArray(value) ? value.join('') : (value || '');
        html += '<div class="nb-output">';
        if (output.output_type === 'stream') {
          html += '<pre>' + escapeHtml(text(output.text)) + '</pre>';
        } else if (output.output_type === 'error') {
          html += '<pre class="nb-error">' + escapeHtml((output.ename || '') + ': ' + (output.evalue || '')) + '</pre>';
        } else if (data['image/png']) {
          html += '<img class="cell-output-image" alt="노트북 셀의 실행 결과" src="data:image/png;base64,' + escapeHtml(text(data['image/png'])) + '">';
        } else if (data['image/svg+xml']) {
          html += '<div class="nb-svg">' + text(data['image/svg+xml']) + '</div>';
        } else if (data['text/html']) {
          html += '<div class="nb-html-out">' + text(data['text/html']) + '</div>';
        } else if (data['text/plain']) {
          html += '<pre>' + escapeHtml(text(data['text/plain'])) + '</pre>';
        }
        html += '</div>';
      }
      parts.push(html + '</div>');
    }
  }
  return parts.join('\n');
}

function finishContent(container) {
  container.querySelectorAll('pre code').forEach(el => {
    if (typeof hljs !== 'undefined') hljs.highlightElement(el);
  });
}

async function renderDiagrams() {
  if (!document.querySelector('.mermaid')) return;
  try {
    await new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js';
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
    mermaid.initialize({ startOnLoad: false, theme: 'neutral' });
    await mermaid.run();
  } catch {
    // Keep diagram source readable when its renderer is unavailable.
  }
}

(async () => {
  const article = document.getElementById('post-content');
  try {
    if (typeof marked === 'undefined') throw new Error('Markdown renderer unavailable');
    marked.use({
      renderer: {
        code({ text, lang }) {
          return lang === 'mermaid' ? '<pre class="mermaid">' + escapeHtml(text) + '</pre>' : false;
        }
      },
      extensions: [{
        name: 'youtube',
        level: 'block',
        start(source) { return source.match(/^https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)/m)?.index; },
        tokenizer(source) {
          const match = source.match(/^(https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([\w-]+)[^\s]*)\n?/);
          if (match) return { type: 'youtube', raw: match[0], videoId: match[2] };
        },
        renderer(token) {
          return '<div class="video-container"><iframe title="YouTube 동영상" src="https://www.youtube.com/embed/' + token.videoId + '" loading="lazy" allowfullscreen></iframe></div>';
        }
      }]
    });
    document.querySelectorAll('.markdown-source').forEach(container => {
      container.innerHTML = renderMarkdown(container.textContent);
      container.classList.remove('markdown-source');
      finishContent(container);
    });
    if (article) {
      const response = await fetch(article.dataset.source);
      if (!response.ok) throw new Error('Content unavailable');
      article.innerHTML = article.dataset.notebook === 'true'
        ? renderNotebook(await response.json())
        : renderMarkdown(stripFrontmatter(await response.text()));
      finishContent(article);
    }
    await renderDiagrams();
  } catch {
    if (article) {
      article.replaceChildren();
      const message = document.createElement('p');
      message.textContent = '글을 불러오지 못했습니다. 잠시 후 다시 시도하거나 ';
      const link = document.createElement('a');
      link.href = article.dataset.source;
      link.textContent = '원본 파일을 열어 주세요.';
      message.appendChild(link);
      article.appendChild(message);
    }
  } finally {
    if (article) article.setAttribute('aria-busy', 'false');
  }
})();
