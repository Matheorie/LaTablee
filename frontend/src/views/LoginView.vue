<script setup>
import { reactive, ref } from 'vue'
import { api, setSession } from '../api'

// Trois modes : connexion, création d'une colocation, rejoindre avec un code.
const mode = ref('login')
const form = reactive({ email: '', password: '', display_name: '', household_name: '', invite_code: '' })
const error = ref('')
const busy = ref(false)

const modes = [
  { id: 'login', label: 'Connexion' },
  { id: 'create', label: 'Nouvelle coloc' },
  { id: 'join', label: 'Rejoindre' },
]

async function submit() {
  error.value = ''
  busy.value = true
  try {
    let data
    if (mode.value === 'login') {
      data = await api('users', '/auth/login', { body: { email: form.email, password: form.password } })
    } else {
      const body = { email: form.email, password: form.password, display_name: form.display_name }
      if (mode.value === 'create') body.household_name = form.household_name
      else body.invite_code = form.invite_code
      data = await api('users', '/auth/register', { body })
    }
    setSession(data)
    window.location.hash = '#/repas'
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="g-screen">
    <header class="g-header">
      <div class="g-header-text">
        <span class="g-eyebrow">Les repas partagés de la coloc</span>
        <h1 class="g-h1">À table !</h1>
      </div>
    </header>

    <main class="g-main">
      <div class="g-glass g-segmented g-materialize" role="tablist">
        <button
          v-for="m in modes"
          :key="m.id"
          type="button"
          role="tab"
          :aria-selected="mode === m.id"
          :class="['g-tab', 'g-press', { cur: mode === m.id }]"
          style="min-height: 44px; padding: 0 4px; cursor: pointer; background-color: transparent"
          @click="mode = m.id"
        >
          {{ m.label }}
        </button>
      </div>

      <form class="g-glass g-materialize g-card" style="animation-delay: 60ms" @submit.prevent="submit">
        <label class="g-field">
          <span>Email</span>
          <input v-model="form.email" class="g-input" type="email" required autocomplete="email" />
        </label>
        <label class="g-field">
          <span>Mot de passe</span>
          <input
            v-model="form.password"
            class="g-input"
            type="password"
            required
            minlength="8"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
          />
        </label>
        <template v-if="mode !== 'login'">
          <label class="g-field">
            <span>Prénom</span>
            <input v-model="form.display_name" class="g-input" required maxlength="50" autocomplete="given-name" />
          </label>
          <label v-if="mode === 'create'" class="g-field">
            <span>Nom de la coloc</span>
            <input v-model="form.household_name" class="g-input" required maxlength="100" />
          </label>
          <label v-else class="g-field">
            <span>Code d'invitation</span>
            <input v-model="form.invite_code" class="g-input" required placeholder="TABLE-XXXX" autocapitalize="characters" />
          </label>
        </template>
        <p v-if="error" class="g-error" role="alert">{{ error }}</p>
        <button class="g-press g-big" :disabled="busy">
          {{ mode === 'login' ? 'Se connecter' : 'Créer mon compte' }}
        </button>
      </form>
    </main>
  </div>
</template>
