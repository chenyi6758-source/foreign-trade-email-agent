import nodemailer from 'nodemailer'
import { ImapFlow } from 'imapflow'
import { simpleParser } from 'mailparser'

let transporter

export function initSMTP(config) {
  transporter = nodemailer.createTransport({
    host: config.smtp.host,
    port: config.smtp.port,
    secure: config.smtp.port === 465,
    auth: {
      user: config.smtp.user,
      pass: config.smtp.pass,
    },
  })
  return transporter
}

export async function sendEmail({ config, to, subject, body, inReplyTo }) {
  if (config.dryRun) {
    return `dry-run-${Date.now()}`
  }
  if (!transporter) initSMTP(config)
  const info = await transporter.sendMail({
    from: `"${config.company.senderName} · ${config.company.name}" <${config.smtp.user}>`,
    to,
    subject,
    text: body,
    ...(inReplyTo ? { inReplyTo, references: inReplyTo } : {}),
  })
  return info.messageId
}

function stripHtml(html = '') {
  return html
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

export async function fetchNewEmails({ config, processedIds = [] }) {
  const client = new ImapFlow({
    host: config.imap.host,
    port: config.imap.port,
    secure: config.imap.port === 993,
    auth: {
      user: config.imap.user,
      pass: config.imap.pass,
    },
    logger: false,
  })

  const emails = []
  try {
    await client.connect()
    const mailbox = await client.mailboxOpen('INBOX')
    const total = mailbox.exists || 0
    if (total === 0) return emails

    let sequence = `${Math.max(1, total - config.maxEmailsPerScan + 1)}:*`
    if (config.unseenOnly) {
      const unseen = await client.search({ seen: false })
      sequence = unseen.slice(-config.maxEmailsPerScan)
      if (sequence.length === 0) return emails
    }

    const lock = await client.getMailboxLock('INBOX')
    try {
      for await (const msg of client.fetch(sequence, { source: true, uid: true, envelope: true })) {
        const parsed = await simpleParser(msg.source)
        const fromAddr = parsed.from?.value?.[0]
        const fromEmail = fromAddr?.address || ''
        if (!fromEmail) continue
        if (fromEmail.toLowerCase() === config.imap.user.toLowerCase()) continue

        const uid = String(msg.uid)
        const messageId = parsed.messageId || uid
        const processedId = `${uid}:${messageId}`
        if (processedIds.includes(processedId)) continue

        emails.push({
          uid,
          processedId,
          messageId,
          from: {
            email: fromEmail,
            name: fromAddr?.name || '',
          },
          subject: parsed.subject || '(no subject)',
          text: parsed.text || stripHtml(parsed.html || ''),
          date: parsed.date || new Date(),
        })
      }
    } finally {
      lock.release()
    }
  } finally {
    try {
      await client.logout()
    } catch {
      // Ignore logout failures after connection errors.
    }
  }

  return emails.sort((a, b) => new Date(a.date) - new Date(b.date))
}
