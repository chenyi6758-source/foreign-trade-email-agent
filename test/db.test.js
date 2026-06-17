import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp } from 'node:fs/promises'
import path from 'node:path'
import os from 'node:os'
import { initDB, upsertContact, appendThread, getThreadHistory, markProcessed, isProcessed, getDB } from '../src/db.js'

async function tempDb() {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'trade-agent-'))
  return path.join(dir, 'db.json')
}

test('database stores contacts, threads, and processed states', async () => {
  await initDB(await tempDb())
  await upsertContact({ email: 'buyer@example.com', name: 'Buyer' })
  await appendThread({
    contactEmail: 'buyer@example.com',
    direction: 'inbound',
    subject: 'Inquiry',
    body: 'Hello',
    messageId: 'm1',
  })
  await markProcessed('1:m1', 'sent')

  assert.equal(getDB().data.contacts.length, 1)
  assert.equal(getThreadHistory('buyer@example.com').length, 1)
  assert.equal(isProcessed('1:m1'), true)
})
