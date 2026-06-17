async function api(path, options) {
  const response = await fetch(path, {
    headers: { 'content-type': 'application/json' },
    ...options,
  })
  if (!response.ok) throw new Error(await response.text())
  return response.json()
}

function metric(label, value) {
  return `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`
}

function empty(text) {
  return `<div class="item"><p class="meta">${text}</p></div>`
}

async function load() {
  const [summary, leads, drafts, followups] = await Promise.all([
    api('/api/summary'),
    api('/api/leads'),
    api('/api/drafts'),
    api('/api/followups'),
  ])

  document.querySelector('#metrics').innerHTML = [
    metric('Contacts', summary.contacts),
    metric('Leads', summary.leads),
    metric('Drafts', summary.drafts),
    metric('Open follow-ups', summary.openFollowUps),
    metric('High score leads', summary.highScoreLeads),
  ].join('')

  document.querySelector('#leads').innerHTML = leads.length ? leads.map((lead) => `
    <div class="item">
      <h3>${lead.company || lead.email || 'Unnamed lead'} <span class="score">${lead.score || 0}</span></h3>
      <div class="meta">${lead.email || 'no email'} · ${lead.website || 'no website'} · ${lead.country || 'unknown market'} · ${lead.stage}</div>
      <p>${lead.notes || lead.rawText || ''}</p>
      <button data-draft="${lead.id}" ${lead.email ? '' : 'disabled'}>Create outreach draft</button>
    </div>
  `).join('') : empty('No leads yet. Import CSV to start.')

  document.querySelector('#drafts').innerHTML = drafts.length ? drafts.map((draft) => `
    <div class="item">
      <h3>${draft.subject}</h3>
      <div class="meta">${draft.to || 'no recipient'} · ${draft.channel} · ${draft.status}</div>
      <pre>${draft.body}</pre>
    </div>
  `).join('') : empty('No drafts yet.')

  document.querySelector('#followups').innerHTML = followups.length ? followups.map((item) => `
    <div class="item">
      <span>${item.contactEmail || item.leadId || 'lead'} · ${item.reason}</span>
      <span class="meta">${new Date(item.dueAt).toLocaleDateString()}</span>
    </div>
  `).join('') : empty('No open follow-ups.')
}

document.querySelector('#refresh').addEventListener('click', load)

document.querySelector('#import').addEventListener('click', async () => {
  await api('/api/leads/import', {
    method: 'POST',
    body: JSON.stringify({
      csv: document.querySelector('#csv').value,
      targetKeywords: document.querySelector('#keywords').value,
    }),
  })
  await load()
})

document.body.addEventListener('click', async (event) => {
  const id = event.target.dataset?.draft
  if (!id) return
  await api('/api/drafts/outreach', {
    method: 'POST',
    body: JSON.stringify({ leadId: id }),
  })
  await load()
})

load().catch((error) => {
  document.body.insertAdjacentHTML('beforeend', `<pre>${error.message}</pre>`)
})
