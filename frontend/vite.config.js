import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	css: {
		// Tailwind/DaisyUI are compiled to static/app.css by scripts/build-css.mjs.
		// Keep Vite's own CSS pipeline neutral so component <style> blocks are
		// not re-processed by the postcss.config.js tailwind/autoprefixer plugins.
		postcss: {
			plugins: []
		}
	}
});
