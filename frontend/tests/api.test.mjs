import { test, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { api, getApiBase } from '../lib/api.ts';
const originalFetch = globalThis.fetch;
const originalWindow = globalThis.window;
const originalStorage = globalThis.localStorage;
let values;
beforeEach(() => {
  values = new Map([['access_token', 'old'], ['refresh_token', 'refresh']]);
  globalThis.localStorage = { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: (key) => values.delete(key) };
  globalThis.window = { location: { hostname: 'localhost', pathname: '/', search: '', assign: () => {} } };
});
afterEach(() => { globalThis.fetch = originalFetch; globalThis.window = originalWindow; globalThis.localStorage = originalStorage; });
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

test('concurrent unauthorized requests share refresh rotation', async () => {
  let refreshes = 0;
  globalThis.fetch = async (url, init) => {
    if (url.endsWith('/auth/refresh')) { refreshes++; await new Promise((r) => setTimeout(r, 5)); return json({ access_token: 'new', refresh_token: 'rotated' }); }
    return new Headers(init.headers).get('Authorization') === 'Bearer new' ? json([]) : json({}, 401);
  };
  await Promise.all([api.listTasks(), api.listTasks()]);
  assert.equal(refreshes, 1);
  assert.equal(values.get('refresh_token'), 'rotated');
});

test('validation errors are readable', async () => {
  globalThis.fetch = async () => json({ detail: [{ msg: 'Goal is required' }] }, 422);
  await assert.rejects(api.createTask(''), /Goal is required/);
});

test('transient refresh failure preserves the session', async () => {
  globalThis.fetch = async (url) => url.endsWith('/auth/refresh') ? json({}, 503) : json({}, 401);
  await assert.rejects(api.listTasks());
  assert.equal(values.get('refresh_token'), 'refresh');
});

test('SSE accepts CRLF framing and delivers completion once', async () => {
  const encoder = new TextEncoder();
  globalThis.fetch = async () => new Response(new ReadableStream({ start(controller) {
    controller.enqueue(encoder.encode('data: {"status":"completed"}\r'));
    controller.enqueue(encoder.encode('\n\r\ndata: [DONE]\r\n\r\n'));
    controller.close();
  } }));
  const events = [];
  await new Promise((resolve, reject) => api.runTask(1, (event) => events.push(event), resolve, reject));
  assert.deepEqual(events, [{ status: 'completed' }]);
});

test('API base normalizes trailing slash', () => {
  const oldBase = process.env.NEXT_PUBLIC_API_BASE;
  process.env.NEXT_PUBLIC_API_BASE = 'https://example.com/api/v1/';
  assert.equal(getApiBase(), 'https://example.com/api/v1');
  if (oldBase === undefined) delete process.env.NEXT_PUBLIC_API_BASE; else process.env.NEXT_PUBLIC_API_BASE = oldBase;
});

test('auth redirects reject protocol-relative and backslash URLs', async () => {
  const { safeRedirect } = await import('../lib/navigation.ts');
  for (const value of ['https://evil.example', '//evil.example', '/\\evil.example', 'javascript:alert(1)']) assert.equal(safeRedirect(value), '/');
  assert.equal(safeRedirect('/tasks/2?view=plan'), '/tasks/2?view=plan');
});
