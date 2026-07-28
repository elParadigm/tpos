<script>
    import { goto } from '$app/navigation';
    import { currentWorker } from '$lib/auth';
    import { Delete, LogIn, Lock } from '@lucide/svelte';

    import { BASE } from '$lib/config';

    let pin = $state('');
    let error = $state('');
    let loading = $state(false);

    async function handleLogin() {
        if (pin.length < 4) { error = 'Le code PIN doit comporter au moins 4 chiffres'; return; }
        loading = true;
        error = '';
        try {
            const res = await fetch(`${BASE}/workers/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin })
            });
            const data = await res.json();
            if (!res.ok) { error = data.error || 'Code PIN incorrect'; return; }
            currentWorker.set(data);
            goto('/pos');
        } catch (e) {
            error = 'Erreur de connexion au serveur';
        } finally {
            loading = false;
            pin = '';
        }
    }

    function pressKey(key) {
        if (key === 'del') { pin = pin.slice(0, -1); return; }
        if (pin.length >= 6) return;
        pin += key;
    }
</script>

<div class="min-h-screen flex items-center justify-center bg-base-200">
    <div class="card bg-base-100 shadow-2xl border border-base-300 w-88">
        <div class="card-body items-center gap-4">
            <div class="p-3 bg-primary/10 rounded-full text-primary">
                <Lock size="32" />
            </div>
            
            <h1 class="text-xl font-bold text-center">Connexion Caissier / Gérant</h1>
            <p class="text-xs text-base-content/60 text-center">Saisissez votre code PIN pour ouvrir la caisse</p>

            <!-- PIN dots -->
            <div class="flex gap-3 my-2">
                {#each Array(6) as _, i}
                <div class="w-4 h-4 rounded-full border-2 transition-all
                    {i < pin.length ? 'bg-primary border-primary scale-110' : 'border-base-300'}">
                </div>
                {/each}
            </div>

            {#if error}
                <div class="alert alert-error text-xs py-2 w-full">{error}</div>
            {/if}

            <!-- Numpad -->
            <div class="grid grid-cols-3 gap-2 w-full">
                {#each ['1','2','3','4','5','6','7','8','9','','0','del'] as key}
                    {#if key === ''}
                        <div></div>
                    {:else}
                        <button
                            class="btn btn-outline text-lg h-14 font-mono font-bold
                                {key === 'del' ? 'btn-error' : ''}"
                            onclick={() => pressKey(key)}>
                            {#if key === 'del'}
                                <Delete size="20" />
                            {:else}
                                {key}
                            {/if}
                        </button>
                    {/if}
                {/each}
            </div>

            <button class="btn btn-primary w-full font-bold gap-2 text-white shadow-md"
                onclick={handleLogin}
                disabled={loading || pin.length < 4}>
                {#if loading}
                    <span class="loading loading-spinner loading-sm"></span>
                    Connexion...
                {:else}
                    <LogIn size="18" /> Se Connecter
                {/if}
            </button>
        </div>
    </div>
</div>
