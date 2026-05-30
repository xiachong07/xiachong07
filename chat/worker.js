/**
 * Cloudflare Worker · DeepSeek Chat Proxy
 *
 * 部署:
 * 1. npm install -g wrangler
 * 2. wrangler login
 * 3. wrangler secret put DEEPSEEK_API_KEY
 *    → https://platform.deepseek.com/api_keys
 * 4. wrangler deploy
 * 5. 将 chat.html 中的 API_URL 替换为你的 worker 地址
 */

const API_BASE = 'https://api.deepseek.com/v1/chat/completions';
const MODEL = 'deepseek-chat';   // deepseek-chat / deepseek-reasoner

export default {
  async fetch(request, env) {
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
      return new Response('POST { "message": "..." }', { status: 405 });
    }

    const { message } = await request.json();
    if (!message) {
      return new Response(JSON.stringify({ error: 'Empty message' }), { status: 400 });
    }

    const body = JSON.stringify({
      model: MODEL,
      messages: [
        { role: 'system', content: 'You are a helpful assistant on @xiaochong07\'s GitHub profile. Keep responses concise. Reply in the same language as the user.' },
        { role: 'user', content: message }
      ],
      max_tokens: 1024,
    });

    const resp = await fetch(API_BASE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${env.DEEPSEEK_API_KEY}`,
      },
      body,
    });

    const data = await resp.json();
    const reply = data?.choices?.[0]?.message?.content || 'Sorry, no response.';

    return new Response(JSON.stringify({ reply }), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      }
    });
  }
};
