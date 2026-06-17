import test from 'node:test'
import assert from 'node:assert/strict'
import { extractJsonObject, classifyEmail, generateReply } from '../src/ai.js'

const config = {
  anthropic: { apiKey: 'test', model: 'test-model' },
  company: {
    name: 'Acme Export',
    products: 'LED lights',
    senderName: 'Jane',
    senderTitle: 'Sales Manager',
    replyLanguage: 'English',
  },
}

test('extractJsonObject parses fenced JSON', () => {
  assert.deepEqual(extractJsonObject('```json\n{"subject":"Hi","body":"Hello"}\n```'), {
    subject: 'Hi',
    body: 'Hello',
  })
})

test('classifyEmail falls back on invalid AI JSON', async () => {
  const client = { messages: { create: async () => ({ content: [{ text: 'not json' }] }) } }
  const result = await classifyEmail({ config, subject: 'hello', body: 'world', client })
  assert.deepEqual(result, { intent: 'general', priority: 'medium' })
})

test('generateReply returns parsed reply', async () => {
  const client = {
    messages: {
      create: async () => ({ content: [{ text: '{"subject":"Re: Inquiry","body":"Thanks for your inquiry."}' }] }),
    },
  }
  const result = await generateReply({
    config,
    inboundSubject: 'Inquiry',
    inboundBody: 'Price?',
    senderEmail: 'buyer@example.com',
    senderName: 'Buyer',
    history: [],
    client,
  })
  assert.equal(result.subject, 'Re: Inquiry')
  assert.equal(result.body, 'Thanks for your inquiry.')
})
