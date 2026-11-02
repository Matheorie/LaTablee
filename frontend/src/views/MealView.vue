<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, nameOf, otherIndex, session } from '../api'
import { AVATAR_COLORS, TINTS, euros, hour, longDate, mediumDate, parseCents } from '../format'
import Icon from '../components/Icon.vue'

const props = defineProps({ mealId: { type: Number, required: true } })

const meal = ref(null)
const booking = ref({ participants: [], total_portions: 0 })
const expense = ref(null)
const portions = ref(1)
const amount = ref('')
const error = ref('')
const busy = ref(false)

const mine = computed(() => booking.value.participants.find((p) => p.user_id === session.user.id))
const isCook = computed(() => meal.value?.cook_user_id === session.user.id)
const open = computed(() => meal.value?.status === 'open')
const palette = computed(() => TINTS[props.mealId % TINTS.length])
const status = computed(
  () => ({ open: 'Inscriptions ouvertes', closed: 'Clos', cancelled: 'Annulé' })[meal.value?.status],
)

const people = computed(() =>
  booking.value.participants.map((p) => {
    const isMe = p.user_id === session.user.id
    return {
      id: p.user_id,
      isMe,
      k: nameOf(p.user_id).charAt(0).toUpperCase(),
      name: isMe ? 'Toi' : nameOf(p.user_id),
      sub: `${p.portions} part${p.portions > 1 ? 's' : ''}`,
      bg: isMe ? '#1B1530' : AVATAR_COLORS[otherIndex(p.user_id) % AVATAR_COLORS.length],
      fg: isMe ? '#FFFFFF' : '#1B1530',
    }
  }),
)

