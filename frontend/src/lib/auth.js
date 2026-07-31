
import { writable } from 'svelte/store'
import { browser } from '$app/environment'

// Initialize safely depending on whether we are in the browser or server
const initialWorker = browser
	? JSON.parse(localStorage.getItem('worker') || 'null')
	: null;

export const currentWorker = writable(initialWorker)

currentWorker.subscribe(worker => {
	// If SvelteKit is rendering this on the backend server, stop here!
	if (!browser) return;

	if (worker) {
		localStorage.setItem('worker', JSON.stringify(worker))
		localStorage.setItem('auth_token', worker.token || '')
	} else {
		localStorage.removeItem('worker')
		localStorage.removeItem('auth_token')
	}
})

// Send the session token on every API call.
export function authFetch(path, options = {}) {
	const token = browser ? localStorage.getItem('auth_token') || '' : '';
	return fetch(path, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			'X-Auth-Token': token,
			...(options.headers || {})
		}
	});
}

// Reject a worker record from the login response to only keep what we
// display, and never persist it.
export function logout() {
	currentWorker.set(null)
}

// The backend requires X-Auth-Token on every /api request. Many pages use
// plain fetch() with no header, which would get 401s. Patch window.fetch
// once (browser only) so the token is attached to any API request
// automatically, and a 401 clears the session (the layout then redirects
// to /login). This keeps every call site working without editing each one.
if (browser) {
	const originalFetch = window.fetch.bind(window);
	window.fetch = (input, init = {}) => {
		const url =
			typeof input === 'string'
				? input
				: input && input.url
					? input.url
					: '';
		if (!url.includes('/api/')) {
			return originalFetch(input, init);
		}

		const token = localStorage.getItem('auth_token') || '';
		const headers = new Headers(
			init.headers || (input instanceof Request ? input.headers : undefined),
		);
		if (token && !headers.has('X-Auth-Token')) {
			headers.set('X-Auth-Token', token);
		}
		init = { ...init, headers };

		return originalFetch(input, init).then((res) => {
			// Session expired / invalid: log out (unless this is the login
			// attempt itself, where 401 just means a wrong PIN).
			if (
				res.status === 401 &&
				!url.includes('/workers/login') &&
				!location.pathname.startsWith('/login')
			) {
				currentWorker.set(null);
			}
			return res;
		});
	};
}

