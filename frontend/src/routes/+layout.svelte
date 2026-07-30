<script>
	import { page } from "$app/stores";
	import { goto } from "$app/navigation";
	import { currentWorker, logout } from "$lib/auth";
	import StockAlerts from "$lib/StockAlerts.svelte";
	import KioskBar from "$lib/KioskBar.svelte";
	import { onMount } from "svelte";
	import { BASE } from "$lib/config";
	import {
		ScanBarcode,
		Users,
		ChartPie,
		ChartBarStacked,
		Van,
		Pickaxe,
		Box,
		Warehouse,
		Settings,
		History,
		LogOut,
		Menu,
	} from "@lucide/svelte";

	const allLinks = [
		{ href: "/pos", label: "Caisse", icon: ScanBarcode },
		{ href: "/stock", label: "Stock", icon: Warehouse },
		{ href: "/customers", label: "Clients", icon: Users },
		{ href: "/settings/products", label: "Produits", icon: Box },
		{ href: "/settings/categories", label: "Catégories", icon: ChartBarStacked },
		{ href: "/settings/suppliers", label: "Fournisseurs", icon: Van },
		{ href: "/analytics", label: "Rapports", icon: ChartPie },
		{ href: "/history", label: "Historique", icon: History },
		{ href: "/settings", label: "Configuration", icon: Settings },
		{ href: "/settings/workers", label: "Personnel", icon: Pickaxe },
	];

	let storeName = $state("TPOS Commerce");

	onMount(async () => {
		try {
			const res = await fetch(`${BASE}/settings`);
			if (res.ok) {
				const data = await res.json();
				if (data.store_name) storeName = data.store_name;
			}
		} catch (e) {
			// keep default
		}
	});

	$effect(() => {
		if ($page.url.pathname !== "/login" && !$currentWorker) {
			goto("/login");
		}
	});

	function handleLogout() {
		logout();
		goto("/login");
	}

	let mainLinks = $derived(allLinks.slice(0, 6));
	let settingsLinks = $derived(
		$currentWorker?.role === "admin" ||
			$currentWorker?.role === "manager"
			? allLinks.slice(6)
			: [],
	);
</script>

{#if $page.url.pathname === "/login"}
	<slot />
{:else if $currentWorker}
	<div class="drawer lg:drawer-open">
		<input id="drawer" type="checkbox" class="drawer-toggle" />
		<div class="drawer-content flex flex-col">
			<!-- Mobile topbar -->
			<div class="navbar bg-base-100 shadow lg:hidden">
				<label
					for="drawer"
					class="btn btn-ghost btn-square"
				>
					<Menu size="20" />
				</label>
				<span class="font-bold text-lg flex-1"
					>{storeName}</span
				>
				<StockAlerts />
			</div>
			<!-- Page content -->
			<KioskBar />
			<main class="flex-1 bg-base-200 min-h-screen">
				<slot />
			</main>
		</div>
		<div class="drawer-side">
			<label for="drawer" class="drawer-overlay"></label>
			<ul
				class="menu p-4 w-60 min-h-full bg-base-100 gap-1 text-base-content"
			>
				<li
					class="menu-title text-xl font-black text-primary mb-2 tracking-wide border-b pb-2 border-base-200"
				>
					{storeName}
				</li>

				<!-- Worker info + alerts -->
				<li class="mb-3 bg-base-200 rounded-lg">
					<div
						class="flex items-center justify-between px-3 py-2"
					>
						<div
							class="flex flex-col gap-0"
						>
							<span
								class="font-bold text-sm"
								>{$currentWorker.name}</span
							>
							<span
								class="text-xs text-base-content/60 capitalize font-medium"
							>
								{$currentWorker.role ===
								"manager"
									? "Gérant / Manager"
									: "Caissier"}
							</span>
						</div>
						<StockAlerts />
					</div>
				</li>

				<li
					class="menu-title font-bold text-xs uppercase tracking-wider text-base-content/50"
				>
					Menu Principal
				</li>
				{#each mainLinks as link}
					<li>
						<a
							href={link.href}
							class="font-medium text-sm gap-3 {$page
								.url
								.pathname ===
							link.href
								? 'active bg-primary text-primary-content font-bold'
								: ''}"
						>
							<svelte:component
								this={link.icon}
								size="18"
							/>
							{link.label}
						</a>
					</li>
				{/each}

				{#if settingsLinks.length > 0}
					<li
						class="menu-title font-bold text-xs uppercase tracking-wider text-base-content/50 mt-4"
					>
						Administration
					</li>
					{#each settingsLinks as link}
						<li>
							<a
								href={link.href}
								class="font-medium text-sm gap-3 {$page
									.url
									.pathname ===
								link.href
									? 'active bg-primary text-primary-content font-bold'
									: ''}"
							>
								<svelte:component
									this={link.icon}
									size="18"
								/>
								{link.label}
							</a>
						</li>
					{/each}
				{/if}

				<!-- Logout at bottom -->
				<li
					class="mt-auto pt-4 border-t border-base-200"
				>
					<button
						class="text-error font-bold flex items-center gap-3 hover:bg-error/10"
						onclick={handleLogout}
					>
						<LogOut size="18" />
						Déconnexion
					</button>
				</li>
			</ul>
		</div>
	</div>
{/if}
