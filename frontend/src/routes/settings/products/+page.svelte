<script>
	import { onMount } from "svelte";
	import {
		Box,
		Plus,
		Edit,
		Power,
		X,
		Check,
		Search,
		ArrowUpDown,
	} from "@lucide/svelte";
	import { BASE } from "$lib/config";

	let products = $state([]);
	let categories = $state([]);
	let error = $state("");
	let loading = $state(true);
	let pageError = $state("");
	let editingBarcode = $state(null);

	let searchQuery = $state("");
	let filterCategory = $state("");
	let filterLowStock = $state(false);
	let sortField = $state("name");
	let sortDir = $state("asc");

	let filteredProducts = $derived.by(() => {
		let result = products;

		// Search by name or barcode
		if (searchQuery.trim()) {
			const q = searchQuery.toLowerCase();
			result = result.filter(
				(p) =>
					p.name.toLowerCase().includes(q) ||
					(p.barcode &&
						p.barcode
							.toLowerCase()
							.includes(q)),
			);
		}

		// Filter by category
		if (filterCategory) {
			result = result.filter(
				(p) => p.category_id == filterCategory,
			);
		}

		// Filter low stock only
		if (filterLowStock) {
			result = result.filter(
				(p) => p.quantity <= p.min_stock,
			);
		}

		// Sort
		result = [...result].sort((a, b) => {
			let cmp = 0;
			switch (sortField) {
				case "name":
					cmp = a.name.localeCompare(b.name);
					break;
				case "sell_price":
					cmp =
						(parseFloat(a.sell_price) ||
							0) -
						(parseFloat(b.sell_price) || 0);
					break;
				case "quantity":
					cmp =
						(a.quantity || 0) -
						(b.quantity || 0);
					break;
				case "cost_price":
					cmp =
						(parseFloat(a.cost_price) ||
							0) -
						(parseFloat(b.cost_price) || 0);
					break;
			}
			return sortDir === "asc" ? cmp : -cmp;
		});

		return result;
	});

	let barcode = $state("");
	let name = $state("");
	let category_id = $state("");
	let cost_price = $state("");
	let sell_price = $state("");
	let quantity = $state("");
	let min_stock = $state(5);
	let description = $state("");

	onMount(async () => {
		await load();
	});

	async function load() {
		try {
			const [p, c] = await Promise.all([
				fetch(`${BASE}/products`).then((r) => r.json()),
				fetch(`${BASE}/categories`).then((r) =>
					r.json(),
				),
			]);
			products = p;
			categories = c;
		} catch (e) {
			pageError = "Erreur lors du chargement des produits";
		} finally {
			loading = false;
		}
	}

	async function handleSubmit() {
		if (!name.trim() || !sell_price) {
			error = "Le nom et le prix de vente sont obligatoires";
			return;
		}
		if (!editingBarcode && !barcode.trim()) {
			error = "Le code-barres est obligatoire";
			return;
		}
		error = "";

		if (editingBarcode) {
			await fetch(`${BASE}/products/${editingBarcode}`, {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					name,
					category_id: category_id || null,
					sell_price: parseFloat(sell_price),
					min_stock: parseInt(min_stock),
					description,
				}),
			});
		} else {
			const res = await fetch(`${BASE}/products`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					barcode,
					name,
					category_id: category_id || null,
					cost_price: parseFloat(cost_price) || 0,
					sell_price: parseFloat(sell_price),
					quantity: parseInt(quantity) || 0,
					min_stock: parseInt(min_stock) || 5,
					description,
				}),
			});
			const data = await res.json();
			if (data.error) {
				error = data.error;
				return;
			}
		}
		resetForm();
		await load();
	}

	function startEdit(p) {
		editingBarcode = p.barcode;
		name = p.name;
		category_id = p.category_id || "";
		sell_price = p.sell_price;
		min_stock = p.min_stock;
		description = p.description ?? "";
		barcode = p.barcode;
		cost_price = p.cost_price;
		quantity = p.quantity;
		document.getElementById("addProductModal").showModal();
	}

	function resetForm() {
		editingBarcode = null;
		barcode = "";
		name = "";
		category_id = "";
		cost_price = "";
		sell_price = "";
		quantity = "";
		min_stock = 5;
		description = "";
		error = "";
		const modal = document.getElementById("addProductModal");
		if (modal && modal.close) modal.close();
	}

	async function toggleActive(p) {
		const endpoint = p.is_active ? "deactivate" : "reactivate";
		await fetch(`${BASE}/products/${p.barcode}/${endpoint}`, {
			method: "PUT",
		});
		await load();
	}
