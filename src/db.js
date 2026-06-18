import { Low } from 'lowdb'
import { JSONFile } from 'lowdb/node'
import { mkdirSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const dataDir = path.join(__dirname, '..', 'data')
const dbFile = path.join(dataDir, 'db.json')

const defaultData = {
  contacts: [],
  threads: [],
  processed: [],
  leads: [],
  drafts: [],
  followUps: [],
}

let db

function normalizeProcessed(items = []) {
  return items.map((item) => {
    if (typeof item === 'string') {
      return { id: item, status: 'processed', reason: 'legacy', timestamp: new Date().toISOString() }
    }
    return item
  })
}

export async function initDB(file = dbFile) {
  mkdirSync(path.dirname(file), { recursive: true })
  const adapter = new JSONFile(file)
  db = new Low(adapter, defaultData)
  await db.read()
  db.data = { ...defaultData, ...db.data }
  db.data.processed = normalizeProcessed(db.data.processed)
  await db.write()
  return db
}

export function getDB() {
  if (!db) throw new Error('Database is not initialized. Call initDB() first.')
  return db
}

export function getProcessedIds() {
  return getDB().data.processed.map((item) => item.id)
}

export function isProcessed(id) {
  return getProcessedIds().includes(id)
}

export async function markProcessed(id, status = 'processed', reason = '') {
  const database = getDB()
  const existing = database.data.processed.find((item) => item.id === id)
  if (existing) {
    existing.status = status
    existing.reason = reason || existing.reason
    existing.timestamp = new Date().toISOString()
  } else {
    database.data.processed.push({ id, status, reason, timestamp: new Date().toISOString() })
  }
  if (database.data.processed.length > 5000) {
    database.data.processed = database.data.processed.slice(-5000)
  }
  await database.write()
}

export async function upsertContact({ email, name = '', company = '', source = 'inbound_email' }) {
  if (!email) throw new Error('Cannot upsert a contact without email')
  const database = getDB()
  const normalized = email.toLowerCase()
  const existing = database.data.contacts.find((contact) => contact.email.toLowerCase() === normalized)
  if (existing) {
    if (name && !existing.name) existing.name = name
    if (company && !existing.company) existing.company = company
    existing.lastSeen = new Date().toISOString()
    await database.write()
    return existing
  }
  const contact = {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    email,
    name,
    company,
    source,
    status: 'active',
    createdAt: new Date().toISOString(),
    lastSeen: new Date().toISOString(),
  }
  database.data.contacts.push(contact)
  await database.write()
  return contact
}

function createId(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`
}

export async function upsertLead({
  email = '',
  company = '',
  name = '',
  website = '',
  country = '',
  source = 'manual',
  score = 0,
  tags = [],
  notes = '',
  rawText = '',
}) {
  const database = getDB()
  const normalizedEmail = email.toLowerCase()
  const normalizedWebsite = website.toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/$/, '')
  const existing = database.data.leads.find((lead) => (
    (normalizedEmail && lead.email?.toLowerCase() === normalizedEmail) ||
    (normalizedWebsite && lead.website?.toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/$/, '') === normalizedWebsite)
  ))

  if (existing) {
    existing.name = existing.name || name
    existing.company = existing.company || company
    existing.website = existing.website || website
    existing.country = existing.country || country
    existing.score = Math.max(existing.score || 0, score || 0)
    existing.tags = [...new Set([...(existing.tags || []), ...tags])]
    existing.notes = [existing.notes, notes].filter(Boolean).join('\n')
    existing.rawText = existing.rawText || rawText
    existing.updatedAt = new Date().toISOString()
    await database.write()
    return existing
  }

  const lead = {
    id: createId('lead'),
    email,
    name,
    company,
    website,
    country,
    source,
    score,
    tags,
    notes,
    rawText,
    stage: 'new',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
  database.data.leads.push(lead)
  await database.write()
  return lead
}

export function listLeads({ stage } = {}) {
  const leads = getDB().data.leads
  return stage ? leads.filter((lead) => lead.stage === stage) : leads
}

export async function updateLeadStage(id, stage) {
  const lead = getDB().data.leads.find((item) => item.id === id)
  if (!lead) throw new Error(`Lead not found: ${id}`)
  lead.stage = stage
  lead.updatedAt = new Date().toISOString()
  await getDB().write()
  return lead
}

export async function createDraft({
  leadId = '',
  to = '',
  subject,
  body,
  channel = 'email',
  status = 'draft',
  purpose = 'outreach',
}) {
  const database = getDB()
  const draft = {
    id: createId('draft'),
    leadId,
    to,
    subject,
    body,
    channel,
    purpose,
    status,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
  database.data.drafts.push(draft)
  await database.write()
  return draft
}

export function listDrafts({ status } = {}) {
  const drafts = getDB().data.drafts
  return status ? drafts.filter((draft) => draft.status === status) : drafts
}

export async function updateDraftStatus(id, status) {
  const draft = getDB().data.drafts.find((item) => item.id === id)
  if (!draft) throw new Error(`Draft not found: ${id}`)
  draft.status = status
  draft.updatedAt = new Date().toISOString()
  await getDB().write()
  return draft
}

export async function approveDraft(id) {
  return updateDraftStatus(id, 'approved')
}

export async function markDraftSent(id) {
  const database = getDB()
  const draft = database.data.drafts.find((item) => item.id === id)
  if (!draft) throw new Error(`Draft not found: ${id}`)
  draft.status = 'sent'
  draft.sentAt = new Date().toISOString()
  draft.updatedAt = new Date().toISOString()
  if (draft.leadId) {
    const lead = database.data.leads.find((item) => item.id === draft.leadId)
    if (lead && !['replied', 'quoted', 'sample', 'won', 'lost'].includes(lead.stage)) {
      lead.stage = 'contacted'
      lead.updatedAt = new Date().toISOString()
    }
  }
  await database.write()
  return draft
}

export async function scheduleFollowUp({
  leadId = '',
  contactEmail = '',
  dueAt,
  reason = 'follow-up',
  status = 'open',
}) {
  const database = getDB()
  const item = {
    id: createId('followup'),
    leadId,
    contactEmail,
    dueAt,
    reason,
    status,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
  database.data.followUps.push(item)
  await database.write()
  return item
}

export function listFollowUps({ status = 'open', dueBefore } = {}) {
  return getDB().data.followUps.filter((item) => {
    if (status && item.status !== status) return false
    if (dueBefore && new Date(item.dueAt) > new Date(dueBefore)) return false
    return true
  })
}

export async function completeFollowUp(id) {
  const item = getDB().data.followUps.find((followUp) => followUp.id === id)
  if (!item) throw new Error(`Follow-up not found: ${id}`)
  item.status = 'done'
  item.updatedAt = new Date().toISOString()
  await getDB().write()
  return item
}

export async function appendThread({ contactEmail, direction, subject, body, messageId, status = 'recorded' }) {
  const database = getDB()
  database.data.threads.push({
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    contactEmail,
    direction,
    subject,
    body,
    messageId,
    status,
    timestamp: new Date().toISOString(),
  })
  await database.write()
}

export function getThreadHistory(contactEmail, limit = 10) {
  const normalized = contactEmail.toLowerCase()
  return getDB().data.threads
    .filter((thread) => thread.contactEmail.toLowerCase() === normalized)
    .slice(-limit)
}
