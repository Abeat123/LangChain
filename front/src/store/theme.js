import { defineStore } from 'pinia';

const DEFAULT_THEME = 'sky';
const storedTheme = localStorage.getItem('theme') || DEFAULT_THEME;

const THEMES = {
  sky: {
    name: 'Sky',
    backgroundColor: '#ffffff',
    textColor: '#1d2b53',
    primaryColor: '#4d6bfe',
    secondaryColor: '#d8e4ff',
    secondaryTextColor: '#41516d',
    mutedTextColor: '#5f7090',
    surfaceColor: 'rgba(255, 255, 255, 0.66)',
    surfaceStrong: 'rgba(255, 255, 255, 0.86)',
    borderColor: 'rgba(126, 152, 203, 0.2)',
    accentGlow: 'rgba(77, 107, 254, 0.16)',
    tabbarBackground: 'rgba(255, 255, 255, 0.74)',
    backgroundGradient: 'none',
    primaryStrong: '#2498ff',
  },
  mist: {
    name: 'Mist',
    backgroundColor: '#fbfcff',
    textColor: '#1c2b4a',
    primaryColor: '#5b7cff',
    secondaryColor: '#e4edff',
    secondaryTextColor: '#455574',
    mutedTextColor: '#697a98',
    surfaceColor: 'rgba(255, 255, 255, 0.74)',
    surfaceStrong: 'rgba(255, 255, 255, 0.92)',
    borderColor: 'rgba(144, 165, 208, 0.22)',
    accentGlow: 'rgba(91, 124, 255, 0.14)',
    tabbarBackground: 'rgba(255, 255, 255, 0.82)',
    backgroundGradient: 'none',
    primaryStrong: '#2d8dff',
  },
  dawn: {
    name: 'Dawn',
    backgroundColor: '#fffdf8',
    textColor: '#2a2d45',
    primaryColor: '#4d6bfe',
    secondaryColor: '#ffe6d6',
    secondaryTextColor: '#5a5570',
    mutedTextColor: '#80788f',
    surfaceColor: 'rgba(255, 255, 255, 0.76)',
    surfaceStrong: 'rgba(255, 255, 255, 0.94)',
    borderColor: 'rgba(196, 171, 160, 0.22)',
    accentGlow: 'rgba(255, 170, 135, 0.14)',
    tabbarBackground: 'rgba(255, 255, 255, 0.84)',
    backgroundGradient: 'none',
    primaryStrong: '#ff8a4c',
  },
  sage: {
    name: 'Sage',
    backgroundColor: '#fbfdfb',
    textColor: '#1f2e29',
    primaryColor: '#4d8a73',
    secondaryColor: '#dcefe6',
    secondaryTextColor: '#425c53',
    mutedTextColor: '#60786f',
    surfaceColor: 'rgba(255, 255, 255, 0.74)',
    surfaceStrong: 'rgba(255, 255, 255, 0.92)',
    borderColor: 'rgba(133, 167, 151, 0.22)',
    accentGlow: 'rgba(77, 138, 115, 0.14)',
    tabbarBackground: 'rgba(255, 255, 255, 0.82)',
    backgroundGradient: 'none',
    primaryStrong: '#2f9a73',
  },
};

const applyThemeVars = (theme) => {
  document.documentElement.style.setProperty('--background-color', theme.backgroundColor);
  document.documentElement.style.setProperty('--text-color', theme.textColor);
  document.documentElement.style.setProperty('--primary-color', theme.primaryColor);
  document.documentElement.style.setProperty('--primary-strong', theme.primaryStrong);
  document.documentElement.style.setProperty('--secondary-color', theme.secondaryColor);
  document.documentElement.style.setProperty('--secondary-text-color', theme.secondaryTextColor);
  document.documentElement.style.setProperty('--muted-text-color', theme.mutedTextColor);
  document.documentElement.style.setProperty('--surface-color', theme.surfaceColor);
  document.documentElement.style.setProperty('--surface-strong', theme.surfaceStrong);
  document.documentElement.style.setProperty('--border-color', theme.borderColor);
  document.documentElement.style.setProperty('--accent-glow', theme.accentGlow);
  document.documentElement.style.setProperty('--tabbar-background', theme.tabbarBackground);
  document.documentElement.style.setProperty('--background-gradient', theme.backgroundGradient);
};

export const useThemeStore = defineStore('theme', {
  state: () => ({
    currentTheme: storedTheme,
    themes: THEMES,
  }),

  getters: {
    getCurrentTheme: (state) => state.currentTheme,
    getThemeConfig: (state) => state.themes[state.currentTheme] || state.themes[DEFAULT_THEME],
    getAllThemes: (state) =>
      Object.keys(state.themes).map((key) => ({
        id: key,
        name: state.themes[key].name,
        primaryColor: state.themes[key].primaryColor,
      })),
  },

  actions: {
    setTheme(themeName) {
      const nextTheme = this.themes[themeName] ? themeName : DEFAULT_THEME;
      this.currentTheme = nextTheme;
      localStorage.setItem('theme', nextTheme);
      this.applyTheme();
    },

    applyTheme() {
      const theme = this.themes[this.currentTheme] || this.themes[DEFAULT_THEME];
      applyThemeVars(theme);
    },

    initTheme() {
      if (!this.themes[this.currentTheme]) {
        this.currentTheme = DEFAULT_THEME;
        localStorage.setItem('theme', this.currentTheme);
      }
      this.applyTheme();
    },
  },
});
