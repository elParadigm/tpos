<script>
	import { onMount } from "svelte";
	import { Van, Plus, Edit, Trash2, X, Check } from "@lucide/svelte";

	import { BASE } from '$lib/config';

	let suppliers = $state([]);
	let name = $state("");
	let phone = $state("");
	let address = $state("");
	let notes = $state("");
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
			const res = await fetch(`${BASE}/suppliers`);
			suppliers = await res.json();
		} catch (e) {
			pageError = 'Erreur lors du chargement des fournisseurs';
		} finally {
			loading = false;
		}
	}

	function openNewModal() {
		resetForm();
		isModalOpen = true;
	}

	function startEdit(s) {
		editingId = s.id;
		name = s.name;
		phone = s.phone ?? "";
		address = s.address ?? "";
		notes = s.notes ?? "";
		isModalOpen = true;
	}

	function resetForm() {
		editingId = null;
		name = "";
		phone = "";
		address = "";
		notes = "";
		error = "";
		isModalOpen = false;
	}

	async function handleSubmit() {
		if (!name.trim()) {
			error = "Le nom du fournisseur est obligatoire";
			return;
		}
		error = "";
		if (editingId) {
			await fetch(`${BASE}/suppliers/${editingId}`, {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					name,
					phone,
					address,
					notes,
				}),
			});
		} else {
			const res = await fetch(`${BASE}/suppliers`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					name,
					phone,
					address,
					notes,
				}),
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

	async function handleDelete(id) {
		if (!confirm("Voulez-vous vraiment supprimer ce fournisseur ?"))
			return;
		await fetch(`${BASE}/suppliers/${id}`, { method: "DELETE" });
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
				<Van class="text-primary" size="24" />
				Gestion des Fournisseurs
			</h1>
			<p class="text-sm text-base-content/60">
				Gérez les fiches contacts et coordonnées des
				fournisseurs du magasin
			</p>
		</div>
		<button
			class="btn btn-primary font-bold gap-2"
			onclick={openNewModal}
		>
			<Plus size="18" /> Nouveau Fournisseur
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
					<Van class="text-primary" size="20" />
					{editingId
						? "Modifier le Fournisseur"
						: "Nouveau Fournisseur"}
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
							for="sup-name"
							>Nom / Raison Sociale *</label
						>
						<input
							id="sup-name"
							class="input input-bordered w-full"
							placeholder="ex: Société de Matériel Elec"
							bind:value={name}
						/>
					</div>
					<div class="form-control">
						<label
							class="label font-semibold"
							for="sup-phone"
							>Téléphone</label
						>
						<input
							id="sup-phone"
							class="input input-bordered w-full"
							placeholder="ex: 71 800 900"
							bind:value={phone}
						/>
					</div>
					<div class="form-control">
						<label
							class="label font-semibold"
							for="sup-address"
							>Adresse</label
						>
						<input
							id="sup-address"
							class="input input-bordered w-full"
							placeholder="ex: Zone Industrielle, Megrine"
							bind:value={address}
						/>
					</div>
					<div class="form-control">
						<label
							class="label font-semibold"
							for="sup-notes"
							>Notes / Conditions de
							paiement</label
						>
						<textarea
							id="sup-notes"
							class="textarea textarea-bordered w-full"
							placeholder="Notes optionnelles..."
							bind:value={notes}
						></textarea>
					</div>
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
							: "Créer le Fournisseur"}
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
			{#if suppliers.length > 0}
				<div class="overflow-x-auto">
				<table class="table  w-full">
					<thead>
						<tr class="">
							<th>Nom Fournisseur</th>
							<th>Téléphone</th>
							<th>Adresse</th>
							<th class="text-center"
								>Actions</th
							>
						</tr>
					</thead>
					<tbody>
						{#each suppliers as s}
							<tr class="bg-white hover:bg-base-200">
								<td
									class="font-bold"
									>{s.name}</td
								>
								<td
									class="font-mono text-sm"
									>{s.phone ??
										"-"}</td
								>
								<td
									class="text-sm text-base-content/70"
									>{s.address ??
										"-"}</td
								>
								<td
									class="flex justify-center gap-1"
								>
									<button
										class="btn btn-xs btn-outline font-semibold gap-1"
										onclick={() =>
											startEdit(
												s,
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
												s.id,
											)}
									>
										<Trash2
											size="12"
										/>
										Supprimer
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
				</div>
				
			{:else}
				<div class="p-12 text-center text-base-content/40">
					Aucun fournisseur enregistré pour le moment
				</div>
			{/if}
	</div>
</div>
</div>
