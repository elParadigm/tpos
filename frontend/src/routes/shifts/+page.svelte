<script>
	import { onMount } from "svelte";

	const BASE = "http://127.0.0.1:5000/api";

	let openShift = $state(null);
	let shifts = $state([]);
	let workers = $state([]);
	let error = $state("");

	// open shift form
	let worker_id = $state("");
	let opening_cash = $state("");

	// close shift
	let closing_cash = $state("");
	let closeNotes = $state("");

	// summary modal
	let viewingShift = $state(null);

	onMount(async () => {
		await load();
	});

	async function load() {
		const [o, s, w] = await Promise.all([
			fetch(`${BASE}/shifts/open`).then((r) => r.json()),
			fetch(`${BASE}/shifts`).then((r) => r.json()),
			fetch(`${BASE}/workers/active`).then((r) => r.json()),
		]);
		openShift = o;
		shifts = s;
		workers = w;
	}

	async function handleOpen() {
		if (!worker_id) {
			error = "Select a worker";
			return;
		}
		error = "";
		const res = await fetch(`${BASE}/shifts`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				worker_id: parseInt(worker_id),
				opening_cash: parseFloat(opening_cash) || 0,
			}),
		});
		const data = await res.json();
		if (data.error) {
			error = data.error;
			return;
		}
		worker_id = "";
		opening_cash = "";
		await load();
	}

	async function handleClose() {
		if (!closing_cash) {
			error = "Enter closing cash amount";
			return;
		}
		error = "";
		await fetch(`${BASE}/shifts/${openShift.id}/close`, {
			method: "PUT",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				closing_cash: parseFloat(closing_cash),
				notes: closeNotes,
			}),
		});
		closing_cash = "";
		closeNotes = "";
		await load();
	}

	async function viewSummary(shift) {
		const res = await fetch(`${BASE}/shifts/${shift.id}`);
		viewingShift = await res.json();
	}
</script>

<div class="p-8 max-w-4xl mx-auto">
	<h1 class="text-2xl font-bold mb-6">Shifts</h1>

	{#if error}
		<div class="alert alert-error mb-4">{error}</div>
	{/if}

	{#if openShift}
		<!-- Open shift banner -->
		<div
			class="card bg-success/10 border border-success shadow mb-6"
		>
			<div class="card-body">
				<h2 class="card-title text-success">
					Shift Open
				</h2>
				<div class="grid grid-cols-3 gap-4 text-sm">
					<div>
						<span
							class="text-base-content/60"
							>Worker</span
						>
						<p class="font-bold">
							{openShift.worker_name}
						</p>
					</div>
					<div>
						<span
							class="text-base-content/60"
							>Started</span
						>
						<p class="font-bold">
							{openShift.started_at
								?.slice(0, 16)
								.replace(
									"T",
									" ",
								)}
						</p>
					</div>
					<div>
						<span
							class="text-base-content/60"
							>Opening Cash</span
						>
						<p class="font-bold">
							{openShift.opening_cash}
							DT
						</p>
					</div>
				</div>
				<div class="flex gap-3 mt-4 items-end">
					<div class="flex-1">
						<label class="label text-sm"
							>Closing Cash (DT)</label
						>
						<input
							class="input input-bordered w-full"
							type="number"
							bind:value={
								closing_cash
							}
							placeholder="Count the drawer..."
						/>
					</div>
					<div class="flex-1">
						<label class="label text-sm"
							>Notes</label
						>
						<input
							class="input input-bordered w-full"
							bind:value={closeNotes}
							placeholder="Optional"
						/>
					</div>
					<button
						class="btn btn-error"
						onclick={handleClose}
						>Close Shift</button
					>
				</div>
			</div>
		</div>
	{:else}
		<!-- Open new shift -->
		<div class="card bg-base-100 shadow mb-6">
			<div class="card-body">
				<h2 class="card-title">Open New Shift</h2>
				<div class="grid grid-cols-2 gap-3">
					<select
						class="select select-bordered"
						bind:value={worker_id}
					>
						<option value=""
							>Select worker *</option
						>
						{#each workers as w}
							<option value={w.id}
								>{w.name}</option
							>
						{/each}
					</select>
					<input
						class="input input-bordered"
						placeholder="Opening Cash (DT)"
						type="number"
						bind:value={opening_cash}
					/>
				</div>
				<div class="mt-2">
					<button
						class="btn btn-success"
						onclick={handleOpen}
						>Open Shift</button
					>
				</div>
			</div>
		</div>
	{/if}

	<!-- Shift History -->
	<div class="card bg-base-100 shadow">
		<div class="card-body">
			<h2 class="card-title mb-2">Shift History</h2>
			<table class="table table-sm">
				<thead>
					<tr>
						<th>Worker</th>
						<th>Started</th>
						<th>Ended</th>
						<th>Opening</th>
						<th>Closing</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					{#each shifts.filter((s) => s.ended_at) as s}
						<tr>
							<td>{s.worker_name}</td>
							<td class="text-xs"
								>{s.started_at
									?.slice(
										0,
										16,
									)
									.replace(
										"T",
										" ",
									)}</td
							>
							<td class="text-xs"
								>{s.ended_at
									?.slice(
										0,
										16,
									)
									.replace(
										"T",
										" ",
									)}</td
							>
							<td
								>{s.opening_cash}
								DT</td
							>
							<td
								>{s.closing_cash}
								DT</td
							>
							<td>
								<button
									class="btn btn-xs btn-outline"
									onclick={() =>
										viewSummary(
											s,
										)}
									>Summary</button
								>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
</div>

<!-- Summary Modal -->
{#if viewingShift}
	<div class="modal modal-open">
		<div class="modal-box">
			<h3 class="font-bold text-lg mb-4">
				Shift Summary — {viewingShift.worker_name}
			</h3>
			<div class="grid grid-cols-2 gap-3 text-sm">
				<div class="stat bg-base-200 rounded-box p-3">
					<div class="stat-title">
						Total Sales
					</div>
					<div class="stat-value text-lg">
						{viewingShift.total_sales}
					</div>
				</div>
				<div class="stat bg-base-200 rounded-box p-3">
					<div class="stat-title">Revenue</div>
					<div class="stat-value text-lg">
						{viewingShift.revenue} DT
					</div>
				</div>
				<div class="stat bg-base-200 rounded-box p-3">
					<div class="stat-title">
						Expected Cash
					</div>
					<div class="stat-value text-lg">
						{viewingShift.expected_cash} DT
					</div>
				</div>
				<div class="stat bg-base-200 rounded-box p-3">
					<div class="stat-title">
						Discrepancy
					</div>
					<div
						class="stat-value text-lg {viewingShift.cash_discrepancy !==
						0
							? 'text-error'
							: 'text-success'}"
					>
						{viewingShift.cash_discrepancy} DT
					</div>
				</div>
			</div>
			<div class="modal-action">
				<button
					class="btn"
					onclick={() => (viewingShift = null)}
					>Close</button
				>
			</div>
		</div>
	</div>
{/if}
