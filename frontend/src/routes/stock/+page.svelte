<script>
	import { onMount } from "svelte";
	import { Warehouse, Plus, X, Check, CreditCard } from "@lucide/svelte";
	import { currentWorker } from "$lib/auth";

	import { BASE } from '$lib/config';

	let products = $state([]);
	let suppliers = $state([]);
	let unpaid = $state([]);
	let loading = $state(true);
	let pageError = $state('');

	let isDeliveryModalOpen = $state(false);

	let supplier_id = $state("");
	let due_date = $state("");
	let amount_paid = $state("");
	let notes = $state("");

	let items = $state([]);
	let newItem = $state({
		barcode: "",
		quantity: "",
		cost_price: "",
		suggested_sell_price: "",
	});

	let error = $state("");
	let success = $state("");
	let payingEntry = $state(null);
	let paymentAmount = $state("");
	let paymentNotes = $state("");

	// --- PRODUCT SEARCH DROPDOWN STATE ---
	let productSearchQuery = $state("");
	let productDropdownOpen = $state(false);

	let filteredProductsForDropdown = $derived(
		products
			.filter((p) => {
				if (!productSearchQuery.trim()) return true;
				const q = productSearchQuery.toLowerCase();
				return (
					p.name.toLowerCase().includes(q) ||
					(p.barcode &&
						p.barcode
							.toLowerCase()
							.includes(q))
				);
			})
			.slice(0, 50), // Limit to 50 results for performance
	);

	onMount(async () => {
		try {
			await Promise.all([
				loadProducts(),
				loadSuppliers(),
				loadUnpaid(),
			]);
		} catch (e) {
			pageError = 'Erreur de connexion au serveur';
			console.error(e);
		} finally {
			loading = false;
		}

		// Close dropdown when clicking outside
		const handleClickOutside = (e) => {
			if (
				!e.target.closest("#item-product-search") &&
				!e.target.closest(".product-dropdown")
			) {
				productDropdownOpen = false;
			}
		};
		document.addEventListener("click", handleClickOutside);

		return () => {
			document.removeEventListener(
				"click",
				handleClickOutside,
			);
		};
	});

	async function loadProducts() {
		const res = await fetch(`${BASE}/products`);
		products = await res.json();
	}

	async function loadSuppliers() {
		const res = await fetch(`${BASE}/suppliers`);
		suppliers = await res.json();
	}

	async function loadUnpaid() {
		const res = await fetch(`${BASE}/deliveries/unpaid`);
		unpaid = await res.json();
	}

	let totalDue = $derived(
		items
			.reduce((sum, item) => {
				const qty = parseFloat(item.quantity) || 0;
				const cost = parseFloat(item.cost_price) || 0;
				return sum + qty * cost;
			}, 0)
			.toFixed(3),
	);

	function addItem() {
		if (!newItem.barcode) {
			error = "Le produit est obligatoire";
			return;
		}
		if (!newItem.quantity || newItem.quantity <= 0) {
			error = "Veuillez saisir une quantité valide";
			return;
		}
		if (!newItem.cost_price || newItem.cost_price <= 0) {
			error = "Veuillez saisir un prix d'achat valide";
			return;
		}

		error = "";
		items = [...items, { ...newItem }];
		newItem = {
			barcode: "",
			quantity: "",
			cost_price: "",
			suggested_sell_price: "",
		};
		productSearchQuery = ""; // Reset search query after adding
	}

	function removeItem(index) {
		items = items.filter((_, i) => i !== index);
	}

	async function handleSubmit() {
		if (items.length === 0) {
			error = "Ajoutez au moins un produit à la livraison";
			return;
		}
		if (!supplier_id) {
			error = "Le fournisseur est obligatoire";
			return;
		}

		error = "";

		const payload = {
			supplier_id: parseInt(supplier_id),
			amount_due: parseFloat(totalDue),
			amount_paid: parseFloat(amount_paid) || 0,
			due_date: due_date || null,
			notes,
			created_by: $currentWorker?.id ?? null,
			items: items.map((item) => ({
				barcode: item.barcode,
				quantity: parseInt(item.quantity),
				cost_price: parseFloat(item.cost_price),
				suggested_sell_price:
					parseFloat(item.suggested_sell_price) ||
					null,
			})),
		};

		const res = await fetch(`${BASE}/deliveries`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(payload),
		});

		const data = await res.json();
		if (data.error) {
			error = data.error;
			return;
		}

		success = "Livraison enregistrée avec succès";
		isDeliveryModalOpen = false;
		resetForm();
		await loadUnpaid();
		setTimeout(() => (success = ""), 3000);
	}

	function resetForm() {
		supplier_id = "";
		due_date = "";
		amount_paid = "";
		notes = "";
		items = [];
		newItem = {
			barcode: "",
			quantity: "",
			cost_price: "",
			suggested_sell_price: "",
		};
		productSearchQuery = "";
		productDropdownOpen = false;
		error = "";
	}

	async function handlePayment() {
		if (!payingEntry) return;

		const deliveryId = payingEntry.delivery_id || payingEntry.id;
		const amount = parseFloat(paymentAmount);

		if (!deliveryId || isNaN(amount) || amount <= 0) return;

		try {
			const res = await fetch(
				`${BASE}/deliveries/${deliveryId}/payments`,
				{
					method: "POST",
					headers: {
						"Content-Type":
							"application/json",
					},
					body: JSON.stringify({
						amount: amount,
						notes: paymentNotes,
						created_by:
							$currentWorker?.id ?? 1,
					}),
				},
			);

			if (res.ok) {
				payingEntry = null;
				paymentAmount = "";
				paymentNotes = "";
				await loadUnpaid();
			} else {
				const data = await res.json();
				console.error("Payment error:", data);
				alert(data.error || "Échec du paiement");
			}
		} catch (e) {
			console.error("Network error:", e);
		}
	}

	function openDeliveryModal() {
		resetForm();
		isDeliveryModalOpen = true;
	}
