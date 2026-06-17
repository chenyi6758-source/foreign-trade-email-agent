const capabilities = [
  {
    area: 'Email autopilot',
    status: 'runnable',
    command: 'npm run once',
    description: 'IMAP inbox scan, Claude intent classification, safe dry-run reply drafting, optional SMTP sending.',
  },
  {
    area: 'Manual outreach',
    status: 'runnable',
    command: 'npm run outreach -- --to buyer@example.com --name "John" --company "ABC Trading"',
    description: 'Generate and optionally send first-touch foreign trade outreach email.',
  },
  {
    area: 'Customer CRM',
    status: 'runnable',
    command: 'npm run contacts',
    description: 'Local lowdb contacts, processed message state, and conversation history.',
  },
  {
    area: 'Lead discovery workspace',
    status: 'starter module',
    command: 'npm run leads:demo',
    description: 'Extract emails, websites, domains, and score candidate buyers from raw text snippets.',
  },
  {
    area: 'Market intelligence',
    status: 'starter module',
    command: 'npm run intel:demo',
    description: 'Normalize news/RSS-like items into a daily trade intelligence digest shape.',
  },
  {
    area: 'WhatsApp channel',
    status: 'adapter placeholder',
    command: 'npm run whatsapp:status',
    description: 'Documents the integration boundary for whatsapp-web.js without pretending it is connected.',
  },
  {
    area: 'Hermes/Codex skill',
    status: 'valid skill package',
    command: 'skill/foreign-trade-autopilot',
    description: 'Agent instructions for safely extending and operating the project.',
  },
]

export function listCapabilities() {
  return capabilities
}

if (process.argv[1]?.endsWith('capabilities.js')) {
  console.table(capabilities)
}
