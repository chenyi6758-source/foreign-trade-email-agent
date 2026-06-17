import { getConfig, parseArgs } from './config.js'
import { generateReply, classifyEmail } from './ai.js'
import { initDB, getProcessedIds, isProcessed, markProcessed, upsertContact, appendThread, getThreadHistory } from './db.js'
import { fetchNewEmails, initSMTP, sendEmail } from './mailer.js'

const args = parseArgs()
const config = getConfig({ requireMail: true, requireAI: true })
if (args.live) config.dryRun = false

let scanRunning = false

async function processEmail(email) {
  if (isProcessed(email.processedId)) return

  console.log(`\nProcessing: ${email.subject}`)
  console.log(`From: ${email.from.name || email.from.email} <${email.from.email}>`)

  const classification = await classifyEmail({
    config,
    subject: email.subject,
    body: email.text,
  })
  console.log(`Intent: ${classification.intent}; priority: ${classification.priority}`)

  if (classification.intent === 'spam') {
    await markProcessed(email.processedId, 'skipped', 'spam')
    console.log('Skipped spam.')
    return
  }

  await upsertContact({
    email: email.from.email,
    name: email.from.name,
    source: 'inbound_email',
  })

  const history = getThreadHistory(email.from.email)
  const reply = await generateReply({
    config,
    inboundSubject: email.subject,
    inboundBody: email.text,
    senderEmail: email.from.email,
    senderName: email.from.name,
    history,
  })

  if (config.dryRun) {
    console.log('\n--- DRY RUN: reply preview ---')
    console.log(`To: ${email.from.email}`)
    console.log(`Subject: ${reply.subject}`)
    console.log(reply.body)
    console.log('--- end preview ---\n')
  }

  const sentMessageId = await sendEmail({
    config,
    to: email.from.email,
    subject: reply.subject,
    body: reply.body,
    inReplyTo: email.messageId,
  })

  await appendThread({
    contactEmail: email.from.email,
    direction: 'inbound',
    subject: email.subject,
    body: email.text.slice(0, 4000),
    messageId: email.messageId,
  })
  await appendThread({
    contactEmail: email.from.email,
    direction: 'outbound',
    subject: reply.subject,
    body: reply.body,
    messageId: sentMessageId,
    status: config.dryRun ? 'drafted' : 'sent',
  })

  if (!config.dryRun || config.markDryRunProcessed) {
    await markProcessed(email.processedId, config.dryRun ? 'dry-run' : 'sent')
  }

  console.log(config.dryRun ? 'Draft recorded.' : `Sent to ${email.from.email}.`)
}

export async function scanOnce() {
  if (scanRunning) {
    console.log('Previous scan is still running; skipped this interval.')
    return
  }
  scanRunning = true
  try {
    const processedIds = getProcessedIds()
    const emails = await fetchNewEmails({ config, processedIds })
    console.log(`Found ${emails.length} candidate email(s).`)
    for (const email of emails) {
      try {
        await processEmail(email)
      } catch (error) {
        console.error(`Failed to process ${email.processedId}: ${error.message}`)
      }
    }
  } finally {
    scanRunning = false
  }
}

async function main() {
  await initDB()
  if (!config.dryRun) initSMTP(config)

  console.log('Foreign Trade Email Agent')
  console.log(`Mode: ${config.dryRun ? 'dry-run' : 'live send'}`)
  console.log(`Mailbox: ${config.imap.user}`)
  console.log(`Max emails per scan: ${config.maxEmailsPerScan}`)

  await scanOnce()
  if (args.once) return

  const intervalMs = config.checkIntervalSeconds * 1000
  setInterval(scanOnce, intervalMs)
}

main().catch((error) => {
  console.error(error.message)
  process.exit(1)
})
