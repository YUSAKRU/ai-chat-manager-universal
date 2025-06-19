/**
 * 🌓 AI ORCHESTRATOR THEME MANAGER v2.0
 * Modern theme management with dark/light mode support
 */

class ThemeManager {
  constructor() {
    this.themes = ['light', 'dark'];
    this.storageKey = 'ai-orchestrator-theme';
    this.defaultTheme = 'light';
    this.currentTheme = this.getStoredTheme() || this.getSystemTheme() || this.defaultTheme;
    
    this.init();
  }

  /**
   * Initialize theme manager
   */
  init() {
    this.applyTheme(this.currentTheme);
    this.createToggleButton();
    this.bindEvents();
    this.watchSystemTheme();
    
    // Add smooth transition after initial load
    setTimeout(() => {
      document.documentElement.style.transition = 'background-color 300ms ease, color 300ms ease';
    }, 100);
  }

  /**
   * Get stored theme from localStorage
   */
  getStoredTheme() {
    try {
      return localStorage.getItem(this.storageKey);
    } catch (error) {
      console.warn('Theme Manager: localStorage not available');
      return null;
    }
  }

  /**
   * Get system theme preference
   */
  getSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  /**
   * Store theme preference
   */
  storeTheme(theme) {
    try {
      localStorage.setItem(this.storageKey, theme);
    } catch (error) {
      console.warn('Theme Manager: Could not store theme preference');
    }
  }

  /**
   * Apply theme to document
   */
  applyTheme(theme) {
    if (!this.themes.includes(theme)) {
      theme = this.defaultTheme;
    }

    // Remove all theme classes
    this.themes.forEach(t => {
      document.documentElement.removeAttribute(`data-theme`);
    });

    // Apply new theme
    if (theme !== 'light') {
      document.documentElement.setAttribute('data-theme', theme);
    }

    this.currentTheme = theme;
    this.storeTheme(theme);
    this.updateToggleButton();
    
    // Dispatch theme change event
    window.dispatchEvent(new CustomEvent('themeChanged', {
      detail: { theme: theme }
    }));
  }

