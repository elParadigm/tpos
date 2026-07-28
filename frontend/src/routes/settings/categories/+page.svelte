<script>
	import { onMount } from "svelte";
	import {
		ChartBarStacked,
		Plus,
		Edit,
		Trash2,
		X,
		Check,
	} from "@lucide/svelte";

	const BASE = "http://127.0.0.1:5000/api";

	let categories = $state([]);
	let name = $state("");
	let description = $state("");
	let editingId = $state(null);
	let error = $state("");
	let isModalOpen = $state(false);

	onMount(async () => {
		await load();
	});

	async function load() {
		const res = await fetch(`${BASE}/categories`);
		categories = await res.json();
	}

	function openNewModal() {
		cancelEdit();
		isModalOpen = true;
	}

	function startEdit(cat) {
		editingId = cat.id;
		name = cat.name;
		description = cat.description ?? "";
		isModalOpen = true;
	}

	function cancelEdit() {
		editingId = null;
		name = "";
		description = "";
		error = "";
		isModalOpen = false;
	}

	async function handleSubmit() {
		if (!name.trim()) {
			error = "Le nom de la catégorie est obligatoire";
			return;
		}
		error = "";
		if (editingId) {
			await fetch(`${BASE}/categories/${editingId}`, {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ name, description }),
			});
		} else {
			const res = await fetch(`${BASE}/categories`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ name, description }),
			});
			const data = await res.json();
			if (data.error) {
				error = data.error;
				return;
			}
		}
		cancelEdit();
		await load();
	}

	async function handleDelete(id) {
		if (
			!confirm(
				"Voulez-vous vraiment supprimer cette catégorie ?",
			)
		)
			return;
		await fetch(`${BASE}/categories/${id}`, { method: "DELETE" });
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
				<ChartBarStacked
					class="text-primary"
					size="24"
				/>
				Gestion des Catégories
			</h1>
			<p class="text-sm text-base-content/60">
				Organisez vos produits par catégories pour la
				recherche et le filtrage en caisse
			</p>
		</div>
		<button
			class="btn btn-primary font-bold gap-2"
			onclick={openNewModal}
		>
			<Plus size="18" /> Nouvelle Catégorie
		</button>
	</div>

	<!-- Modal -->
	{#if isModalOpen}
		<div class="modal modal-open">
			<div class="modal-box relative">
				<button
					class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
					onclick={cancelEdit}
				>
					<X size="16" />
				</button>

				<h3
					class="font-bold text-lg mb-4 flex items-center gap-2"
				>
					<ChartBarStacked
						class="text-primary"
						size="20"
					/>
					{editingId
						? "Modifier la Catégorie"
						: "Nouvelle Catégorie"}
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
							for="cat-name"
							>Nom de la Catégorie *</label
						>
						<input
							id="cat-name"
							class="input input-bordered w-full"
							placeholder="ex: Outillage, Électricité..."
							bind:value={name}
						/>
					</div>
					<div class="form-control">
						<label
							class="label font-semibold"
							for="cat-desc"
							>Description</label
						>
						<input
							id="cat-desc"
							class="input input-bordered w-full"
							placeholder="Description optionnelle..."
							bind:value={description}
						/>
					</div>
				</div>

				<div class="modal-action">
					<button
						class="btn btn-ghost"
						onclick={cancelEdit}
						>Annuler</button
					>
					<button
						class="btn btn-primary font-bold gap-2"
						onclick={handleSubmit}
					>
						<Check size="18" />
						{editingId
							? "Enregistrer"
							: "Créer la Catégorie"}
					</button>
				</div>
			</div>
			<div class="modal-backdrop" onclick={cancelEdit}></div>
		</div>
	{/if}

	<!-- Table -->
	<div
		class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden"
	>
		<div class="card-body p-0">
			<div class="overflow-x-auto">
				<table class="table table-zebra w-full">
					<thead>
						<tr class="bg-base-200">
							<th
								>Nom de la
								Catégorie</th
							>
							<th>Description</th>
							<th class="text-center"
								>Actions</th
							>
						</tr>
					</thead>
					<tbody>
						{#each categories as cat}
							<tr class="hover">
								<td
									class="font-bold"
									>{cat.name}</td
								>
								<td
									class="text-sm text-base-content/70"
									>{cat.description ??
										"-"}</td
								>
								<td
									class="flex justify-center gap-1"
								>
									<button
										class="btn btn-xs btn-outline font-semibold gap-1"
										onclick={() =>
											startEdit(
												cat,
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
												cat.id,
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
		</div>
	</div>
</div>
