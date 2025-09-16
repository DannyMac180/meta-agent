#!/usr/bin/env node
'use strict';

const fs = require('fs');
const https = require('https');
const url = require('url');
const { spawnSync } = require('child_process');

function logErr(msg) { process.stderr.write(String(msg) + '\n'); }

const action = process.env.TOOLBOX_ACTION;

if (action === 'describe') {
  describe();
  process.exit(0);
} else if (action === 'execute') {
  execute();
} else {
  describe();
  process.exit(0);
}

function describe() {
  const lines = [
    'name: codex-code-review',
    'description: Run OpenAI Codex CLI to review a GitHub PR and output structured feedback',
    'pr_url: string the GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)',
    'model: string optional codex model id (default: GPT-5-Codex)',
    'github_token: string optional GitHub token for higher rate limits/private repos',
    'max_diff_bytes: number optional max bytes of diff to include (default: 160000)'
  ];
  process.stdout.write(lines.join('\n'));
}

function parseInputKV() {
  const input = fs.readFileSync(0, 'utf8');
  const lines = input.split('\n').filter(Boolean);
  const map = {};
  for (const line of lines) {
    const idx = line.indexOf(':');
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const val = line.slice(idx + 1).trim();
    map[key] = val;
  }
  return map;
}

function execute() {
  const params = parseInputKV();
  const prUrl = params.pr_url || params.pr || '';
  if (!prUrl) {
    logErr('Missing required param: pr_url');
    process.exit(1);
  }
  const model = params.model || 'GPT-5-Codex';
  const token = params.github_token || process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
  const maxBytes = parseInt(params.max_diff_bytes || '160000', 10);

  const match = prUrl.match(/^https?:\/\/github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/i);
  if (!match) {
    logErr('Invalid pr_url. Expected format: https://github.com/{owner}/{repo}/pull/{number}');
    process.exit(1);
  }
  const owner = match[1], repo = match[2], number = match[3];
  const diffUrl = `https://api.github.com/repos/${owner}/${repo}/pulls/${number}`;

  fetchDiff(diffUrl, token, (err, diff) => {
    if (err) {
      logErr(`Failed to fetch diff: ${err.message || err}`);
      process.exit(1);
    }
    let diffText = diff || '';
    if (maxBytes > 0 && Buffer.byteLength(diffText, 'utf8') > maxBytes) {
      diffText = truncateUtf8(diffText, maxBytes) + '\n... [truncated] ...\n';
    }

    const prompt = buildPrompt(prUrl, diffText);

    // Verify codex is installed
    const which = spawnSync('which', ['codex'], { encoding: 'utf8' });
    if (which.status !== 0) {
      logErr('The codex CLI is not installed. Install with: npm i -g @openai/codex');
      process.exit(1);
    }

    const args = ['exec', prompt];
    if (model) args.unshift('--model', model);

    const res = spawnSync('codex', args, { stdio: 'inherit', env: process.env });
    process.exit(res.status ?? 0);
  });
}

function fetchDiff(apiUrl, token, cb) {
  const opts = url.parse(apiUrl);
  opts.headers = {
    'User-Agent': 'amp-codex-tool',
    'Accept': 'application/vnd.github.v3.diff'
  };
  if (token) {
    opts.headers.Authorization = `Bearer ${token}`;
  }
  https.get(opts, (res) => {
    let data = '';
    res.setEncoding('utf8');
    res.on('data', chunk => { data += chunk; });
    res.on('end', () => {
      if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
        cb(null, data);
      } else {
        cb(new Error(`HTTP ${res.statusCode}: ${data.slice(0, 200)}`));
      }
    });
  }).on('error', (e) => cb(e));
}

function truncateUtf8(str, maxBytes) {
  let bytes = 0, i = 0;
  for (; i < str.length; i++) {
    const code = str.charCodeAt(i);
    if (code <= 0x7f) bytes += 1;
    else if (code <= 0x7ff) bytes += 2;
    else if (code >= 0xd800 && code <= 0xdfff) { // surrogate pair
      bytes += 4; i++;
    } else bytes += 3;
    if (bytes > maxBytes) break;
  }
  return str.slice(0, i);
}

function buildPrompt(prUrl, diff) {
  const now = new Date().toISOString();
  return [
    `You are a senior software engineer performing a rigorous code review for the GitHub Pull Request at: ${prUrl}.`,
    `Time: ${now}. Your task:`,
    `- Provide a concise Summary of the change.`,
    `- List High-priority issues with concrete remediation steps.`,
    `- Identify Bugs, Security concerns, Performance problems, and edge cases.`,
    `- Call out API, data model, and backward-compat risks.`,
    `- Evaluate Tests: missing cases and suggested test additions.`,
    `- Offer Refactoring and readability improvements.`,
    `- Give an Overall recommendation: approve, request changes, or comment-only.`,
    `- Include Inline comments by filename and hunk context when helpful.`,
    '',
    `Review the following unified diff. Focus on changed lines and their context:`,
    '```diff',
    diff,
    '```'
  ].join('\n');
}
