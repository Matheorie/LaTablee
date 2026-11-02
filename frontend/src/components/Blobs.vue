<script setup>
import { computed } from 'vue'

const COLORS = {
  red: '#E8452C',
  amber: '#F7B21B',
  teal: '#12A5A8',
  purple: '#7A3DB8',
  blue: '#3F73E8',
  pink: '#E0509A',
}

// Téléphone : positions des maquettes (cadre 390 x 844), [couleur, gauche, haut, taille] en px.
// Grand écran : centres en pourcentage de l'écran, répartis en zigzag sur toute la largeur.
const PRESETS = {
  planning: {
    phone: [
      ['red', -60, 150, 230],
      ['amber', 210, 290, 220],
      ['teal', -70, 520, 250],
      ['purple', 200, 640, 230],
      ['blue', 230, 20, 200],
      ['pink', -50, 760, 210],
    ],
    wide: [
      ['red', 8, 25],
      ['teal', 26, 78],
      ['amber', 44, 16],
      ['purple', 62, 84],
      ['blue', 80, 28],
      ['pink', 94, 76],
    ],
  },
  accounts: {
    phone: [
      ['purple', 180, 90, 240],
      ['amber', -70, 330, 230],
      ['teal', 220, 430, 220],
      ['red', -40, 600, 240],
      ['blue', -60, 40, 200],
      ['pink', 230, 720, 210],
    ],
    wide: [
      ['purple', 8, 70],
      ['amber', 26, 22],
      ['teal', 44, 86],
      ['red', 62, 20],
      ['pink', 80, 76],
      ['blue', 94, 26],
    ],
  },
  household: {
    phone: [
      ['teal', 200, 80, 230],
      ['red', -70, 260, 230],
      ['amber', 220, 470, 220],
      ['purple', -50, 600, 250],
      ['blue', -60, 30, 190],
      ['pink', 220, 700, 210],
    ],
    wide: [
      ['teal', 8, 28],
      ['red', 26, 80],
      ['amber', 44, 20],
      ['purple', 62, 82],
      ['blue', 80, 24],
      ['pink', 94, 72],
    ],
  },
}

const props = defineProps({ preset: { type: String, default: 'planning' } })

// Les deux compositions sont portées par des variables CSS, la feuille de style choisit
// selon la largeur d'écran (voir .g-blob dans style.css).
const blobs = computed(() => {
  const { phone, wide } = PRESETS[props.preset]
  return phone.map(([color, left, top, size], i) => ({
    '--c': COLORS[color],
    '--wc': COLORS[wide[i][0]],
    '--l': `${left}px`,
    '--t': `${top}px`,
    '--s': `${size}px`,
    '--wl': `${wide[i][1]}%`,
    '--wt': `${wide[i][2]}%`,
  }))
})
</script>

<template>
  <div class="g-bg" aria-hidden="true">
    <div v-for="(style, i) in blobs" :key="i" class="g-blob" :style="style"></div>
  </div>
</template>
