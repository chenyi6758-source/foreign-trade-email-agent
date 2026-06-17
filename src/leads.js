import { parseArgs } from './config.js'

const EMAIL_PATTERN = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi
const URL_PATTERN = /\bhttps?:\/\/[^\s)>"']+|\b(?:www\.)[^\s)>"']+/gi

export function extractLeadSignals(text = '') {
  const emails = [...new Set(text.match(EMAIL_PATTERN) || [])]
  const websites = [...new Set((text.match(URL_PATTERN) || []).map((url) => {
    const trimmed = url.replace(/[.,;:!?]+$/g, '')
    return trimmed.startsWith('http') ? trimmed : `https://${trimmed}`
  }))]
  const domains = [...new Set([
    ...emails.map((email) => email.split('@')[1].toLowerCase()),
    ...websites.map((url) => {
      try {
        return new URL(url).hostname.replace(/^www\./, '').toLowerCase()
      } catch {
        return ''
      }
    }).filter(Boolean),
  ])]
  return { emails, websites, domains }
}

export function scoreLead({ text = '', targetKeywords = [] }) {
  const normalized = text.toLowerCase()
  const signals = extractLeadSignals(text)
  let score = 0
  if (signals.emails.length) score += 30
  if (signals.websites.length) score += 20
  for (const keyword of targetKeywords) {
    if (normalized.includes(keyword.toLowerCase())) score += 10
  }
  if (/\b(importer|distributor|wholesaler|buyer|procurement|sourcing)\b/i.test(text)) score += 20
  return Math.min(score, 100)
}

export function buildLeadRecord({ text, source = 'manual', targetKeywords = [] }) {
  const signals = extractLeadSignals(text)
  return {
    source,
    score: scoreLead({ text, targetKeywords }),
    emails: signals.emails,
    websites: signals.websites,
    domains: signals.domains,
    rawText: text.slice(0, 1000),
    createdAt: new Date().toISOString(),
  }
}

function runDemo() {
  const sample = `ABC Lighting Importers is a wholesale buyer for LED flood lights.
Contact procurement@abclighting.example or visit www.abclighting.example.`
  console.log(JSON.stringify(buildLeadRecord({
    text: sample,
    source: 'demo',
    targetKeywords: ['LED', 'lighting', 'importer'],
  }), null, 2))
}

const args = parseArgs()
if (args.has('--demo')) runDemo()
