const plugin = require('tailwindcss/plugin')

module.exports = {
  purge: {
    enabled: process.env.NODE_ENV === "production",
    content: [
     './apps/**/*.html',
     './apps/**/*.js',
    ],
    options: {
      whitelistPatterns: [/^alert-/],
    },
  },
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: { },
  },
  variants: {
    extend: {
      backgroundColor: ['disabled'],
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    plugin(function({ addBase, config }) {
      addBase({
        'body': { color: config('theme.colors.gray.700') },
      })
    }),
  ],
}
