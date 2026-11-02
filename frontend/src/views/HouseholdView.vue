<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { api, otherIndex, session } from '../api'
import { AVATAR_COLORS, addDays, cookingDays, mondayOf } from '../format'
import Icon from '../components/Icon.vue'

const household = ref(null)
const meals = ref([])
const error = ref('')
const copied = ref(false)
let resetTimer = null

onMounted(async () => {
  try {
    const monday = mondayOf(new Date())
    const to = new Date(addDays(monday, 7).getTime() - 1)
    ;[household.value, meals.value] = await Promise.all([
      api('users', '/households/me'),
      api('meals', `/meals?from=${monday.toISOString()}&to=${to.toISOString()}`),
    ])
  } catch (e) {
    error.value = e.message
  }
})

onBeforeUnmount(() => clearTimeout(resetTimer))

const members = computed(() => {
  const me = session.members.find((m) => m.id === session.user.id)
  const ordered = me ? [me, ...session.members.filter((m) => m.id !== me.id)] : session.members
  return ordered.map((m) => {
    const days = meals.value
      .filter((meal) => meal.status !== 'cancelled' && meal.cook_user_id === m.id)
      .map((meal) => meal.starts_at)
    const isMe = m.id === session.user.id
    return {
      id: m.id,
      isMe,
      k: m.display_name.charAt(0).toUpperCase(),
      name: isMe ? 'Toi' : m.display_name,
      sub: days.length ? `Cuisine ${cookingDays(days)}` : 'Aucun repas prévu cette semaine',
      bg: isMe ? '#1B1530' : AVATAR_COLORS[otherIndex(m.id) % AVATAR_COLORS.length],
      fg: isMe ? '#FFFFFF' : '#1B1530',
    }
  })
})

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

async function copy() {
  if (!household.value || !(await copyText(household.value.invite_code))) return
  copied.value = true
  clearTimeout(resetTimer)
  resetTimer = setTimeout(() => (copied.value = false), 1800)
}

async function invite() {
  if (!household.value) return
  const text = `Rejoins ${household.value.name} sur LaTablee avec le code ${household.value.invite_code}`
  if (navigator.share) {
    try {
      await navigator.share({ text })
      return
    } catch (e) {
      if (e.name === 'AbortError') return
    }
  }
  if (await copyText(text)) {
    copied.value = true
    clearTimeout(resetTimer)
    resetTimer = setTimeout(() => (copied.value = false), 1800)
  }
}
</script>

<template>
  <div class="g-screen">
    <header class="g-header">
      <div class="g-header-text">
        <span class="g-eyebrow">{{ members.length }} colocataire{{ members.length > 1 ? 's' : '' }}</span>
        <h1 class="g-h1">La coloc</h1>
      </div>
    </header>

    <main class="g-main">
      <p v-if="error" class="g-error" role="alert">{{ error }}</p>

      <section class="g-glass g-materialize g-list">
        <article v-for="p in members" :key="p.id" class="g-row">
          <span class="g-avatar-l" :style="{ background: p.bg, color: p.fg }">{{ p.k }}</span>
          <div class="g-row-text">
            <span class="g-row-name">{{ p.name }}</span>
            <span class="g-row-sub">{{ p.sub }}</span>
          </div>
        </article>
      </section>

      <section v-if="household" class="g-glass g-materialize g-invite">
        <div>
          <span class="g-invite-label">Code d’invitation</span>
          <span class="g-invite-code">{{ household.invite_code }}</span>
        </div>
        <button :class="['g-press', 'g-join', 'is-wide', { on: copied }]" @click="copy">
          <Icon v-if="copied" name="check" :size="16" :stroke="3" />
          <span>{{ copied ? 'Copié' : 'Copier' }}</span>
        </button>
      </section>

      <button class="g-press g-big" style="margin-top: 6px" :disabled="!household" @click="invite">
        <Icon name="plus" :size="20" :stroke="2.6" />
        <span>Inviter un colocataire</span>
      </button>
    </main>
  </div>
</template>
