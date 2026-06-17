export function normalizeIntelItem(item) {
  return {
    title: item.title || '(untitled)',
    source: item.source || item.feed || 'unknown',
    url: item.url || item.link || '',
    publishedAt: item.publishedAt || item.date || new Date().toISOString(),
    tags: item.tags || [],
    summary: item.summary || item.description || '',
  }
}

export function buildDailyDigest(items = []) {
  const normalized = items.map(normalizeIntelItem)
  const tagCounts = new Map()
  for (const item of normalized) {
    for (const tag of item.tags) tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1)
  }
  return {
    generatedAt: new Date().toISOString(),
    totalItems: normalized.length,
    topTags: [...tagCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([tag, count]) => ({ tag, count }))
      .slice(0, 10),
    items: normalized,
  }
}

function runDemo() {
  const digest = buildDailyDigest([
    {
      title: 'EU buyers increase demand for energy efficient lighting',
      source: 'demo-feed',
      url: 'https://example.com/trade-news',
      tags: ['lighting', 'EU', 'energy'],
      summary: 'Potential outreach angle for LED exporters.',
    },
    {
      title: 'Solar product importers request shorter lead times',
      source: 'demo-feed',
      tags: ['solar', 'logistics'],
      summary: 'Follow up with buyers who care about delivery schedule.',
    },
  ])
  console.log(JSON.stringify(digest, null, 2))
}

if (process.argv.includes('--demo')) runDemo()
