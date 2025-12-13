/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'research-dark': '#0f0f11',
                'research-panel': '#1a1a1d',
                'research-blue': '#3b82f6',
                'research-text': '#e5e7eb',
            },
            fontFamily: {
                'sans': ['Inter', 'system-ui', 'sans-serif'],
            }
        },
    },
    plugins: [],
}
