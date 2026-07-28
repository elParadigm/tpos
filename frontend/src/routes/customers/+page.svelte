<script>
	import { onMount } from "svelte";
	import {
		Users,
		Plus,
		Edit,
		Trash2,
		BookOpen,
		CreditCard,
		X,
		Check,
	} from "@lucide/svelte";

	import { BASE } from '$lib/config';

	let customers = $state([]);
	let debtors = $state([]);
	let tab = $state("all");
	let error = $state("");
	let loading = $state(true);
	let pageError = $state("");

	let name = $state("");
	let phone = $state("");
	let notes = $state("");
	let editingId = $state(null);
	let isCustomerModalOpen = $state(false);

	let payingCustomer = $state(null);
	let paymentAmount = $state("");
	let paymentNotes = $state("");

	let viewingCustomer = $state(null);
	let customerSales = $state([]);
	let customerPayments = $state([]);

	onMount(async () => {
		await load();
	});

	async function load() {
		try {
			pageError = '';
			loading = true;
			const [c, d] = await Promise.all([
				fetch(`${BASE}/customers`).then((r) => r.json()),
				fetch(`${BASE}/customers/with-debt`).then((r) =>
					r.json(),
				),
			]);
			customers = c;
			debtors = d;
		} catch (e) {
			pageError = 'Erreur lors du chargement des clients';
		} finally {
			loading = false;
		}
	}

	function openNewCustomerModal() {
		resetForm();
		isCustomerModalOpen = true;
	}

	function startEdit(c) {
		editingId = c.id;
		name = c.name;
		phone = c.phone ?? "";
		notes = c.notes ?? "";
		isCustomerModalOpen = true;
	}

	function resetForm() {
		editingId = null;
		name = "";
		phone = "";
		notes = "";
		error = "";
	}

	async function handleSubmit() {
		if (!name.trim()) {
			error = "Le nom du client est obligatoire";
			return;
		}
		error = "";
		if (editingId) {
			await fetch(`${BASE}/customers/${editingId}`, {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ name, phone, notes }),
			});
		} else {
			const res = await fetch(`${BASE}/customers`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ name, phone, notes }),
			});
			const data = await res.json();
			if (data.error) {
				error = data.error;
				return;
			}
		}
		isCustomerModalOpen = false;
		resetForm();
		await load();
	}

	async function handleDelete(id) {
		if (!confirm("Voulez-vous vraiment supprimer ce client ?"))
			return;
		await fetch(`${BASE}/customers/${id}`, { method: "DELETE" });
		await load();
	}

	function startPayment(c) {
		payingCustomer = c;
		paymentAmount = c.remaining_debt || "";
		paymentNotes = "";
	}

	async function submitPayment() {
		if (!paymentAmount) return;
		await fetch(`${BASE}/customers/${payingCustomer.id}/payments`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				amount: parseFloat(paymentAmount),
				notes: paymentNotes,
			}),
		});
		payingCustomer = null;
		await load();
	}

	async function viewCarnet(c) {
		viewingCustomer = c;
		const [sales, payments] = await Promise.all([
			fetch(`${BASE}/customers/${c.id}/sales`).then((r) =>
				r.json(),
			),
			fetch(`${BASE}/customers/${c.id}/payments`).then((r) =>
				r.json(),
			),
		]);
		customerSales = sales;
		customerPayments = payments;
	}
</script>

