<script>
	import { onMount, onDestroy } from "svelte";
	import {
		ChartPie,
		TrendingUp,
		Banknote,
		CreditCard,
		Package,
		Users,
		BarChart3,
		RefreshCw,
		FileText,
		Printer,
		ClipboardList,
		AlertTriangle,
	} from "@lucide/svelte";

	import { BASE } from '$lib/config';

	let dashboard = $state(null);
	let dailyRevenue = $state([]);
	let topProducts = $state([]);
	let margins = $state([]);
	let shiftHistory = $state([]);
	let customerDebts = $state([]);
	let tab = $state("overview");

	let loading = $state(true);
	let pageError = $state('');
	let dailyReport = $state(null);
	let lowStockList = $state([]);
	let storeSettings = $state({ printer_format: "80mm", currency: "DT" });

	let revenueChart = null;
	let topProductsChart = null;
	let canvasEl = $state(null);
	let topCanvasEl = $state(null);

	onMount(async () => {
		await load();
	});

	onDestroy(() => {
		if (revenueChart) revenueChart.destroy();
		if (topProductsChart) topProductsChart.destroy();
	});

	async function load() {
		try {
			loading = true;
			pageError = '';
			const since30 = new Date();
			since30.setDate(since30.getDate() - 30);
			const sinceStr = since30.toISOString().slice(0, 10);

			const safeJson = async (url) => {
				try { const r = await fetch(url); if (!r.ok) return null; return r.json(); }
				catch { return null; }
			};

			[dashboard, dailyRevenue, topProducts, margins, shiftHistory, customerDebts, dailyReport, lowStockList, storeSettings] = await Promise.all([
				safeJson(`${BASE}/analytics/dashboard`),
				safeJson(`${BASE}/analytics/revenue/daily?since=${sinceStr}`),
				safeJson(`${BASE}/analytics/products/top?since=${sinceStr}&sort=quantity`),
				safeJson(`${BASE}/analytics/products/margins`),
				safeJson(`${BASE}/analytics/shifts`),
				safeJson(`${BASE}/customers/with-debt`),
				safeJson(`${BASE}/reports/daily`),
				safeJson(`${BASE}/products/low-stock`),
				safeJson(`${BASE}/settings`),
			]);

			dailyRevenue ??= []; topProducts ??= []; margins ??= []; shiftHistory ??= []; customerDebts ??= []; dailyReport ??= null; lowStockList ??= []; if (storeSettings && !storeSettings.printer_format) storeSettings = { printer_format: "80mm", currency: "DT" };

			// Build charts after DOM update
			requestAnimationFrame(() => { buildRevenueChart(); buildTopProductsChart(); });
		} catch (e) {
			pageError = 'Erreur lors du chargement des rapports';
		} finally {
			loading = false;
		}
	}

	function getColors(count) {
		const palette = ['#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#0284c7', '#0369a1', '#075985', '#0c4a6e'];
		return palette.slice(0, count);
	}

	function buildRevenueChart() {
		if (!canvasEl || dailyRevenue.length === 0) return;
		if (revenueChart) revenueChart.destroy();

		const ctx = canvasEl.getContext('2d');
		revenueChart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: dailyRevenue.map(d => d.day?.slice(5) || ''),
				datasets: [{
					label: 'Chiffre (DT)',
					data: dailyRevenue.map(d => d.revenue),
					backgroundColor: '#2563eb',
					borderRadius: 3,
				}]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: { legend: { display: false } },
				scales: {
					y: {
						beginAtZero: true,
						ticks: { callback: v => v + ' DT' }
					}
				}
			}
		});
	}

	function buildTopProductsChart() {
		if (!topCanvasEl || topProducts.length === 0) return;
		if (topProductsChart) topProductsChart.destroy();

		const top5 = topProducts.slice(0, 5);
		const ctx = topCanvasEl.getContext('2d');
		topProductsChart = new Chart(ctx, {
			type: 'doughnut',
			data: {
				labels: top5.map(p => p.product_name?.length > 15 ? p.product_name.slice(0, 15) + '…' : p.product_name),
				datasets: [{
					data: top5.map(p => p.units_sold),
					backgroundColor: getColors(top5.length),
				}]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: { position: 'bottom', labels: { font: { size: 12 }, padding: 12 } }
				}
			}
		});
	}

	function refreshAll() {
		load();
	}

	function todayStr() {
		return new Date().toLocaleDateString("fr-FR", {
			weekday: "long", day: "numeric", month: "long", year: "numeric"
		});
	}

	function triggerPrint(id) {
		const el = document.getElementById(id);
		if (!el) return;
		const w = window.open("", "_blank");
		if (!w) { window.print(); return; }

		const fmt = storeSettings.printer_format || "80mm";
		const size = fmt === "80mm" ? "72mm" : fmt === "58mm" ? "54mm" : fmt === "a5" ? "148mm" : "210mm";
		const fsize = fmt === "58mm" ? "10px" : fmt === "80mm" ? "11px" : "14px";

		const html = [
			'<!DOCTYPE html><html><head><meta charset="utf-8"><style>',
			'body{font-family:Inter,sans-serif;margin:0;padding:10px;font-size:' + fsize + '}',
			'.print-receipt{width:' + size + ';margin:0 auto;padding:8px}',
			'.print-title{text-align:center;font-size:15px;font-weight:700;margin:0}',
			'.print-date{text-align:center;font-size:10px;margin:2px 0}',
			'.print-divider{border:none;border-top:1px dashed #000;margin:6px 0}',
			'.print-table{width:100%;border-collapse:collapse}',
			'.print-table th{border-bottom:1px solid #000;padding:3px 0;font-size:10px;text-align:left}',
			'.print-table td{padding:2px 0;font-size:11px}',
			'.center{text-align:center}', '.right{text-align:right}',
			'</style></head><body><div class="print-receipt">',
			el.innerHTML,
			'</div></body></html>'
		].join("");
		w.document.write(html);
		w.document.close();
		w.focus();
		setTimeout(() => { w.print(); w.close(); }, 300);
	}
