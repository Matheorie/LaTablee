<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api, initial, nameOf, session } from '../api'
import { TINTS, addDays, dayNumber, euros, hour, mondayOf, shortDay, toLocalInput, weekRange } from '../format'
import Icon from '../components/Icon.vue'
import Sheet from '../components/Sheet.vue'

const weekStart = ref(mondayOf(new Date()))
const meals = ref([])
const bookings = reactive({})
const expenses = ref([])
const error = ref('')
const loaded = ref(false)
const showForm = ref(false)

const form = reactive({
  title: '',
  menu: '',
  starts_at: '',
  booking_deadline: '',
  max_portions: '',
  repeat_weeks: 1,
  cook_user_id: session.user.id,
})
let deadlineTouched = false

async function load() {
  error.value = ''
  const from = weekStart.value
  const to = new Date(addDays(from, 7).getTime() - 1)
  try {
    const [week, spent] = await Promise.all([
      api('meals', `/meals?from=${from.toISOString()}&to=${to.toISOString()}`),
      api('accounts', '/expenses'),
    ])
    meals.value = week.filter((m) => m.status !== 'cancelled')
    expenses.value = spent
    await Promise.all(
      meals.value.map(async (m) => {
        bookings[m.id] = await api('bookings', `/bookings/meals/${m.id}`)
      }),
    )
  } catch (e) {
    error.value = e.message
  } finally {
    loaded.value = true
  }
}

onMounted(load)
watch(weekStart, () => {
  loaded.value = false
  load()
})

const shiftWeek = (weeks) => (weekStart.value = addDays(weekStart.value, weeks * 7))

const cards = computed(() =>
  meals.value.map((meal, i) => {
    const booking = bookings[meal.id] ?? { participants: [], total_portions: 0 }
    const me = booking.participants.find((p) => p.user_id === session.user.id)
    const others = booking.participants.filter((p) => p.user_id !== session.user.id)
    const letters = others.map((p) => ({ key: p.user_id, k: initial(p.user_id), me: false }))
    if (me) letters.push({ key: 'me', k: initial(session.user.id), me: true })
    const expense = expenses.value.find((e) => e.meal_id === meal.id)
    let price = ''
    if (expense) {
      const parts = expense.shares.reduce((sum, s) => sum + s.portions, 0)
      price = `${euros(Math.round(expense.amount_cents / parts))} / part`
    } else if (meal.status === 'closed') {
      price = 'Prix à saisir'
    }
    const people = booking.participants.length
    const capacity = meal.max_portions ?? session.members.length
    return {
      meal,
      joined: !!me,
      letters: letters.slice(0, 5),
      more: Math.max(letters.length - 5, 0),
      count: meal.max_portions
        ? `${booking.total_portions} sur ${capacity}`
        : `${people} sur ${capacity || people}`,
      names: letters.map((l) => nameOf(l.key === 'me' ? session.user.id : l.key)).join(', '),
      price,
      palette: TINTS[i % TINTS.length],
      delay: `${Math.min(i * 60, 360)}ms`,
    }
  }),
)

function open(meal) {
  window.location.hash = `#/repas/${meal.id}`
}

// Réponse immédiate : l'interface change au toucher, puis le serveur confirme ou annule.
async function toggle(card) {
  const meal = card.meal
  const booking = bookings[meal.id]
  const previous = booking
  const mine = booking.participants.find((p) => p.user_id === session.user.id)
  bookings[meal.id] = mine
    ? {
        ...booking,
        total_portions: booking.total_portions - mine.portions,
        participants: booking.participants.filter((p) => p.user_id !== session.user.id),
      }
    : {
        ...booking,
        total_portions: booking.total_portions + 1,
        participants: [...booking.participants, { user_id: session.user.id, portions: 1 }],
      }
  error.value = ''
  try {
    if (mine) await api('bookings', `/bookings/meals/${meal.id}`, { method: 'DELETE' })
    else await api('bookings', `/bookings/meals/${meal.id}`, { method: 'PUT', body: { portions: 1 } })
  } catch (e) {
    bookings[meal.id] = previous
    error.value = e.message
  }
}

function openForm() {
  const start = new Date()
  start.setDate(start.getDate() + 1)
  start.setHours(20, 0, 0, 0)
  Object.assign(form, {
    title: '',
    menu: '',
    starts_at: toLocalInput(start),
    booking_deadline: toLocalInput(new Date(start.getTime() - 4 * 3600 * 1000)),
    max_portions: '',
    repeat_weeks: 1,
    cook_user_id: session.user.id,
  })
  deadlineTouched = false
  error.value = ''
  showForm.value = true
}

// Tant que la date limite n'est pas modifiée à la main, elle suit l'heure du repas.
watch(
  () => form.starts_at,
  (value) => {
    if (!deadlineTouched && value) {
      form.booking_deadline = toLocalInput(new Date(new Date(value).getTime() - 4 * 3600 * 1000))
    }
  },
)

async function createMeal() {
  error.value = ''
  try {
    await api('meals', '/meals', {
      body: {
        title: form.title,
        menu: form.menu,
        starts_at: new Date(form.starts_at).toISOString(),
        booking_deadline: new Date(form.booking_deadline).toISOString(),
        max_portions: form.max_portions ? Number(form.max_portions) : null,
        repeat_weeks: Number(form.repeat_weeks),
        cook_user_id: Number(form.cook_user_id),
      },
    })
    showForm.value = false
    const first = mondayOf(new Date(form.starts_at))
    if (first.getTime() === weekStart.value.getTime()) await load()
    else weekStart.value = first
  } catch (e) {
    error.value = e.message
  }
}

