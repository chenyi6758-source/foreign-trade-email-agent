# Foreign Trade SOHO Workflow Reference

## Inputs The Assistant Can Accept

- CSV text or file with headers such as `company,name,email,website,country,notes`.
- A pasted buyer list from Google, exhibitions, directories, B2B platforms, or LinkedIn notes.
- A target product line and market, for example `solar garden lights for US importers`.
- Existing inbound email replies from buyers.
- Company profile: company name, products, sender name, title, MOQ, certificates, lead time, and target markets.

## Lead Qualification Rules

Prioritize leads with:

- A valid business email.
- A company website or recognizable domain.
- Importer, distributor, wholesaler, buyer, procurement, sourcing, retailer, contractor, or project keywords.
- Product-market match with the user's target keywords.
- A country or market the SOHO user can serve.

Deprioritize leads with:

- Generic free-mail addresses without company context.
- No website and no company name.
- Obvious spam, job seekers, unrelated services, or competitors.
- Duplicate email/domain.

## Lead Stages

Use these stages:

- `new`: imported but not reviewed.
- `qualified`: worth outreach.
- `drafted`: outreach draft created.
- `contacted`: user sent or approved sending.
- `replied`: buyer responded.
- `quoted`: quotation sent.
- `sample`: sample discussion.
- `won`: converted.
- `lost`: not relevant, bounced, unsubscribed, or declined.

## Outreach Draft Rules

Every first-touch draft should:

- Mention the buyer/company context if available.
- Keep the email short.
- State the product category clearly.
- Ask for a low-friction next step: catalog, quotation, sample, specification check, or short call.
- Ask for missing buying details: quantity, specification, certification, market, target price, and timeline.
- Avoid fake personalization and unsupported claims.

Recommended first-touch structure:

1. Greeting.
2. One sentence showing relevance.
3. One sentence about the exporter/product category.
4. One specific next-step question.
5. Signature.

## Follow-Up Plan

- Day 3: polite check-in and offer catalog/quote.
- Day 7: share one useful angle such as certification, application, packaging, or sample option.
- Day 14: final light touch asking whether to close the file or revisit later.

Stop follow-ups when:

- The buyer replies.
- The email bounces.
- The buyer declines or unsubscribes.
- The lead is marked lost.

## Inbound Email Review

For inbound replies:

- Classify intent: inquiry, complaint, follow-up, general, spam.
- Extract buying signals: product, quantity, specification, target price, market, certification, timeline.
- Draft a reply but keep it review-first unless live sending is authorized.
- Update CRM stage based on the reply.

## Daily Summary Format

Report:

- New leads imported.
- High-score leads.
- Drafts created.
- Follow-ups due or overdue.
- Buyer replies needing attention.
- Risks or missing configuration.
- Recommended next 3 actions.

## Safety And Compliance

- Do not scrape or message platforms in ways that violate their terms.
- Do not mass-send without rate limits and unsubscribe handling.
- Do not store credentials in repo files.
- Do not expose the local dashboard publicly without authentication.
- Keep WhatsApp automation human-reviewed until account risk is understood.
