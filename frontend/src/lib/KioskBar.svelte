<script>
	import { onMount, onDestroy } from "svelte";
	import { Clock, Battery, BatteryLow, BatteryMedium, BatteryFull, Power, PowerOff, RotateCw } from "@lucide/svelte";
	import { logout, authFetch } from "$lib/auth";

	let datetime = $state("");
	let batteryLevel = $state(100);
	let batteryCharging = $state(false);
	let batteryOk = $state(false);
	let showPowerMenu = $state(false);
	let powerMenuEl = $state(null);
	let powering = $state(false);

	let intervalId = null;

	onMount(() => {
		updateClock();
		intervalId = setInterval(updateClock, 60000);
		initBattery();

		const handleClick = (e) => {
			if (powerMenuEl && !powerMenuEl.contains(e.target)) {
				showPowerMenu = false;
			}
		};
		document.addEventListener("click", handleClick);

		const handleKey = (e) => {
			if (e.ctrlKey && e.shiftKey && e.key === "P") {
				showPowerMenu = !showPowerMenu;
			}
		};
		document.addEventListener("keydown", handleKey);

		return () => {
			clearInterval(intervalId);
			document.removeEventListener("click", handleClick);
			document.removeEventListener("keydown", handleKey);
		};
	});

	function updateClock() {
		const now = new Date();
		const day = now.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
		const time = now.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
		datetime = `${day} · ${time}`;
	}

	async function initBattery() {
		if (!navigator.getBattery) return;
		try {
			const battery = await navigator.getBattery();
			batteryOk = true;
			updateBattery(battery);
			battery.addEventListener("levelchange", () => updateBattery(battery));
			battery.addEventListener("chargingchange", () => updateBattery(battery));
		} catch {
			batteryOk = false;
		}
	}

	function updateBattery(battery) {
		batteryLevel = Math.round(battery.level * 100);
		batteryCharging = battery.charging;
	}

	function batteryIcon() {
		if (batteryCharging) return Battery;
		if (batteryLevel > 60) return BatteryFull;
		if (batteryLevel > 20) return BatteryMedium;
		return BatteryLow;
	}

	function batteryColor() {
		if (batteryCharging) return "text-success";
		if (batteryLevel > 20) return "text-base-content";
		return "text-error";
	}

	async function doPower(action) {
		powering = true;
		logout();
		try {
			const res = await authFetch(`${import.meta.env.DEV ? "http://127.0.0.1:5000/api" : "/api"}/system/${action}`, {
				method: "POST",
			});
			if (!res.ok) {
				const data = await res.json();
				alert(data.error || "Erreur");
			}
		} catch (e) {
			alert("Impossible de contacter le serveur");
		} finally {
			powering = false;
			showPowerMenu = false;
		}
	}
</script>

<div class="no-print kiosk-bar flex items-center justify-between px-4 py-1 bg-base-100 border-b border-base-300 text-sm font-medium select-none">
	<div class="flex items-center gap-2">
		<Clock size="15" class="text-base-content/50" />
		<span class="text-base-content/80">{datetime}</span>
	</div>

	<div class="flex items-center gap-3">
		{#if batteryOk}
			<span class="flex items-center gap-1.5 {batteryColor()}">
				<svelte:component this={batteryIcon()} size="15" />
				<span class="text-xs font-mono">{batteryLevel}%</span>
			</span>
		{/if}

		<div class="relative" bind:this={powerMenuEl}>
			<button class="btn btn-ghost btn-xs gap-1 text-base-content/60 hover:text-error"
				onclick={() => showPowerMenu = !showPowerMenu}>
				<Power size="15" />
			</button>

			{#if showPowerMenu}
				<div class="absolute right-0 top-full mt-1 w-36 bg-base-100 border border-base-300 rounded-lg shadow-xl z-50 overflow-hidden">
					<button class="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm hover:bg-base-200"
						onclick={() => doPower("shutdown")} disabled={powering}>
						<PowerOff size="15" class="text-error" /> Éteindre
					</button>
					<button class="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm hover:bg-base-200"
						onclick={() => doPower("reboot")} disabled={powering}>
						<RotateCw size="15" /> Redémarrer
					</button>
				</div>
			{/if}
		</div>
	</div>
</div>
