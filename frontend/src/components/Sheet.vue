<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

// Feuille modale : glisse depuis le bas, se ferme par le même chemin, suit le doigt 1:1
// quand on la tire par la poignée et se ferme sur un geste rapide ou une distance suffisante.
defineProps({
  open: { type: Boolean, required: true },
  title: { type: String, required: true },
})
const emit = defineEmits(['close'])

const sheet = ref(null)
let drag = null

function onKey(event) {
  if (event.key === 'Escape') emit('close')
}

onMounted(() => document.addEventListener('keydown', onKey))
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))

function down(event) {
  event.currentTarget.setPointerCapture(event.pointerId)
  drag = { startY: event.clientY, lastY: event.clientY, lastT: event.timeStamp, velocity: 0 }
  sheet.value.style.transition = 'none'
}

function move(event) {
  if (!drag) return
  const dy = event.clientY - drag.startY
  // Résistance progressive quand on tire vers le haut, au lieu d'un arrêt net.
  const offset = dy < 0 ? -Math.sqrt(-dy) * 2 : dy
  sheet.value.style.transform = `translateY(${offset}px)`
  const dt = Math.max(event.timeStamp - drag.lastT, 1)
  drag.velocity = (event.clientY - drag.lastY) / dt
  drag.lastY = event.clientY
  drag.lastT = event.timeStamp
}

function up(event) {
  if (!drag) return
  const dy = event.clientY - drag.startY
  const velocity = drag.velocity
  drag = null
  sheet.value.style.transition = ''
  if (dy > 120 || velocity > 0.5) {
    emit('close')
  } else {
    sheet.value.style.transform = ''
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="open">
        <div class="g-scrim" @click="emit('close')"></div>
        <div class="g-sheet-wrap">
          <section
            ref="sheet"
            class="g-sheet g-glass"
            role="dialog"
            aria-modal="true"
            :aria-label="title"
          >
            <div
              class="g-grabber"
              @pointerdown="down"
              @pointermove="move"
              @pointerup="up"
              @pointercancel="up"
            ></div>
            <h2 class="g-sheet-title">{{ title }}</h2>
            <slot />
          </section>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
