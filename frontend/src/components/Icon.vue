<script setup>
// Icônes des maquettes (viewBox 24, trait arrondi).
defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 22 },
  stroke: { type: Number, default: 2 },
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="stroke"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path v-if="name === 'plus'" d="M12 5v14M5 12h14" />
    <path v-else-if="name === 'minus'" d="M5 12h14" />
    <path v-else-if="name === 'check'" d="M5 12.5l4.5 4.5L19 7.5" />
    <path v-else-if="name === 'back'" d="M15 5l-7 7 7 7" />
    <path v-else-if="name === 'next'" d="M9 5l7 7-7 7" />
    <template v-else-if="name === 'calendar'">
      <rect x="3" y="5" width="18" height="16" rx="4" />
      <path d="M3 10h18M8 3v4M16 3v4" />
    </template>
    <template v-else-if="name === 'wallet'">
      <path d="M4 8a2 2 0 0 1 2-2h12v3" />
      <rect x="3" y="9" width="18" height="11" rx="4" />
      <circle cx="16.5" cy="14.5" r="1" />
    </template>
    <template v-else-if="name === 'people'">
      <circle cx="9" cy="8" r="3.2" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
      <circle cx="17" cy="9" r="2.6" />
      <path d="M17.5 14.2c2.4.3 4.5 2.3 4.5 5.3" />
    </template>
  </svg>
</template>
