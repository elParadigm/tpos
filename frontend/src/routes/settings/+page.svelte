<script>
	import { onMount } from "svelte";
	import {
		Building2,
		Printer,
		FileText,
		HardDrive,
		Save,
		CheckCircle2,
		AlertTriangle,
		RefreshCw,
		User,
		Phone,
		Mail,
	} from "@lucide/svelte";

	import { BASE } from '$lib/config';

	let settings = $state({
		store_name: "",
		tax_id: "",
		phone: "",
		address: "",
		receipt_header: "",
		receipt_footer: "",
		printer_format: "80mm",
		currency: "DT",
	});

	let loading = $state(true);
	let saving = $state(false);
	let backingUp = $state(false);
	let restoring = $state(false);
	let backups = $state([]);
	let showBackups = $state(false);
	let usbDrives = $state([]);
	let toastMessage = $state("");
	let toastType = $state("success");

	onMount(async () => {
		try {
			const res = await fetch(`${BASE}/settings`);
			if (res.ok) {
				const data = await res.json();
				settings = { ...settings, ...data };
			}
			checkUsbDrives();
		} catch (err) {
			showToast(
				"Erreur lors du chargement des paramètres",
				"error",
			);
		} finally {
			loading = false;
		}
	});

	async function checkUsbDrives() {
		try {
			const res = await fetch(`${BASE}/backup/drives`);
			if (res.ok) {
				const data = await res.json();
				usbDrives = data.drives || [];
			}
		} catch (e) {
			console.error(e);
		}
	}

	async function triggerUsbBackup() {
		backingUp = true;
		try {
			const res = await fetch(`${BASE}/backup/export`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({}),
			});
			const data = await res.json();
			if (res.ok && data.success) {
				showToast(data.message, "success");
			} else {
				showToast(
					data.error ||
						"Erreur lors de la sauvegarde",
					"error",
				);
			}
		} catch (e) {
			showToast(
				"Erreur de connexion au serveur pour la sauvegarde",
				"error",
			);
		} finally {
			backingUp = false;
			checkUsbDrives();
		}
	}

	async function listBackups() {
		showBackups = !showBackups;
		if (!showBackups) return;
		backups = [];
		try {
			const res = await fetch(`${BASE}/backup/list`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({}),
			});
			const data = await res.json();
			if (res.ok) backups = data.backups || [];
			else showToast(data.error || "Erreur", "error");
		} catch { showToast("Erreur de connexion", "error"); }
	}

	async function triggerRestore(backupPath) {
		if (!confirm("Voulez-vous vraiment restaurer cette sauvegarde ?\n\nLa base de données actuelle sera remplacée. Une sauvegarde de sécurité sera créée automatiquement.")) return;
		restoring = true;
		try {
			const res = await fetch(`${BASE}/backup/restore`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ backup_path: backupPath }),
			});
			const data = await res.json();
			if (res.ok && data.success) {
				showToast(data.message, "success");
				showBackups = false;
			} else {
				showToast(data.error || "Erreur", "error");
			}
		} catch { showToast("Erreur de connexion", "error"); }
		finally { restoring = false; }
	}

	async function saveSettings() {
		saving = true;
		try {
			const res = await fetch(`${BASE}/settings`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(settings),
			});
			if (res.ok) {
				showToast(
					"Paramètres enregistrés avec succès !",
					"success",
				);
			} else {
				showToast(
					"Erreur lors de l'enregistrement",
					"error",
				);
			}
		} catch (err) {
			showToast("Erreur de connexion au serveur", "error");
		} finally {
			saving = false;
		}
	}

	function showToast(msg, type = "success") {
		toastMessage = msg;
		toastType = type;
		setTimeout(() => {
			toastMessage = "";
		}, 4000);
	}
</script>

