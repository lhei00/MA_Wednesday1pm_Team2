(function () {
    const THEME_BLOCK_LIST = ["blue-theme", "sepia-theme", "forest-theme"];
    const getToggleEl = () => document.querySelector(".toggle-switch");

    const applyDarkMode = (enabled) => {
        document.documentElement.classList.toggle("dark", enabled);
        if (document.body) {
            document.body.classList.toggle("dark", enabled);
        }
    };

    const canUseDarkMode = () => {
        if (!document.body) return false;
        const hasBlockedTheme = THEME_BLOCK_LIST.some((cls) =>
            document.body.classList.contains(cls)
        );
        if (hasBlockedTheme) {
            return false;
        }
        const hasLightTheme = document.body.classList.contains("light-theme");
        const hasAnyTheme =
            hasLightTheme ||
            THEME_BLOCK_LIST.some((cls) => document.body.classList.contains(cls));
        return hasLightTheme || !hasAnyTheme;
    };

    const syncToggleAvailability = () => {
        const toggle = getToggleEl();
        if (!toggle) return;
        const allowDark = canUseDarkMode();
        toggle.classList.toggle("disabled", !allowDark);
        toggle.setAttribute("aria-disabled", String(!allowDark));
        if (!allowDark && document.documentElement.classList.contains("dark")) {
            applyDarkMode(false);
            localStorage.setItem("darkMode", "false");
        }
    };

    const savedPreference = localStorage.getItem("darkMode");
    applyDarkMode(savedPreference === "true");

    window.toggleDarkMode = function () {
        if (!canUseDarkMode()) {
            return;
        }
        const nextState = !document.documentElement.classList.contains("dark");
        applyDarkMode(nextState);
        localStorage.setItem("darkMode", String(nextState));
    };

    window.toggleSidebar = function () {
        const sidebar = document.querySelector(".sidebar");
        if (sidebar) {
            sidebar.classList.toggle("close");
        }
    };

    window.syncDarkToggleAvailability = syncToggleAvailability;

    document.addEventListener("DOMContentLoaded", syncToggleAvailability);
})();
