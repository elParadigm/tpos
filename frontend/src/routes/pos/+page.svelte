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
		User,
	} from "@lucide/svelte";

	import { BASE } from '$lib/config';

	let cart = $state([]);
	let searchQuery = $state("");
	let categories = $state([]);
	let selectedCategory = $state(null);
	let products = $state([]);
	let discount = $state(0);
	let paymentMethod = $state("cash");

	// --- Checkout: client selection + amount paid ---
	let customers = $state([]);
	let customerSearch = $state("");
	let customerSearchEl = $state(null);
	let customerDropdownOpen = $state(false);
	let selectedCustomer = $state(null);
	let customerDebt = $state(null);

	let showCheckoutModal = $state(false);
	let checkoutPaidAmount = $state("");
	let checkoutError = $state("");
	let checkoutSubmitting = $state(false);

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
		loadCustomers();

		window.addEventListener("keydown", handleGlobalKeydown);
		const handleDocClick = (e) => {
			if (!e.target.closest("#customer-search-wrap")) {
				customerDropdownOpen = false;
			}
		};
		document.addEventListener("click", handleDocClick);
		focusSearch();

		return () => {
			window.removeEventListener(
				"keydown",
				handleGlobalKeydown,
			);
			document.removeEventListener("click", handleDocClick);
		};
	});

	async function loadCustomers() {
		try {
			const res = await fetch(`${BASE}/customers`);
			if (res.ok) customers = await res.json();
		} catch (e) {
			console.error(e);
		}
	}

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
		const target = e.target;

		// Ignore keystrokes inside form fields: typing a price/discount/
		// quantity and pressing Enter must never be mistaken for a barcode.
		if (
			target &&
			(target.tagName === "INPUT" ||
				target.tagName === "TEXTAREA" ||
				target.tagName === "SELECT" ||
				target.isContentEditable)
		) {
			return;
		}

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

	// --- Customer selection helpers ---
	let filteredCustomers = $derived(
		customers
			.filter((c) => {
				if (!customerSearch.trim()) return true;
				const q = customerSearch.toLowerCase();
				return (
					c.name.toLowerCase().includes(q) ||
					(c.phone && c.phone.toLowerCase().includes(q))
				);
			})
			.slice(0, 20),
	);

	async function refreshCustomerDebt(id) {
		try {
			const res = await fetch(`${BASE}/customers/${id}`);
			if (res.ok) {
				const data = await res.json();
				customerDebt = data.remaining_debt || 0;
			}
		} catch (e) {
			customerDebt = null;
		}
	}

	async function selectCustomer(c) {
		selectedCustomer = c;
		customerSearch = "";
		customerDropdownOpen = false;
		await refreshCustomerDebt(c.id);
	}

	// Picking a customer also acts as a "use this one" action.
	// Starting a new search does not clear the selection silently — the
	// selected customer stays until removed explicitly or a new one is
	// picked, so a confirm can't attach debt to the wrong person.
	function onCustomerSearchInput() {
		customerDropdownOpen = true;
		if (selectedCustomer && customerSearch.trim()) {
			clearCustomer();
			customerDebt = null;
		}
	}

	function clearCustomer() {
		selectedCustomer = null;
		customerDebt = null;
		customerSearch = "";
		customerDropdownOpen = false;
	}

	// amount paid: null/empty = full payment; 0 = nothing; other = partial.
	// checkoutPaidAmount is a number input -> Svelte binds it as number|null.
	let amountPaid = $derived(
		checkoutPaidAmount === "" || checkoutPaidAmount === null
			? null
			: Number(checkoutPaidAmount),
	);
	// A partial or zero payment leaves a remainder -> the client is required
	let needsCustomer = $derived(
		amountPaid !== null &&
			(isNaN(amountPaid) || amountPaid < total),
	);

	function lineTotal(item) {
		return (item.unit_price - item.discount) * item.quantity;
	}

	let subtotal = $derived(cart.reduce((sum, i) => sum + lineTotal(i), 0));
	let total = $derived(Math.max(0, subtotal - discount));

	async function completeSale() {
		if (cart.length === 0) return;

		// Reset the client + amount for a fresh checkout decision
		clearCustomer();
		checkoutPaidAmount = "";
		checkoutError = "";
		showCheckoutModal = true;
	}

	async function submitSale() {
		if (checkoutSubmitting) return;
		if (!selectedCustomer && needsCustomer) {
			checkoutError =
				"Veuillez sélectionner un client : cette vente laisse un reste à payer.";
			return;
		}
		checkoutError = "";
		checkoutSubmitting = true;

		const salePayload = {
			total: total,
			discount: Number(discount) || 0,
			payment_method: paymentMethod,
			customer_id: selectedCustomer?.id ?? null,
			// null (not "") = full payment; keep the sentinel consistent
			amount_paid: amountPaid === null ? null : Number(amountPaid),
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
					checkoutError =
						responseData.error || "Erreur lors de la vente";
				}
				return;
			}

			showCheckoutModal = false;

			// Effective paid amount: empty => full total; else min(input, total),
			// excess is ignored. Anything not covered becomes debt.
			const paid =
				amountPaid === null || isNaN(amountPaid)
					? total
					: Math.min(amountPaid, total);
			const remaining = Math.max(0, total - paid);

			lastCompletedSale = {
				id: responseData.sale_id || responseData.id || Date.now(),
				date: new Date().toLocaleString("fr-FR"),
				items: [...cart],
				subtotal: subtotal,
				discount: discount,
				total: total,
				paymentMethod: paymentMethod,
				workerName: $currentWorker?.name || "Caisse",
				customerName: selectedCustomer?.name || null,
				amountPaid: paid,
				remaining: remaining,
			};
			showReceiptModal = true;
			// Refresh product stock display
			loadProducts(selectedCategory);
			// Refresh the selected customer's balance
			if (selectedCustomer) {
				await refreshCustomerDebt(selectedCustomer.id);
			}
		} catch (e) {
			console.error("Sale failed", e);
			checkoutError = "Erreur de connexion au serveur";
		} finally {
			checkoutSubmitting = false;
		}
	}

	function handleNextSale() {
		showReceiptModal = false;
		cart = [];
		discount = 0;
		paymentMethod = "cash";
		lastCompletedSale = null;
		clearCustomer();
		checkoutPaidAmount = "";
		checkoutError = "";
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
							>Crédit</option
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
					class="input input-bordered input-lg w-full pl-12 shadow-sm font-medium"
					placeholder="Scannez un code-barres ou tapez le nom d'un produit..."
					bind:value={searchQuery}
				/>
				<Search
					class="absolute left-4 top-1/2 -translate-y-1/2 text-base-content/40"
					size="20"
				/>
				{#if searchQuery}
					<button
						class="btn btn-circle btn-ghost btn-xs absolute right-3 top-1/2 -translate-y-1/2"
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

<!-- CHECKOUT MODAL: client + amount paid -->
{#if showCheckoutModal}
	<div class="modal modal-open no-print">
		<div class="modal-box max-w-md relative">
			<button
				class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
				onclick={() => (showCheckoutModal = false)}
			>
				<X size="16" />
			</button>

			<h3 class="font-bold text-lg mb-1 flex items-center gap-2">
				<CheckCircle2 class="text-success" size="20" />
				Valider la Vente
			</h3>
			<p
				class="text-sm font-semibold text-base-content/70 mb-4"
			>
				Total: <span class="text-success font-extrabold font-mono">{total.toFixed(3)} {storeSettings.currency}</span>
			</p>

			{#if checkoutError}
				<div class="alert alert-error mb-4 py-2 text-sm">
					{checkoutError}
				</div>
			{/if}

			<!-- Client picker -->
			<div class="form-control mb-3">
				<label
					class="label font-semibold"
					for="checkout-customer-search"
					>Client (nécessaire s'il reste à payer)</label
				>
				<div class="relative" id="customer-search-wrap">
					<div class="relative">
						<input
							bind:this={customerSearchEl}
							id="checkout-customer-search"
							type="text"
							class="input input-bordered w-full pl-8 pr-8 font-medium"
							placeholder="Rechercher un client par nom ou téléphone..."
							bind:value={customerSearch}
							oninput={onCustomerSearchInput}
							onfocus={() =>
								(customerDropdownOpen = true)}
						/>
						<User
							class="absolute left-2.5 top-1/2 -translate-y-1/2 text-base-content/40"
							size="14"
						/>
						{#if customerSearch}
							<button
								class="btn btn-xs btn-circle btn-ghost absolute right-1 top-1.5"
								onclick={() => {
									customerSearch = "";
									customerDropdownOpen = false;
									clearCustomer();
								}}
							>
								<X size="12" />
							</button>
						{/if}
					</div>

					{#if customerDropdownOpen && filteredCustomers.length > 0}
						<div
							class="absolute z-50 w-full mt-1 max-h-52 overflow-y-auto bg-base-100 border border-base-300 rounded-lg shadow-xl"
						>
							{#each filteredCustomers as c}
								<button
									type="button"
									class="w-full text-left px-3 py-2 hover:bg-base-200 border-b border-base-200 last:border-0"
									onclick={() => selectCustomer(c)}
								>
									<div
										class="font-semibold text-sm"
									>
										{c.name}
									</div>
									<div
										class="text-xs text-base-content/60"
									>
										{c.phone ?? "—"}
									</div>
								</button>
							{/each}
						</div>
					{/if}
				</div>

				{#if selectedCustomer}
					<div
						class="flex items-center gap-2 mt-2"
					>
						<span
							class="badge badge-ghost font-bold"
						>
							{selectedCustomer.name}
						</span>
						{#if customerDebt > 0}
							<span
								class="badge badge-error text-white font-bold"
							>
								Dette actuelle: {customerDebt.toFixed(3)}
								{storeSettings.currency}
							</span>
						{/if}
						<button
							class="btn btn-xs btn-ghost text-error"
							onclick={clearCustomer}
							title="Retirer le client"
						>
							<X size="13" />
						</button>
					</div>
				{/if}
			</div>

			<!-- Amount paid -->
			<div class="form-control">
				<label
					class="label font-semibold"
					for="checkout-paid-amount"
					>Montant Payé ({storeSettings.currency})</label
				>
				<input
					id="checkout-paid-amount"
					class="input input-bordered w-full font-mono"
					type="number"
					step="0.1"
					min="0"
					bind:value={checkoutPaidAmount}
					placeholder="Laisser vide = paiement complet"
				/>
				<p class="text-[11px] text-base-content/50 mt-1 font-medium">
					Vide = paiement complet · 0 = tout à crédit · autre
					montant = acompte, le reste devient une dette
				</p>
				{#if needsCustomer && !selectedCustomer}
					<p
						class="text-[11px] font-semibold text-warning mt-1"
					>
						⚠ Un client est nécessaire : ce paiement laisse
						un reste à payer
					</p>
				{/if}
			</div>

			<div class="modal-action">
				<button
					class="btn btn-ghost"
					onclick={() => (showCheckoutModal = false)}
					>Annuler</button
				>
				<button
					class="btn btn-success text-white font-bold gap-2"
					onclick={submitSale}
					disabled={checkoutSubmitting}
				>
					{#if checkoutSubmitting}
						<span
							class="loading loading-spinner loading-sm"
						></span>
						Enregistrement...
					{:else}
						<CheckCircle2 size="18" /> Confirmer la vente
					{/if}
				</button>
			</div>
		</div>
		<div
			class="modal-backdrop"
			onclick={() => (showCheckoutModal = false)}
		></div>
	</div>
{/if}

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
			{#if lastCompletedSale.customerName}
				<p>
					<strong>Client:</strong>
					{lastCompletedSale.customerName}
				</p>
			{/if}
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
			<div class="total-row">
				<span>Payé:</span>
				<span
					>{lastCompletedSale.amountPaid.toFixed(3)}
					{storeSettings.currency}</span
				>
			</div>
			{#if lastCompletedSale.remaining > 0}
				<div class="total-row remaining-row">
					<span>Reste à payer:</span>
					<span
						>{lastCompletedSale.remaining.toFixed(3)}
						{storeSettings.currency}</span
					>
				</div>
			{/if}
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

		.remaining-row {
			font-weight: bold;
			font-size: 14px;
			border-top: 1px solid #000;
			padding-top: 3px;
			margin-top: 3px;
		}

		.receipt-footer {
			text-align: center;
			font-size: 11px;
			margin-top: 10px;
		}
	}
</style>
