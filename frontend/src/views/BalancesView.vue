<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api, initial, nameOf, session } from '../api'
import { TILE_TINTS, addDays, dayMonth, euros, mediumDate, parseCents } from '../format'
import Icon from '../components/Icon.vue'
import Sheet from '../components/Sheet.vue'

const balances = ref([])
const settlements = ref([])
const expenses = ref([])
const closedMeals = ref([])
const error = ref('')
const loaded = ref(false)
const paidTo = ref([])
const showForm = ref(false)
const form = reactive({ meal_id: '', amount: '', paid_by: session.user.id })

async function load() {
  try {
    const since = addDays(new Date(), -90).toISOString()
    ;[balances.value, settlements.value, expenses.value, closedMeals.value] = await Promise.all([
      api('accounts', '/balances'),
      api('accounts', '/settlements'),
      api('accounts', '/expenses'),
      api('meals', `/meals?from=${since}`),
    ])
    closedMeals.value = closedMeals.value.filter((m) => m.status === 'closed')
  } catch (e) {
    error.value = e.message
  } finally {
    loaded.value = true
  }
}

onMounted(load)

const myBalance = computed(
  () => balances.value.find((b) => b.user_id === session.user.id)?.balance_cents ?? 0,
)

const eyebrow = computed(() => {
  if (!expenses.value.length) return 'Aucune dépense pour le moment'
  const oldest = expenses.value.reduce((a, b) => (a.created_at < b.created_at ? a : b))
  return `Depuis le ${dayMonth(oldest.created_at)}`
})

const owedToMe = computed(() => settlements.value.filter((s) => s.to_user === session.user.id))
const iOwe = computed(() => settlements.value.filter((s) => s.from_user === session.user.id))

const summary = computed(() => {
  const parts = []
  const names = owedToMe.value.map((s) => nameOf(s.from_user))
  if (names.length) {
    const list = names.length > 1 ? `${names.slice(0, -1).join(', ')} et ${names[names.length - 1]}` : names[0]
    parts.push(`${list} ${names.length > 1 ? 'te doivent' : 'te doit'}`)
  }
  iOwe.value.forEach((s) => parts.push(`tu dois ${euros(s.amount_cents)} à ${nameOf(s.to_user)}`))
  if (!parts.length) return 'Tout le monde est à jour.'
  const text = parts.join(', ')
  return `${text.charAt(0).toUpperCase()}${text.slice(1)}.`
})

// Une tuile par colocataire : ce qu'il te doit ou ce que tu lui dois, d'après les remboursements proposés.
const tiles = computed(() =>
  session.members
    .filter((m) => m.id !== session.user.id)
    .map((m, i) => {
      const owesMe = owedToMe.value.find((s) => s.from_user === m.id)
      const iOweHim = iOwe.value.find((s) => s.to_user === m.id)
      const cents = owesMe?.amount_cents ?? iOweHim?.amount_cents ?? 0
      return {
        id: m.id,
        k: initial(m.id),
        name: m.display_name,
        label: owesMe ? 'te doit' : iOweHim ? 'tu dois' : 'à jour',
        amount: euros(cents),
        palette: TILE_TINTS[i % TILE_TINTS.length],
        delay: `${70 + i * 55}ms`,
      }
    }),
)

const payButtons = computed(() => [
  ...iOwe.value.map((s) => ({ key: `${s.to_user}`, settlement: s, label: `Régler ${euros(s.amount_cents)} à ${nameOf(s.to_user)}`, on: false })),
  ...paidTo.value.map((id) => ({ key: `paid-${id}`, label: `Réglé avec ${nameOf(id)}`, on: true })),
])

async function pay(button) {
  if (button.on) return
  error.value = ''
  try {
    await api('accounts', '/payments', {
      body: { to_user: button.settlement.to_user, amount_cents: button.settlement.amount_cents },
    })
    paidTo.value = [...paidTo.value, button.settlement.to_user]
    await load()
  } catch (e) {
    error.value = e.message
  }
}

const mealsToCharge = computed(() =>
  closedMeals.value.filter((m) => !expenses.value.some((e) => e.meal_id === m.id)),
)

