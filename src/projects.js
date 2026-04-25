// projects.js — projects.json card rendering.

function renderProjectCards(projects, container) {
  container.innerHTML = '';
  container.className = 'project-scroll';
  projects.forEach(project => {
    const card = document.createElement('a');
    card.href = project.link || '#';
    card.target = '_blank';
    card.rel = 'noopener noreferrer';
    card.className = 'project-card';
    card.innerHTML = `
      <h3>${project.title}</h3>
      <p>${project.description}</p>
      <div class="card-tags">
        ${(project.tags || []).map(t => `<span class="tag">${t}</span>`).join('')}
      </div>
    `;
    container.appendChild(card);
  });
}
