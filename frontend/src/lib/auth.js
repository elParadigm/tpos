
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
	} else {
		localStorage.removeItem('worker')
	}
})

export function logout() {
	currentWorker.set(null)
}

