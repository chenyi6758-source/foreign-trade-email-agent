import 'dotenv/config'

function boolValue(name, defaultValue = false) {
  const raw = process.env[name]
  if (raw == null || raw === '') return defaultValue
  return ['1', 'true', 'yes', 'y', 'on'].includes(raw.toLowerCase())
}

function intValue(name, defaultValue, { min = 1, max = Number.MAX_SAFE_INTEGER } = {}) {
  const raw = process.env[name]
  const parsed = raw == null || raw === '' ? defaultValue : Number.parseInt(raw, 10)
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    throw new Error(`${name} must be an integer between ${min} and ${max}`)
  }
  return parsed
}

export function getConfig({ requireMail = false, requireAI = false } = {}) {
  const config = {
    dryRun: boolValue('DRY_RUN', true),
    markDryRunProcessed: boolValue('MARK_DRY_RUN_PROCESSED', false),
    checkIntervalSeconds: intValue('CHECK_INTERVAL', 60, { min: 15, max: 86400 }),
    maxEmailsPerScan: intValue('MAX_EMAILS_PER_SCAN', 20, { min: 1, max: 200 }),
    unseenOnly: boolValue('UNSEEN_ONLY', false),
    smtp: {
      host: process.env.SMTP_HOST,
      port: intValue('SMTP_PORT', 465, { min: 1, max: 65535 }),
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
    imap: {
      host: process.env.IMAP_HOST,
      port: intValue('IMAP_PORT', 993, { min: 1, max: 65535 }),
      user: process.env.IMAP_USER,
      pass: process.env.IMAP_PASS,
    },
    anthropic: {
      apiKey: process.env.ANTHROPIC_API_KEY,
      model: process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-6',
    },
    company: {
      name: process.env.COMPANY_NAME || '',
      products: process.env.COMPANY_PRODUCTS || '',
      senderName: process.env.YOUR_NAME || '',
      senderTitle: process.env.YOUR_TITLE || '',
      replyLanguage: process.env.REPLY_LANGUAGE || 'English',
    },
  }

  const missing = []
  if (requireMail) {
    for (const [key, value] of Object.entries({
      SMTP_HOST: config.smtp.host,
      SMTP_USER: config.smtp.user,
      SMTP_PASS: config.smtp.pass,
      IMAP_HOST: config.imap.host,
      IMAP_USER: config.imap.user,
      IMAP_PASS: config.imap.pass,
    })) {
      if (!value) missing.push(key)
    }
  }
  if (!config.dryRun && requireMail) {
    for (const [key, value] of Object.entries({
      YOUR_NAME: config.company.senderName,
      COMPANY_NAME: config.company.name,
    })) {
      if (!value) missing.push(key)
    }
  }
  if (requireAI && !config.anthropic.apiKey) missing.push('ANTHROPIC_API_KEY')
  if (requireAI) {
    for (const [key, value] of Object.entries({
      COMPANY_NAME: config.company.name,
      COMPANY_PRODUCTS: config.company.products,
      YOUR_NAME: config.company.senderName,
      YOUR_TITLE: config.company.senderTitle,
    })) {
      if (!value) missing.push(key)
    }
  }

  if (missing.length) {
    throw new Error(`Missing required environment values: ${[...new Set(missing)].join(', ')}`)
  }

  return config
}

export function parseArgs(argv = process.argv.slice(2)) {
  const args = new Map()
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i]
    if (!token.startsWith('--')) continue
    const next = argv[i + 1]
    if (next && !next.startsWith('--')) {
      args.set(token, next)
      i += 1
    } else {
      args.set(token, true)
    }
  }
  return {
    once: args.has('--once'),
    live: args.has('--live'),
    get: (name, fallback = '') => args.get(name) ?? fallback,
    has: (name) => args.has(name),
  }
}
