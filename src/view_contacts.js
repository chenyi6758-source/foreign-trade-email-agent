import { initDB, getDB, getThreadHistory } from './db.js'
import { parseArgs } from './config.js'

const args = parseArgs()

async function main() {
  await initDB()
  const db = getDB()
  const email = args.get('--email')

  if (email) {
    const contact = db.data.contacts.find((item) => item.email.toLowerCase() === email.toLowerCase())
    if (!contact) {
      console.log('Contact not found.')
      return
    }
    console.table([contact])
    const history = getThreadHistory(email, 50)
    for (const item of history) {
      console.log(`\n[${item.direction} / ${item.status}] ${new Date(item.timestamp).toLocaleString()}`)
      console.log(`Subject: ${item.subject}`)
      console.log(item.body.slice(0, 600))
    }
    return
  }

  if (db.data.contacts.length === 0) {
    console.log('No contacts yet.')
    return
  }

  console.table(db.data.contacts.map((contact) => ({
    email: contact.email,
    name: contact.name || '-',
    company: contact.company || '-',
    source: contact.source,
    lastSeen: contact.lastSeen,
  })))
  console.log(`Threads: ${db.data.threads.length}; processed states: ${db.data.processed.length}`)
}

main().catch((error) => {
  console.error(error.message)
  process.exit(1)
})
