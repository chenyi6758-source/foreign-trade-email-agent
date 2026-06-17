import test from 'node:test'
import assert from 'node:assert/strict'
import { buildLeadRecord, buildOutreachDraft, extractLeadSignals, parseLeadCsv, scoreLead } from '../src/leads.js'
import { buildDailyDigest } from '../src/market_intel.js'
import { whatsappStatus } from '../src/whatsapp.js'

test('extractLeadSignals finds emails, websites, and domains', () => {
  const signals = extractLeadSignals('Email buyer@example.com and visit www.example.com')
  assert.deepEqual(signals.emails, ['buyer@example.com'])
  assert.equal(signals.websites[0], 'https://www.example.com')
  assert.ok(signals.domains.includes('example.com'))
})

test('scoreLead rewards contact signals and target keywords', () => {
  const score = scoreLead({
    text: 'LED importer procurement@example.com www.example.com',
    targetKeywords: ['LED'],
  })
  assert.ok(score >= 70)
})

test('buildLeadRecord returns a portable lead object', () => {
  const lead = buildLeadRecord({ text: 'buyer@example.com', source: 'test' })
  assert.equal(lead.source, 'test')
  assert.equal(lead.emails[0], 'buyer@example.com')
})

test('parseLeadCsv maps rows into lead records', () => {
  const [lead] = parseLeadCsv('company,name,email,website,country,notes\nABC,John,john@example.com,www.example.com,US,LED buyer', {
    targetKeywords: ['LED'],
  })
  assert.equal(lead.company, 'ABC')
  assert.equal(lead.email, 'john@example.com')
  assert.ok(lead.score >= 60)
})

test('buildOutreachDraft creates a first-touch email draft', () => {
  const draft = buildOutreachDraft({
    lead: { email: 'buyer@example.com', company: 'ABC', name: 'John' },
    companyProfile: {
      name: 'Export Co',
      products: 'LED lights',
      senderName: 'Jane',
      senderTitle: 'Sales Manager',
    },
  })
  assert.equal(draft.to, 'buyer@example.com')
  assert.match(draft.body, /LED lights/)
})

test('buildDailyDigest summarizes tags', () => {
  const digest = buildDailyDigest([{ title: 'A', tags: ['EU'] }, { title: 'B', tags: ['EU', 'solar'] }])
  assert.equal(digest.totalItems, 2)
  assert.deepEqual(digest.topTags[0], { tag: 'EU', count: 2 })
})

test('whatsappStatus is explicit about not being connected', () => {
  assert.equal(whatsappStatus().status, 'not-connected')
})
