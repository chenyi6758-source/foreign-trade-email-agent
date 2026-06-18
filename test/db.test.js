import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp } from 'node:fs/promises'
import path from 'node:path'
import os from 'node:os'
import {
  initDB,
  upsertContact,
  appendThread,
  getThreadHistory,
  markProcessed,
  isProcessed,
  getDB,
  upsertLead,
  listLeads,
  createDraft,
  listDrafts,
  scheduleFollowUp,
  listFollowUps,
  completeFollowUp,
  approveDraft,
  markDraftSent,
} from '../src/db.js'

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

test('database stores leads, drafts, and follow-ups', async () => {
  await initDB(await tempDb())
  const lead = await upsertLead({ email: 'lead@example.com', company: 'Lead Co', score: 88 })
  const draft = await createDraft({
    leadId: lead.id,
    to: lead.email,
    subject: 'Hello',
    body: 'Draft body',
  })
  await scheduleFollowUp({
    leadId: lead.id,
    contactEmail: lead.email,
    dueAt: new Date(Date.now() + 86400000).toISOString(),
  })

  assert.equal(listLeads().length, 1)
  assert.equal(listDrafts()[0].id, draft.id)
  assert.equal(listFollowUps().length, 1)
})

test('database updates lead workflow states', async () => {
  await initDB(await tempDb())
  const lead = await upsertLead({ email: 'lead@example.com', company: 'Lead Co', score: 88 })
  const draft = await createDraft({
    leadId: lead.id,
    to: lead.email,
    subject: 'Hello',
    body: 'Draft body',
  })
  const followUp = await scheduleFollowUp({
    leadId: lead.id,
    contactEmail: lead.email,
    dueAt: new Date(Date.now() + 86400000).toISOString(),
  })

  assert.equal((await approveDraft(draft.id)).status, 'approved')
  assert.equal((await markDraftSent(draft.id)).status, 'sent')
  assert.equal(listLeads()[0].stage, 'contacted')
  assert.equal((await completeFollowUp(followUp.id)).status, 'done')
  assert.equal(listFollowUps().some((item) => item.id === followUp.id), false)
})