</script>

<div class="p-6 mx-auto space-y-6">
	<!-- Page Header -->
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4"
	>
		<div>
			<h1 class="text-2xl font-bold flex items-center gap-2">
				<Box class="text-primary" size="24" />
				Gestion du Catalogue Produits
			</h1>
			<p class="text-sm text-base-content/60">
				Gérez les articles, prix d'achat/vente,
				catégories et niveaux de stock d'alerte
			</p>
		</div>
		<button
			class="btn btn-primary font-bold gap-2"
			onclick={() => {
				resetForm();
				document.getElementById(
					"addProductModal",
				).showModal();
			}}
		>
			<Plus size="18" /> Nouveau Produit
		</button>
	</div>

	{#if loading}
		<div class="flex justify-center p-12">
			<span
				class="loading loading-spinner loading-lg text-primary"
			></span>
		</div>
	{:else if pageError}
		<div class="alert alert-error shadow-lg">{pageError}</div>
	{/if}

	<!-- Modal Dialog for Add/Edit -->
	<dialog id="addProductModal" class="modal">
		<div class="modal-box max-w-2xl bg-base-100 shadow-2xl">
			<button
				class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
				onclick={resetForm}
			>
				<X size="16" />
			</button>

			<h3
				class="font-bold text-lg mb-4 flex items-center gap-2"
			>
				<Box class="text-primary" size="20" />
				{editingBarcode
					? "Modifier le Produit"
					: "Nouveau Produit"}
			</h3>

			{#if error}
				<div class="alert alert-error mb-4">
					{error}
				</div>
			{/if}

			<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
				<div class="form-control">
					<label
						class="label font-semibold"
						for="prod-barcode"
						>Code-Barres *</label
					>
					<input
						id="prod-barcode"
						class="input input-bordered font-mono"
						placeholder="ex: 619123456789"
						bind:value={barcode}
						disabled={!!editingBarcode}
					/>
				</div>

				<div class="form-control">
					<label
						class="label font-semibold"
						for="prod-name"
						>Nom du Produit *</label
					>
					<input
						id="prod-name"
						class="input input-bordered"
						placeholder="ex: Tournevis Philips 6x100"
						bind:value={name}
					/>
				</div>

				<div class="form-control">
					<label
						class="label font-semibold"
						for="prod-cat">Catégorie</label
					>
					<select
						id="prod-cat"
						class="select select-bordered"
						bind:value={category_id}
					>
						<option value=""
							>Sans catégorie</option
						>
						{#each categories as c}
							<option value={c.id}
								>{c.name}</option
							>
						{/each}
					</select>
				</div>

				<div class="form-control">
					<label
						class="label font-semibold"
						for="prod-cost"
						>Prix d'Achat (DT)</label
					>
					<input
						id="prod-cost"
						class="input input-bordered font-mono"
						type="number"
						step="0.001"
						bind:value={cost_price}
						disabled={!!editingBarcode}
						placeholder="0.000"
					/>
				</div>

				<div class="form-control">
					<label
						class="label font-semibold"
						for="prod-sell"
						>Prix de Vente (DT) *</label
					>
					<input
						id="prod-sell"
						class="input input-bordered font-mono"
						type="number"
						step="0.001"
						bind:value={sell_price}
						placeholder="0.000"
					/>
				</div>

				<div class="form-control">
					<label
						class="label font-semibold"
						for="prod-qty"
						>Quantité Initiale en Stock</label
					>
					<input
						id="prod-qty"
						class="input input-bordered font-mono"
						type="number"
						bind:value={quantity}
						disabled={!!editingBarcode}
						placeholder="0"
					/>
				</div>

				<div class="form-control">
					<label
						class="label font-semibold"
						for="prod-min"
						>Stock Alerte Minimum</label
					>
					<input
						id="prod-min"
						class="input input-bordered font-mono"
						type="number"
						bind:value={min_stock}
					/>
				</div>

				<div
					class="form-control col-span-1 md:col-span-2"
				>
					<label
						class="label font-semibold"
						for="prod-desc"
						>Description / Référence</label
					>
					<input
						id="prod-desc"
						class="input input-bordered"
						placeholder="Notes optionnelles..."
						bind:value={description}
					/>
				</div>
			</div>

			<div class="modal-action">
				<button
					class="btn btn-ghost"
					onclick={resetForm}>Annuler</button
				>
				<button
					class="btn btn-primary font-bold gap-2"
					onclick={handleSubmit}
				>
					<Check size="18" />
					{editingBarcode
						? "Enregistrer"
						: "Créer le Produit"}
				</button>
			</div>
		</div>
		<div class="modal-backdrop" onclick={resetForm}></div>
	</dialog>

	<!-- Search & Filters -->
	<div class="card bg-base-100 shadow-md border border-base-200 p-4">
		<div class="flex flex-col md:flex-row gap-3 items-center">
			<div class="relative w-full md:w-72">
				<Search
					class="absolute left-3 top-2.5 text-base-content/40"
					size="16"
				/>
				<input
					type="text"
					class="input input-sm input-bordered w-full pl-9"
					placeholder="Rechercher par nom ou code-barres..."
					bind:value={searchQuery}
				/>
				{#if searchQuery}
					<button
						class="btn btn-xs btn-ghost absolute right-1 top-1.5"
						onclick={() =>
							(searchQuery = "")}
					>
						<X size="14" />
					</button>
				{/if}
			</div>

			<select
				class="select select-sm select-bordered w-full md:w-44"
				bind:value={filterCategory}
			>
				<option value="">Toutes les catégories</option>
				{#each categories as c}
					<option value={c.id}>{c.name}</option>
				{/each}
			</select>

			<button
				class="btn btn-sm {filterLowStock
					? 'btn-error'
					: 'btn-outline'} gap-1.5"
				onclick={() =>
					(filterLowStock = !filterLowStock)}
			>
				Stock faible {filterLowStock ? "✓" : ""}
			</button>

			<div class="flex-1"></div>

			<div class="flex items-center gap-2">
				<span
					class="text-xs text-base-content/60 font-medium"
					>Trier par:</span
				>
				<select
					class="select select-xs select-bordered w-32"
					bind:value={sortField}
				>
					<option value="name">Nom</option>
					<option value="sell_price"
						>Prix vente</option
					>
					<option value="quantity">Stock</option>
					<option value="cost_price"
						>Prix achat</option
					>
				</select>
				<button
					class="btn btn-xs btn-ghost"
					onclick={() =>
						(sortDir =
							sortDir === "asc"
								? "desc"
								: "asc")}
				>
					<ArrowUpDown size="14" />
					{sortDir === "asc" ? "↑" : "↓"}
				</button>
			</div>
		</div>
	</div>

	<!-- Table -->
	<div
		class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden"
	>
		<div class="card-body p-0">
			{#if filteredProducts.length > 0}
				<div class="overflow-x-auto">
					<table class="table w-full">
						<thead>
							<tr class="">
								<th
									>Code-Barres</th
								>
								<th
									>Nom
									Produit</th
								>
								<th
									>Catégorie</th
								>
								<th
									>Prix
									d'Achat</th
								>
								<th
									>Prix de
									Vente</th
								>
								<th>Stock</th>
								<th
									>Alerte
									Min</th
								>
								<th
									class="text-center"
									>Actions</th
								>
							</tr>
						</thead>
						<tbody>
							{#each filteredProducts as p}
								<tr>
									<td
										class="font-mono text-xs font-bold"
										>{p.barcode}</td
									>
									<td
										class="font-bold"
										>{p.name}</td
									>
									<td
										><span
											class="badge badge-ghost font-medium"
											>{p.category ??
												"-"}</span
										></td
									>
									<td
										class="font-mono text-sm"
										>{parseFloat(
											p.cost_price,
										).toFixed(
											3,
										)}
										DT</td
									>
									<td
										class="font-mono text-sm font-bold text-success"
										>{parseFloat(
											p.sell_price,
										).toFixed(
											3,
										)}
										DT</td
									>
									<td>
										<span
											class="badge {p.quantity <=
											p.min_stock
												? 'badge-error text-white font-bold'
												: 'badge-success text-white font-bold'}"
										>
											{p.quantity}
										</span>
									</td>
									<td
										class="font-mono text-xs text-center"
										>{p.min_stock}</td
									>
									<td
										class="flex justify-center gap-1"
									>
										<button
											class="btn btn-xs btn-outline font-semibold gap-1"
											onclick={() =>
												startEdit(
													p,
												)}
										>
											<Edit
												size="12"
											/>
											Modifier
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<div
					class="p-12 text-center text-base-content/40"
				>
					Aucun produit enregistré
				</div>
			{/if}
		</div>
	</div>
</div>
