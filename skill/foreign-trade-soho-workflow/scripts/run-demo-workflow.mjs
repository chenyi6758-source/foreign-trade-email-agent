import { mkdtemp, rm } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import {
  initDB,
  upsertLead,
  listLeads,
  createDraft,
  listDrafts,
  scheduleFollowUp,
  listFollowUps,
} from '../../../src/db.js'
import { buildOutreachDraft, parseLeadCsv } from '../../../src/leads.js'

const tempDir = await mkdtemp(path.join(os.tmpdir(), 'foreign-trade-soho-workflow-'))
const tempDb = path.join(tempDir, 'db.json')

try {
  await initDB(tempDb)

  const csv = `company,name,email,website,country,notes
Demo Solar Importers,Alice,alice@demosolar.example,www.demosolar.example,United States,solar garden light importer looking for CE compliant suppliers
Demo Hotel Supply,Bob,bob@demohotel.example,www.demohotel.example,United Arab Emirates,hotel project buyer for LED strip lights`

  const leads = parseLeadCsv(csv, {
    source: 'workflow-demo',
    targetKeywords: ['solar', 'LED', 'importer', 'hotel'],
  })

  const savedLeads = []
  for (const lead of leads) {
    savedLeads.push(await upsertLead(lead))
  }

  const qualified = listLeads().filter((lead) => lead.score >= 70)
  for (const lead of qualified) {
    const draft = buildOutreachDraft({
      lead,
      companyProfile: {
        name: 'Demo Export Co',
        products: 'solar garden lights and LED strip lights',
        senderName: 'SOHO Exporter',
        senderTitle: 'Foreign Trade Manager',
      },
    })
    await createDraft({
      leadId: lead.id,
      to: draft.to,
      subject: draft.subject,
      body: draft.body,
      purpose: 'first-touch-demo',
    })
    await scheduleFollowUp({
      leadId: lead.id,
      contactEmail: lead.email,
      dueAt: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
      reason: 'Day 3 first-touch follow-up',
    })
  }

  const summary = {
    importedLeads: savedLeads.length,
    qualifiedLeads: qualified.length,
    draftsCreated: listDrafts().length,
    followUpsScheduled: listFollowUps().length,
    sampleDraftSubject: listDrafts()[0]?.subject,
    mode: 'dry-run-demo-no-email-sent',
  }

  console.log(JSON.stringify(summary, null, 2))
} finally {
  await rm(tempDir, { recursive: true, force: true })
}
