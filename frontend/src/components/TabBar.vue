<script setup>
import Icon from './Icon.vue'

defineProps({ current: { type: String, required: true } })

const tabs = [
  { id: 'repas', label: 'Repas', icon: 'calendar' },
  { id: 'comptes', label: 'Comptes', icon: 'wallet' },
  { id: 'coloc', label: 'Coloc', icon: 'people' },
]
</script>

<template>
  <nav class="g-nav g-glass" aria-label="Navigation principale">
    <a
      v-for="tab in tabs"
      :key="tab.id"
      :href="`#/${tab.id}`"
      :class="['g-tab', { cur: current === tab.id }]"
      :aria-current="current === tab.id ? 'page' : undefined"
    >
      <Icon :name="tab.icon" />
      <span>{{ tab.label }}</span>
    </a>
  </nav>
</template>