<div class="p-6 mx-auto space-y-6">
	<!-- Page Header -->
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4"
	>
		<div>
			<h1 class="text-2xl font-bold flex items-center gap-2">
				<Users class="text-primary" size="24" />
				Gestion des Clients & Carnet de Crédit
			</h1>
			<p class="text-sm text-base-content/60">
				Gérez les coordonnées clients et suivez le
				carnet des crédits / dettes en cours
			</p>
		</div>

		<button
			class="btn btn-primary font-bold gap-2"
			onclick={openNewCustomerModal}
		>
			<Plus size="18" /> Nouveau Client
		</button>
	</div>

	{#if loading}
		<div class="flex justify-center p-12">
			<span class="loading loading-spinner loading-lg text-primary"></span>
		</div>
	{:else if pageError}
		<div class="alert alert-error shadow-lg">{pageError}</div>
	{/if}

	<!-- Tabs -->
	<div
		role="tablist"
		class="tabs tabs-bordered bg-base-100 p-2 rounded-lg shadow-sm border border-base-200"
	>
		<button
			role="tab"
			class="tab font-semibold {tab === 'all'
				? 'tab-active text-primary border-primary font-bold'
				: ''}"
			onclick={() => (tab = "all")}
		>
			Tous les Clients ({customers.length})
		</button>
		<button
			role="tab"
			class="tab font-semibold {tab === 'debt'
				? 'tab-active text-error border-error font-bold'
				: ''}"
			onclick={() => (tab = "debt")}
		>
			Clients avec Crédit en cours
			{#if debtors.length > 0}
				<span
					class="badge badge-error text-white font-bold ml-2"
					>{debtors.length}</span
				>
			{/if}
		</button>
	</div>

	{#if loading}
		<div class="flex justify-center p-12">
			<span class="loading loading-spinner loading-lg text-primary"></span>
		</div>
	{:else if pageError}
		<div class="alert alert-error shadow-lg">{pageError}</div>
	{:else}
	{#if tab === "all"}
		<div
			class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden"
		>
			<div class="card-body p-0">
				{#if customers.length === 0}
					<div
						class="p-12 text-center text-base-content/40"
					>
						Aucun client enregistré pour
						l'instant
					</div>
				{:else}
					<div class="overflow-x-auto">
						<table
							class="table  w-full"
						>
							<thead>
								<tr
									class="bg-primary text-primary-content font-bold text-base tracking-wide"
								>
									<th
										>Nom
										Client</th
									>
									<th
										>Téléphone</th
									>
									<th
										>Notes</th
									>
									<th
										class="text-center"
										>Actions</th
									>
								</tr>
							</thead>
							<tbody>
								{#each customers as c}
									<tr
										class="hover"
									>
										<td
											class="font-bold"
											>{c.name}</td
										>
										<td
											class="font-mono text-sm"
											>{c.phone ??
												"-"}</td
										>
										<td
											class="text-sm text-base-content/70"
											>{c.notes ??
												"-"}</td
										>
										<td
											class="flex justify-center gap-1"
										>
											<button
												class="btn btn-xs btn-outline btn-info font-semibold gap-1"
												onclick={() =>
													viewCarnet(
														c,
													)}
											>
												<BookOpen
													size="12"
												/>
												Carnet
											</button>
											<button
												class="btn btn-xs btn-outline font-semibold gap-1"
												onclick={() =>
													startEdit(
														c,
													)}
											>
												<Edit
													size="12"
												/>
												Modifier
											</button>
											<button
												class="btn btn-xs btn-error font-semibold gap-1"
												onclick={() =>
													handleDelete(
														c.id,
													)}
											>
												<Trash2
													size="12"
												/>
											</button>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		</div>
	{:else}
		<div
			class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden"
		>
			<div class="card-body p-0">
				{#if debtors.length === 0}
					<div
						class="p-12 text-center text-base-content/40"
					>
						Aucun client n'a de crédit en
						cours actuellement
					</div>
				{:else}
					<div class="overflow-x-auto">
						<table
							class="table  w-full"
						>
							<thead>
								<tr
									class="bg-primary text-primary-content font-bold text-base tracking-wide"
								>
									<th
										>Nom
										Client</th
									>
									<th
										>Téléphone</th
									>
									<th
										>Dette
										Restante</th
									>
									<th
										class="text-center"
										>Actions</th
									>
								</tr>
							</thead>
							<tbody>
								{#each debtors as c}
									<tr
										class="hover"
									>
										<td
											class="font-bold"
											>{c.name}</td
										>
										<td
											class="font-mono text-sm"
											>{c.phone ??
												"-"}</td
										>
										<td
											class="font-bold text-error font-mono"
											>{c.remaining_debt}
											DT</td
										>
										<td
											class="flex justify-center gap-1"
										>
											<button
												class="btn btn-xs btn-outline btn-info font-semibold gap-1"
												onclick={() =>
													viewCarnet(
														c,
													)}
											>
												<BookOpen
													size="12"
												/>
												Carnet
											</button>
											<button
												class="btn btn-xs btn-success text-white font-bold gap-1"
												onclick={() =>
													startPayment(
														c,
													)}
											>
												<CreditCard
													size="12"
												/>
												Régler
											</button>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		</div>
	{/if}
	{/if}
</div>

<!-- ADD/EDIT CUSTOMER MODAL -->
{#if isCustomerModalOpen}
	<div class="modal modal-open">
		<div class="modal-box relative">
			<button
				class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
				onclick={() => (isCustomerModalOpen = false)}
			>
				<X size="16" />
			</button>

			<h3
				class="font-bold text-lg mb-4 flex items-center gap-2"
			>
				<Users class="text-primary" size="20" />
				{editingId
					? "Modifier le Client"
					: "Nouveau Client"}
			</h3>

			{#if error}
				<div class="alert alert-error mb-4">
					{error}
				</div>
			{/if}

			<div class="flex flex-col gap-3">
				<div class="form-control">
					<label
						class="label font-semibold"
						for="cust-name"
						>Nom Complet / Raison Sociale *</label
					>
					<input
						id="cust-name"
						class="input input-bordered w-full"
						placeholder="ex: Mohamed Ali"
						bind:value={name}
					/>
				</div>
				<div class="form-control">
					<label
						class="label font-semibold"
						for="cust-phone"
						>Numéro de Téléphone</label
					>
					<input
						id="cust-phone"
						class="input input-bordered w-full"
						placeholder="ex: 98 123 456"
						bind:value={phone}
					/>
				</div>
				<div class="form-control">
					<label
						class="label font-semibold"
						for="cust-notes"
						>Notes / Observations</label
					>
					<input
						id="cust-notes"
						class="input input-bordered w-full"
						placeholder="Notes optionnelles..."
						bind:value={notes}
					/>
				</div>
			</div>

			<div class="modal-action">
				<button
					class="btn btn-ghost"
					onclick={() =>
						(isCustomerModalOpen = false)}
					>Annuler</button
				>
				<button
					class="btn btn-primary font-bold gap-2"
					onclick={handleSubmit}
				>
					<Check size="18" />
					{editingId
						? "Enregistrer"
						: "Créer le Client"}
				</button>
			</div>
		</div>
		<div
			class="modal-backdrop"
			onclick={() => (isCustomerModalOpen = false)}
		></div>
	</div>
{/if}

<!-- PAYMENT MODAL -->
{#if payingCustomer}
	<div class="modal modal-open">
		<div class="modal-box relative">
			<button
				class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
				onclick={() => (payingCustomer = null)}
			>
				<X size="16" />
			</button>

			<h3 class="font-bold text-lg mb-1">
				Règlement Crédit Client
			</h3>
			<p
				class="text-sm font-semibold text-base-content/70 mb-4"
			>
				{payingCustomer.name}
			</p>

			<div class="flex flex-col gap-3">
				<div class="form-control">
					<label
						class="label font-semibold"
						for="pay-amount-cust"
						>Montant Versé (DT) *</label
					>
					<input
						id="pay-amount-cust"
						class="input input-bordered w-full font-mono"
						type="number"
						step="0.1"
						bind:value={paymentAmount}
						placeholder="0.000"
					/>
				</div>
				<div class="form-control">
					<label
						class="label font-semibold"
						for="pay-notes-cust"
						>Notes / Référence Règlement</label
					>
					<input
						id="pay-notes-cust"
						class="input input-bordered w-full"
						bind:value={paymentNotes}
						placeholder="ex: Virement, Espèces..."
					/>
				</div>
			</div>

			<div class="modal-action">
				<button
					class="btn btn-ghost"
					onclick={() => (payingCustomer = null)}
					>Annuler</button
				>
				<button
					class="btn btn-success text-white font-bold gap-2"
					onclick={submitPayment}
				>
					<Check size="18" /> Confirmer le Paiement
				</button>
			</div>
		</div>
		<div
			class="modal-backdrop"
			onclick={() => (payingCustomer = null)}
		></div>
	</div>
{/if}

<!-- CARNET MODAL -->
{#if viewingCustomer}
	<div class="modal modal-open">
		<div class="modal-box w-11/12 max-w-3xl relative">
			<button
				class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
				onclick={() => (viewingCustomer = null)}
			>
				<X size="16" />
			</button>

			<h3
				class="font-bold text-lg mb-1 flex items-center gap-2"
			>
				<BookOpen class="text-primary" size="20" />
				Carnet de Crédit — {viewingCustomer.name}
			</h3>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
				<div class="card bg-base-200 p-3">
					<h4
						class="font-bold text-base tracking-wide mb-2 text-error"
					>
						Ventes à Crédit
					</h4>
					<div class="max-h-60 overflow-y-auto">
						<table
							class="table table-xs w-full"
						>
							<thead>
								<tr
									><th
										>Date</th
									><th
										>Montant</th
									></tr
								>
							</thead>
							<tbody>
								{#each customerSales as s}
									<tr>
										<td
											class="font-mono"
											>{s.sale_date?.slice(
												0,
												10,
											)}</td
										>
										<td
											class="text-error font-bold font-mono"
											>{s.net_total}
											DT</td
										>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>

				<div class="card bg-base-200 p-3">
					<h4
						class="font-bold text-base tracking-wide mb-2 text-success"
					>
						Règlements Effectués
					</h4>
					<div class="max-h-60 overflow-y-auto">
						<table
							class="table table-xs w-full"
						>
							<thead>
								<tr
									><th
										>Date</th
									><th
										>Montant
										Versé</th
									></tr
								>
							</thead>
							<tbody>
								{#each customerPayments as p}
									<tr>
										<td
											class="font-mono"
											>{p.paid_at?.slice(
												0,
												10,
											)}</td
										>
										<td
											class="text-success font-bold font-mono"
											>{p.amount}
											DT</td
										>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<div class="modal-action">
				<button
					class="btn btn-primary"
					onclick={() => (viewingCustomer = null)}
					>Fermer</button
				>
			</div>
		</div>
		<div
			class="modal-backdrop"
			onclick={() => (viewingCustomer = null)}
		></div>
	</div>
{/if}
