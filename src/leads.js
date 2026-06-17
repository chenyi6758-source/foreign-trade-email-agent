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

function splitCsvLine(line) {
  const cells = []
  let current = ''
  let quoted = false
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i]
    const next = line[i + 1]
    if (char === '"' && quoted && next === '"') {
      current += '"'
      i += 1
    } else if (char === '"') {
      quoted = !quoted
    } else if (char === ',' && !quoted) {
      cells.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  cells.push(current.trim())
  return cells
}

export function parseLeadCsv(csvText = '', { source = 'csv', targetKeywords = [] } = {}) {
  const lines = csvText.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
  if (lines.length === 0) return []
  const headers = splitCsvLine(lines[0]).map((header) => header.toLowerCase())
  return lines.slice(1).map((line) => {
    const cells = splitCsvLine(line)
    const row = Object.fromEntries(headers.map((header, index) => [header, cells[index] || '']))
    const rawText = [
      row.company,
      row.name,
      row.email,
      row.website,
      row.country,
      row.notes,
      row.product,
      row.keyword,
    ].filter(Boolean).join(' ')
    const signals = extractLeadSignals(rawText)
    return {
      email: row.email || signals.emails[0] || '',
      name: row.name || row.contact || '',
      company: row.company || '',
      website: row.website || signals.websites[0] || '',
      country: row.country || row.market || '',
      source,
      score: scoreLead({ text: rawText, targetKeywords }),
      tags: targetKeywords.filter((keyword) => rawText.toLowerCase().includes(keyword.toLowerCase())),
      notes: row.notes || '',
      rawText,
    }
  })
}

export function buildOutreachDraft({ lead, companyProfile = {} }) {
  const companyName = companyProfile.name || 'our company'
  const products = companyProfile.products || 'our products'
  const senderName = companyProfile.senderName || 'Sales Team'
  const senderTitle = companyProfile.senderTitle || 'Foreign Trade Manager'
  const recipient = lead.name || 'there'
  const subjectCompany = lead.company ? ` for ${lead.company}` : ''
  return {
    to: lead.email,
    subject: `Product cooperation${subjectCompany}`,
    body: `Hi ${recipient},

I noticed ${lead.company || 'your company'} may be interested in ${products}. I am ${senderName}, ${senderTitle} at ${companyName}.

Could I send you a short catalog and quotation for your market? If you have target specifications, quantity, or certification requirements, I can prepare a more accurate proposal.

Best regards,
${senderName}`,
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
