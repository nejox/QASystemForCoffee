/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#202e50',
        'accent': '#ff6a00',
        'primary-dark': '#19243f',
      }
    },
  },
  plugins: [],
}
