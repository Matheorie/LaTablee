<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { loadMembers, session } from './api'
import Blobs from './components/Blobs.vue'
import TabBar from './components/TabBar.vue'
import LoginView from './views/LoginView.vue'
import PlanningView from './views/PlanningView.vue'
import MealView from './views/MealView.vue'
import BalancesView from './views/BalancesView.vue'
import HouseholdView from './views/HouseholdView.vue'

// Routage par ancre : #/repas, #/repas/12, #/comptes, #/coloc.
const hash = ref(window.location.hash)
const onHashChange = () => {
  hash.value = window.location.hash
  window.scrollTo(0, 0)
}

onMounted(() => window.addEventListener('hashchange', onHashChange))
onBeforeUnmount(() => window.removeEventListener('hashchange', onHashChange))

const route = computed(() => {
  const [tab = 'repas', id] = hash.value.replace(/^#\/?/, '').split('/')
  const known = ['repas', 'comptes', 'coloc'].includes(tab) ? tab : 'repas'
  return { tab: known, mealId: known === 'repas' && /^\d+$/.test(id ?? '') ? Number(id) : null }
})

const blobs = computed(
  () => ({ repas: 'planning', comptes: 'accounts', coloc: 'household' })[route.value.tab],
)

watch(
  () => session.token,
  (token) => {
    if (token) loadMembers().catch(() => {})
  },
  { immediate: true },
)
</script>

<template>
  <div class="g-app">
    <Blobs :preset="session.token ? blobs : 'planning'" />
    <LoginView v-if="!session.token" />
    <template v-else>
      <MealView v-if="route.mealId" :key="`meal-${route.mealId}`" :meal-id="route.mealId" />
      <PlanningView v-else-if="route.tab === 'repas'" />
      <BalancesView v-else-if="route.tab === 'comptes'" />
      <HouseholdView v-else />
      <TabBar :current="route.tab" />
    </template>
  </div>
</template>
