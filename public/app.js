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

const leadStages = ['new', 'qualified', 'drafted', 'contacted', 'replied', 'quoted', 'sample', 'won', 'lost']

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
      <div class="actions">
        <select data-stage="${lead.id}">
          ${leadStages.map((stage) => `<option value="${stage}" ${stage === lead.stage ? 'selected' : ''}>${stage}</option>`).join('')}
        </select>
        <button data-draft="${lead.id}" ${lead.email ? '' : 'disabled'}>Create outreach draft</button>
      </div>
    </div>
  `).join('') : empty('No leads yet. Import CSV to start.')

  document.querySelector('#drafts').innerHTML = drafts.length ? drafts.map((draft) => `
    <div class="item">
      <h3>${draft.subject}</h3>
      <div class="meta">${draft.to || 'no recipient'} · ${draft.channel} · ${draft.status}</div>
      <pre>${draft.body}</pre>
      <div class="actions">
        <button class="secondary" data-approve="${draft.id}" ${draft.status !== 'draft' ? 'disabled' : ''}>Approve</button>
        <button data-sent="${draft.id}" ${draft.status === 'sent' ? 'disabled' : ''}>Mark sent</button>
      </div>
    </div>
  `).join('') : empty('No drafts yet.')

  document.querySelector('#followups').innerHTML = followups.length ? followups.map((item) => `
    <div class="item">
      <span>${item.contactEmail || item.leadId || 'lead'} · ${item.reason}</span>
      <span class="meta">${new Date(item.dueAt).toLocaleDateString()}</span>
      <button class="secondary" data-complete-followup="${item.id}">Done</button>
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
  const { draft, approve, sent, completeFollowup } = event.target.dataset || {}
  if (draft) {
    await api('/api/drafts/outreach', {
      method: 'POST',
      body: JSON.stringify({ leadId: draft }),
    })
  } else if (approve) {
    await api(`/api/drafts/${encodeURIComponent(approve)}/approve`, { method: 'POST' })
  } else if (sent) {
    await api(`/api/drafts/${encodeURIComponent(sent)}/sent`, { method: 'POST' })
  } else if (completeFollowup) {
    await api(`/api/followups/${encodeURIComponent(completeFollowup)}/complete`, { method: 'POST' })
  } else {
    return
  }
  await load()
})

document.body.addEventListener('change', async (event) => {
  const id = event.target.dataset?.stage
  if (!id) return
  await api(`/api/leads/${encodeURIComponent(id)}/stage`, {
    method: 'POST',
    body: JSON.stringify({ stage: event.target.value }),
  })
  await load()
})

load().catch((error) => {
  document.body.insertAdjacentHTML('beforeend', `<pre>${error.message}</pre>`)
})
