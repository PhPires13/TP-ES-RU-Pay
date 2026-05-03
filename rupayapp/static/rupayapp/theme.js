/**
 * Theme Management System
 * Handles theme selection, persistence, and application
 */

const STORAGE_KEY = 'theme_preference';
const VALID_THEMES = ['light', 'dark', 'high_contrast'];

/**
 * Initialize theme on page load
 * Priority: localStorage > data-theme attribute > 'light'
 * (localStorage takes priority for non-authenticated users)
 */
function initTheme() {
  const htmlElement = document.documentElement;
  
  // 1. Check localStorage first (for non-authenticated users and offline scenarios)
  let currentTheme = localStorage.getItem(STORAGE_KEY);
  
  // 2. If not in localStorage, check if theme is set via data-theme attribute (from backend)
  if (!currentTheme) {
    currentTheme = htmlElement.getAttribute('data-theme');
  }
  
  // 3. Default to 'light' if still not found
  if (!currentTheme || !VALID_THEMES.includes(currentTheme)) {
    currentTheme = 'light';
  }
  
  // Apply theme
  applyTheme(currentTheme);
}

/**
 * Apply theme to the page
 * @param {string} themeName - Theme name: 'light', 'dark', or 'high_contrast'
 */
function applyTheme(themeName) {
  if (!VALID_THEMES.includes(themeName)) {
    console.warn(`Invalid theme: ${themeName}. Using 'light' instead.`);
    themeName = 'light';
  }
  
  document.documentElement.setAttribute('data-theme', themeName);
  localStorage.setItem(STORAGE_KEY, themeName);
}

/**
 * Set user theme with persistence
 * - Saves to localStorage immediately (for instant visual feedback)
 * - If user is authenticated, sends POST to backend to save in DB
 * @param {string} themeName - Theme name
 */
function setTheme(themeName) {
  if (!VALID_THEMES.includes(themeName)) {
    console.error(`Invalid theme: ${themeName}`);
    return;
  }
  
  // Apply immediately for instant visual feedback
  applyTheme(themeName);
  
  // Send to backend (async, non-blocking)
  sendThemeToBackend(themeName);
}

/**
 * Send theme preference to backend
 * Uses debounce to avoid multiple requests
 * @param {string} themeName
 */
let debounceTimer = null;
function sendThemeToBackend(themeName) {
  // Clear previous debounce timer
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  
  // Debounce: wait 300ms before sending
  debounceTimer = setTimeout(() => {
    fetch('/api/set-theme/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({ theme: themeName }),
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        console.log(`Theme saved: ${themeName}`);
      } else {
        console.warn('Failed to save theme:', data.message);
      }
    })
    .catch(error => {
      console.warn('Error saving theme:', error);
      // Theme is already applied locally, so it's okay if backend fails
    });
  }, 300);
}

/**
 * Get CSRF token from cookie
 * Required for Django POST requests
 * @returns {string} CSRF token
 */
function getCookie(name) {
  let cookieValue = '';
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Initialize theme when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initTheme);
} else {
  initTheme();
}

/**
 * Initialize theme dropdown in header
 */
function initThemeDropdown() {
  const dropdown = document.querySelector('.theme-selector-dropdown');
  const toggleBtn = document.querySelector('.theme-toggle-btn');
  const dropdownItems = document.querySelectorAll('.theme-dropdown-item');
  
  if (!toggleBtn || !dropdownItems.length) {
    return; // Dropdown not present on this page
  }
  
  // Get current theme
  function updateDropdownUI() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    dropdownItems.forEach(item => {
      const itemTheme = item.getAttribute('data-theme');
      if (itemTheme === currentTheme) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }
  
  // Toggle dropdown
  toggleBtn.addEventListener('click', () => {
    dropdown.classList.toggle('active');
    updateDropdownUI();
  });
  
  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) {
      dropdown.classList.remove('active');
    }
  });
  
  // Handle theme selection
  dropdownItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const theme = item.getAttribute('data-theme');
      setTheme(theme);
      updateDropdownUI();
      dropdown.classList.remove('active');
    });
  });
  
  // Initial UI update
  updateDropdownUI();
}

// Initialize dropdown when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initThemeDropdown);
} else {
  initThemeDropdown();
}
