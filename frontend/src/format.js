// Formats d'affichage en français, alignés sur les maquettes.

const MONTHS = [
  'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
]
const SHORT_MONTHS = [
  'janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin',
  'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.',
]
const SHORT_DAYS = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.']

const dayOfMonth = (date) => (date.getDate() === 1 ? '1er' : String(date.getDate()))

/** "4,80 €" */
export const euros = (cents) => `${(Math.abs(cents) / 100).toFixed(2).replace('.', ',')} €`

/** "20 h", "19 h 30" */
export function hour(iso) {
  const date = new Date(iso)
  const minutes = date.getMinutes()
  return minutes === 0 ? `${date.getHours()} h` : `${date.getHours()} h ${String(minutes).padStart(2, '0')}`
}

export const dayNumber = (iso) => String(new Date(iso).getDate())

/** "lun." */
export const shortDay = (iso) => SHORT_DAYS[new Date(iso).getDay()]

/** "lun. 2" */
export const shortDate = (iso) => `${shortDay(iso)} ${new Date(iso).getDate()}`

/** "mercredi 4 novembre" */
export function longDate(iso) {
  const date = new Date(iso)
  const weekday = date.toLocaleDateString('fr-FR', { weekday: 'long' })
  return `${weekday} ${dayOfMonth(date)} ${MONTHS[date.getMonth()]}`
}

/** "mer. 4 novembre" */
export function mediumDate(iso) {
  const date = new Date(iso)
  return `${SHORT_DAYS[date.getDay()]} ${dayOfMonth(date)} ${MONTHS[date.getMonth()]}`
}

/** "2 au 8 novembre" ou "26 octobre au 1er novembre" */
export function weekRange(monday) {
  const sunday = addDays(monday, 6)
  const from = dayOfMonth(monday)
  const to = dayOfMonth(sunday)
  if (monday.getMonth() === sunday.getMonth()) return `${from} au ${to} ${MONTHS[sunday.getMonth()]}`
  return `${from} ${MONTHS[monday.getMonth()]} au ${to} ${MONTHS[sunday.getMonth()]}`
}

/** "1er novembre" */
export function dayMonth(iso) {
  const date = new Date(iso)
  return `${dayOfMonth(date)} ${MONTHS[date.getMonth()]}`
}

/** "lun. 2 et dim. 8 nov." : le mois n'est répété que s'il change. */
export function cookingDays(isoDates) {
  const dates = isoDates.map((iso) => new Date(iso))
  const parts = dates.map((date, i) => {
    const label = `${SHORT_DAYS[date.getDay()]} ${date.getDate()}`
    const next = dates[i + 1]
    const monthChanges = !next || next.getMonth() !== date.getMonth()
    return monthChanges ? `${label} ${SHORT_MONTHS[date.getMonth()]}` : label
  })
  if (parts.length < 2) return parts.join('')
  return `${parts.slice(0, -1).join(', ')} et ${parts[parts.length - 1]}`
}

export function addDays(date, days) {
  const copy = new Date(date)
  copy.setDate(copy.getDate() + days)
  return copy
}

/** Lundi 00:00 de la semaine contenant la date. */
export function mondayOf(date) {
  const copy = new Date(date)
  copy.setHours(0, 0, 0, 0)
  copy.setDate(copy.getDate() - ((copy.getDay() + 6) % 7))
  return copy
}

/** Valeur d'un champ datetime-local à partir d'une date. */
export function toLocalInput(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/** "12,40" ou "12.40" vers des centimes, 0 si invalide. */
export function parseCents(text) {
  const value = Number.parseFloat(String(text).replace(',', '.'))
  return Number.isFinite(value) ? Math.round(value * 100) : 0
}

// Palettes des maquettes : teinte de carte et couleur du chiffre.
export const TINTS = [
  { tint: 'rgba(232,69,44,0.42)', num: '#B02A12' },
  { tint: 'rgba(18,165,168,0.40)', num: '#0A6063' },
  { tint: 'rgba(247,178,27,0.46)', num: '#7A4B00' },
  { tint: 'rgba(122,61,184,0.36)', num: '#5B2A86' },
  { tint: 'rgba(201,184,255,0.55)', num: '#4A2C9A' },
]

// Tuiles de la page Comptes : ambre, sarcelle, rouge, lavande.
export const TILE_TINTS = [
  { tint: 'rgba(247,178,27,0.46)', num: '#7A4B00' },
  { tint: 'rgba(18,165,168,0.40)', num: '#0A6063' },
  { tint: 'rgba(232,69,44,0.42)', num: '#A82810' },
  { tint: 'rgba(201,184,255,0.55)', num: '#4A2C9A' },
]

// Pastilles des colocataires dans la liste.
export const AVATAR_COLORS = ['#FFD7C2', '#CFE3FF', '#D2EFCB', '#E6D6FF']
