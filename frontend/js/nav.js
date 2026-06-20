/**
 * nav.js — Shared navigation bar component for Adhera.
 */
function renderNav(activePage) {
    const navRoot = document.getElementById('nav-root');
    if (!navRoot) return;

    const pages = [
        { id: 'dashboard', href: 'dashboard.html', key: 'nav.dashboard', label: 'Dashboard' },
        { id: 'medicines', href: 'medicines.html', key: 'nav.medicines', label: 'Medicines' },
        { id: 'feedback',  href: 'feedback.html',  key: 'nav.feedback',  label: 'Feedback' },
        { id: 'profile',   href: 'profile.html',   key: 'nav.profile',   label: 'Profile' }
    ];

    const linksHtml = pages.map(page => {
        const isActive = page.id === activePage;
        const className = isActive ? 'text-cyan-400' : 'hover:text-cyan-400 transition-colors';
        return `<a href="${page.href}" class="${className}" x-text="t('${page.key}')">${page.label}</a>`;
    }).join('\n            ');

    navRoot.innerHTML = `
    <nav class="glass p-4 sticky top-0 z-50 flex justify-between items-center mb-6 rounded-none border-t-0 border-l-0 border-r-0">
        <a href="dashboard.html" class="flex items-center" style="height: 40px; overflow: visible;">
            <div style="transform: scale(0.25); transform-origin: left center; width: 50px;">
                <svg width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <linearGradient id="glow" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stop-color="#00F2FF" />
                      <stop offset="100%" stop-color="#3B82F6" />
                    </linearGradient>
                  </defs>
                  <circle cx="100" cy="100" r="80" fill="url(#glow)" fill-opacity="0.1" stroke="url(#glow)" stroke-width="2" />
                  <circle cx="100" cy="100" r="60" fill="white" fill-opacity="0.05" style="backdrop-filter: blur(10px)" stroke="white" stroke-opacity="0.2" />
                  <path d="M100 60L135 140H115L100 105L85 140H65L100 60Z" fill="url(#glow)" />
                  <rect x="92" y="110" width="16" height="4" rx="2" fill="white" fill-opacity="0.8" />
                </svg>
            </div>
            <span style="color: #00dbe7; font-weight: 700; font-size: 1.5rem; letter-spacing: -0.02em;">Adhera</span>
        </a>
        <div class="space-x-4 font-medium text-sm">
            ${linksHtml}
            <button @click="logout" class="text-red-400 hover:text-red-300 ml-4" x-text="t('nav.logout')">Logout</button>
        </div>
    </nav>
    `;
}

// Expose renderNav to window
window.renderNav = renderNav;
