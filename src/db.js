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
