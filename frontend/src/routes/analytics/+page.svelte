<script>
	import { onMount } from "svelte";
	import {
		ChartPie,
		TrendingUp,
		Banknote,
		CreditCard,
		Package,
		Users,
		BarChart3,
	} from "@lucide/svelte";

	const BASE = "http://127.0.0.1:5000/api";

	let dashboard = $state(null);
	let dailyRevenue = $state([]);
	let topProducts = $state([]);
	let margins = $state([]);
	let shiftHistory = $state([]);
	let customerDebts = $state([]);
	let tab = $state("overview");

	let loading = $state(false);

	onMount(async () => {
		await load();
	});

	async function load() {
		loading = true;
		const since30 = new Date();
		since30.setDate(since30.getDate() - 30);
		const sinceStr = since30.toISOString().slice(0, 10);

		const safeJson = async (url) => {
			try {
				const r = await fetch(url);
				if (!r.ok) return null;
				return r.json();
			} catch {
				return null;
			}
		};

		[
			dashboard,
			dailyRevenue,
			topProducts,
			margins,
			shiftHistory,
			customerDebts,
		] = await Promise.all([
			safeJson(`${BASE}/analytics/dashboard`),
			safeJson(
				`${BASE}/analytics/revenue/daily?since=${sinceStr}`,
			),
			safeJson(
				`${BASE}/analytics/products/top?since=${sinceStr}&sort=quantity`,
			),
			safeJson(`${BASE}/analytics/products/margins`),
			safeJson(`${BASE}/analytics/shifts`),
			safeJson(`${BASE}/customers/with-debt`),
		]);

		dailyRevenue ??= [];
		topProducts ??= [];
		margins ??= [];
		shiftHistory ??= [];
		customerDebts ??= [];
		loading = false;
	}

	let maxRevenue = $derived(
		dailyRevenue.length > 0
			? Math.max(...dailyRevenue.map((d) => d.revenue))
			: 1,
	);
</script>

