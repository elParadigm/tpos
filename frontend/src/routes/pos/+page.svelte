<script>
	import { onMount, tick } from "svelte";
	import { currentWorker } from "$lib/auth";
	import {
		ShoppingCart,
		Trash2,
		Search,
		Plus,
		Minus,
		X,
		CheckCircle2,
		Printer,
		Package,
		Tag,
		Banknote,
		CreditCard,
		FileText,
		DollarSign,
	} from "@lucide/svelte";

	import { BASE } from '$lib/config';

	let cart = $state([]);
	let searchQuery = $state("");
	let categories = $state([]);
	let selectedCategory = $state(null);
	let products = $state([]);
	let discount = $state(0);
	let paymentMethod = $state("cash");

	let customName = $state("");
	let customPrice = $state("");

	let storeSettings = $state({
		store_name: "Mon Commerce",
		tax_id: "",
		phone: "",
		address: "",
		receipt_header: "Bienvenue chez nous !",
		receipt_footer: "Merci pour votre visite",
		printer_format: "80mm",
		currency: "DT",
	});

	let showReceiptModal = $state(false);
	let lastCompletedSale = $state(null);
	let searchInputEl = $state(null);

	let barcodeBuffer = "";
	let lastKeyTime = Date.now();

	onMount(async () => {
		loadCategories();
		loadProducts();
		loadSettings();

		window.addEventListener("keydown", handleGlobalKeydown);
		focusSearch();

		return () => {
			window.removeEventListener(
				"keydown",
				handleGlobalKeydown,
			);
		};
	});

	function focusSearch() {
		tick().then(() => {
			if (searchInputEl) searchInputEl.focus();
		});
	}

	async function loadCategories() {
		try {
			const res = await fetch(`${BASE}/categories`);
			if (res.ok) categories = await res.json();
		} catch (e) {
			console.error(e);
		}
	}

	async function loadProducts(catId = null) {
		try {
			const url = catId
				? `${BASE}/products?category_id=${catId}`
				: `${BASE}/products`;
			const res = await fetch(url);
			if (res.ok) products = await res.json();
		} catch (e) {
			console.error(e);
		}
	}

	async function loadSettings() {
		try {
			const res = await fetch(`${BASE}/settings`);
			if (res.ok) {
				const data = await res.json();
				storeSettings = { ...storeSettings, ...data };
			}
		} catch (e) {
			console.error(e);
		}
	}

	function handleGlobalKeydown(e) {
		const now = Date.now();
		if (now - lastKeyTime > 300) barcodeBuffer = "";
		lastKeyTime = now;

		if (e.key === "Enter" && barcodeBuffer.length > 2) {
			addByBarcode(barcodeBuffer);
			barcodeBuffer = "";
			return;
		}

		if (e.key.length === 1) {
			barcodeBuffer += e.key;
		}
	}

	async function addByBarcode(barcode) {
		try {
			const res = await fetch(`${BASE}/products/${barcode}`);
			if (!res.ok) return;
			const product = await res.json();
			addToCart(product);
		} catch (e) {
			console.error(e);
		}
	}

	function selectCategory(catId) {
		selectedCategory = catId;
		loadProducts(catId);
	}

	let filteredProducts = $derived(
		products.filter((p) => {
			if (!searchQuery.trim()) return true;
			const q = searchQuery.toLowerCase();
			return (
				p.name.toLowerCase().includes(q) ||
				(p.barcode &&
					p.barcode.toLowerCase().includes(q))
			);
		}),
	);

	function addToCart(product) {
		const stock = parseInt(product.quantity);
		if (isNaN(stock) || stock < 1) return;
		const existingIndex = cart.findIndex(
			(i) =>
				i.barcode === product.barcode &&
				product.barcode !== null,
		);
		if (existingIndex !== -1) {
			if (cart[existingIndex].quantity >= stock) return;
			cart[existingIndex].quantity += 1;
			cart = [...cart];
		} else {
			cart = [
				...cart,
				{
					barcode: product.barcode || null,
					name: product.name,
					unit_price: parseFloat(
						product.sell_price,
					),
					quantity: 1,
					discount: 0,
					max_stock: stock,
				},
			];
		}
		searchQuery = "";
		focusSearch();
	}

	function addCustomItem() {
		if (
			!customName.trim() ||
			!customPrice ||
			parseFloat(customPrice) <= 0
		)
			return;
		cart = [
			...cart,
			{
				barcode: null,
				name: customName.trim(),
				unit_price: parseFloat(customPrice),
				quantity: 1,
				discount: 0,
			},
		];
		customName = "";
		customPrice = "";
		focusSearch();
	}

	function incrementQty(index) {
		const item = cart[index];
		if (item.max_stock && item.quantity >= item.max_stock) return;
		item.quantity += 1;
		cart = [...cart];
	}

	function decrementQty(index) {
		if (cart[index].quantity > 1) {
			cart[index].quantity -= 1;
			cart = [...cart];
		} else {
			removeFromCart(index);
		}
	}

	function setQty(index, value) {
		const n = parseInt(value);
		if (!n || n < 1) {
			removeFromCart(index);
			return;
		}
		const item = cart[index];
		if (item.max_stock && n > item.max_stock) {
			item.quantity = item.max_stock;
		} else {
			item.quantity = n;
		}
		cart = [...cart];
	}

	function removeFromCart(index) {
		cart = cart.filter((_, i) => i !== index);
	}

	function clearCart() {
		cart = [];
		discount = 0;
	}

	function lineTotal(item) {
		return (item.unit_price - item.discount) * item.quantity;
	}

	let subtotal = $derived(cart.reduce((sum, i) => sum + lineTotal(i), 0));
	let total = $derived(Math.max(0, subtotal - discount));

	async function completeSale() {
		if (cart.length === 0) return;

		const salePayload = {
			total: total,
			discount: discount,
			payment_method: paymentMethod,
			created_by: $currentWorker?.id ?? null,
			items: cart.map((i) => ({
				barcode: i.barcode,
				custom_name: i.barcode ? null : i.name,
				quantity: i.quantity,
				unit_price: i.unit_price,
				discount: i.discount,
			})),
		};

		try {
			const res = await fetch(`${BASE}/sales`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(salePayload),
			});

			const responseData = await res.json();

			if (!res.ok) {
				if (res.status === 409) {
					alert("Stock insuffisant:\n" + (responseData.details || []).join("\n"));
				} else {
					alert(responseData.error || "Erreur lors de la vente");
				}
				return;
			}

			lastCompletedSale = {
				id: responseData.sale_id || responseData.id || Date.now(),
				date: new Date().toLocaleString("fr-FR"),
				items: [...cart],
				subtotal: subtotal,
				discount: discount,
				total: total,
				paymentMethod: paymentMethod,
				workerName: $currentWorker?.name || "Caisse",
			};
			showReceiptModal = true;
			// Refresh product stock display
			loadProducts(selectedCategory);
		} catch (e) {
			console.error("Sale failed", e);
		}
	}

	function handleNextSale() {
		showReceiptModal = false;
		cart = [];
		discount = 0;
		paymentMethod = "cash";
		lastCompletedSale = null;
		focusSearch();
	}

	function triggerPrint() {
		window.print();
	}
