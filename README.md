# Foreign Trade Autopilot

面向外贸团队的安全默认型 AI 自动化工作台。它不只是邮件自动回复，而是把外贸常见流程拆成可逐步上线的模块：收件箱处理、AI 回复、客户 CRM、开发信、获客线索整理、市场情报摘要，以及 WhatsApp 通道适配边界。

当前仓库采用“能真实运行的核心 + 清晰可扩展的模块骨架”方式开源：

| 模块 | 状态 | 命令 |
| --- | --- | --- |
| 邮件自动处理 | 可运行 | `npm run once` / `npm start` |
| 手动开发信 | 可运行 | `npm run outreach -- --to buyer@example.com` |
| 本地客户 CRM | 可运行 | `npm run contacts` |
| 获客线索抽取/评分 | starter module | `npm run leads:demo` |
| 市场情报摘要 | starter module | `npm run intel:demo` |
| WhatsApp 通道 | adapter placeholder | `npm run whatsapp:status` |
| Hermes/Codex skill | 已整理 | `skill/foreign-trade-autopilot/` |

## 为什么从原包升级

原始压缩包是一个邮件 MVP，但存在这些问题：

- 自动发送 AI 生成的回复，缺少安全默认设置。
- IMAP 扫描使用 `1:*`，第一次运行可能处理整个邮箱历史。
- `npm test` 指向不存在的文件。
- `nodemailer@6.x` 审计存在漏洞。
- 没有环境变量校验、dry-run 模式、扫描重叠保护。
- 归档包含 `node_modules`，不适合 GitHub 开源。
- 项目定位太窄，只体现“外贸电子邮件代理”，没有覆盖获客、CRM、多渠道和 skill。

## 快速开始

```bash
npm install
cp .env.example .env
npm run capabilities
npm run once
```

默认是 `DRY_RUN=true`，第一次运行只会打印建议回复，不会发送邮件。

确认配置、安全策略和测试邮箱都没问题后，再启用真实发送：

```env
DRY_RUN=false
```

然后运行：

```bash
npm start
```

## 常用命令

```bash
npm run capabilities
npm run once
npm start
npm run contacts
npm run outreach -- --to buyer@example.com --name "John" --company "ABC Trading"
npm run leads:demo
npm run intel:demo
npm run whatsapp:status
npm test
npm run check
```

## 核心安全设计

- `DRY_RUN=true` 默认不发信。
- `MAX_EMAILS_PER_SCAN` 限制每次只检查最近邮件。
- `UNSEEN_ONLY=true` 可限制只处理未读邮件。
- 主循环有运行锁，避免 AI/邮箱接口慢时重叠扫描。
- 已处理消息、联系人和会话历史记录在 `data/db.json`。
- dry-run 默认不标记已处理，除非设置 `MARK_DRY_RUN_PROCESSED=true`。
- WhatsApp 只提供适配边界，不默认接入扫码登录和自动发送，避免账号风控和误发。

## 目录结构

```text
src/
  ai.js              Claude 分类与回复生成
  config.js          环境变量和 CLI 参数
  db.js              本地 CRM、会话、处理状态
  mailer.js          IMAP/SMTP 邮件通道
  main.js            邮件自动处理主入口
  send_outreach.js   手动开发信
  view_contacts.js   查看客户和历史
  leads.js           线索抽取与评分 starter
  market_intel.js    市场情报摘要 starter
  whatsapp.js        WhatsApp 适配边界说明
  capabilities.js    项目能力清单
skill/
  foreign-trade-autopilot/
```

## 后续路线图

- 接入 Google Search / 企业黄页 / 展会名录线索采集。
- 将 `leads.js` 扩展为可导入 CSV、网页文本、搜索结果的获客管道。
- 将 `market_intel.js` 扩展为 RSS/网页监控与每日邮件摘要。
- 在 WhatsApp 模块中接入 `whatsapp-web.js`，但保留 dry-run、人审和频率限制。
- 增加 Web UI，用于查看客户、草稿、发送队列和线索池。
- 增加 GitHub Actions 自动测试和 npm 审计。

## GitHub 开源注意

- 不要提交 `.env`、`data/`、真实客户邮件、邮箱授权码或 `node_modules/`。
- 生产邮箱建议使用专门测试账号和应用专用密码。
- AI 生成内容适合做草稿，高价值客户、投诉、价格、交期、法律事项建议人工确认。

## Hermes / Codex Skill

完整 skill 包在：

```text
skill/foreign-trade-autopilot/
```

它用于指导 Codex/Hermes 后续继续开发这个项目，包括邮件、线索、CRM、市场情报、WhatsApp 适配和安全上线流程。
