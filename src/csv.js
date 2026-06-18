function escapeCell(value = '') {
  const text = String(value ?? '')
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

export function toCsv(rows = [], columns = []) {
  const header = columns.map((column) => escapeCell(column.label || column.key)).join(',')
  const body = rows.map((row) => columns
    .map((column) => escapeCell(typeof column.value === 'function' ? column.value(row) : row[column.key]))
    .join(','))
  return [header, ...body].join('\n')
}

export const leadColumns = [
  { key: 'company', label: 'company' },
  { key: 'name', label: 'name' },
  { key: 'email', label: 'email' },
  { key: 'website', label: 'website' },
  { key: 'country', label: 'country' },
  { key: 'score', label: 'score' },
  { key: 'stage', label: 'stage' },
  { key: 'source', label: 'source' },
  { key: 'tags', label: 'tags', value: (row) => (row.tags || []).join('|') },
  { key: 'notes', label: 'notes' },
]

export const draftColumns = [
  { key: 'to', label: 'to' },
  { key: 'subject', label: 'subject' },
  { key: 'channel', label: 'channel' },
  { key: 'purpose', label: 'purpose' },
  { key: 'status', label: 'status' },
  { key: 'createdAt', label: 'createdAt' },
  { key: 'sentAt', label: 'sentAt' },
]

export const followUpColumns = [
  { key: 'contactEmail', label: 'contactEmail' },
  { key: 'dueAt', label: 'dueAt' },
  { key: 'reason', label: 'reason' },
  { key: 'status', label: 'status' },
  { key: 'createdAt', label: 'createdAt' },
]