</script>

<div class="flex h-[calc(100vh-4rem)] bg-base-200 overflow-hidden no-print">
	<!-- LEFT PANEL: CART & CHECKOUT -->
	<div
		class="flex flex-col w-5/12 bg-base-100 p-4 border-r border-base-300 gap-3 shadow-md"
	>
		<div
			class="flex justify-between items-center pb-2 border-b border-base-200"
		>
			<h2
				class="text-xl font-extrabold flex items-center gap-2"
			>
				<ShoppingCart class="text-primary" size="22" />
				Panier
				<span class="badge badge-primary badge-lg"
					>{cart.length} articles</span
				>
			</h2>
			{#if cart.length > 0}
				<button
					class="btn btn-ghost btn-xs text-error font-bold gap-1"
					onclick={clearCart}
				>
					<Trash2 size="14" /> Effacer
				</button>
			{/if}
		</div>

		<!-- Cart Items Table -->
		<div class="flex-1 overflow-y-auto">
			{#if cart.length === 0}
				<div
					class="flex flex-col items-center justify-center h-full text-base-content/40 space-y-2"
				>
					<ShoppingCart
						size="48"
						class="stroke-1 text-base-content/30"
					/>
					<p class="font-medium text-lg">
						Le panier est vide
					</p>
					<p class="text-xs text-center">
						Scannez un article ou cliquez
						sur un produit à droite
					</p>
				</div>
			{:else}
				<table class="table table-sm w-full">
					<thead>
						<tr class="">
							<th>Article</th>
							<th class="text-right"
								>P.U</th
							>
							<th class="text-center"
								>Qté</th
							>
							<th class="text-right"
								>Total</th
							>
							<th></th>
						</tr>
					</thead>
					<tbody>
						{#each cart as item, i}
							<tr class="hover">
								<td
									class="font-semibold text-sm"
								>
									{item.name}
									{#if item.discount > 0}
										<div
											class="text-xs text-warning"
										>
											Remise:
											-{item.discount.toFixed(
												3,
											)}
											{storeSettings.currency}
										</div>
									{/if}
								</td>
								<td
									class="text-right font-mono text-sm"
								>
									{item.unit_price.toFixed(
										3,
									)}
								</td>
								<td>
									<div
										class="flex items-center justify-center gap-1"
									>
										<button
											class="btn btn-square btn-xs btn-outline btn-error font-bold"
											onclick={() =>
												decrementQty(
													i,
												)}
										>
											<Minus
												size="12"
											/>
										</button>
										<input
											type="number"
											min="1"
											value={item.quantity}
											onchange={(
												e,
											) =>
												setQty(
													i,
													e
														.target
														.value,
												)}
											onclick={(
												e,
											) =>
												e.target.select()}
											class="input input-bordered input-xs w-14 text-center font-bold text-base px-1"
										/>
										<button
											class="btn btn-square btn-xs btn-outline btn-success font-bold"
											onclick={() =>
												incrementQty(
													i,
												)}
										>
											<Plus
												size="12"
											/>
										</button>
									</div>
								</td>
								<td
									class="text-right font-mono font-bold text-base tracking-wide"
								>
									{lineTotal(
										item,
									).toFixed(
										3,
									)}
								</td>
								<td
									class="text-center"
								>
									<button
										class="btn btn-ghost btn-xs text-error font-bold"
										onclick={() =>
											removeFromCart(
												i,
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
				</table>
			{/if}
		</div>

		<!-- Cart Summary -->
		<div
			class="border-t border-base-300 pt-3 flex flex-col gap-3 bg-base-100"
		>
			<div
				class="flex justify-between items-center text-sm font-medium"
			>
				<span>Sous-total</span>
				<span class="font-mono text-base"
					>{subtotal.toFixed(3)}
					{storeSettings.currency}</span
				>
			</div>

			<div class="flex justify-between items-center text-sm">
				<span
					>Remise Globale ({storeSettings.currency})</span
				>
				<input
					type="number"
					step="0.1"
					min="0"
					class="input input-sm input-bordered w-28 text-right font-mono"
					bind:value={discount}
				/>
			</div>

			<div
				class="flex justify-between items-center text-xl font-black text-success bg-success/10 p-3 rounded-lg border border-success/20"
			>
				<span>NET À PAYER</span>
				<span class="font-mono text-2xl"
					>{total.toFixed(3)}
					{storeSettings.currency}</span
				>
			</div>

			<div class="grid grid-cols-2 gap-2">
				<div class="form-control">
					<label
						class="label p-0 mb-1 text-xs font-semibold"
						for="payment-method"
						>Paiement</label
					>
					<select
						id="payment-method"
						class="select select-bordered select-sm w-full font-bold"
						bind:value={paymentMethod}
					>
						<option value="cash"
							>Espèces (Cash)</option
						>
						<option value="check"
							>Chèque</option
						>
						<option value="credit"
							>Crédit / Carte</option
						>
					</select>
				</div>

				<div class="flex items-end">
					<button
						class="btn btn-success btn-block font-extrabold text-white text-base shadow-lg gap-2"
						disabled={cart.length === 0}
						onclick={completeSale}
					>
						<CheckCircle2 size="18" />
						VALIDER LA VENTE
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- RIGHT PANEL: CATEGORIES & PRODUCT GRID -->
	<div class="flex flex-col w-7/12 p-4 gap-4 overflow-y-auto">
		<!-- Search Field -->
		<div class="form-control w-full">
			<div class="relative">
				<input
					bind:this={searchInputEl}
					type="text"
					class="input input-bordered input-lg w-full pl-11 shadow-sm font-medium"
					placeholder="Scannez un code-barres ou tapez le nom d'un produit..."
					bind:value={searchQuery}
				/>
				<Search
					class="absolute left-4 top-4 text-base-content/40"
					size="20"
				/>
				{#if searchQuery}
					<button
						class="btn btn-circle btn-ghost btn-xs absolute right-3 top-4"
						onclick={() => {
							searchQuery = "";
							focusSearch();
						}}
					>
						<X size="14" />
					</button>
				{/if}
			</div>
		</div>

		<!-- Category Tabs -->
		<div
			class="flex items-center gap-2 overflow-x-auto pb-2 border-b border-base-300"
		>
			<button
				class="btn btn-sm shrink-0 gap-1.5 {selectedCategory ===
				null
					? 'btn-primary'
					: 'btn-outline'}"
				onclick={() => selectCategory(null)}
			>
				<Package size="16" />
				Tous les produits
			</button>
			{#each categories as cat}
				<button
					class="btn btn-sm shrink-0 gap-1.5 {selectedCategory ===
					cat.id
						? 'btn-primary'
						: 'btn-outline'}"
					onclick={() => selectCategory(cat.id)}
				>
					<Tag size="16" />
					{cat.name}
				</button>
			{/each}
		</div>

		<!-- Product Cards Grid -->
		<div class="flex-1 overflow-y-auto">
			{#if filteredProducts.length === 0}
				<div
					class="text-center py-12 text-base-content/50"
				>
					Aucun produit trouvé dans cette
					catégorie.
				</div>
			{:else}
				<div
					class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3"
				>
					{#each filteredProducts as product}
						<button
							class="card bg-base-100 shadow hover:shadow-md hover:border-primary border border-base-200 transition-all text-left p-3 flex flex-col justify-between h-28 group"
							onclick={() =>
								addToCart(
									product,
								)}
						>
							<div>
								<span
									class="font-bold text-base tracking-wide text-base-content group-hover:text-primary line-clamp-2"
								>
									{product.name}
								</span>
								{#if product.category}
									<span
										class="badge badge-ghost badge-xs mt-1"
										>{product.category}</span
									>
								{/if}
							</div>

							<div
								class="flex justify-between items-end mt-2"
							>
								<span
									class="text-xs text-base-content/60 font-semibold"
								>
									Stock: {product.quantity}
								</span>
								<span
									class="text-base font-extrabold text-success font-mono"
								>
									{parseFloat(
										product.sell_price,
									).toFixed(
										3,
									)}
									<span
										class="text-xs font-normal"
										>{storeSettings.currency}</span
									>
								</span>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Custom Article -->
		<div
			class="card bg-base-100 shadow-sm border border-base-300 p-3"
		>
			<h3
				class="text-sm font-bold mb-2 flex items-center gap-1.5"
			>
				<Plus size="16" class="text-primary" />
				Article Hors Catalogue (Sur mesure / Coupe)
			</h3>
			<div class="flex items-center gap-2">
				<input
					type="text"
					class="input input-sm input-bordered flex-1"
					placeholder="Nom de l'article (ex: Câble 5m)"
					bind:value={customName}
				/>
				<input
					type="number"
					step="0.1"
					class="input input-sm input-bordered w-32 font-mono"
					placeholder="Prix ({storeSettings.currency})"
					bind:value={customPrice}
				/>
				<button
					class="btn btn-sm btn-secondary font-bold gap-1"
					onclick={addCustomItem}
				>
					<Plus size="14" /> Ajouter
				</button>
			</div>
		</div>
	</div>
</div>

<!-- POST-SALE RECEIPT MODAL -->
{#if showReceiptModal && lastCompletedSale}
	<div class="modal modal-open no-print">
		<div class="modal-box max-w-md">
			<h3
				class="font-bold text-lg text-success flex items-center gap-2"
			>
				<CheckCircle2 size="22" /> Vente Validée avec Succès
			</h3>
			<p class="py-2 text-sm text-base-content/70">
				Vente N° <span class="font-bold font-mono"
					>#{lastCompletedSale.id}</span
				>
				— Montant Total:
				<span
					class="font-extrabold text-success font-mono"
					>{lastCompletedSale.total.toFixed(3)}
					{storeSettings.currency}</span
				>
			</p>

			<!-- Action Buttons -->
			<div class="flex flex-col gap-2 my-4">
				<button
					class="btn btn-primary btn-lg font-bold gap-2 text-white shadow-md"
					onclick={triggerPrint}
				>
					<Printer size="20" /> IMPRIMER LA FACTURE
					/ TICKET
				</button>
				<button
					class="btn btn-outline btn-lg font-bold gap-2"
					onclick={handleNextSale}
				>
					<Plus size="20" /> VENTE SUIVANTE
				</button>
			</div>
		</div>
	</div>

	<!-- HIDDEN PRINT AREA -->
	<div
		id="printable-receipt"
		class="only-print print-container format-{storeSettings.printer_format}"
	>
		<div class="receipt-header">
			<h1 class="store-title">{storeSettings.store_name}</h1>
			{#if storeSettings.tax_id}<p class="tax-info">
					MF: {storeSettings.tax_id}
				</p>{/if}
			{#if storeSettings.phone}<p class="phone-info">
					Tél: {storeSettings.phone}
				</p>{/if}
			{#if storeSettings.address}<p class="address-info">
					{storeSettings.address}
				</p>{/if}
			{#if storeSettings.receipt_header}<p class="header-msg">
					{storeSettings.receipt_header}
				</p>{/if}
			<hr class="divider" />
		</div>

		<div class="receipt-meta">
			<p>
				<strong>N° Ticket:</strong>
				#{lastCompletedSale.id}
			</p>
			<p><strong>Date:</strong> {lastCompletedSale.date}</p>
			<p>
				<strong>Caissier:</strong>
				{lastCompletedSale.workerName}
			</p>
			<p>
				<strong>Paiement:</strong>
				{lastCompletedSale.paymentMethod.toUpperCase()}
			</p>
			<hr class="divider" />
		</div>

		<table class="receipt-table">
			<thead>
				<tr>
					<th>Article</th>
					<th class="center">Qté</th>
					<th class="right">P.U</th>
					<th class="right">Total</th>
				</tr>
			</thead>
			<tbody>
				{#each lastCompletedSale.items as item}
					<tr>
						<td>{item.name}</td>
						<td class="center"
							>{item.quantity}</td
						>
						<td class="right"
							>{item.unit_price.toFixed(
								3,
							)}</td
						>
						<td class="right"
							>{lineTotal(
								item,
							).toFixed(3)}</td
						>
					</tr>
				{/each}
			</tbody>
		</table>

		<hr class="divider" />

		<div class="receipt-totals">
			{#if lastCompletedSale.discount > 0}
				<div class="total-row">
					<span>Sous-total:</span>
					<span
						>{lastCompletedSale.subtotal.toFixed(
							3,
						)}
						{storeSettings.currency}</span
					>
				</div>
				<div class="total-row">
					<span>Remise:</span>
					<span
						>-{lastCompletedSale.discount.toFixed(
							3,
						)}
						{storeSettings.currency}</span
					>
				</div>
			{/if}
			<div class="total-row grand-total">
				<span>TOTAL NET:</span>
				<span
					>{lastCompletedSale.total.toFixed(3)}
					{storeSettings.currency}</span
				>
			</div>
		</div>

		{#if storeSettings.receipt_footer}
			<hr class="divider" />
			<div class="receipt-footer">
				<p>{storeSettings.receipt_footer}</p>
			</div>
		{/if}
	</div>
{/if}

<style>
	@media screen {
		.only-print {
			display: none !important;
		}
	}

	@media print {
		.no-print {
			display: none !important;
		}

		body {
			background: #ffffff !important;
			color: #000000 !important;
			font-family: "Courier New", Courier, monospace,
				sans-serif;
		}

		.only-print {
			display: block !important;
			margin: 0 auto;
			padding: 10px;
			color: #000;
		}

		.format-80mm {
			width: 78mm;
			font-size: 12px;
		}

		.format-58mm {
			width: 54mm;
			font-size: 10px;
		}

		.format-a5 {
			width: 148mm;
			font-size: 14px;
		}

		.format-a4 {
			width: 210mm;
			font-size: 14px;
		}

		.receipt-header {
			text-align: center;
			margin-bottom: 10px;
		}

		.store-title {
			font-size: 18px;
			font-weight: bold;
			margin: 0;
		}

		.divider {
			border: none;
			border-top: 1px dashed #000;
			margin: 8px 0;
		}

		.receipt-table {
			width: 100%;
			border-collapse: collapse;
		}

		.receipt-table th,
		.receipt-table td {
			padding: 3px 0;
			font-size: 12px;
		}

		.receipt-table th {
			border-bottom: 1px solid #000;
			text-align: left;
		}

		.center {
			text-align: center;
		}
		.right {
			text-align: right;
		}

		.receipt-totals {
			margin-top: 10px;
		}

		.total-row {
			display: flex;
			justify-content: space-between;
			font-size: 13px;
		}

		.grand-total {
			font-size: 16px;
			font-weight: bold;
			border-top: 1px solid #000;
			padding-top: 4px;
		}

		.receipt-footer {
			text-align: center;
			font-size: 11px;
			margin-top: 10px;
		}
	}
</style>
