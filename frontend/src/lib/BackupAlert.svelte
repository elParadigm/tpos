<script>
	import { onMount, onDestroy } from 'svelte';
	import { HardDrive, AlertTriangle, X } from '@lucide/svelte';

	import { BASE } from '$lib/config';

	let status   = $state(null);   // { drives, newest_backup_days, overdue }
	let open     = $state(false);
	let btnEl    = $state(null);
	let pos      = $state({ top: 0, left: 0 });
	let interval;

	async function fetchStatus() {
		try {
			const res = await fetch(`${BASE}/backup/status`);
			if (res.ok) status = await res.json();
		} catch {}
	}

	onMount(() => {
		fetchStatus();
		interval = setInterval(fetchStatus, 60_000);
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

	function portal(node) {
		document.body.appendChild(node);
		return {
			destroy() { node.remove(); }
		};
	}

	let days = $derived(status?.newest_backup_days ?? null);
	let overdue = $derived(status?.overdue ?? false);
	let dayLabel = $derived(
		days === null ? "jamais" : `${Math.floor(days)} jour${days >= 2 ? "s" : ""}`,
	);
</script>

{#if overdue}
	<!-- Warning button (stays in sidebar) -->
	<button
		bind:this={btnEl}
		class="btn btn-ghost w-14 h-14 relative"
		onclick={toggle}
		title="Sauvegarde en retard"
	>
		<HardDrive size="40" class="text-error" />
		<span class="absolute -top-1 -right-1 min-w-[24px] h-[24px] px-1.5 rounded-full
		             bg-error text-white text-xs font-bold flex items-center justify-center
		             animate-pulse">
			!
		</span>
	</button>

	<!-- Portal: rendered directly on document.body, escapes all stacking contexts -->
	{#if open}
		<div use:portal
			style="position:fixed;inset:0;z-index:9998;"
			onclick={close}
			aria-hidden="true"
		></div>

		<div use:portal
			style="position:fixed;top:{pos.top}px;left:{pos.left}px;z-index:9999;width:320px;"
			class="bg-base-100 rounded-2xl shadow-2xl border border-base-200 overflow-hidden"
		>
			<div class="flex items-center justify-between px-4 py-3 bg-base-200 border-b border-base-300">
				<div class="flex items-center gap-2 font-bold text-sm">
					<AlertTriangle size="16" class="text-error" />
					Sauvegarde en retard
				</div>
				<button class="btn btn-ghost btn-xs btn-square" onclick={close}>
					<X size="14" />
				</button>
			</div>

			<div class="px-4 py-3">
				<p class="text-sm font-medium">
					{#if days === null}
						Aucune sauvegarde n'a encore été effectuée.
					{:else}
						Dernière sauvegarde il y a {dayLabel}.
					{/if}
				</p>
				<p class="text-xs text-base-content/60 mt-1">
					Insérez une clé USB pour sauvegarder automatiquement, ou faites-le
					manuellement dans la configuration.
				</p>
				<a
					href="/settings"
					class="btn btn-primary btn-sm w-full mt-3 font-bold gap-1"
				>
					<HardDrive size="14" /> Aller à la Configuration
				</a>
			</div>
		</div>
	{/if}
{/if}
