import Anthropic from '@anthropic-ai/sdk'

export function extractJsonObject(text = '') {
  const cleaned = text.trim().replace(/^```json\s*/i, '').replace(/\s*```$/, '').trim()
  const start = cleaned.indexOf('{')
  const end = cleaned.lastIndexOf('}')
  if (start === -1 || end === -1 || end <= start) {
    throw new Error('No JSON object found in AI response')
  }
  return JSON.parse(cleaned.slice(start, end + 1))
}

function createClient(config) {
  return new Anthropic({ apiKey: config.anthropic.apiKey })
}

export async function classifyEmail({ config, subject, body, client = createClient(config) }) {
  const response = await client.messages.create({
    model: config.anthropic.model,
    max_tokens: 120,
    messages: [{
      role: 'user',
      content: `Classify this email intent. Return only JSON:
{"intent":"inquiry|complaint|general|spam|followup","priority":"high|medium|low"}

Subject: ${subject}
Body preview: ${body.slice(0, 800)}`,
    }],
  })

  try {
    return extractJsonObject(response.content[0].text)
  } catch {
    return { intent: 'general', priority: 'medium' }
  }
}

export async function generateReply({
  config,
  inboundSubject,
  inboundBody,
  senderEmail,
  senderName,
  history = [],
  client = createClient(config),
}) {
  const historyText = history.length
    ? history.map((item) => `[${item.direction}] ${item.subject}\n${item.body}`).join('\n\n---\n\n')
    : '(No previous conversation.)'

  const system = `You are an experienced foreign trade sales representative for ${config.company.name}.
Products: ${config.company.products}
Writer: ${config.company.senderName}, ${config.company.senderTitle}
Reply language: ${config.company.replyLanguage}

Write concise, professional, truthful email replies. Do not invent prices, certifications, specifications, stock, delivery dates, or promises. If details are missing, ask for quantity, target market, specifications, timeline, and any compliance requirements. Return only JSON with "subject" and "body".`

  const response = await client.messages.create({
    model: config.anthropic.model,
    max_tokens: 1200,
    system,
    messages: [{
      role: 'user',
      content: `Conversation history:
${historyText}

Latest email:
From: ${senderName || senderEmail} <${senderEmail}>
Subject: ${inboundSubject}
Body:
${inboundBody}

Return JSON like:
{"subject":"Re: ...","body":"plain text email body"}`,
    }],
  })

  try {
    const parsed = extractJsonObject(response.content[0].text)
    return {
      subject: parsed.subject || `Re: ${inboundSubject}`,
      body: parsed.body || response.content[0].text,
    }
  } catch {
    return {
      subject: `Re: ${inboundSubject}`,
      body: response.content[0].text.trim(),
    }
  }
}