function openForm() {
  Object.assign(form, { meal_id: mealsToCharge.value[0]?.id ?? '', amount: '', paid_by: session.user.id })
  error.value = ''
  showForm.value = true
}

async function addExpense() {
  error.value = ''
  const cents = parseCents(form.amount)
  if (cents <= 0) {
    error.value = 'Saisis un montant supérieur à zéro.'
    return
  }
  try {
    await api('accounts', '/expenses', {
      body: { meal_id: Number(form.meal_id), amount_cents: cents, paid_by: Number(form.paid_by) },
    })
    showForm.value = false
    await load()
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="g-screen">
    <header class="g-header">
      <div class="g-header-text">
        <span class="g-eyebrow">{{ eyebrow }}</span>
        <h1 class="g-h1 is-40">Qui doit quoi</h1>
      </div>
    </header>

    <main class="g-main">
      <p v-if="error && !showForm" class="g-error" role="alert">{{ error }}</p>

      <section class="g-glass g-materialize g-hero">
        <span class="g-hero-label">{{ myBalance < 0 ? 'Tu dois' : myBalance > 0 ? 'Tu récupères' : 'Tu es à jour' }}</span>
        <span class="g-hero-amount">{{ euros(myBalance) }}</span>
        <span class="g-hero-summary">{{ summary }}</span>
      </section>

      <div v-if="tiles.length" class="g-tiles">
        <article
          v-for="t in tiles"
          :key="t.id"
          class="g-glass g-materialize g-tile"
          :style="{ backgroundImage: `linear-gradient(135deg,${t.palette.tint},rgba(255,255,255,0.34))`, animationDelay: t.delay }"
        >
          <div class="g-tile-head">
            <span class="g-avatar-m">{{ t.k }}</span>
            <span class="g-tile-name">{{ t.name }}</span>
          </div>
          <div>
            <span class="g-tile-label">{{ t.label }}</span>
            <span class="g-tile-amount" :style="{ color: t.palette.num }">{{ t.amount }}</span>
          </div>
        </article>
      </div>
      <p v-else-if="loaded" class="g-glass g-materialize g-empty">
        Tu es seul dans la coloc. Partage le code d'invitation depuis l'onglet Coloc.
      </p>

      <div class="g-actions">
        <button class="g-press g-big" @click="openForm">
          <Icon name="plus" :size="20" :stroke="2.6" />
          <span>Ajouter une dépense</span>
        </button>
        <button
          v-for="b in payButtons"
          :key="b.key"
          :class="['g-press', 'g-glass', 'g-alt', { on: b.on }]"
          :aria-disabled="b.on"
          @click="pay(b)"
        >
          {{ b.label }}
        </button>
      </div>
    </main>

    <Sheet :open="showForm" title="Ajouter une dépense" @close="showForm = false">
      <p v-if="!mealsToCharge.length" class="g-muted">
        Aucun repas clos sans dépense. Clôture d'abord les inscriptions d'un repas depuis son détail.
      </p>
      <form v-else style="display: flex; flex-direction: column; gap: 12px" @submit.prevent="addExpense">
        <label class="g-field">
          <span>Repas clos</span>
          <select v-model="form.meal_id" class="g-input" required>
            <option v-for="m in mealsToCharge" :key="m.id" :value="m.id">{{ m.title }}, {{ mediumDate(m.starts_at) }}</option>
          </select>
        </label>
        <label class="g-field">
          <span>Montant (€)</span>
          <input v-model="form.amount" class="g-input" inputmode="decimal" required placeholder="24,00" />
        </label>
        <label class="g-field">
          <span>Payé par</span>
          <select v-model="form.paid_by" class="g-input">
            <option v-for="m in session.members" :key="m.id" :value="m.id">{{ m.id === session.user.id ? 'Moi' : m.display_name }}</option>
          </select>
        </label>
        <p v-if="error" class="g-error" role="alert">{{ error }}</p>
        <button class="g-press g-big"><Icon name="plus" :size="20" :stroke="2.6" /><span>Enregistrer la dépense</span></button>
      </form>
    </Sheet>
  </div>
</template>