</script>

<div class="p-6 mx-auto space-y-6 no-print">
	<!-- Page Header -->
	<div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold flex items-center gap-2">
				<ChartPie class="text-primary" size="26" />
				Rapports & Statistiques
			</h1>
			<p class="text-sm text-base-content/60">Performances de vente, marges et état des crédits</p>
		</div>
		<button class="btn btn-primary btn-sm gap-2" onclick={refreshAll} disabled={loading}>
			<RefreshCw size="14" /> Actualiser
		</button>
	</div>

	{#if loading}
		<div class="flex justify-center p-12">
			<span class="loading loading-spinner loading-lg text-primary"></span>
		</div>
	{:else if pageError}
		<div class="alert alert-error shadow-lg">{pageError}</div>
	{/if}

	<!-- Today Snapshot -->
	{#if dashboard}
		<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
			<div class="stat bg-base-100 shadow-md border border-base-200 rounded-box">
				<div class="stat-figure text-primary"><TrendingUp size="24" /></div>
				<div class="stat-title font-bold uppercase">Ventes du Jour</div>
				<div class="stat-value text-primary">{dashboard.sales_count}</div>
				<div class="stat-desc">Transactions</div>
			</div>
			<div class="stat bg-base-100 shadow-md border border-base-200 rounded-box">
				<div class="stat-figure text-success"><Banknote size="24" /></div>
				<div class="stat-title font-bold uppercase">Recette Totale</div>
				<div class="stat-value text-success font-mono">{dashboard.revenue?.toFixed(3)} DT</div>
				<div class="stat-desc">Chiffre d'affaires</div>
			</div>
			<div class="stat bg-base-100 shadow-md border border-base-200 rounded-box">
				<div class="stat-figure text-info"><Banknote size="24" /></div>
				<div class="stat-title font-bold uppercase">Espèces</div>
				<div class="stat-value text-info font-mono">{dashboard.cash_revenue?.toFixed(3)} DT</div>
				<div class="stat-desc">En caisse</div>
			</div>
			<div class="stat bg-base-100 shadow-md border border-base-200 rounded-box">
				<div class="stat-figure text-warning"><CreditCard size="24" /></div>
				<div class="stat-title font-bold uppercase">Crédits</div>
				<div class="stat-value text-warning font-mono">{dashboard.credit_revenue?.toFixed(3)} DT</div>
				<div class="stat-desc">À encaisser</div>
			</div>
		</div>
	{/if}

	<!-- Tabs -->
	<div role="tablist" class="tabs tabs-bordered bg-base-100 p-2 rounded-lg shadow-sm border border-base-200">
		<button role="tab" class="tab font-semibold gap-2 {tab === 'overview' ? 'tab-active text-primary border-primary font-bold' : ''}"
			onclick={() => tab = 'overview'}>
			<BarChart3 size="16" /> Évolution CA
		</button>
		<button role="tab" class="tab font-semibold gap-2 {tab === 'products' ? 'tab-active text-primary border-primary font-bold' : ''}"
			onclick={() => tab = 'products'}>
			<Package size="16" /> Top Ventes & Marges
		</button>
		<button role="tab" class="tab font-semibold gap-2 {tab === 'debts' ? 'tab-active text-primary border-primary font-bold' : ''}"
			onclick={() => tab = 'debts'}>
			<Users size="16" /> Crédits & Caisses
		</button>
		<button role="tab" class="tab font-semibold gap-2 {tab === 'cloture' ? 'tab-active text-primary border-primary font-bold' : ''}"
			onclick={() => tab = 'cloture'}>
			<FileText size="16" /> Clôture
		</button>
	</div>

	<!-- TAB: Overview -->
	{#if tab === "overview"}
		<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
			<div class="card bg-base-100 shadow-xl border border-base-200 md:col-span-2">
				<div class="card-body">
					<h2 class="card-title flex items-center gap-2">
						<BarChart3 class="text-primary" size="20" />
						Chiffre d'Affaires Journalier (30 jours)
					</h2>
					{#if dailyRevenue.length === 0}
						<p class="text-base-content/40 py-8 text-center">Aucune vente enregistrée.</p>
					{:else}
						<div class="h-64">
							<canvas bind:this={canvasEl}></canvas>
						</div>
					{/if}
				</div>
			</div>

			<div class="card bg-base-100 shadow-xl border border-base-200">
				<div class="card-body">
					<h2 class="card-title flex items-center gap-2">
						<Package class="text-primary" size="20" />
						Top 5 Produits
					</h2>
					{#if topProducts.length === 0}
						<p class="text-base-content/40 py-8 text-center">Aucune donnée.</p>
					{:else}
						<div class="h-64">
							<canvas bind:this={topCanvasEl}></canvas>
						</div>
					{/if}
				</div>
			</div>
		</div>

	{:else if tab === "products"}
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<div class="card bg-base-100 shadow-xl border border-base-200">
				<div class="card-body">
					<h2 class="card-title flex items-center gap-2"><Package class="text-primary" size="18" /> Meilleures Ventes</h2>
					<div class="overflow-x-auto">
						<table class="table w-full">
							<thead>
								<tr><th>Produit</th><th class="text-center">Qté Vendue</th><th class="text-right">Total</th></tr>
							</thead>
							<tbody>
								{#each topProducts as p}
									<tr class="hover">
										<td class="font-bold">{p.product_name}</td>
										<td class="text-center font-bold">{p.units_sold}</td>
										<td class="text-right font-mono font-bold text-success">{p.revenue?.toFixed(3)} DT</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<div class="card bg-base-100 shadow-xl border border-base-200">
				<div class="card-body">
					<h2 class="card-title flex items-center gap-2"><TrendingUp class="text-success" size="18" /> Marges Bénéficiaires</h2>
					<div class="overflow-x-auto">
						<table class="table w-full">
							<thead>
								<tr><th>Produit</th><th class="text-right">Marge Unit.</th><th class="text-center">Taux</th></tr>
							</thead>
							<tbody>
								{#each margins.slice(0, 10) as p}
									<tr class="hover">
										<td class="font-bold">{p.name}</td>
										<td class="text-right font-mono font-bold text-success">{p.margin?.toFixed(3)} DT</td>
										<td class="text-center">
											<span class="badge {p.margin_percent > 20 ? 'badge-success' : p.margin_percent > 10 ? 'badge-warning' : 'badge-error'} font-bold">
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
		</div>

	{:else if tab === "debts"}
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<div class="card bg-base-100 shadow-xl border border-base-200">
				<div class="card-body">
					<h2 class="card-title flex items-center gap-2"><Users class="text-error" size="18" /> Crédits Clients</h2>
					{#if customerDebts.length === 0}
						<p class="text-base-content/40 text-sm py-4 text-center">Aucun crédit en cours.</p>
					{:else}
						<div class="overflow-x-auto">
							<table class="table w-full">
								<thead>
									<tr><th>Client</th><th>Téléphone</th><th class="text-right">Dette</th></tr>
								</thead>
								<tbody>
									{#each customerDebts as c}
										<tr class="hover">
											<td class="font-bold">{c.name}</td>
											<td class="font-mono text-sm">{c.phone ?? "-"}</td>
											<td class="text-right text-error font-bold font-mono">{c.remaining_debt} DT</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				</div>
			</div>

			<div class="card bg-base-100 shadow-xl border border-base-200">
				<div class="card-body">
					<h2 class="card-title flex items-center gap-2"><Banknote class="text-info" size="18" /> Ventes par Caissier</h2>
					<div class="overflow-x-auto">
						<table class="table w-full">
							<thead>
								<tr><th>Caissier</th><th>Jour</th><th class="text-center">Ventes</th><th class="text-right">CA</th><th class="text-right">Espèces</th></tr>
							</thead>
							<tbody>
								{#if shiftHistory.length === 0}
									<tr><td colspan="5" class="text-center text-base-content/40 py-4">Aucune donnée.</td></tr>
								{:else}
									{#each shiftHistory.slice(0, 10) as s}
										<tr class="hover">
											<td class="font-bold">{s.worker_name}</td>
											<td class="font-mono text-sm">{s.day}</td>
											<td class="text-center">{s.sales_count}</td>
											<td class="text-right font-mono">{s.revenue?.toFixed(3)} DT</td>
											<td class="text-right font-mono text-info">{s.cash_revenue?.toFixed(3)} DT</td>
										</tr>
									{/each}
								{/if}
							</tbody>
						</table>
					</div>
				</div>
			</div>
		</div>

		{:else if tab === "cloture"}

		<!-- Daily Closing Report -->
		<div class="grid grid-cols-2 md:grid-cols-5 gap-4">
			<div class="stat bg-base-100 shadow-md border border-base-200 rounded-box">
				<div class="stat-figure text-primary"><TrendingUp size="22" /></div>
				<div class="stat-title font-bold uppercase text-xs">Ventes</div>
				<div class="stat-value text-primary text-2xl">{dailyReport?.summary?.sales_count ?? 0}</div>
				<div class="stat-desc">Aujourd'hui</div>
			</div>
			<div class="stat bg-base-100 shadow-md border border-base-200 rounded-box">
				<div class="stat-figure text-success"><Banknote size="22" /></div>
				<div class="stat-title font-bold uppercase text-xs">Recette Totale</div>
				<div class="stat-value text-success font-mono text-2xl">{dailyReport?.summary?.revenue?.toFixed(3) ?? "0,000"} DT</div>
				<div class="stat-desc">{dailyReport?.summary?.sales_count > 0 ? (dailyReport.summary.revenue / dailyReport.summary.sales_count).toFixed(3) : "0,000"} DT/vente</div>
			</div>
			<div class="stat bg-base-100 shadow-md border border-base-200 rounded-box">
				<div class="stat-figure text-info"><Banknote size="22" /></div>
				<div class="stat-title font-bold uppercase text-xs">Espèces</div>
				<div class="stat-value text-info font-mono text-2xl">{dailyReport?.summary?.cash_revenue?.toFixed(3) ?? "0,000"} DT</div>
				<div class="stat-desc">En caisse attendu</div>
			</div>
			<div class="stat bg-base-100 shadow-md border border-base-200 rounded-box">
				<div class="stat-figure text-warning"><CreditCard size="22" /></div>
				<div class="stat-title font-bold uppercase text-xs">Chèques</div>
				<div class="stat-value text-warning font-mono text-2xl">{dailyReport?.summary?.check_revenue?.toFixed(3) ?? "0,000"} DT</div>
				<div class="stat-desc">À déposer</div>
			</div>
			<div class="stat bg-base-100 shadow-md border border-base-200 rounded-box">
				<div class="stat-figure text-error"><CreditCard size="22" /></div>
				<div class="stat-title font-bold uppercase text-xs">Crédit</div>
				<div class="stat-value text-error font-mono text-2xl">{dailyReport?.summary?.credit_revenue?.toFixed(3) ?? "0,000"} DT</div>
				<div class="stat-desc">À encaisser</div>
			</div>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<div class="card bg-base-100 shadow-xl border border-base-200">
				<div class="card-body">
					<h2 class="card-title flex items-center gap-2"><Users class="text-primary" size="18" /> Ventes par Caissier</h2>
					{#if dailyReport?.workers?.length > 0}
						<div class="overflow-x-auto">
							<table class="table w-full">
								<thead><tr><th>Caissier</th><th class="text-center">Ventes</th><th class="text-right">CA</th></tr></thead>
								<tbody>
									{#each dailyReport.workers as w}
										<tr class="hover"><td class="font-bold">{w.worker_name}</td><td class="text-center">{w.sales_count}</td><td class="text-right font-mono font-bold text-success">{w.revenue?.toFixed(3)} DT</td></tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<p class="text-base-content/40 py-4 text-center">Aucune vente aujourd'hui.</p>
					{/if}
				</div>
			</div>
			<div class="card bg-base-100 shadow-xl border border-base-200">
				<div class="card-body">
					<h2 class="card-title flex items-center gap-2"><Package class="text-primary" size="18" /> Top Ventes du Jour</h2>
					{#if dailyReport?.top_products?.length > 0}
						<div class="overflow-x-auto">
							<table class="table w-full">
								<thead><tr><th>Produit</th><th class="text-center">Qté</th></tr></thead>
								<tbody>
									{#each dailyReport.top_products as p}
										<tr class="hover"><td class="font-bold">{p.product_name}</td><td class="text-center font-bold">{p.units_sold}</td></tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<p class="text-base-content/40 py-4 text-center">Aucune vente aujourd'hui.</p>
					{/if}
				</div>
			</div>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<div class="card bg-base-100 shadow-xl border border-base-200">
				<div class="card-body">
					<h2 class="card-title flex items-center gap-2"><ClipboardList class="text-primary" size="18" /> Actions</h2>
					<div class="flex flex-col gap-3">
						<button class="btn btn-primary font-bold gap-2" onclick={() => triggerPrint("print-report")}>
							<Printer size="16" /> Imprimer le Rapport de Clôture
						</button>
						<button class="btn btn-outline font-bold gap-2" onclick={() => triggerPrint("print-checklist")}>
							<ClipboardList size="16" /> Imprimer la Liste d'Achat (Stock Faible)
						</button>
					</div>
				</div>
			</div>
			<div class="card bg-base-100 shadow-xl border border-base-200">
				<div class="card-body">
					<h2 class="card-title flex items-center gap-2"><AlertTriangle class="text-error" size="18" /> Stock Faible</h2>
					{#if lowStockList.length > 0}
						<p class="text-sm"><span class="font-bold text-error">{lowStockList.length} produits</span> en dessous du seuil d'alerte.</p>
						<div class="overflow-x-auto mt-2">
							<table class="table table-sm w-full">
								<thead><tr><th>Produit</th><th class="text-center">Stock</th><th class="text-center">Alerte</th><th class="text-center">Manque</th></tr></thead>
								<tbody>
									{#each lowStockList as p}
										<tr><td class="font-bold">{p.name}</td><td class="text-center text-error font-bold">{p.quantity}</td><td class="text-center">{p.min_stock}</td><td class="text-center font-bold text-warning">{p.deficit}</td></tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<p class="text-base-content/40 py-4 text-center">Tous les stocks sont suffisants.</p>
					{/if}
				</div>
			</div>
		</div>

	{/if}
</div>


<!-- PRINT: Closing Report -->
<div id="print-report" class="only-print">
	<div class="print-{storeSettings.printer_format} print-receipt">
		<div class="print-header">
			<h1 class="print-title">Rapport de Clôture</h1>
			<p class="print-date">{todayStr()}</p>
			<hr class="print-divider" />
		</div>
		<table class="print-table">
			<tbody>
				<tr><td>Ventes</td><td class="right">{dailyReport?.summary?.sales_count ?? 0}</td></tr>
				<tr><td>Recette totale</td><td class="right">{dailyReport?.summary?.revenue?.toFixed(3) ?? "0,000"} DT</td></tr>
				<tr><td>Espèces</td><td class="right">{dailyReport?.summary?.cash_revenue?.toFixed(3) ?? "0,000"} DT</td></tr>
				<tr><td>Chèques</td><td class="right">{dailyReport?.summary?.check_revenue?.toFixed(3) ?? "0,000"} DT</td></tr>
				<tr><td>Crédits</td><td class="right">{dailyReport?.summary?.credit_revenue?.toFixed(3) ?? "0,000"} DT</td></tr>
			</tbody>
		</table>
	</div>
</div>

<!-- PRINT: Shopping Checklist -->
<div id="print-checklist" class="only-print">
	<div class="print-{storeSettings.printer_format} print-receipt">
		<div class="print-header">
			<h1 class="print-title">Liste d'Achat — Stock Faible</h1>
			<p class="print-date">{todayStr()}</p>
			<hr class="print-divider" />
		</div>
		<table class="print-table">
			<thead><tr><th>Produit</th><th class="center">Stock</th><th class="center">Min</th><th class="center">Manque</th><th class="center">✓</th></tr></thead>
			<tbody>
				{#each lowStockList as p}
					<tr><td>{p.name}</td><td class="center">{p.quantity}</td><td class="center">{p.min_stock}</td><td class="center">{p.deficit}</td><td class="center">[  ]</td></tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>

<style>
	@media screen { .only-print { display: none; } }
	@media print {
		.no-print { display: none !important; }
		.only-print { display: block !important; }
		body { background: #fff; color: #000; font-family: "Inter", sans-serif; }
		.print-receipt { margin: 0 auto; padding: 8px; font-size: 11px; }
		.format-80mm, .print-80mm { width: 72mm; font-size: 11px; }
		.format-58mm { width: 54mm; font-size: 10px; }
		.format-a5 { width: 148mm; font-size: 13px; }
		.format-a4 { width: 210mm; font-size: 14px; }
		.print-title { text-align: center; font-size: 15px; font-weight: bold; margin: 0; }
		.print-date { text-align: center; font-size: 10px; margin: 2px 0; }
		.print-divider { border: none; border-top: 1px dashed #000; margin: 6px 0; }
		.print-table { width: 100%; border-collapse: collapse; }
		.print-table th { border-bottom: 1px solid #000; padding: 3px 0; font-size: 10px; text-align: left; }
		.print-table td { padding: 2px 0; font-size: 11px; }
		.center { text-align: center; }
		.right { text-align: right; }
	}
</style>