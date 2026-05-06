import React from 'react';

const ThemeToggle = ({ theme, onToggle }) => (
  <button className="theme-toggle" onClick={onToggle} aria-label={`Cambiar a modo ${theme === 'dark' ? 'claro' : 'oscuro'}`}>
    <span className="theme-toggle-icon">{theme === 'dark' ? '\u2600\uFE0F' : '\u{1F319}'}</span>
    <span>{theme === 'dark' ? 'Claro' : 'Oscuro'}</span>
  </button>
);

export default ThemeToggle;