  /**
   * Toggle between themes
   */
  toggle() {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.applyTheme(newTheme);
    
    // Add small haptic feedback on mobile
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }
  }

  /**
   * Set specific theme
   */
  setTheme(theme) {
    this.applyTheme(theme);
  }

  /**
   * Get current theme
   */
  getTheme() {
    return this.currentTheme;
  }

  /**
   * Check if dark mode is active
   */
  isDark() {
    return this.currentTheme === 'dark';
  }

  /**
   * Create theme toggle button
   */
  createToggleButton() {
    // Check if toggle already exists
    if (document.querySelector('.theme-toggle-wrapper')) {
      return;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'theme-toggle-wrapper';
    wrapper.innerHTML = `
      <button class="theme-toggle" 
              aria-label="Toggle theme" 
              title="Switch between light and dark mode">
        <span class="theme-toggle-icon">
          <svg class="sun-icon" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path d="M8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm0 1a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM8 0a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 0zm0 13a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 13zm8-5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2a.5.5 0 0 1 .5.5zM3 8a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2A.5.5 0 0 1 3 8zm10.657-5.657a.5.5 0 0 1 0 .707l-1.414 1.415a.5.5 0 1 1-.707-.708l1.414-1.414a.5.5 0 0 1 .707 0zm-9.193 9.193a.5.5 0 0 1 0 .707L3.05 13.657a.5.5 0 0 1-.707-.707l1.414-1.414a.5.5 0 0 1 .707 0zm9.193 2.121a.5.5 0 0 1-.707 0l-1.414-1.414a.5.5 0 0 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .707zM4.464 4.465a.5.5 0 0 1-.707 0L2.343 3.05a.5.5 0 1 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .708z"/>
          </svg>
          <svg class="moon-icon" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path d="M6 .278a.768.768 0 0 1 .08.858 7.208 7.208 0 0 0-.878 3.46c0 4.021 3.278 7.277 7.318 7.277.527 0 1.04-.055 1.533-.16a.787.787 0 0 1 .81.316.733.733 0 0 1-.031.893A8.349 8.349 0 0 1 8.344 16C3.734 16 0 12.286 0 7.71 0 4.266 2.114 1.312 5.124.06A.752.752 0 0 1 6 .278z"/>
          </svg>
        </span>
      </button>
    `;

    // Add CSS for toggle button
    this.addToggleStyles();

    // Insert into navbar or header
    const navbar = document.querySelector('.navbar .navbar-nav');
    const header = document.querySelector('nav .container-fluid');
    
    if (navbar) {
      navbar.appendChild(wrapper);
    } else if (header) {
      header.appendChild(wrapper);
    } else {
      // Fallback: add to body
      document.body.appendChild(wrapper);
      wrapper.style.position = 'fixed';
      wrapper.style.top = '20px';
      wrapper.style.right = '20px';
      wrapper.style.zIndex = '1000';
    }

    this.updateToggleButton();
  }

  /**
   * Add CSS styles for toggle button
   */
  addToggleStyles() {
    if (document.querySelector('#theme-toggle-styles')) {
      return;
    }

    const styles = document.createElement('style');
    styles.id = 'theme-toggle-styles';
    styles.innerHTML = `
      .theme-toggle-wrapper {
        display: flex;
        align-items: center;
        margin-left: var(--space-4, 1rem);
      }

      .theme-toggle {
        position: relative;
        width: 44px;
        height: 24px;
        border: none;
        border-radius: var(--radius-full, 12px);
        background: var(--border-secondary, #cbd5e1);
        cursor: pointer;
        transition: all var(--transition-base, 300ms ease);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
      }

      .theme-toggle:hover {
        transform: scale(1.05);
        box-shadow: var(--shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1));
      }

      .theme-toggle:focus-visible {
        outline: 2px solid var(--border-focus, #3b82f6);
        outline-offset: 2px;
      }

      .theme-toggle-icon {
        position: relative;
        width: 16px;
        height: 16px;
        transition: transform var(--transition-base, 300ms ease);
      }

      .sun-icon, .moon-icon {
        position: absolute;
        top: 0;
        left: 0;
        color: var(--text-secondary, #475569);
        transition: all var(--transition-base, 300ms ease);
      }

      .sun-icon {
        opacity: 1;
        transform: scale(1) rotate(0deg);
      }

      .moon-icon {
        opacity: 0;
        transform: scale(0.5) rotate(-90deg);
      }

      [data-theme="dark"] .theme-toggle {
        background: var(--primary-500, #3b82f6);
      }

      [data-theme="dark"] .sun-icon {
        opacity: 0;
        transform: scale(0.5) rotate(90deg);
      }

      [data-theme="dark"] .moon-icon {
        opacity: 1;
        transform: scale(1) rotate(0deg);
        color: white;
      }

      /* Mobile adjustments */
      @media (max-width: 768px) {
        .theme-toggle-wrapper {
          margin-left: var(--space-2, 0.5rem);
        }
        
        .theme-toggle {
          width: 40px;
          height: 22px;
        }
      }
    `;

    document.head.appendChild(styles);
  }

  /**
   * Update toggle button state
   */
  updateToggleButton() {
    const toggle = document.querySelector('.theme-toggle');
    if (toggle) {
      const isDark = this.currentTheme === 'dark';
      toggle.setAttribute('aria-label', `Switch to ${isDark ? 'light' : 'dark'} mode`);
      toggle.title = `Switch to ${isDark ? 'light' : 'dark'} mode`;
    }
  }

  /**
   * Bind event listeners
   */
  bindEvents() {
    // Toggle button click
    document.addEventListener('click', (e) => {
      if (e.target.closest('.theme-toggle')) {
        e.preventDefault();
        this.toggle();
      }
    });

    // Keyboard support
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'L') {
        e.preventDefault();
        this.toggle();
      }
    });

    // Update meta theme-color for mobile browsers
    window.addEventListener('themeChanged', (e) => {
      this.updateMetaThemeColor(e.detail.theme);
    });
  }

  /**
   * Watch for system theme changes
   */
  watchSystemTheme() {
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      mediaQuery.addEventListener('change', (e) => {
        // Only auto-switch if no stored preference
        if (!this.getStoredTheme()) {
          this.applyTheme(e.matches ? 'dark' : 'light');
        }
      });
    }
  }

  /**
   * Update meta theme-color for mobile
   */
  updateMetaThemeColor(theme) {
    let themeColorMeta = document.querySelector('meta[name="theme-color"]');
    
    if (!themeColorMeta) {
      themeColorMeta = document.createElement('meta');
      themeColorMeta.name = 'theme-color';
      document.head.appendChild(themeColorMeta);
    }

    const colors = {
      light: '#ffffff',
      dark: '#0f172a'
    };

    themeColorMeta.content = colors[theme] || colors.light;
  }

  /**
   * Get theme stats for debugging
   */
  getStats() {
    return {
      current: this.currentTheme,
      stored: this.getStoredTheme(),
      system: this.getSystemTheme(),
      available: this.themes
    };
  }

  /**
   * Reset to system preference
   */
  resetToSystem() {
    localStorage.removeItem(this.storageKey);
    this.applyTheme(this.getSystemTheme());
  }
}

// Auto-initialize theme manager
let themeManager;

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    themeManager = new ThemeManager();
  });
} else {
  themeManager = new ThemeManager();
}

// Export for global access
window.themeManager = themeManager;

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ThemeManager;
} 