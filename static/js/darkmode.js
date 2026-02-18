// Dark mode toggle — persists preference to localStorage
(function () {
  const html = document.documentElement;
  const key = 'qr-attendance-dark';

  // Apply saved preference (or system preference)
  if (localStorage.getItem(key) === 'true' ||
      (!localStorage.getItem(key) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    html.classList.add('dark');
  }

  window.toggleDarkMode = function () {
    html.classList.toggle('dark');
    localStorage.setItem(key, html.classList.contains('dark'));
  };
})();
