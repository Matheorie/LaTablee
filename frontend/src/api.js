import { reactive } from 'vue'

function loadUser() {
  try {
    return JSON.parse(localStorage.getItem('user'))
  } catch {
    return null
  }
}

// État partagé : session de l'utilisateur et liste des colocataires (id vers nom).
export const session = reactive({
  token: localStorage.getItem('token'),
  user: loadUser(),
  members: [],
})

export function setSession(data) {
  session.token = data.access_token
  session.user = data.user
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('user', JSON.stringify(data.user))
}

export function logout() {
  session.token = null
  session.user = null
  session.members = []
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

function describe(detail) {
  if (Array.isArray(detail)) return detail.map((d) => `${d.loc.slice(1).join('.')} : ${d.msg}`).join(', ')
  return typeof detail === 'string' ? detail : 'Erreur inattendue'
}

// Les appels passent par le reverse proxy du frontend : /api/<service>/<route>.
export async function api(service, path, { method, body } = {}) {
  method = method ?? (body === undefined ? 'GET' : 'POST')
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (session.token) headers.Authorization = `Bearer ${session.token}`
  const response = await fetch(`/api/${service}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (response.status === 401 && session.token && !path.startsWith('/auth/')) {
    logout()
    throw new Error('Session expirée')
  }
  if (!response.ok) {
    let detail
    try {
      detail = (await response.json()).detail
    } catch {
      detail = null
    }
    throw new Error(describe(detail))
  }
  return response.status === 204 ? null : response.json()
}

export async function loadMembers() {
  session.members = await api('users', '/households/me/members')
}

export function nameOf(userId) {
  const member = session.members.find((m) => m.id === userId)
  return member ? member.display_name : `Utilisateur ${userId}`
}

export const initial = (userId) => nameOf(userId).trim().charAt(0).toUpperCase()

/** Position du colocataire dans la liste, hors utilisateur connecté. Sert à choisir sa couleur. */
export function otherIndex(userId) {
  return session.members.filter((m) => m.id !== session.user?.id).findIndex((m) => m.id === userId)
}
