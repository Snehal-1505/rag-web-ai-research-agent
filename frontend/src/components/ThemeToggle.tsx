import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      type="button"
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
      className="p-2 rounded-xl transition-all duration-200 border border-loomi-border dark:border-loomi-dark-border bg-loomi-sand/50 dark:bg-loomi-dark-surface hover:bg-loomi-sand dark:hover:bg-loomi-dark-elevated text-loomi-secondary dark:text-loomi-dark-muted hover:text-loomi-ink dark:hover:text-loomi-dark-text focus:outline-none focus:ring-2 focus:ring-loomi-coral/40"
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? (
        <Moon className="w-4 h-4 transition-transform duration-200 hover:-rotate-12" />
      ) : (
        <Sun className="w-4 h-4 text-amber-400 transition-transform duration-200 hover:rotate-45" />
      )}
    </button>
  );
};
