// Toggle the visibility of the theme selection menu
function toggleThemeMenu(e) {
    e.preventDefault();
    const menu = document.getElementById('themeMenu');
    menu.classList.toggle('active');
}

function clearThemeClasses() {
    const themes = ['light-theme', 'blue-theme', 'sepia-theme', 'forest-theme'];
    themes.forEach(t => document.body.classList.remove(t));
}

function setTheme(theme) {
    const root = document.documentElement;

    const isDark = document.body.classList.contains('dark');

    clearThemeClasses();
    document.body.classList.add(`${theme}-theme`);

    if (isDark) document.body.classList.add('dark');

    // base (light) defaults for CSS variables
    const baseColors = {
        '--body-color': 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
        '--sidebar-color': '#FFF',
        '--primary-color': '#695CFE',
        '--primary-color-light': '#F6F5FF',
        '--text-color': '#707070',
        '--black-color': '#0a0909',
        '--accent-gradient': 'linear-gradient(135deg, #ff8a65 0%, #ffb74d 100%)',
        '--accent-icon-bg': '#ff8a65'
    };
    Object.entries(baseColors).forEach(([k, v]) => root.style.setProperty(k, v));

    switch (theme) {
        case 'light':
            break;
        case 'blue':
            root.style.setProperty('--body-color', 'linear-gradient(135deg, #2563eb 0%, #60a5fa 100%)');
            root.style.setProperty('--accent-gradient', 'linear-gradient(135deg, #2153c0ff 0%, #60a5fa 100%)');
            root.style.setProperty('--accent-icon-bg', '#2563eb');
            break;
        case 'sepia':
            root.style.setProperty('--body-color', 'linear-gradient(135deg, #b08457 0%, #d1a054 100%)');
            root.style.setProperty('--accent-gradient', 'linear-gradient(135deg, #94714cff 0%, #e4a951ff 100%)');
            root.style.setProperty('--accent-icon-bg', '#b08457');
            break;
        case 'forest':
            root.style.setProperty('--body-color', 'linear-gradient(135deg, #2c7744 0%, #5a9458 100%)');
            root.style.setProperty('--accent-gradient', 'linear-gradient(135deg, #43a047 0%, #66bb6a 100%)');
            root.style.setProperty('--accent-icon-bg', '#43a047');
            break;
    }

    localStorage.setItem('selectedTheme', theme);
    document.getElementById('themeMenu').classList.remove('active');
    if (typeof window.syncDarkToggleAvailability === 'function') {
        window.syncDarkToggleAvailability();
    }
}

// Load saved theme (and keep dark mode if enabled)
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('selectedTheme') || 'light';
    const darkOn = localStorage.getItem('darkMode') === 'true';
    setTheme(savedTheme);
    document.body.classList.toggle('dark', darkOn);
    if (typeof window.syncDarkToggleAvailability === 'function') {
        window.syncDarkToggleAvailability();
    }
});
