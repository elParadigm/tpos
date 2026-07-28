<script>
	import { onMount } from "svelte";
	import {
		History,
		RefreshCw,
		Globe,
		Banknote,
		Settings,
		Package,
		Search,
	} from "@lucide/svelte";

	const BASE = "http://127.0.0.1:5000/api";

	let logs = $state([]);
	let loading = $state(true);
	let selectedFilter = $state("ALL");
	let searchQuery = $state("");

	onMount(async () => {
		fetchHistory();
	});

	async function fetchHistory(filter = selectedFilter) {
		loading = true;
		try {
			const url =
				filter !== "ALL"
					? `${BASE}/history?action=${filter}`
					: `${BASE}/history`;
			const res = await fetch(url);
			if (res.ok) {
				logs = await res.json();
			}
		} catch (e) {
			console.error(e);
		} finally {
			loading = false;
		}
	}

	function setFilter(filter) {
		selectedFilter = filter;
		fetchHistory(filter);
	}

	let filteredLogs = $derived(
		logs.filter((log) => {
			if (!searchQuery.trim()) return true;
			const q = searchQuery.toLowerCase();
			return (
				log.description.toLowerCase().includes(q) ||
				(log.worker_name &&
					log.worker_name
						.toLowerCase()
						.includes(q)) ||
				log.action_type.toLowerCase().includes(q)
			);
		}),
	);

	function getBadgeClass(type) {
		switch (type) {
			case "SALE":
				return "badge-success";
			case "SETTINGS":
				return "badge-info";
			case "STOCK":
				return "badge-warning";
			case "PRODUCT":
				return "badge-secondary";
			default:
				return "badge-ghost";
		}
	}

	function formatTimestamp(ts) {
		if (!ts) return "-";
		return new Date(ts).toLocaleString("fr-FR", {
			day: "2-digit",
			month: "2-digit",
			year: "numeric",
			hour: "2-digit",
			minute: "2-digit",
			second: "2-digit",
		});
	}
</script>

<div class="p-6 mx-auto space-y-6">
	<!-- Page Header -->
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4"
	>
		<div>
			<h1 class="text-2xl font-bold flex items-center gap-2">
				<History class="text-primary" size="24" />
				Journal d'Activité & Historique
			</h1>
			<p class="text-sm text-base-content/60">
				Consultez toutes les opérations effectuées dans
				le système (Ventes, modifications de stock,
				configuration)
			</p>
		</div>

		<button
			class="btn btn-outline btn-sm gap-2"
			onclick={() => fetchHistory(selectedFilter)}
			disabled={loading}
		>
			<RefreshCw size="14" /> Actualiser
		</button>
	</div>

	<!-- Filter Tabs & Search Bar -->
	<div
		class="card bg-base-100 shadow-md border border-base-200 p-4 space-y-4"
	>
		<div
			class="flex flex-col md:flex-row justify-between gap-3 items-center"
		>
			<!-- Category Tabs -->
			<div class="flex flex-wrap gap-2">
				<button
					class="btn btn-sm gap-1.5 {selectedFilter ===
					'ALL'
						? 'btn-primary'
						: 'btn-ghost'}"
					onclick={() => setFilter("ALL")}
				>
					<Globe size="14" /> Tous ({logs.length})
				</button>
				<button
					class="btn btn-sm gap-1.5 {selectedFilter ===
					'SALE'
						? 'btn-success'
						: 'btn-ghost'}"
					onclick={() => setFilter("SALE")}
				>
					<Banknote size="14" /> Ventes
				</button>
				<button
					class="btn btn-sm gap-1.5 {selectedFilter ===
					'SETTINGS'
						? 'btn-info'
						: 'btn-ghost'}"
					onclick={() => setFilter("SETTINGS")}
				>
					<Settings size="14" /> Configuration
				</button>
				<button
					class="btn btn-sm gap-1.5 {selectedFilter ===
					'STOCK'
						? 'btn-warning'
						: 'btn-ghost'}"
					onclick={() => setFilter("STOCK")}
				>
					<Package size="14" /> Stock
				</button>
			</div>

			<!-- Search -->
			<div class="w-full md:w-72 relative">
				<input
					type="text"
					class="input input-sm input-bordered w-full pl-8"
					placeholder="Rechercher dans l'historique..."
					bind:value={searchQuery}
				/>
				<Search
					class="absolute left-2.5 top-2 text-base-content/40"
					size="14"
				/>
			</div>
		</div>
	</div>

	<!-- Audit Log Table -->
	<div
		class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden"
	>
		{#if loading}
			<div class="flex justify-center p-12">
				<span
					class="loading loading-spinner loading-lg text-primary"
				></span>
			</div>
		{:else if filteredLogs.length === 0}
			<div class="text-center p-12 text-base-content/50">
				Aucune activité enregistrée pour le moment.
			</div>
		{:else}
			<div class="overflow-x-auto">
				<table class="table table-zebra w-full">
					<thead>
						<tr class="bg-base-200">
							<th class="w-48"
								>Date & Heure</th
							>
							<th class="w-32"
								>Type d'action</th
							>
							<th
								>Description de
								l'évènement</th
							>
							<th class="w-36"
								>Intervenant</th
							>
						</tr>
					</thead>
					<tbody>
						{#each filteredLogs as log}
							<tr class="hover">
								<td
									class="font-mono text-xs font-semibold text-base-content/70"
								>
									{formatTimestamp(
										log.created_at,
									)}
								</td>
								<td>
									<span
										class="badge {getBadgeClass(
											log.action_type,
										)} font-bold text-xs"
									>
										{log.action_type}
									</span>
								</td>
								<td
									class="font-medium text-sm"
								>
									{log.description}
								</td>
								<td
									class="text-xs font-semibold"
								>
									{log.worker_name ||
										"Système"}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>