</script>

<div class="p-6 mx-auto space-y-6">
	{#if loading}
		<div class="flex justify-center p-12">
			<span class="loading loading-spinner loading-lg text-primary"></span>
		</div>
	{:else if pageError}
		<div class="alert alert-error shadow-lg">{pageError}</div>
	{/if}

	<!-- Page Header -->
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4"
	>
		<div>
			<h1 class="text-2xl font-bold flex items-center gap-2">
				<Warehouse class="text-primary" size="24" />
				Gestion du Stock & Livraisons
			</h1>
			<p class="text-sm text-base-content/60">
				Enregistrez les nouvelles arrivées de stock
				fournisseurs et suivez les règlements
			</p>
		</div>
		<button
			class="btn btn-primary font-bold gap-2"
			onclick={openDeliveryModal}
		>
			<Plus size="18" /> Nouvelle Livraison Fournisseur
		</button>
	</div>

	{#if success}
		<div class="alert alert-success shadow-lg">{success}</div>
	{/if}

	<!-- Unpaid Deliveries Table -->
	<div
		class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden"
	>
		<div class="card-body p-0">
			<div
				class="p-4 bg-base-200 border-b border-base-300 font-bold text-sm"
			>
				Livraisons Fournisseurs Non Soldees / Échéances
			</div>
			{#if unpaid.length === 0}
				<div
					class="p-12 text-center text-base-content/40"
				>
					Aucune livraison en attente de paiement
				</div>
			{:else}
				<div class="overflow-x-auto">
					<table class="table  w-full">
						<thead>
							<tr>
								<th
									>Fournisseur</th
								>
								<th
									>Date
									Livraison</th
								>
								<th
									>Date
									Échéance</th
								>
								<th
									>Montant
									Total</th
								>
								<th
									>Reste à
									Payer</th
								>
								<th
									class="text-center"
									>Action</th
								>
							</tr>
						</thead>
						<tbody>
							{#each unpaid as entry}
								<tr
									class="hover"
								>
									<td
										class="font-bold"
										>{entry.supplier_name ??
											"Inconnu"}</td
									>
									<td
										class="font-mono text-xs"
										>{entry.delivery_date?.slice(
											0,
											10,
										)}</td
									>
									<td
										class={entry.due_date &&
										entry.due_date <
											new Date()
												.toISOString()
												.slice(
													0,
													10,
												)
											? "text-error font-bold"
											: ""}
									>
										{entry.due_date ??
											"-"}
									</td>
									<td
										class="font-mono"
										>{entry.amount_due}
										DT</td
									>
									<td
										class="text-error font-bold font-mono"
										>{entry.remaining}
										DT</td
									>
									<td
										class="text-center"
									>
										<button
											class="btn btn-sm btn-success text-white font-bold gap-1"
											onclick={() => {
												payingEntry =
													entry;
												paymentAmount =
													entry.remaining;
											}}
										>
											<CreditCard
												size="14"
											/>
											Régler
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	</div>
</div>

<!-- NEW DELIVERY MODAL -->
{#if isDeliveryModalOpen}
	<div class="modal modal-open">
		<div class="modal-box max-w-4xl relative">
			<button
				class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
				onclick={() => (isDeliveryModalOpen = false)}
			>
				<X size="16" />
			</button>

			<h3
				class="font-bold text-lg mb-4 flex items-center gap-2"
			>
				<Plus size="20" class="text-primary" />
				Enregistrer une Nouvelle Livraison
			</h3>

			{#if error}
				<div class="alert alert-error mb-4">
					{error}
				</div>
			{/if}

			<!-- Delivery Info -->
			<div
				class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 p-4 bg-base-200 rounded-lg"
			>
				<div class="form-control">
					<label
						class="label font-semibold"
						for="supplier-select"
						>Fournisseur *</label
					>
					<select
						id="supplier-select"
						class="select select-bordered w-full"
						bind:value={supplier_id}
					>
						<option value=""
							>Sélectionner un
							Fournisseur</option
						>
						{#each suppliers as s}
							<option value={s.id}
								>{s.name}</option
							>
						{/each}
					</select>
				</div>
				<div class="form-control">
					<label
						class="label font-semibold"
						for="due-date"
						>Date d'Échéance</label
					>
					<input
						id="due-date"
						class="input input-bordered w-full"
						type="date"
						bind:value={due_date}
					/>
				</div>
				<div class="form-control">
					<label
						class="label font-semibold"
						for="paid-amount"
						>Acompte / Montant Payé
						Immédiatement (DT)</label
					>
					<input
						id="paid-amount"
						class="input input-bordered w-full"
						type="number"
						step="0.1"
						bind:value={amount_paid}
						placeholder="0.000"
					/>
				</div>
				<div class="form-control">
					<label
						class="label font-semibold"
						for="delivery-notes"
						>Notes / N° Bon de Livraison</label
					>
					<input
						id="delivery-notes"
						class="input input-bordered w-full"
						bind:value={notes}
						placeholder="Notes optionnelles..."
					/>
				</div>
			</div>

			<!-- Add Item Line -->
			<h4 class="font-bold mb-2">
				Ajouter des Produits à la Livraison
			</h4>
			<div
				class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4 p-4 border border-base-300 rounded-lg"
			>
				<!-- SEARCHABLE PRODUCT DROPDOWN -->
				<!-- SEARCHABLE PRODUCT DROPDOWN -->
				<div class="form-control">
					<label
						class="label font-semibold"
						for="item-product-search"
						>Produit *</label
					>
					<div class="relative">
						<input
							id="item-product-search"
							class="input input-bordered w-full pr-8"
							type="text"
							placeholder="Rechercher par nom ou barcode..."
							bind:value={
								productSearchQuery
							}
							oninput={() => {
								productDropdownOpen = true;
							}}
							onfocus={() => {
								productDropdownOpen = true;
							}}
						/>

						<!-- Clear button when a product is selected -->
						{#if newItem.barcode}
							<button
								type="button"
								class="absolute right-2 top-1/2 -translate-y-1/2 text-base-content/40 hover:text-error transition-colors"
								onclick={() => {
									newItem.barcode =
										"";
									productSearchQuery =
										"";
								}}
							>
								<X size="16" />
							</button>
						{/if}

						{#if productDropdownOpen && filteredProductsForDropdown.length > 0}
							<div
								class="product-dropdown absolute z-50 w-full mt-1 max-h-60 overflow-y-auto bg-base-100 border border-base-300 rounded-lg shadow-lg"
							>
								{#each filteredProductsForDropdown as product}
									<button
										type="button"
										class="w-full text-left px-3 py-2 hover:bg-base-200 border-b border-base-200 last:border-0"
										onclick={() => {
											newItem.barcode =
												product.barcode;
											productSearchQuery = `${product.name} (${product.barcode})`;
											productDropdownOpen = false;
										}}
									>
										<div
											class="font-semibold text-sm"
										>
											{product.name}
										</div>
										<div
											class="text-xs text-base-content/60"
										>
											Barcode:
											{product.barcode}
											|
											Stock:
											{product.quantity}
											|
											Prix:
											{product.sell_price}
											DT
										</div>
									</button>
								{/each}
							</div>
						{/if}
					</div>
				</div>
				<div class="form-control">
					<label
						class="label font-semibold"
						for="item-qty"
						>Quantité Reçue *</label
					>
					<input
						id="item-qty"
						class="input input-bordered w-full"
						type="number"
						bind:value={newItem.quantity}
						placeholder="0"
					/>
				</div>

				<div class="form-control">
					<label
						class="label font-semibold"
						for="item-cost"
						>Prix d'Achat Unit. (DT) *</label
					>
					<input
						id="item-cost"
						class="input input-bordered w-full"
						type="number"
						step="0.001"
						bind:value={newItem.cost_price}
						placeholder="0.000"
					/>
				</div>

				<div class="form-control">
					<label
						class="label font-semibold"
						for="item-sell"
						>Prix de Vente Conseillé</label
					>
					<div class="flex gap-2">
						<input
							id="item-sell"
							class="input input-bordered w-full"
							type="number"
							step="0.001"
							bind:value={
								newItem.suggested_sell_price
							}
							placeholder="0.000"
						/>
						<button
							class="btn btn-primary font-bold"
							onclick={addItem}
						>
							<Plus size="16" />
						</button>
					</div>
				</div>
			</div>

			<!-- Table Items -->
			{#if items.length > 0}
				<div class="overflow-x-auto mb-6">
					<table class="table  w-full">
						<thead>
							<tr>
								<th>Produit</th>
								<th>Quantité</th
								>
								<th
									>Prix
									d'Achat</th
								>
								<th
									>Total
									Ligne</th
								>
								<th>Action</th>
							</tr>
						</thead>
						<tbody>
							{#each items as item, index}
								{@const product =
									products.find(
										(
											p,
										) =>
											p.barcode ===
											item.barcode,
									)}
								<tr>
									<td
										class="font-bold"
										>{product
											? product.name
											: item.barcode}</td
									>
									<td
										>{item.quantity}</td
									>
									<td
										class="font-mono"
										>{item.cost_price}
										DT</td
									>
									<td
										class="font-mono font-bold"
										>{(
											item.quantity *
											item.cost_price
										).toFixed(
											3,
										)}
										DT</td
									>
									<td>
										<button
											class="btn btn-xs btn-error btn-ghost"
											onclick={() =>
												removeItem(
													index,
												)}
										>
											<X
												size="14"
											/>
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
						<tfoot>
							<tr
								class="font-bold text-lg bg-base-200"
							>
								<td
									colspan="3"
									class="text-right"
									>Valeur
									Totale
									Livraison:</td
								>
								<td
									class="font-mono text-primary"
									>{totalDue}
									DT</td
								>
								<td></td>
							</tr>
						</tfoot>
					</table>
				</div>
			{:else}
				<div
					class="text-center text-base-content/50 py-8 border border-dashed border-base-300 rounded-lg mb-6"
				>
					Aucun produit ajouté pour l'instant.
					Utilisez le formulaire ci-dessus.
				</div>
			{/if}

			<!-- Submit Action -->
			<div class="modal-action">
				<button
					class="btn btn-ghost"
					onclick={() =>
						(isDeliveryModalOpen = false)}
				>
					Annuler
				</button>
				<button
					class="btn btn-primary font-bold gap-2"
					onclick={handleSubmit}
					disabled={items.length === 0}
				>
					<Check size="18" /> Enregistrer la Livraison
				</button>
			</div>
		</div>
		<div
			class="modal-backdrop"
			onclick={() => (isDeliveryModalOpen = false)}
		></div>
	</div>
{/if}

<!-- PAYMENT MODAL -->
{#if payingEntry}
	<div class="modal modal-open">
		<div class="modal-box relative">
			<button
				class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
				onclick={() => (payingEntry = null)}
			>
				<X size="16" />
			</button>

			<h3 class="font-bold text-lg mb-4">
				Règlement Fournisseur — {payingEntry.supplier_name ??
					"Fournisseur"}
			</h3>
			<p class="mb-4 text-sm text-base-content/60">
				Reste dû: <span
					class="text-error font-bold font-mono"
					>{payingEntry.remaining} DT</span
				>
			</p>

			<div class="flex flex-col gap-3">
				<div class="form-control">
					<label
						class="label font-semibold"
						for="payment-amount"
						>Montant à Régler (DT)</label
					>
					<input
						id="payment-amount"
						class="input input-bordered w-full font-mono"
						type="number"
						step="0.1"
						bind:value={paymentAmount}
					/>
				</div>
				<div class="form-control">
					<label
						class="label font-semibold"
						for="payment-notes-input"
						>Notes / N° Chèque</label
					>
					<input
						id="payment-notes-input"
						class="input input-bordered w-full"
						bind:value={paymentNotes}
						placeholder="Référence du paiement..."
					/>
				</div>
			</div>

			<div class="modal-action">
				<button
					class="btn btn-ghost"
					onclick={() => (payingEntry = null)}
					>Annuler</button
				>
				<button
					class="btn btn-success text-white font-bold gap-2"
					onclick={handlePayment}
				>
					<Check size="18" /> Confirmer le Règlement
				</button>
			</div>
		</div>
		<div
			class="modal-backdrop"
			onclick={() => (payingEntry = null)}
		></div>
	</div>
{/if}
