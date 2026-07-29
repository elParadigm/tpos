<script>
	import { onMount } from "svelte";
	import {
		Pickaxe,
		Plus,
		Edit,
		Power,
		Trash2,
		X,
		Check,
	} from "@lucide/svelte";

	import { BASE } from '$lib/config';

	let workers = $state([]);
	let name = $state("");
	let phone = $state("");
	let role = $state("cashier");
	let pin = $state("");
	let confirmPin = $state("");
	let editingId = $state(null);
	let error = $state("");
	let loading = $state(true);
	let pageError = $state("");
	let isModalOpen = $state(false);

	onMount(async () => {
		await load();
	});

	async function load() {
		try {
			const res = await fetch(`${BASE}/workers`);
			workers = await res.json();
		} catch (e) {
			pageError = 'Erreur lors du chargement des employés';
		} finally {
			loading = false;
		}
	}

	function openNewModal() {
		resetForm();
		isModalOpen = true;
	}

	function startEdit(w) {
		editingId = w.id;
		name = w.name;
		phone = w.phone ?? "";
		role = w.role ?? "cashier";
		pin = "";
		confirmPin = "";
		isModalOpen = true;
	}

	function resetForm() {
		editingId = null;
		name = "";
		phone = "";
		role = "cashier";
		pin = "";
		confirmPin = "";
		error = "";
		isModalOpen = false;
	}

	async function handleSubmit() {
		if (!name.trim()) {
			error = "Le nom de l'employé est obligatoire";
			return;
		}
		if (!editingId && !pin) {
			error = "Le code PIN est obligatoire";
			return;
		}
		if (!editingId && pin !== confirmPin) {
			error = "Les codes PIN ne correspondent pas";
			return;
		}
		if (pin && pin.length < 4) {
			error =
				"Le code PIN doit comporter au moins 4 chiffres";
			return;
		}
		error = "";

		const body = { name, phone, role };
		if (pin) body.pin = pin;

		if (editingId) {
			await fetch(`${BASE}/workers/${editingId}`, {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(body),
			});
		} else {
			const res = await fetch(`${BASE}/workers`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(body),
			});
			const data = await res.json();
			if (data.error) {
				error = data.error;
				return;
			}
		}
		resetForm();
		await load();
	}

	async function toggleActive(w) {
		const endpoint = w.is_active ? "deactivate" : "reactivate";
		await fetch(`${BASE}/workers/${w.id}/${endpoint}`, {
			method: "PUT",
		});
		await load();
	}

	async function handleDelete(id) {
		if (!confirm("Voulez-vous vraiment supprimer cet employé ?"))
			return;
		await fetch(`${BASE}/workers/${id}`, { method: "DELETE" });
		await load();
	}
</script>