const bump = (field, delta, min, max) => {
  form[field] = Math.min(max, Math.max(min, Number(form[field]) + delta))
}
</script>

<template>
  <div class="g-screen">
    <header class="g-header">
      <div class="g-header-text">
        <span class="g-eyebrow">
          {{ weekRange(weekStart) }}
          <button class="g-step g-press" aria-label="Semaine précédente" @click="shiftWeek(-1)">
            <Icon name="back" :size="16" :stroke="2.6" />
          </button>
          <button class="g-step g-press" aria-label="Semaine suivante" @click="shiftWeek(1)">
            <Icon name="next" :size="16" :stroke="2.6" />
          </button>
        </span>
        <h1 class="g-h1">À table !</h1>
      </div>
      <button class="g-press g-glass g-round" aria-label="Proposer un repas" @click="openForm">
        <Icon name="plus" :stroke="2.4" />
      </button>
    </header>

    <main class="g-main">
      <p v-if="error && !showForm" class="g-error" role="alert">{{ error }}</p>

      <article
        v-for="card in cards"
        :key="card.meal.id"
        class="g-glass g-materialize g-meal"
        tabindex="0"
        role="link"
        :aria-label="`${card.meal.title}, ouvrir le détail`"
        :style="{
          backgroundImage: `linear-gradient(135deg,${card.palette.tint},rgba(255,255,255,0.34))`,
          animationDelay: card.delay,
        }"
        @click="open(card.meal)"
        @keydown.enter="open(card.meal)"
      >
        <div class="g-meal-date">
          <span class="g-meal-day" :style="{ color: card.palette.num }">{{ dayNumber(card.meal.starts_at) }}</span>
          <span class="g-meal-dow">{{ shortDay(card.meal.starts_at).replace('.', '') }}</span>
        </div>

        <div class="g-meal-body">
          <h2 class="g-meal-title">{{ card.meal.title }}</h2>
          <span class="g-meal-sub">{{ nameOf(card.meal.cook_user_id) }} cuisine · {{ hour(card.meal.starts_at) }}</span>
          <div class="g-meal-people">
            <div class="g-avatars" role="img" :aria-label="card.names ? `Inscrits : ${card.names}` : 'Aucun inscrit'">
              <span v-for="l in card.letters" :key="l.key" :class="['g-avatar-s', { 'is-me': l.me }]">{{ l.k }}</span>
              <span v-if="card.more" class="g-avatar-s">+{{ card.more }}</span>
            </div>
            <span class="g-meal-count">{{ card.count }}</span>
          </div>
        </div>

        <div class="g-meal-side">
          <button
            :class="['g-press', 'g-join', { on: card.joined }]"
            :aria-pressed="card.meal.status === 'open' ? String(card.joined) : undefined"
            :disabled="card.meal.status !== 'open'"
            @click.stop="toggle(card)"
          >
            <Icon v-if="card.joined" name="check" :size="16" :stroke="3" />
            <span>{{ card.meal.status !== 'open' ? 'Clos' : card.joined ? 'Inscrit' : 'Je mange' }}</span>
          </button>
          <span v-if="card.price" class="g-meal-price">{{ card.price }}</span>
        </div>
      </article>

      <p v-if="loaded && !cards.length && !error" class="g-glass g-materialize g-empty">
        Aucun repas cette semaine. Appuie sur + pour en proposer un.
      </p>
    </main>

    <Sheet :open="showForm" title="Proposer un repas" @close="showForm = false">
      <form class="g-sheet-form" style="display: flex; flex-direction: column; gap: 12px" @submit.prevent="createMeal">
        <label class="g-field"><span>Titre</span><input v-model="form.title" class="g-input" required maxlength="120" placeholder="Dahl de lentilles" /></label>
        <label class="g-field"><span>Menu (optionnel)</span><input v-model="form.menu" class="g-input" maxlength="2000" /></label>
        <label class="g-field"><span>Cuisinier</span>
          <select v-model="form.cook_user_id" class="g-input">
            <option v-for="m in session.members" :key="m.id" :value="m.id">{{ m.id === session.user.id ? 'Moi' : m.display_name }}</option>
          </select>
        </label>
        <label class="g-field"><span>Date et heure</span><input v-model="form.starts_at" class="g-input" type="datetime-local" required /></label>
        <label class="g-field"><span>Inscriptions jusqu'au</span><input v-model="form.booking_deadline" class="g-input" type="datetime-local" required @input="deadlineTouched = true" /></label>
        <div class="g-two">
          <label class="g-field"><span>Places max</span><input v-model="form.max_portions" class="g-input" type="number" min="1" inputmode="numeric" placeholder="Illimité" /></label>
          <div class="g-field">
            <span>Chaque semaine pendant</span>
            <div class="g-stepper">
              <button type="button" class="g-press g-glass g-round" aria-label="Moins" :disabled="Number(form.repeat_weeks) <= 1" @click="bump('repeat_weeks', -1, 1, 12)"><Icon name="minus" :size="18" :stroke="2.6" /></button>
              <span class="g-stepper-value"><span class="g-stepper-number" style="font-size: 28px">{{ form.repeat_weeks }}</span></span>
              <button type="button" class="g-press g-glass g-round" aria-label="Plus" :disabled="Number(form.repeat_weeks) >= 12" @click="bump('repeat_weeks', 1, 1, 12)"><Icon name="plus" :size="18" :stroke="2.6" /></button>
            </div>
          </div>
        </div>
        <p v-if="error" class="g-error" role="alert">{{ error }}</p>
        <button class="g-press g-big"><Icon name="plus" :size="20" :stroke="2.6" /><span>Planifier</span></button>
      </form>
    </Sheet>
  </div>
</template>
