import daisyui from 'daisyui';

/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}', './src/app.html'],
	theme: {
		extend: {
			fontFamily: {
				sans: ['Inter', 'system-ui', 'sans-serif'],
				mono: ['Inter', 'system-ui', 'sans-serif'],
			},
			fontSize: {
				xs: ['0.8rem', { lineHeight: '1.2rem' }],
				sm: ['0.9rem', { lineHeight: '1.4rem' }],
				base: ['1.05rem', { lineHeight: '1.6rem' }],
				lg: ['1.2rem', { lineHeight: '1.7rem' }],
				xl: ['1.4rem', { lineHeight: '1.8rem' }],
				'2xl': ['1.6rem', { lineHeight: '2rem' }],
			},
		},
	},
	plugins: [daisyui],
	daisyui: {
		themes: ['corporate'],
	},
};