<div class="p-6 mx-auto space-y-6">
	<!-- Page Header -->
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4"
	>
		<div>
			<h1 class="text-2xl font-bold flex items-center gap-2">
				<Pickaxe class="text-primary" size="24" />
				Gestion du Personnel & Caissiers
			</h1>
			<p class="text-sm text-base-content/60">
				Gérez les comptes employés, rôles (Caissier /
				Gérant) et codes PIN d'accès
			</p>
		</div>
		<button
			class="btn btn-primary font-bold gap-2"
			onclick={openNewModal}
		>
			<Plus size="18" /> Nouvel Employé
		</button>
	</div>

	{#if loading}
		<div class="flex justify-center p-12">
			<span class="loading loading-spinner loading-lg text-primary"></span>
		</div>
	{:else if pageError}
		<div class="alert alert-error shadow-lg">{pageError}</div>
	{/if}

	<!-- Modal -->
	{#if isModalOpen}
		<div class="modal modal-open">
			<div class="modal-box relative">
				<button
					class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
					onclick={resetForm}
				>
					<X size="16" />
				</button>

				<h3
					class="font-bold text-lg mb-4 flex items-center gap-2"
				>
					<Pickaxe
						class="text-primary"
						size="20"
					/>
					{editingId
						? "Modifier l'Employé"
						: "Nouveau Compte Employé"}
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
							for="work-name"
							>Nom Complet *</label
						>
						<input
							id="work-name"
							class="input input-bordered w-full"
							placeholder="ex: Ahmed Ben Salah"
							bind:value={name}
						/>
					</div>

					<div class="form-control">
						<label
							class="label font-semibold"
							for="work-phone"
							>Téléphone</label
						>
						<input
							id="work-phone"
							class="input input-bordered w-full"
							placeholder="ex: 98 000 000"
							bind:value={phone}
						/>
					</div>

					<div class="form-control">
						<label
							class="label font-semibold"
							for="work-role"
							>Rôle / Accès</label
						>
						<select
							id="work-role"
							class="select select-bordered w-full"
							bind:value={role}
						>
							<option value="cashier"
								>Caissier</option
							>
							<option value="manager"
								>Gérant /
								Manager</option
							>
						</select>
					</div>

					<div class="form-control">
						<label
							class="label font-semibold"
							for="work-pin"
						>
							{editingId
								? "Nouveau Code PIN (laisser vide pour conserver l'actuel)"
								: "Code PIN (4 chiffres) *"}
						</label>
						<input
							id="work-pin"
							class="input input-bordered w-full font-mono"
							type="password"
							maxlength="6"
							bind:value={pin}
						/>
					</div>

					{#if !editingId || pin}
						<div class="form-control">
							<label
								class="label font-semibold"
								for="work-conf"
								>Confirmer le
								Code PIN *</label
							>
							<input
								id="work-conf"
								class="input input-bordered w-full font-mono"
								type="password"
								maxlength="6"
								bind:value={
									confirmPin
								}
							/>
						</div>
					{/if}
				</div>

				<div class="modal-action">
					<button
						class="btn btn-ghost"
						onclick={resetForm}
						>Annuler</button
					>
					<button
						class="btn btn-primary font-bold gap-2"
						onclick={handleSubmit}
					>
						<Check size="18" />
						{editingId
							? "Enregistrer"
							: "Créer l'Employé"}
					</button>
				</div>
			</div>
			<div class="modal-backdrop" onclick={resetForm}></div>
		</div>
	{/if}

	<!-- Table -->
	<div
		class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden"
	>
		<div class="card-body p-0">
			{#if workers.length > 0}
				<div class="overflow-x-auto">
				<table class="table  w-full">
					<thead>
						<tr class="">
							<th>Nom Employé</th>
							<th>Téléphone</th>
							<th>Rôle</th>
							<th>Statut</th>
							<th class="text-center"
								>Actions</th
							>
						</tr>
					</thead>
					<tbody>
						{#each workers as w}
							<tr
								class={!w.is_active
									? "opacity-50 bg-base-200"
									: "bg-white hover:bg-base-200"}
							>
								<td
									class="font-bold"
									>{w.name}</td
								>
								<td
									class="font-mono text-sm"
									>{w.phone ??
										"-"}</td
								>
								<td>
									<span
										class="badge {w.role ===
										'manager'
											? 'badge-primary font-bold'
											: 'badge-ghost'}"
									>
										{w.role ===
										"manager"
											? "Gérant"
											: "Caissier"}
									</span>
								</td>
								<td>
									<span
										class="badge {w.is_active
											? 'badge-success text-white font-bold'
											: 'badge-ghost'}"
									>
										{w.is_active
											? "Actif"
											: "Inactif"}
									</span>
								</td>
								<td
									class="flex justify-center gap-1"
								>
									<button
										class="btn btn-xs btn-outline font-semibold gap-1"
										onclick={() =>
											startEdit(
												w,
											)}
									>
										<Edit
											size="12"
										/>
										Modifier
									</button>
									<button
										class="btn btn-xs {w.is_active
											? 'btn-warning'
											: 'btn-success'} text-white font-semibold gap-1"
										onclick={() =>
											toggleActive(
												w,
											)}
									>
										<Power
											size="12"
										/>
										{w.is_active
											? "Désactiver"
											: "Activer"}
									</button>
									<button
										class="btn btn-xs btn-error font-semibold gap-1"
										onclick={() =>
											handleDelete(
												w.id,
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
				
			{:else}
				<div class="p-12 text-center text-base-content/40">
					Aucun employé enregistré pour le moment
				</div>
			{/if}
	</div>
</div>
</div>