<div class="p-6 mx-auto space-y-6">
	<!-- Page Header -->
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4"
	>
		<div>
			<h1 class="text-2xl font-bold flex items-center gap-2">
				<ChartPie class="text-primary" size="24" />
				Rapports & Statistiques
			</h1>
			<p class="text-sm text-base-content/60">
				Aperçu des performances de vente, chiffre
				d'affaires, marges et état des crédits
			</p>
		</div>
		<button
			class="btn btn-primary btn-sm gap-2"
			onclick={load}
			disabled={loading}
		>
			{#if loading}
				<span class="loading loading-spinner loading-xs"
				></span>
			{:else}
				↺
			{/if}
			Actualiser
		</button>
	</div>

	<!-- Today snapshot -->
	{#if dashboard}
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
					Ventes d'Aujourd'hui
				</div>
				<div class="stat-value text-primary">
					{dashboard.sales_count}
				</div>
				<div class="stat-desc">
					Transactions effectuées
				</div>
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
					Recette du Jour
				</div>
				<div class="stat-value text-success font-mono">
					{dashboard.revenue?.toFixed(3)} DT
				</div>
				<div class="stat-desc">
					Chiffre d'affaires global
				</div>
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
					Espèces (Cash)
				</div>
				<div class="stat-value text-info font-mono">
					{dashboard.cash_revenue?.toFixed(3)} DT
				</div>
				<div class="stat-desc">En caisse</div>
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
					Crédit / Chèques
				</div>
				<div class="stat-value text-warning font-mono">
					{dashboard.credit_revenue?.toFixed(3)} DT
				</div>
				<div class="stat-desc">
					A encaisser / Crédits
				</div>
			</div>
		</div>
	{/if}

	<!-- Tabs -->
	<div
		role="tablist"
		class="tabs tabs-bordered bg-base-100 p-2 rounded-lg shadow-sm border border-base-200"
	>
		<button
			role="tab"
			class="tab font-semibold gap-2 {tab === 'overview'
				? 'tab-active text-primary border-primary font-bold'
				: ''}"
			onclick={() => (tab = "overview")}
		>
			<BarChart3 size="16" /> Évolution Chiffre d'Affaires
		</button>
		<button
			role="tab"
			class="tab font-semibold gap-2 {tab === 'products'
				? 'tab-active text-primary border-primary font-bold'
				: ''}"
			onclick={() => (tab = "products")}
		>
			<Package size="16" /> Top Ventes & Marges
		</button>
		<button
			role="tab"
			class="tab font-semibold gap-2 {tab === 'debts'
				? 'tab-active text-primary border-primary font-bold'
				: ''}"
			onclick={() => (tab = "debts")}
		>
			<Users size="16" /> Crédits & Historique Caisses
		</button>
	</div>

	{#if tab === "overview"}
		<div class="card bg-base-100 shadow-xl border border-base-200">
			<div class="card-body">
				<h2
					class="card-title text-lg mb-4 flex items-center gap-2"
				>
					<BarChart3
						class="text-primary"
						size="20"
					/>
					Chiffre d'Affaires Journalier (30 derniers
					jours)
				</h2>
				{#if dailyRevenue.length === 0}
					<p
						class="text-base-content/40 py-8 text-center"
					>
						Aucune vente enregistrée pour le
						moment.
					</p>
				{:else}
					<div
						class="flex items-end gap-2 h-56 pt-6 overflow-x-auto"
					>
						{#each dailyRevenue as d}
							<div
								class="flex-1 min-w-[28px] flex flex-col items-center gap-1"
							>
								<span
									class="text-[10px] font-mono text-base-content/70"
								>
									{d.revenue.toFixed(
										0,
									)}
								</span>
								<div
									class="w-full bg-primary rounded-t transition-all hover:bg-primary-focus"
									style="height: {(d.revenue /
										maxRevenue) *
										160}px"
									title="{d.day}: {d.revenue.toFixed(
										3,
									)} DT"
								></div>
								<span
									class="text-[10px] font-mono text-base-content/50 -rotate-45 origin-top-left mt-2"
								>
									{d.day?.slice(
										5,
									)}
								</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{:else if tab === "products"}
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<div
				class="card bg-base-100 shadow-xl border border-base-200"
			>
				<div class="card-body">
					<h2
						class="card-title text-base mb-3 flex items-center gap-2"
					>
						<Package
							class="text-primary"
							size="18"
						/>
						Meilleures Ventes (30 derniers jours)
					</h2>
					<table
						class="table table-sm table-zebra w-full"
					>
						<thead>
							<tr class="bg-base-200">
								<th>Produit</th>
								<th
									class="text-center"
									>Quantité
									Vendue</th
								>
								<th
									class="text-right"
									>Total
									Ventes</th
								>
							</tr>
						</thead>
						<tbody>
							{#each topProducts as p}
								<tr
									class="hover"
								>
									<td
										class="font-bold"
										>{p.product_name}</td
									>
									<td
										class="text-center font-bold"
										>{p.units_sold}</td
									>
									<td
										class="text-right font-mono font-bold"
										>{p.revenue?.toFixed(
											3,
										)}
										DT</td
									>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>

			<div
				class="card bg-base-100 shadow-xl border border-base-200"
			>
				<div class="card-body">
					<h2
						class="card-title text-base mb-3 flex items-center gap-2"
					>
						<TrendingUp
							class="text-success"
							size="18"
						/>
						Marges Bénéficiaires par Produit
					</h2>
					<table
						class="table table-sm table-zebra w-full"
					>
						<thead>
							<tr class="bg-base-200">
								<th>Produit</th>
								<th
									class="text-right"
									>Marge
									Unit.</th
								>
								<th
									class="text-center"
									>Taux %</th
								>
							</tr>
						</thead>
						<tbody>
							{#each margins.slice(0, 10) as p}
								<tr
									class="hover"
								>
									<td
										class="font-bold"
										>{p.name}</td
									>
									<td
										class="text-right font-mono font-bold text-success"
										>{p.margin?.toFixed(
											3,
										)}
										DT</td
									>
									<td
										class="text-center"
									>
										<span
											class="badge {p.margin_percent >
											20
												? 'badge-success'
												: p.margin_percent >
													  10
													? 'badge-warning'
													: 'badge-error'} font-bold"
										>
											{p.margin_percent}%
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<div
				class="card bg-base-100 shadow-xl border border-base-200"
			>
				<div class="card-body">
					<h2
						class="card-title text-base mb-3 flex items-center gap-2"
					>
						<Users
							class="text-error"
							size="18"
						/>
						Crédits Clients en cours
					</h2>
					{#if customerDebts.length === 0}
						<p
							class="text-base-content/40 text-sm py-4 text-center"
						>
							Aucun crédit en cours.
						</p>
					{:else}
						<table
							class="table table-sm table-zebra w-full"
						>
							<thead>
								<tr
									class="bg-base-200"
								>
									<th
										>Client</th
									>
									<th
										>Téléphone</th
									>
									<th
										class="text-right"
										>Dette</th
									>
								</tr>
							</thead>
							<tbody>
								{#each customerDebts as c}
									<tr
										class="hover"
									>
										<td
											class="font-bold"
											>{c.name}</td
										>
										<td
											class="font-mono text-xs"
											>{c.phone ??
												"-"}</td
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

			<div
				class="card bg-base-100 shadow-xl border border-base-200"
			>
				<div class="card-body">
					<h2
						class="card-title text-base mb-3 flex items-center gap-2"
					>
						<Banknote
							class="text-info"
							size="18"
						/>
						Historique des Caisses & Écarts
					</h2>
					<table
						class="table table-sm table-zebra w-full"
					>
						<thead>
							<tr class="bg-base-200">
								<th>Caissier</th
								>
								<th>Jour</th>
								<th
									class="text-center"
									>Ventes</th
								>
								<th
									class="text-right"
									>CA (DT)</th
								>
								<th
									class="text-right"
									>Espèces</th
								>
							</tr>
						</thead>
						<tbody>
							{#if shiftHistory.length === 0}
								<tr
									><td
										colspan="5"
										class="text-center text-base-content/40 py-4"
										>Aucune
										donnée.</td
									></tr
								>
							{:else}
								{#each shiftHistory.slice(0, 10) as s}
									<tr
										class="hover"
									>
										<td
											class="font-bold"
											>{s.worker_name}</td
										>
										<td
											class="font-mono text-xs"
											>{s.day}</td
										>
										<td
											class="text-center"
											>{s.sales_count}</td
										>
										<td
											class="text-right font-mono"
											>{s.revenue?.toFixed(
												3,
											)}
											DT</td
										>
										<td
											class="text-right font-mono text-info"
											>{s.cash_revenue?.toFixed(
												3,
											)}
											DT</td
										>
									</tr>
								{/each}
							{/if}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	{/if}
</div>
