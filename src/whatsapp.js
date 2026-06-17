export function whatsappStatus() {
  return {
    status: 'not-connected',
    recommendedAdapter: 'whatsapp-web.js',
    reason: 'WhatsApp automation requires QR login, browser session storage, and anti-spam controls. This repository keeps the adapter boundary explicit instead of shipping an unsafe default bot.',
    nextSteps: [
      'Install whatsapp-web.js only when you are ready to test on a dedicated account.',
      'Reuse src/ai.js for draft generation.',
      'Reuse src/db.js for contacts and conversation history.',
      'Keep human approval or dry-run enabled during rollout.',
    ],
  }
}

if (process.argv[1]?.endsWith('whatsapp.js')) {
  console.log(JSON.stringify(whatsappStatus(), null, 2))
}
