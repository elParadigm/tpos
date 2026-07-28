<script>
	import { onMount, onDestroy } from 'svelte';
	import { Bell, Package, AlertTriangle, X } from '@lucide/svelte';

	const BASE = 'http://127.0.0.1:5000/api';

	let alerts   = $state([]);
	let open     = $state(false);
	let btnEl    = $state(null);
	let pos      = $state({ top: 0, left: 0 });
	let interval;

	async function fetchAlerts() {
		try {
			const res = await fetch(`${BASE}/products/low-stock`);
			if (res.ok) alerts = await res.json();
		} catch {}
	}

	onMount(() => {
		fetchAlerts();
		interval = setInterval(fetchAlerts, 60_000);
	});

	onDestroy(() => {
		clearInterval(interval);
	});

	function toggle() {
		if (!open && btnEl) {
			const rect = btnEl.getBoundingClientRect();
			pos = { top: rect.bottom + 8, left: rect.left };
		}
		open = !open;
	}

	function close() { open = false; }

	// Svelte action: teleports the node to document.body
	function portal(node) {
		document.body.appendChild(node);
		return {
			destroy() { node.remove(); }
		};
	}

	let critical = $derived(alerts.filter(a => a.quantity === 0));
	let warning  = $derived(alerts.filter(a => a.quantity > 0));
	let count    = $derived(alerts.length);
</script>

<!-- Bell button (stays in sidebar) -->
<button
	bind:this={btnEl}
	class="btn btn-ghost btn-sm btn-square relative"
	onclick={toggle}
	title="Alertes de stock"
>
	<Bell size="20" class={count > 0 ? 'text-warning' : 'text-base-content/60'} />
	{#if count > 0}
		<span class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full
		             bg-error text-white text-[10px] font-bold flex items-center justify-center
		             animate-pulse">
			{count > 99 ? '99+' : count}
		</span>
	{/if}
</button>

<!-- Portal: rendered directly on document.body, escapes all stacking contexts -->
{#if open}
	<!-- Click-away -->
	<div use:portal
		style="position:fixed;inset:0;z-index:9998;"
		onclick={close}
		aria-hidden="true"
	></div>

	<!-- Panel -->
	<div use:portal
		style="position:fixed;top:{pos.top}px;left:{pos.left}px;z-index:9999;width:320px;max-height:480px;"
		class="bg-base-100 rounded-2xl shadow-2xl border border-base-200 overflow-hidden flex flex-col"
	>
		<!-- Header -->
		<div class="flex items-center justify-between px-4 py-3 bg-base-200 border-b border-base-300">
			<div class="flex items-center gap-2 font-bold text-sm">
				<AlertTriangle size="16" class="text-warning" />
				Alertes Stock
				{#if count > 0}
					<span class="badge badge-error badge-sm text-white font-bold">{count}</span>
				{/if}
			</div>
			<button class="btn btn-ghost btn-xs btn-square" onclick={close}>
				<X size="14" />
			</button>
		</div>

		<div class="overflow-y-auto flex-1">
			{#if count === 0}
				<div class="flex flex-col items-center justify-center gap-2 py-10 text-base-content/40">
					<Package size="32" />
					<p class="text-sm font-medium">Tous les stocks sont suffisants</p>
				</div>
			{:else}
				{#if critical.length > 0}
					<div class="px-4 pt-3 pb-1">
						<p class="text-[10px] font-bold uppercase tracking-widest text-error mb-2">
							⛔ Rupture de stock ({critical.length})
						</p>
						{#each critical as item}
							<a href="/settings/products" onclick={close}
								class="flex items-center justify-between gap-3 py-2 px-3 rounded-xl
								       hover:bg-error/10 transition-colors group mb-1">
								<div class="flex items-center gap-2 min-w-0">
									<Package size="14" class="text-error shrink-0" />
									<span class="text-sm font-semibold truncate group-hover:text-error">{item.name}</span>
								</div>
								<span class="badge badge-error badge-sm font-bold text-white shrink-0">
									{item.quantity} / {item.min_stock}
								</span>
							</a>
						{/each}
					</div>
				{/if}

				{#if warning.length > 0}
					<div class="px-4 pt-2 pb-3">
						<p class="text-[10px] font-bold uppercase tracking-widest text-warning mb-2">
							⚠️ Stock faible ({warning.length})
						</p>
						{#each warning as item}
							<a href="/settings/products" onclick={close}
								class="flex items-center justify-between gap-3 py-2 px-3 rounded-xl
								       hover:bg-warning/10 transition-colors group mb-1">
								<div class="flex items-center gap-2 min-w-0">
									<Package size="14" class="text-warning shrink-0" />
									<span class="text-sm font-semibold truncate group-hover:text-warning">{item.name}</span>
								</div>
								<span class="badge badge-warning badge-sm font-bold shrink-0">
									{item.quantity} / {item.min_stock}
								</span>
							</a>
						{/each}
					</div>
				{/if}
			{/if}
		</div>

		{#if count > 0}
			<div class="border-t border-base-200 px-4 py-2">
				<a href="/stock" onclick={close}
					class="text-xs text-primary font-bold hover:underline flex items-center gap-1">
					Voir la page Stock →
				</a>
			</div>
		{/if}
	</div>
{/if}
