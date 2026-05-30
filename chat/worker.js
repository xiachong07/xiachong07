/**
 * Cloudflare Worker · Claude Chat Proxy
 *
 * 部署步骤:
 * 1. 注册 https://workers.cloudflare.com (免费)
 * 2. npm install -g wrangler
 * 3. wrangler login
 * 4. wrangler secret put CLAUDE_API_KEY
 *    → 粘贴你的 Anthropic API Key: https://console.anthropic.com
 * 5. 修改下方 ANTHROPIC_BASE_URL（如使用代理请替换）
 * 6. wrangler deploy
 * 7. 将 chat.html 中的 API_URL 替换为你的 worker 地址
 *
 * 费用: Cloudflare Workers 免费额度 10万次/天, 足够个人使用
 */

// ═══════════ 配置 ═══════════════════════════════════════════
const ANTHROPIC_BASE_URL = 'https://api.anthropic.com/v1/messages';
const MODEL = 'claude-sonnet-4-6';   // 可选: claude-opus-4-7, claude-haiku-4-5
const MAX_TOKENS = 1024;
// ═════════════════════════════════════════════════════════════

export default {
  async fetch(request, env) {
    // CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    }

    if (request.method !== 'POST') {
      return new Response('Send a POST with { "message": "..." }', { status: 405 });
    }

    const { message } = await request.json();
    if (!message) {
      return new Response(JSON.stringify({ error: 'Empty message' }), { status: 400 });
    }

    // Rate limit: 20 req/min per IP (free tier protection)
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    // Simple in-memory rate limiting (resets on worker cold start)

    const body = JSON.stringify({
      model: MODEL,
      max_tokens: MAX_TOKENS,
      messages: [
        {
          role: 'user',
          content: `You are a helpful AI assistant embedded in @xiaochong07's GitHub profile chat. `
            + `Keep responses concise and friendly. The user knows you're an AI. `
            + `If asked about coding, math, data science, or the BirdCLEF competition, `
            + `share relevant knowledge. Speak in the same language as the user.\n\n`
            + `User message: ${message}`
        }
      ]
    });

    const resp = await fetch(ANTHROPIC_BASE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': env.CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01',
      },
      body,
    });

    const data = await resp.json();
    const reply = data?.content?.[0]?.text || 'Sorry, I could not process that.';

    return new Response(JSON.stringify({ reply }), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      }
    });
  }
};
