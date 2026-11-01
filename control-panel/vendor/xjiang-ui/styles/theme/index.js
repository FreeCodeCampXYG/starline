const setTheme = ( themeColor ) => {
  if (themeColor) {
    document.documentElement.style.setProperty(`--active-color`, themeColor);
  }
};

export const getTheme = () => {
};

export default {
  setTheme,
  getTheme
};