import readline from 'node:readline/promises'
import { stdin as input, stdout as output } from 'node:process'
import { getConfig, parseArgs } from './config.js'
import { generateReply } from './ai.js'
import { initDB, upsertContact, appendThread } from './db.js'
import { initSMTP, sendEmail } from './mailer.js'

const args = parseArgs()
const config = getConfig({ requireMail: true, requireAI: true })
if (args.live) config.dryRun = false

async function main() {
  const toEmail = args.get('--to')
  const toName = args.get('--name')
  const toCompany = args.get('--company')

  if (!toEmail) {
    console.log('Usage: npm run outreach -- --to buyer@example.com --name "John" --company "ABC Trading"')
    process.exit(1)
  }

  await initDB()
  if (!config.dryRun) initSMTP(config)

  const reply = await generateReply({
    config,
    inboundSubject: `Introductory email to ${toCompany || toEmail}`,
    inboundBody: `Write a first-touch foreign trade outreach email to ${toName || toEmail}${toCompany ? ` at ${toCompany}` : ''}. Keep it under 150 words and ask whether a catalog or quotation would be useful.`,
    senderEmail: toEmail,
    senderName: toName,
    history: [],
  })

  console.log('\n--- Preview ---')
  console.log(`To: ${toEmail}`)
  console.log(`Subject: ${reply.subject}`)
  console.log(reply.body)
  console.log('--- End preview ---\n')

  const rl = readline.createInterface({ input, output })
  const answer = await rl.question(config.dryRun ? 'Dry-run mode. Record this draft? (y/N) ' : 'Send this email now? (y/N) ')
  rl.close()

  if (answer.toLowerCase() !== 'y') {
    console.log('Cancelled.')
    return
  }

  const messageId = await sendEmail({
    config,
    to: toEmail,
    subject: reply.subject,
    body: reply.body,
  })
  await upsertContact({ email: toEmail, name: toName, company: toCompany, source: 'outreach' })
  await appendThread({
    contactEmail: toEmail,
    direction: 'outbound',
    subject: reply.subject,
    body: reply.body,
    messageId,
    status: config.dryRun ? 'drafted' : 'sent',
  })

  console.log(config.dryRun ? 'Draft recorded.' : 'Email sent.')
}

main().catch((error) => {
  console.error(error.message)
  process.exit(1)
})
