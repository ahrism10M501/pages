const searchInput = document.getElementById('search-input');
const rows = [...document.querySelectorAll('[data-post]')];
const status = document.getElementById('search-status');

document.querySelector('.search').hidden = false;

function filterPosts() {
  const words = searchInput.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  let count = 0;
  rows.forEach(row => {
    row.hidden = !words.every(word => row.dataset.search.toLocaleLowerCase().includes(word));
    if (!row.hidden) count++;
  });
  status.textContent = count + '개의 글';
  document.getElementById('search-empty').hidden = count !== 0;
}

searchInput.addEventListener('input', filterPosts);
searchInput.addEventListener('search', filterPosts);
