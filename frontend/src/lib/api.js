const BASE = 'http://127.0.0.1:5000/api'

export async function getCategories() {
	const res = await fetch(`${BASE}/categories`)
	return res.json()
}

export async function createCategory(name, description) {
	const res = await fetch(`${BASE}/categories`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name, description })
	})
	return res.json()
}

export async function deleteCategory(id) {
	const res = await fetch(`${BASE}/categories/${id}`, { method: 'DELETE' })
	return res.json()
}
