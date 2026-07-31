// Build-time CSS compilation + asset vendoring for the offline SPA.
// 1. Compiles Tailwind v3 + DaisyUI v4 (theme: corporate) + autoprefixer -> static/app.css
// 2. Copies the self-hosted Inter variable font subsets -> static/fonts/
// 3. Copies the Chart.js 4.4.7 UMD build -> static/chart.umd.min.js
// Files land in SvelteKit's static/ dir, are copied verbatim into the build
// output, and are served by Flask at /app.css, /fonts/*, /chart.umd.min.js.
import { readFileSync, writeFileSync, copyFileSync, mkdirSync } from 'node:fs';
import postcss from 'postcss';
import tailwindcss from 'tailwindcss';
import autoprefixer from 'autoprefixer';

const from = 'src/styles/app.css';
const css = readFileSync(from, 'utf8');
const result = await postcss([tailwindcss, autoprefixer]).process(css, {
	from,
	to: 'static/app.css'
});

// daisyui v4 generates its theme CSS (e.g. [data-theme=corporate]) only for
// classes present in the scanned content files; the `data-theme` attribute
// is never picked up by Tailwind's content scan. Extract the theme block
// from the pre-built full.css and append it so the corporate palette applies.
const fullCss = readFileSync('node_modules/daisyui/dist/full.css', 'utf8');
const themeMatch = fullCss.match(/\[data-theme=corporate\]\s*\{[\s\S]*?\n\}/);
let out = result.css;
if (themeMatch) {
	out += '\n' + themeMatch[0] + '\n';
	console.log('corporate theme appended');
} else {
	console.warn('WARNING: corporate theme block not found in daisyui full.css');
}

writeFileSync('static/app.css', out);
console.log(`app.css generated (${out.length} bytes)`);

mkdirSync('static/fonts', { recursive: true });

const assets = [
	['node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2', 'static/fonts/inter-latin-wght-normal.woff2'],
	['node_modules/@fontsource-variable/inter/files/inter-latin-ext-wght-normal.woff2', 'static/fonts/inter-latin-ext-wght-normal.woff2'],
	['node_modules/chart.js/dist/chart.umd.js', 'static/chart.umd.min.js'],
];
for (const [src, dest] of assets) {
	copyFileSync(src, dest);
	console.log(`vendored ${src} -> ${dest}`);
}