async function load() {
  try {
    meal.value = await api('meals', `/meals/${props.mealId}`)
    booking.value = await api('bookings', `/bookings/meals/${props.mealId}`)
    portions.value = mine.value?.portions ?? portions.value
    const expenses = await api('accounts', '/expenses')
    expense.value = expenses.find((e) => e.meal_id === props.mealId) ?? null
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)

async function run(action) {
  error.value = ''
  busy.value = true
  try {
    await action()
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

const bump = (delta) => (portions.value = Math.min(20, Math.max(1, portions.value + delta)))
const save = () =>
  run(() => api('bookings', `/bookings/meals/${props.mealId}`, { method: 'PUT', body: { portions: portions.value } }))
const unbook = () => run(() => api('bookings', `/bookings/meals/${props.mealId}`, { method: 'DELETE' }))
const close = () => run(() => api('meals', `/meals/${props.mealId}/close`, { method: 'POST' }))
const cancel = () =>
  run(async () => {
    await api('meals', `/meals/${props.mealId}`, { method: 'DELETE' })
    window.location.hash = '#/repas'
  })

function addExpense() {
  const cents = parseCents(amount.value)
  if (cents <= 0) {
    error.value = 'Saisis un montant supérieur à zéro.'
    return
  }
  run(() => api('accounts', '/expenses', { body: { meal_id: props.mealId, amount_cents: cents } }))
}
</script>

<template>
  <div class="g-screen">
    <header class="g-header">
      <div class="g-header-text">
        <span class="g-eyebrow">{{ meal ? `${longDate(meal.starts_at)} · ${hour(meal.starts_at)}` : ' ' }}</span>
        <h1 class="g-h1 is-40 is-wrap">{{ meal?.title ?? ' ' }}</h1>
      </div>
      <a class="g-press g-glass g-round" href="#/repas" aria-label="Retour au planning">
        <Icon name="back" :stroke="2.4" />
      </a>
    </header>

    <main v-if="meal" class="g-main">
      <p v-if="error" class="g-error" role="alert">{{ error }}</p>

      <section
        class="g-glass g-materialize g-card"
        :style="{ backgroundImage: `linear-gradient(135deg,${palette.tint},rgba(255,255,255,0.34))` }"
      >
        <span class="g-chip">{{ status }}</span>
        <p class="g-text"><strong>{{ nameOf(meal.cook_user_id) }}</strong> cuisine</p>
        <p v-if="meal.menu" class="g-text">{{ meal.menu }}</p>
        <p class="g-muted">
          Inscriptions jusqu'au {{ mediumDate(meal.booking_deadline) }}, {{ hour(meal.booking_deadline) }}
        </p>
      </section>

      <section class="g-glass g-materialize g-card" style="animation-delay: 60ms">
        <h2 class="g-card-title">
          {{ booking.total_portions }} part{{ booking.total_portions > 1 ? 's' : '' }}
          <template v-if="meal.max_portions">sur {{ meal.max_portions }}</template>
        </h2>
        <p v-if="!people.length" class="g-muted">Personne n'est encore inscrit.</p>
        <div v-else style="margin: 0 -18px">
          <article v-for="p in people" :key="p.id" class="g-row">
            <span class="g-avatar-l" :style="{ background: p.bg, color: p.fg }">{{ p.k }}</span>
            <div class="g-row-text">
              <span class="g-row-name">{{ p.name }}</span>
              <span class="g-row-sub">{{ p.sub }}</span>
            </div>
          </article>
        </div>
      </section>

      <section v-if="open" class="g-glass g-materialize g-card" style="animation-delay: 120ms">
        <h2 class="g-card-title">{{ mine ? 'Ton inscription' : 'Je mange' }}</h2>
        <div class="g-stepper">
          <button class="g-press g-glass g-round" aria-label="Une part de moins" :disabled="portions <= 1" @click="bump(-1)">
            <Icon name="minus" :size="20" :stroke="2.6" />
          </button>
          <span class="g-stepper-value">
            <span class="g-stepper-number">{{ portions }}</span>
            <span class="g-muted">{{ portions === 1 ? 'toi seul' : `toi + ${portions - 1} invité${portions > 2 ? 's' : ''}` }}</span>
          </span>
          <button class="g-press g-glass g-round" aria-label="Une part de plus" :disabled="portions >= 20" @click="bump(1)">
            <Icon name="plus" :size="20" :stroke="2.6" />
          </button>
        </div>
        <button class="g-press g-big" :disabled="busy" @click="save">
          <Icon v-if="mine" name="check" :size="20" :stroke="2.6" />
          <span>{{ mine ? 'Mettre à jour' : "Je m'inscris" }}</span>
        </button>
        <button v-if="mine" class="g-press g-glass g-alt" :disabled="busy" @click="unbook">Me désinscrire</button>
      </section>

      <section v-if="open && isCook" class="g-glass g-materialize g-card" style="animation-delay: 180ms">
        <h2 class="g-card-title">Cuisinier</h2>
        <button class="g-press g-big" :disabled="busy" @click="close">Clôturer les inscriptions</button>
        <button class="g-press g-glass g-alt" :disabled="busy" @click="cancel">Annuler le repas</button>
      </section>

      <section v-if="meal.status === 'closed'" class="g-glass g-materialize g-card" style="animation-delay: 180ms">
        <h2 class="g-card-title">Dépense</h2>
        <template v-if="expense">
          <p class="g-text">
            <strong>{{ euros(expense.amount_cents) }}</strong> payés par {{ nameOf(expense.paid_by) }}
          </p>
          <div style="margin: 0 -18px">
            <article v-for="s in expense.shares" :key="s.user_id" class="g-row">
              <div class="g-row-text">
                <span class="g-row-name">{{ nameOf(s.user_id) }}</span>
                <span class="g-row-sub">{{ s.portions }} part{{ s.portions > 1 ? 's' : '' }}</span>
              </div>
              <span class="g-row-end">{{ euros(s.amount_cents) }}</span>
            </article>
          </div>
        </template>
        <form v-else style="display: flex; flex-direction: column; gap: 12px" @submit.prevent="addExpense">
          <label class="g-field">
            <span>Montant payé par toi (€)</span>
            <input v-model="amount" class="g-input" inputmode="decimal" required placeholder="24,00" />
          </label>
          <button class="g-press g-big" :disabled="busy"><Icon name="plus" :size="20" :stroke="2.6" /><span>Saisir la dépense</span></button>
        </form>
      </section>
    </main>
  </div>
</template>
