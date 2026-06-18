import test from 'node:test'
import assert from 'node:assert/strict'
import { leadColumns, toCsv } from '../src/csv.js'

test('toCsv escapes commas and quotes', () => {
  const csv = toCsv([
    { company: 'ACME, Inc.', name: 'Alice "Buyer"', email: 'alice@example.com' },
  ], leadColumns)
  assert.match(csv, /"ACME, Inc\."/)
  assert.match(csv, /"Alice ""Buyer"""/)
})
