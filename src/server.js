import http from 'node:http'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { getConfig } from './config.js'
import {
  initDB,
  getDB,
  listLeads,
  upsertLead,
  listDrafts,
  createDraft,
  listFollowUps,
  scheduleFollowUp,
} from './db.js'
import { buildOutreachDraft, parseLeadCsv } from './leads.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const publicDir = path.join(__dirname, '..', 'public')
const port = Number.parseInt(process.env.PORT || '8787', 10)

function json(res, statusCode, payload) {
  res.writeHead(statusCode, { 'content-type': 'application/json; charset=utf-8' })
  res.end(JSON.stringify(payload, null, 2))
}

async function readJson(req) {
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  if (chunks.length === 0) return {}
  return JSON.parse(Buffer.concat(chunks).toString('utf8'))
}

function buildSummary() {
  const db = getDB()
  const openFollowUps = listFollowUps({ status: 'open' })
  return {
    contacts: db.data.contacts.length,
    leads: db.data.leads.length,
    drafts: db.data.drafts.length,
    openFollowUps: openFollowUps.length,
    highScoreLeads: db.data.leads.filter((lead) => lead.score >= 70).length,
  }
}

async function routeApi(req, res, url) {
  if (req.method === 'GET' && url.pathname === '/api/summary') {
    json(res, 200, buildSummary())
    return true
  }
  if (req.method === 'GET' && url.pathname === '/api/leads') {
    json(res, 200, listLeads().sort((a, b) => (b.score || 0) - (a.score || 0)))
    return true
  }
  if (req.method === 'GET' && url.pathname === '/api/drafts') {
    json(res, 200, listDrafts())
    return true
  }
  if (req.method === 'GET' && url.pathname === '/api/followups') {
    json(res, 200, listFollowUps({ status: 'open' }))
    return true
  }
  if (req.method === 'POST' && url.pathname === '/api/leads/import') {
    const body = await readJson(req)
    const targetKeywords = String(body.targetKeywords || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
    const parsed = parseLeadCsv(body.csv || '', { source: 'dashboard-csv', targetKeywords })
    const saved = []
    for (const lead of parsed) {
      saved.push(await upsertLead(lead))
    }
    json(res, 200, { imported: saved.length, leads: saved })
    return true
  }
  if (req.method === 'POST' && url.pathname === '/api/drafts/outreach') {
    const body = await readJson(req)
    const lead = listLeads().find((item) => item.id === body.leadId)
    if (!lead) {
      json(res, 404, { error: 'Lead not found' })
      return true
    }
    const config = getConfig()
    const draftContent = buildOutreachDraft({
      lead,
      companyProfile: config.company,
    })
    const draft = await createDraft({
      leadId: lead.id,
      to: draftContent.to,
      subject: draftContent.subject,
      body: draftContent.body,
      purpose: 'first-touch',
    })
    const dueAt = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
    await scheduleFollowUp({
      leadId: lead.id,
      contactEmail: lead.email,
      dueAt,
      reason: 'Check first-touch outreach result',
    })
    json(res, 200, draft)
    return true
  }
  return false
}

async function serveStatic(res, pathname) {
  const file = pathname === '/' ? 'index.html' : pathname.replace(/^\//, '')
  const fullPath = path.join(publicDir, file)
  if (!fullPath.startsWith(publicDir)) {
    json(res, 403, { error: 'Forbidden' })
    return
  }
  const content = await readFile(fullPath)
  const type = fullPath.endsWith('.css') ? 'text/css; charset=utf-8'
    : fullPath.endsWith('.js') ? 'application/javascript; charset=utf-8'
      : 'text/html; charset=utf-8'
  res.writeHead(200, { 'content-type': type })
  res.end(content)
}

await initDB()

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`)
    if (url.pathname.startsWith('/api/')) {
      const handled = await routeApi(req, res, url)
      if (!handled) json(res, 404, { error: 'Not found' })
      return
    }
    await serveStatic(res, url.pathname)
  } catch (error) {
    json(res, 500, { error: error.message })
  }
})

server.listen(port, () => {
  console.log(`Foreign Trade Autopilot dashboard: http://localhost:${port}`)
})
