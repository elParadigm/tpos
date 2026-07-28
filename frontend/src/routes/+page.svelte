<script>
	import { onMount } from "svelte";
	import {
		TrendingUp,
		Banknote,
		CreditCard,
		AlertTriangle,
		Users,
		ScanBarcode,
	} from "@lucide/svelte";

	import { BASE } from '$lib/config';

	let dashboard = $state(null);
	let lowStock = $state([]);
	let debtors = $state([]);
	let loading = $state(true);
	let pageError = $state('');

	onMount(async () => {
		try {
			const [d, l, c] = await Promise.all([
				fetch(`${BASE}/analytics/dashboard`).then((r) =>
					r.json(),
				),
				fetch(`${BASE}/products/low-stock`).then((r) =>
					r.json(),
				),
				fetch(`${BASE}/customers/with-debt`).then((r) =>
					r.json(),
				),
			]);
			dashboard = d;
			lowStock = l;
			debtors = c;
		} catch (e) {
			pageError = 'Erreur de connexion au serveur';
			console.error(e);
		} finally {
			loading = false;
		}
	});
</script>

<div class="p-6 mx-auto space-y-6">
	<!-- Page Header -->
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4"
	>
		<div>
			<h1 class="text-2xl font-bold flex items-center gap-2">
				<TrendingUp class="text-primary" size="24" />
				Tableau de Bord / Accueil
			</h1>
			<p class="text-sm text-base-content/60">
				Aperçu rapide de l'activité du magasin, alertes
				de stock et dettes clients
			</p>
		</div>
		<a href="/pos" class="btn btn-primary font-bold gap-2">
			<ScanBarcode size="18" /> Ouvrir la Caisse (POS)
		</a>
	</div>

	{#if loading}
		<div class="flex justify-center p-12">
			<span class="loading loading-spinner loading-lg text-primary"></span>
		</div>
	{:else if pageError}
		<div class="alert alert-error shadow-lg">{pageError}</div>
	{:else if dashboard}
		<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
			<div
				class="stat bg-base-100 shadow-md border border-base-200 rounded-box"
			>
				<div class="stat-figure text-primary">
					<TrendingUp size="24" />
				</div>
				<div
					class="stat-title text-xs font-bold uppercase"
				>
					Ventes du Jour
				</div>
				<div class="stat-value text-primary">
					{dashboard.sales_count}
				</div>
				<div class="stat-desc">Transactions</div>
			</div>

			<div
				class="stat bg-base-100 shadow-md border border-base-200 rounded-box"
			>
				<div class="stat-figure text-success">
					<Banknote size="24" />
				</div>
				<div
					class="stat-title text-xs font-bold uppercase"
				>
					Recette Totale
				</div>
				<div class="stat-value text-success font-mono">
					{dashboard.revenue?.toFixed(3)} DT
				</div>
				<div class="stat-desc">Chiffre d'affaires</div>
			</div>

			<div
				class="stat bg-base-100 shadow-md border border-base-200 rounded-box"
			>
				<div class="stat-figure text-info">
					<Banknote size="24" />
				</div>
				<div
					class="stat-title text-xs font-bold uppercase"
				>
					Espèces en Caisse
				</div>
				<div class="stat-value text-info font-mono">
					{dashboard.cash_revenue?.toFixed(3)} DT
				</div>
				<div class="stat-desc">Paiements cash</div>
			</div>

			<div
				class="stat bg-base-100 shadow-md border border-base-200 rounded-box"
			>
				<div class="stat-figure text-warning">
					<CreditCard size="24" />
				</div>
				<div
					class="stat-title text-xs font-bold uppercase"
				>
					Crédits / Chèques
				</div>
				<div class="stat-value text-warning font-mono">
					{dashboard.credit_revenue?.toFixed(3)} DT
				</div>
				<div class="stat-desc">A encaisser</div>
			</div>
		</div>
	{/if}

	<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
		<div class="card bg-base-100 shadow-xl border border-base-200">
			<div class="card-body">
				<h2
					class="card-title text-error text-base mb-2 flex items-center justify-between"
				>
					<span class="flex items-center gap-2">
						<AlertTriangle size="20" />
						Alertes Stock Faible
					</span>
					{#if lowStock.length > 0}
						<span
							class="badge badge-error text-white font-bold"
							>{lowStock.length}</span
						>
					{/if}
				</h2>
				{#if lowStock.length === 0}
					<p
						class="text-base-content/40 text-sm py-4 text-center"
					>
						Tous les produits sont
						suffisamment approvisionnés.
					</p>
				{:else}
					<table
						class="table table-sm table-zebra w-full"
					>
						<thead>
							<tr class="bg-primary text-primary-content font-bold text-base tracking-wide">
								<th>Produit</th>
								<th
									class="text-center"
									>Stock
									Actuel</th
								>
								<th
									class="text-center"
									>Stock
									Alerte</th
								>
							</tr>
						</thead>
						<tbody>
							{#each lowStock as p}
								<tr
									class="hover"
								>
									<td
										class="font-bold"
										>{p.name}</td
									>
									<td
										class="text-center text-error font-bold font-mono"
										>{p.quantity}</td
									>
									<td
										class="text-center font-mono"
										>{p.min_stock}</td
									>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}
			</div>
		</div>

		<div class="card bg-base-100 shadow-xl border border-base-200">
			<div class="card-body">
				<h2
					class="card-title text-warning text-base mb-2 flex items-center justify-between"
				>
					<span class="flex items-center gap-2">
						<Users size="20" />
						Dettes Clients en cours
					</span>
					{#if debtors.length > 0}
						<span
							class="badge badge-warning font-bold"
							>{debtors.length}</span
						>
					{/if}
				</h2>
				{#if debtors.length === 0}
					<p
						class="text-base-content/40 text-sm py-4 text-center"
					>
						Aucun crédit client en cours.
					</p>
				{:else}
					<table
						class="table table-sm table-zebra w-full"
					>
						<thead>
							<tr class="bg-primary text-primary-content font-bold text-base tracking-wide">
								<th>Client</th>
								<th
									class="text-right"
									>Reste
									Dû</th
								>
							</tr>
						</thead>
						<tbody>
							{#each debtors.slice(0, 5) as c}
								<tr
									class="hover"
								>
									<td
										class="font-bold"
										>{c.name}</td
									>
									<td
										class="text-right text-error font-bold font-mono"
										>{c.remaining_debt}
										DT</td
									>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}
			</div>
		</div>
	</div>
</div>