<div class="p-6 mx-auto space-y-6">
	<!-- Page Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold">
				Configuration du Magasin
			</h1>
			<p class="text-sm text-base-content/60">
				Gérez les coordonnées du commerce, l'en-tête du
				ticket, l'impression et les sauvegardes USB
			</p>
		</div>
		<button
			class="btn btn-primary gap-2 font-bold"
			onclick={saveSettings}
			disabled={saving || loading}
		>
			{#if saving}
				<span class="loading loading-spinner loading-sm"
				></span>
				Enregistrement...
			{:else}
				<Save size="18" /> Enregistrer les modifications
			{/if}
		</button>
	</div>

	{#if toastMessage}
		<div
			class="alert alert-{toastType} shadow-lg transition-all flex items-center gap-2"
		>
			{#if toastType === "success"}
				<CheckCircle2 size="20" />
			{:else}
				<AlertTriangle size="20" />
			{/if}
			<span>{toastMessage}</span>
		</div>
	{/if}

	{#if loading}
		<div class="flex justify-center p-12">
			<span
				class="loading loading-spinner loading-lg text-primary"
			></span>
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<!-- Section 1: Informations du Commerce -->
			<div
				class="card bg-base-100 shadow-xl border border-base-200"
			>
				<div class="card-body">
					<h2
						class="card-title text-lg border-b pb-2 mb-4 flex items-center gap-2"
					>
						<Building2
							class="text-primary"
							size="20"
						/>
						Informations Générales
					</h2>

					<div class="form-control mb-4">
						<label
							class="label font-semibold"
							for="store-name"
							>Nom du Commerce /
							Raison Sociale</label
						>
						<input
							id="store-name"
							type="text"
							class="input input-bordered w-full"
							placeholder="ex: Quincaillerie Bourguiba"
							bind:value={
								settings.store_name
							}
						/>
					</div>

					<div class="form-control mb-4">
						<label
							class="label font-semibold"
							for="tax-id"
							>Matricule Fiscal (MF)</label
						>
						<input
							id="tax-id"
							type="text"
							class="input input-bordered w-full"
							placeholder="ex: 1234567/A/M/000"
							bind:value={
								settings.tax_id
							}
						/>
					</div>

					<div class="form-control mb-4">
						<label
							class="label font-semibold"
							for="phone"
							>Numéro de Téléphone</label
						>
						<input
							id="phone"
							type="text"
							class="input input-bordered w-full"
							placeholder="ex: +216 71 123 456"
							bind:value={
								settings.phone
							}
						/>
					</div>

					<div class="form-control mb-4">
						<label
							class="label font-semibold"
							for="address"
							>Adresse du Commerce</label
						>
						<textarea
							id="address"
							class="textarea textarea-bordered w-full h-20"
							placeholder="ex: Avenue Habib Bourguiba, Tunis"
							bind:value={
								settings.address
							}
						></textarea>
					</div>

					<div class="form-control">
						<label
							class="label font-semibold"
							for="currency"
							>Symbole Monétaire</label
						>
						<input
							id="currency"
							type="text"
							class="input input-bordered w-full"
							placeholder="DT"
							bind:value={
								settings.currency
							}
						/>
					</div>
				</div>
			</div>

			<!-- Section 2: Imprimante, Ticket & Sauvegarde USB -->
			<div class="space-y-6">
				<!-- Section Sauvegarde USB -->
				<div
					class="card bg-base-100 shadow-xl border border-base-200"
				>
					<div class="card-body">
						<h2
							class="card-title text-lg border-b pb-2 mb-3 flex items-center gap-2"
						>
							<HardDrive
								class="text-secondary"
								size="20"
							/>
							Sauvegarde sur Clé USB
						</h2>
						<p
							class="text-xs text-base-content/70 mb-3"
						>
							Insérez une clé USB sur
							l'ordinateur et cliquez
							ci-dessous pour
							effectuer une copie
							intégrale de la base de
							données.
						</p>

						{#if usbDrives.length > 0}
							<div
								class="badge badge-success gap-1.5 mb-3 font-semibold p-3"
							>
								<CheckCircle2
									size="14"
								/> Clé USB détectée:
								{usbDrives[0]
									.name}
							</div>
						{:else}
							<div
								class="badge badge-ghost gap-1.5 mb-3 text-xs p-3"
							>
								<RefreshCw
									size="14"
								/> Aucune clé USB
								détectée (Insérez
								une clé USB)
							</div>
						{/if}

						<button
							class="btn btn-secondary btn-block font-extrabold gap-2 text-white shadow-md"
							onclick={triggerUsbBackup}
							disabled={backingUp}
						>
							{#if backingUp}
								<span
									class="loading loading-spinner loading-sm"
								></span>
								Sauvegarde en cours...
							{:else}
								<HardDrive
									size="18"
								/> SAUVEGARDER SUR
								CLÉ USB
							{/if}
						</button>

						<button class="btn btn-outline btn-block gap-2 mt-2"
							onclick={listBackups} disabled={restoring}>
							{#if restoring}
								<span class="loading loading-spinner loading-sm"></span>
								Restauration en cours...
							{:else}
								<HardDrive size="18" /> {showBackups ? "Masquer" : "Voir les Sauvegardes"}
							{/if}
						</button>

						{#if showBackups}
							<div class="mt-3 border border-base-300 rounded-lg overflow-hidden">
								{#if backups.length === 0}
									<div class="p-4 text-center text-base-content/40 text-sm">Aucune sauvegarde trouvée sur la clé USB.</div>
								{:else}
									<div class="divide-y divide-base-200 max-h-60 overflow-y-auto">
										{#each backups as b}
											<div class="flex items-center justify-between px-3 py-2.5 hover:bg-base-200">
												<div class="min-w-0 flex-1">
													<p class="text-sm font-medium truncate">{b.filename}</p>
													<p class="text-xs text-base-content/50">{b.date} · {(b.size / 1024).toFixed(0)} Ko</p>
												</div>
												<button class="btn btn-sm btn-warning gap-1.5 font-bold"
													onclick={() => triggerRestore(b.path)}>
													<RefreshCw size="14" /> Restaurer
												</button>
											</div>
										{/each}
									</div>
								{/if}
							</div>
						{/if}
					</div>
				</div>

				<!-- Section Format Impression -->
				<div
					class="card bg-base-100 shadow-xl border border-base-200"
				>
					<div class="card-body">
						<h2
							class="card-title text-lg border-b pb-2 mb-4 flex items-center gap-2"
						>
							<Printer
								class="text-primary"
								size="20"
							/>
							Format d'Impression
						</h2>

						<div class="form-control mb-2">
							<label
								class="label font-semibold"
								for="printer-format"
								>Format de la
								Facture / Ticket</label
							>
							<select
								id="printer-format"
								class="select select-bordered w-full font-medium"
								bind:value={
									settings.printer_format
								}
							>
								<option
									value="a4"
									>Facture
									A4
									(Imprimante
									classique
									/
									bureau)</option
								>
								<option
									value="a5"
									>Bon A5
									(Demi-page
									imprimante
									classique)</option
								>
								<option
									value="80mm"
									>Ticket
									Thermique
									80mm
									(Imprimante
									Caisse)</option
								>
								<option
									value="58mm"
									>Ticket
									Thermique
									58mm
									(Imprimante
									Caisse
									Compacte)</option
								>
							</select>
						</div>
					</div>
				</div>

				<!-- Section Message Ticket -->
				<div
					class="card bg-base-100 shadow-xl border border-base-200"
				>
					<div class="card-body">
						<h2
							class="card-title text-lg border-b pb-2 mb-4 flex items-center gap-2"
						>
							<FileText
								class="text-primary"
								size="20"
							/>
							En-tête & Pied de Ticket
						</h2>

						<div class="form-control mb-4">
							<label
								class="label font-semibold"
								for="receipt-header"
								>Message
								d'En-tête (Haut
								de
								Facture/Ticket)</label
							>
							<textarea
								id="receipt-header"
								class="textarea textarea-bordered w-full h-16"
								placeholder="ex: Bienvenue dans notre magasin !"
								bind:value={
									settings.receipt_header
								}
							></textarea>
						</div>

						<div class="form-control">
							<label
								class="label font-semibold"
								for="receipt-footer"
								>Message de Pied
								de Page (Bas de
								Facture/Ticket)</label
							>
							<textarea
								id="receipt-footer"
								class="textarea textarea-bordered w-full h-16"
								placeholder="ex: Merci de votre visite. Les articles ne sont ni repris ni échangés."
								bind:value={
									settings.receipt_footer
								}
							></textarea>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Contact Support Technique - compact footer card -->
		<div
			class="card bg-base-100 shadow border border-base-200"
		>
			<div class="card-body py-3 px-5">
				<div
					class="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm"
				>
					<span
						class="flex items-center gap-2 font-semibold text-base-content/70"
					>
						<User size="15" class="text-primary" />
						Abderraouf Talbi
					</span>
					<a
						href="tel:+21628424428"
						class="flex items-center gap-2 text-base-content/70 hover:text-primary transition-colors"
					>
						<Phone size="15" class="text-primary" />
						+216 28 424 428
					</a>
					<a
						href="mailto:abderraouf.talbi@proton.me"
						class="flex items-center gap-2 text-base-content/70 hover:text-primary transition-colors"
					>
						<Mail size="15" class="text-primary" />
						abderraouf.talbi@proton.me
					</a>
				</div>
			</div>
		</div>
	{/if}
</div>
