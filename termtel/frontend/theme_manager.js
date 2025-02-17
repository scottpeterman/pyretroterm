class ThemeManager {
   constructor() {
       if (window.themeManager) {
           return window.themeManager;
       }
       window.themeManager = this;

       console.log('ThemeManager: Initializing...');
       this.styleElement = document.createElement('style');
       document.head.appendChild(this.styleElement);
       this.initialized = false;

       // Initialize immediately if possible
       this.initialize();

       // Connect to the WebChannel
       this.connectToBackend();
   }

   connectToBackend() {
       console.log('ThemeManager: Connecting to backend...');

       initializeSharedWebChannel((channel) => {
           console.log('ThemeManager: WebChannel initialized');
           if (channel.objects.messageBridge?.system_message) {
               // Set up message handler
               channel.objects.messageBridge.system_message.connect(this.handleSystemMessage.bind(this));
               console.log('ThemeManager: Connected to message bridge');

               // Request saved theme
               const initMessage = JSON.stringify({
                   target: "system",
                   type: "theme_manager_ready",
                   payload: null
               });
               channel.objects.messageBridge.handle_message(initMessage);
           } else {
               console.warn('ThemeManager: Message bridge not available in channel');
           }
       });
   }

   handleSystemMessage(target, type, payload) {
       console.log('ThemeManager: Received system message:', { target, type, payload });
       if (target === 'system' && type === 'theme') {
           console.log('ThemeManager: Processing theme change request');
           this.applyTheme(payload, true);
           // Update select element if it exists
           const themeSelect = document.getElementById('theme-select');
           if (themeSelect && themeSelect.value !== payload) {
               themeSelect.value = payload;
           }
       } else {
           console.log('ThemeManager: Ignoring non-theme message:', { target, type });
       }
   }

   initialize() {
       if (this.initialized) {
           console.warn('ThemeManager: Already initialized!');
           return;
       }

       console.log('ThemeManager: Starting initialization');

       // Verify theme constants are available
       if (!window.THEME_STYLES || !window.TERMINAL_THEMES || !window.THEME_COLORS) {
           console.error('ThemeManager: Theme constants are not loaded!', {
               styles: !!window.THEME_STYLES,
               terminal: !!window.TERMINAL_THEMES,
               colors: !!window.THEME_COLORS
           });
           return;
       }

       // Set up theme selector
       const themeSelect = document.getElementById('theme-select');
       if (themeSelect) {
           console.log('ThemeManager: Found theme selector');

           // Remove any existing listeners before adding new one
           const newListener = (e) => {
               console.log('ThemeManager: Theme selection changed to:', e.target.value);
               this.applyTheme(e.target.value, false);
           };
           themeSelect.removeEventListener('change', newListener);
           themeSelect.addEventListener('change', newListener);
       } else {
           console.error('ThemeManager: Theme selector element not found!');
       }

       this.initialized = true;
       console.log('ThemeManager: Initialization complete');
   }

   applyTheme(themeName, fromBackend = false) {
       console.log('ThemeManager: Applying theme:', themeName, 'from backend:', fromBackend);

       if (!window.THEME_STYLES || !window.TERMINAL_THEMES) {
           console.error('ThemeManager: Theme constants are missing.');
           return;
       }

       // Apply the theme locally
       this.styleElement.textContent = THEME_STYLES[themeName];
       if (window.term) {
           window.term.setOption('theme', window.TERMINAL_THEMES[themeName]);
       }

       // Apply CSS variables for the theme
       const themeColors = window.THEME_COLORS[themeName];
       if (themeColors) {
           Object.entries(themeColors).forEach(([key, value]) => {
               document.documentElement.style.setProperty(key, value);
           });
       }

       // Update scrollbar styles dynamically
       this.updateScrollbarStyles(themeName);

       // Update dynamic UI elements
       this.updateDynamicElements();

       // Only send to backend if the change originated from frontend
       if (!fromBackend) {
           if (window.messageBridge?.handle_message) {
               console.log('ThemeManager: Sending theme change to backend:', themeName);
               const message = JSON.stringify({
                   target: "system",
                   type: "theme",
                   payload: themeName
               });
               window.messageBridge.handle_message(message);
           } else {
               console.warn('ThemeManager: Cannot send theme to backend - messageBridge not ready');
           }
       }

       // Save the current theme
       localStorage.setItem('preferredTheme', themeName);

       // Dispatch theme change event locally
       window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: themeName } }));
   }

   updateScrollbarStyles(themeName) {
       const theme = window.THEME_COLORS[themeName];
       if (!theme) return;

       const style = document.getElementById('scrollbar-style') || document.createElement('style');
       style.id = 'scrollbar-style';
       style.textContent = `
           ::-webkit-scrollbar {
               width: 8px;
               height: 8px;
           }
           ::-webkit-scrollbar-track {
               background: var(--scrollbar-track);
               border-radius: 4px;
           }
           ::-webkit-scrollbar-thumb {
               background: var(--scrollbar-thumb);
               border-radius: 4px;
           }
           ::-webkit-scrollbar-thumb:hover {
               background: var(--scrollbar-thumb-hover);
               transition: background-color 0.2s ease;
           }
       `;
       if (!style.parentNode) {
           document.head.appendChild(style);
       }
   }

   updateDynamicElements() {
       document.querySelectorAll('.hud-panel-title').forEach((el) => {
           el.style.color = 'var(--text-secondary)';
           el.style.background = 'var(--bg-primary)';
       });

       document.querySelectorAll('.hud-panel::before').forEach((el) => {
           el.style.background = 'var(--bg-secondary)';
           el.style.border = '1px solid var(--border-color)';
       });

       document.querySelectorAll('.tab').forEach((el) => {
           el.style.color = 'var(--text-primary)';
       });

       document.querySelectorAll('.tab.active').forEach((el) => {
           el.style.color = 'var(--accent-color)';
           el.style.borderBottom = '2px solid var(--accent-color)';
       });

       document.querySelectorAll('.chart-grid').forEach((el) => {
           el.style.backgroundImage = `
               linear-gradient(var(--grid-color) 1px, transparent 1px),
               linear-gradient(90deg, var(--grid-color) 1px, transparent 1px)
           `;
       });
   }

   getCurrentTheme() {
       return localStorage.getItem('preferredTheme') || 'cyber';
   }

   getTerminalTheme() {
       const theme = this.getCurrentTheme();
       console.log('ThemeManager: Getting terminal theme for:', theme);
       return TERMINAL_THEMES[theme];
   }
}

// Only create an instance if one doesn't exist
if (!window.themeManager) {
   new ThemeManager();
}

// Export the ThemeManager class (not instance) for module systems
if (typeof module !== 'undefined' && module.exports) {
   module.exports = ThemeManager;
}