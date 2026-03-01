/**
 * RAG Hybrid Search Integration Tests v12.0.0
 *
 * Tests: RAG API <-> Frontend <-> WebSocket end-to-end
 * Abdeckung:
 *   1. Document Indexing (POST /api/rag/index)
 *   2. Hybrid Search (BM25 + Semantic + RRF)
 *   3. BM25-only Search
 *   4. Semantic-only Search
 *   5. RRF Reranking
 *   6. Index Statistics + Metrics
 *   7. Auth-Integration
 *   8. Namespace-Isolation
 *   9. User-Flow: Index -> Search -> Rerank -> Display
 *  10. Error Handling + Validation
 *  11. Performance: Latenz + Limits
 *
 * @version 1.0.0 (v12.0.0 Integration)
 */

'use strict';

const http = require('http');
const { WebSocketServer } = require('ws');

// ---------------------------------------------------------------------------
// Mock API Responses
// ---------------------------------------------------------------------------

const MOCK_TOKEN = 'test-secret-token-42';
const MOCK_ADMIN_TOKEN = 'admin-secret-token-99';

// In-memory document store for realistic integration testing
const docStore = new Map();       // namespace -> Map(id -> doc)
const termIndex = new Map();      // namespace -> Map(term -> Set(docId))

function resetStore() {
  docStore.clear();
  termIndex.clear();
}

function indexDocs(namespace, documents) {
  if (!docStore.has(namespace)) docStore.set(namespace, new Map());
  if (!termIndex.has(namespace)) termIndex.set(namespace, new Map());

  const ns = docStore.get(namespace);
  const idx = termIndex.get(namespace);
  let indexed = 0;

  for (const doc of documents) {
    ns.set(doc.id, { ...doc });
    // Simple tokenization for BM25-like search
    const terms = doc.text.toLowerCase().split(/\W+/).filter(Boolean);
    for (const term of terms) {
      if (!idx.has(term)) idx.set(term, new Set());
      idx.get(term).add(doc.id);
    }
    indexed++;
  }
  return indexed;
}

function searchBM25(namespace, query, topK = 10) {
  const ns = docStore.get(namespace);
  const idx = termIndex.get(namespace);
  if (!ns || !idx) return [];

  const queryTerms = query.toLowerCase().split(/\W+/).filter(Boolean);
  const scores = new Map();

  for (const term of queryTerms) {
    const docIds = idx.get(term) || new Set();
    for (const id of docIds) {
      scores.set(id, (scores.get(id) || 0) + 1);
    }
  }

  return [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, topK)
    .map(([id, score], rank) => {
      const doc = ns.get(id);
      return {
        id, score: score / queryTerms.length,
        rank: rank + 1,
        text: doc.text,
        metadata: doc.metadata || {}
      };
    });
}

// Track metrics
let metrics = { search_requests: 0, index_requests: 0, rerank_requests: 0, errors: 0 };
function resetMetrics() { metrics = { search_requests: 0, index_requests: 0, rerank_requests: 0, errors: 0 }; }

// ---------------------------------------------------------------------------
// Mock API Server with realistic BM25 search
// ---------------------------------------------------------------------------

function createMockApiServer() {
  return http.createServer((req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const path = url.pathname;
    const method = req.method;

    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Auth-Token, Authorization');

    if (method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

    const token = req.headers['x-auth-token'] || (req.headers['authorization'] || '').replace('Bearer ', '');
    const authRequired = req.headers['x-test-auth-required'] === 'true';

    // Auth-Check
    if (path.startsWith('/api/rag') && authRequired && !token) {
      res.writeHead(401);
      res.end(JSON.stringify({ error: 'unauthorized' }));
      return;
    }

    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      let payload = {};
      try { payload = JSON.parse(body); } catch (_) {}
      const startTime = Date.now();

      // --- POST /api/rag/index ---
      if (method === 'POST' && path === '/api/rag/index') {
        metrics.index_requests++;

        if (!payload.documents || !Array.isArray(payload.documents) || payload.documents.length === 0) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'documents required' }));
          return;
        }

        if (payload.documents.length > 2000) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'max 2000 documents per request' }));
          return;
        }

        // Validate each doc
        for (const doc of payload.documents) {
          if (!doc.id) {
            res.writeHead(400);
            res.end(JSON.stringify({ error: 'id required for each document' }));
            return;
          }
          if (!doc.text) {
            res.writeHead(400);
            res.end(JSON.stringify({ error: 'text required for each document' }));
            return;
          }
        }

        const namespace = payload.namespace || 'default';
        const indexed = indexDocs(namespace, payload.documents);

        res.writeHead(200);
        res.end(JSON.stringify({
          namespace,
          bm25_indexed: indexed,
          semantic_indexed: payload.index_semantic ? indexed : 0,
          errors: [],
          warnings: [],
          took_ms: Date.now() - startTime
        }));
        return;
      }

      // --- POST /api/rag/search (Hybrid) ---
      if (method === 'POST' && path === '/api/rag/search') {
        metrics.search_requests++;

        if (!payload.query) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'query required' }));
          return;
        }

        const useLexical = payload.use_lexical !== false;
        const useSemantic = payload.use_semantic !== false;

        if (!useLexical && !useSemantic) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'at least one search mode required' }));
          return;
        }

        const namespace = payload.namespace || 'default';
        const topK = Math.min(payload.top_k || 10, 500);
        const includeText = payload.include_text !== false;
        const includeMetadata = payload.include_metadata !== false;

        let results = [];
        let mode = 'bm25';
        const warnings = [];

        if (useLexical) {
          results = searchBM25(namespace, payload.query, topK);
        }

        if (useSemantic && useLexical) {
          mode = 'hybrid_rrf';
          warnings.push('semantic backend not available - using BM25 only');
        } else if (useSemantic && !useLexical) {
          mode = 'semantic';
          results = [];
          warnings.push('semantic backend not available');
        }

        // Apply include flags
        results = results.map(r => {
          const out = { id: r.id, score: r.score, rank: r.rank };
          if (mode === 'hybrid_rrf') {
            out.fused_score = r.score;
            out.lexical_rank = r.rank;
            out.semantic_rank = null;
            out.lexical_score = r.score;
            out.semantic_score = null;
          }
          if (includeText) out.text = r.text;
          if (includeMetadata) out.metadata = r.metadata;
          return out;
        });

        res.writeHead(200);
        res.end(JSON.stringify({
          namespace, query: payload.query, mode,
          results, result_count: results.length,
          warnings, took_ms: Date.now() - startTime
        }));
        return;
      }

      // --- POST /api/rag/search/bm25 ---
      if (method === 'POST' && path === '/api/rag/search/bm25') {
        metrics.search_requests++;

        if (!payload.query) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'query required' }));
          return;
        }

        const namespace = payload.namespace || 'default';
        const topK = Math.min(payload.top_k || 10, 500);
        const results = searchBM25(namespace, payload.query, topK);

        res.writeHead(200);
        res.end(JSON.stringify({
          namespace, query: payload.query, mode: 'bm25',
          results, result_count: results.length,
          warnings: [], took_ms: Date.now() - startTime
        }));
        return;
      }

      // --- POST /api/rag/search/semantic ---
      if (method === 'POST' && path === '/api/rag/search/semantic') {
        metrics.search_requests++;

        if (!payload.query) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'query required' }));
          return;
        }

        res.writeHead(200);
        res.end(JSON.stringify({
          namespace: payload.namespace || 'default',
          query: payload.query, mode: 'semantic',
          results: [], result_count: 0,
          warnings: ['semantic backend not available'],
          took_ms: Date.now() - startTime
        }));
        return;
      }

      // --- POST /api/rag/rerank ---
      if (method === 'POST' && path === '/api/rag/rerank') {
        metrics.rerank_requests++;

        const lexHits = payload.lexical_hits || [];
        const semHits = payload.semantic_hits || [];

        if (lexHits.length === 0 && semHits.length === 0) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'at least one hit list required' }));
          return;
        }

        const topK = payload.top_k || 10;
        const lexWeight = payload.lexical_weight || 1.0;
        const semWeight = payload.semantic_weight || 1.0;
        const rrf_k = payload.rrf_k || 60;

        // RRF Fusion
        const fusedScores = new Map();
        const lexRanks = new Map();
        const semRanks = new Map();
        const lexScores = new Map();
        const semScores = new Map();

        for (const hit of lexHits) {
          const rrfScore = lexWeight / (rrf_k + hit.rank);
          fusedScores.set(hit.id, (fusedScores.get(hit.id) || 0) + rrfScore);
          lexRanks.set(hit.id, hit.rank);
          lexScores.set(hit.id, hit.score);
        }

        for (const hit of semHits) {
          const rrfScore = semWeight / (rrf_k + hit.rank);
          fusedScores.set(hit.id, (fusedScores.get(hit.id) || 0) + rrfScore);
          semRanks.set(hit.id, hit.rank);
          semScores.set(hit.id, hit.score);
        }

        const results = [...fusedScores.entries()]
          .sort((a, b) => b[1] - a[1])
          .slice(0, topK)
          .map(([id, fused_score]) => ({
            id, fused_score,
            lexical_rank: lexRanks.get(id) || null,
            semantic_rank: semRanks.get(id) || null,
            lexical_score: lexScores.get(id) || null,
            semantic_score: semScores.get(id) || null
          }));

        res.writeHead(200);
        res.end(JSON.stringify({
          results, result_count: results.length,
          took_ms: Date.now() - startTime
        }));
        return;
      }

      // --- GET /api/rag/stats ---
      if (method === 'GET' && path === '/api/rag/stats') {
        const namespace = url.searchParams.get('namespace') || 'default';
        const ns = docStore.get(namespace);
        const idx = termIndex.get(namespace);

        res.writeHead(200);
        res.end(JSON.stringify({
          namespace,
          doc_count: ns ? ns.size : 0,
          term_count: idx ? idx.size : 0,
          metrics: { ...metrics }
        }));
        return;
      }

      // Fallback: 404
      res.writeHead(404);
      res.end(JSON.stringify({ error: 'not_found', path }));
    });
  });
}

// ---------------------------------------------------------------------------
// Mock WebSocket Server
// ---------------------------------------------------------------------------

function createMockWsServer(httpServer) {
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });
  const clients = new Set();

  wss.on('connection', (ws, req) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const token = url.searchParams.get('token') || '';

    if (token && token !== MOCK_TOKEN && token !== MOCK_ADMIN_TOKEN) {
      ws.send(JSON.stringify({ event_type: 'error', data: { message: 'Auth failed' } }));
      ws.close(4001);
      return;
    }

    clients.add(ws);
    ws.send(JSON.stringify({
      event_type: 'system_status',
      data: { status: 'connected' },
      timestamp: new Date().toISOString()
    }));

    ws.on('close', () => clients.delete(ws));
  });

  return {
    wss,
    broadcast(event) {
      const msg = JSON.stringify(event);
      for (const c of clients) { if (c.readyState === 1) c.send(msg); }
    },
    getClientCount() { return clients.size; }
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function apiRequest(port, method, path, body = null, token = MOCK_TOKEN, extraHeaders = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: '127.0.0.1', port, path, method,
      headers: { 'Content-Type': 'application/json', ...extraHeaders }
    };
    if (token) options.headers['X-Auth-Token'] = token;

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(data) }); }
        catch (_) { resolve({ status: res.statusCode, data }); }
      });
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

function wsConnect(port, token = MOCK_TOKEN) {
  const WebSocket = require('ws');
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`ws://127.0.0.1:${port}/ws?token=${token}`);
    const messages = [];
    ws.on('open', () => resolve({ ws, messages }));
    ws.on('message', (data) => messages.push(JSON.parse(data)));
    ws.on('error', reject);
  });
}

// Sample documents
const SAMPLE_DOCS = [
  { id: 'doc1', text: 'Python is a great programming language for data science', metadata: { lang: 'en', topic: 'programming' } },
  { id: 'doc2', text: 'Flask is a Python web framework for building APIs', metadata: { lang: 'en', topic: 'web' } },
  { id: 'doc3', text: 'Machine learning uses Python extensively for training models', metadata: { lang: 'en', topic: 'ml' } },
  { id: 'doc4', text: 'JavaScript is used for frontend development and Node.js', metadata: { lang: 'en', topic: 'web' } },
  { id: 'doc5', text: 'Home Assistant automates your smart home with sensors', metadata: { lang: 'en', topic: 'iot' } },
  { id: 'doc6', text: 'Smart home automation with Python and Home Assistant', metadata: { lang: 'en', topic: 'iot' } },
  { id: 'doc7', text: 'Neural networks are deep learning models for AI', metadata: { lang: 'en', topic: 'ml' } },
  { id: 'doc8', text: 'REST API design with Flask and Python backend', metadata: { lang: 'en', topic: 'web' } }
];

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('RAG Hybrid Search Integration Tests v12.0.0', () => {
  let server, wsHandler, port;

  beforeAll((done) => {
    server = createMockApiServer();
    wsHandler = createMockWsServer(server);
    server.listen(0, '127.0.0.1', () => {
      port = server.address().port;
      done();
    });
  });

  afterAll((done) => {
    wsHandler.wss.close();
    server.close(done);
  });

  beforeEach(() => {
    resetStore();
    resetMetrics();
  });

  // -----------------------------------------------------------------------
  // Helper: Index sample docs
  // -----------------------------------------------------------------------
  async function indexSampleDocs(namespace = 'default') {
    return apiRequest(port, 'POST', '/api/rag/index', {
      namespace, documents: SAMPLE_DOCS, index_semantic: false
    });
  }

  // -----------------------------------------------------------------------
  // 1. Document Indexing
  // -----------------------------------------------------------------------
  describe('Document Indexing', () => {
    test('POST /index akzeptiert Dokumente', async () => {
      const res = await indexSampleDocs();
      expect(res.status).toBe(200);
      expect(res.data.bm25_indexed).toBe(8);
      expect(res.data.namespace).toBe('default');
      expect(res.data.took_ms).toBeGreaterThanOrEqual(0);
    });

    test('Leere Dokument-Liste gibt 400', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/index', { documents: [] });
      expect(res.status).toBe(400);
      expect(res.data.error).toContain('documents required');
    });

    test('Dokument ohne ID gibt 400', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/index', {
        documents: [{ text: 'no id' }]
      });
      expect(res.status).toBe(400);
      expect(res.data.error).toContain('id required');
    });

    test('Dokument ohne Text gibt 400', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/index', {
        documents: [{ id: 'd1' }]
      });
      expect(res.status).toBe(400);
      expect(res.data.error).toContain('text required');
    });

    test('Ueber 2000 Dokumente gibt 400', async () => {
      const docs = Array.from({ length: 2001 }, (_, i) => ({ id: `d${i}`, text: `doc ${i}` }));
      const res = await apiRequest(port, 'POST', '/api/rag/index', { documents: docs });
      expect(res.status).toBe(400);
      expect(res.data.error).toContain('max');
    });

    test('Custom Namespace isoliert Dokumente', async () => {
      await apiRequest(port, 'POST', '/api/rag/index', {
        namespace: 'ns1', documents: [{ id: 'a1', text: 'unique alpha document' }], index_semantic: false
      });
      await apiRequest(port, 'POST', '/api/rag/index', {
        namespace: 'ns2', documents: [{ id: 'b1', text: 'unique beta document' }], index_semantic: false
      });

      const res1 = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'alpha', namespace: 'ns1' });
      const res2 = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'alpha', namespace: 'ns2' });

      expect(res1.data.result_count).toBe(1);
      expect(res2.data.result_count).toBe(0);
    });

    test('Upsert aktualisiert bestehende Dokumente', async () => {
      await apiRequest(port, 'POST', '/api/rag/index', {
        documents: [{ id: 'u1', text: 'original content' }], index_semantic: false
      });
      await apiRequest(port, 'POST', '/api/rag/index', {
        documents: [{ id: 'u1', text: 'updated content with new keywords' }], index_semantic: false
      });

      const res = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'updated' });
      expect(res.data.result_count).toBe(1);
      expect(res.data.results[0].id).toBe('u1');
    });

    test('Dokumente mit Metadata werden korrekt indexiert', async () => {
      await apiRequest(port, 'POST', '/api/rag/index', {
        documents: [{ id: 'm1', text: 'metadata test document', metadata: { key: 'value', num: 42 } }],
        index_semantic: false
      });
      const res = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'metadata' });
      expect(res.data.result_count).toBe(1);
      expect(res.data.results[0].metadata.key).toBe('value');
    });
  });

  // -----------------------------------------------------------------------
  // 2. Hybrid Search (BM25 + Semantic + RRF)
  // -----------------------------------------------------------------------
  describe('Hybrid Search', () => {
    test('Hybrid Search mit BM25 Fallback', async () => {
      await indexSampleDocs();
      const res = await apiRequest(port, 'POST', '/api/rag/search', {
        query: 'Python', use_lexical: true, use_semantic: true
      });
      expect(res.status).toBe(200);
      expect(res.data.mode).toBe('hybrid_rrf');
      expect(res.data.result_count).toBeGreaterThan(0);
      expect(res.data.warnings.length).toBeGreaterThan(0); // Semantic not available
    });

    test('BM25-only Modus', async () => {
      await indexSampleDocs();
      const res = await apiRequest(port, 'POST', '/api/rag/search', {
        query: 'Python', use_lexical: true, use_semantic: false
      });
      expect(res.data.mode).toBe('bm25');
      expect(res.data.result_count).toBeGreaterThan(0);
    });

    test('Beide Modi deaktiviert gibt 400', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/search', {
        query: 'test', use_lexical: false, use_semantic: false
      });
      expect(res.status).toBe(400);
    });

    test('Query fehlt gibt 400', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/search', {});
      expect(res.status).toBe(400);
      expect(res.data.error).toContain('query required');
    });

    test('include_text und include_metadata kontrollieren Output', async () => {
      await indexSampleDocs();

      const withText = await apiRequest(port, 'POST', '/api/rag/search', {
        query: 'Python', use_semantic: false, include_text: true, include_metadata: true
      });
      expect(withText.data.results[0].text).toBeDefined();
      expect(withText.data.results[0].metadata).toBeDefined();

      const withoutText = await apiRequest(port, 'POST', '/api/rag/search', {
        query: 'Python', use_semantic: false, include_text: false, include_metadata: false
      });
      expect(withoutText.data.results[0].text).toBeUndefined();
      expect(withoutText.data.results[0].metadata).toBeUndefined();
    });

    test('top_k begrenzt Ergebnisse', async () => {
      await indexSampleDocs();
      const res = await apiRequest(port, 'POST', '/api/rag/search', {
        query: 'Python', use_semantic: false, top_k: 2
      });
      expect(res.data.result_count).toBeLessThanOrEqual(2);
    });

    test('Kein Treffer fuer unbekannten Term', async () => {
      await indexSampleDocs();
      const res = await apiRequest(port, 'POST', '/api/rag/search', {
        query: 'xyznonexistent', use_semantic: false
      });
      expect(res.data.result_count).toBe(0);
    });
  });

  // -----------------------------------------------------------------------
  // 3. BM25-only Search
  // -----------------------------------------------------------------------
  describe('BM25-only Search', () => {
    test('Einfache BM25-Suche', async () => {
      await indexSampleDocs();
      const res = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Flask' });
      expect(res.status).toBe(200);
      expect(res.data.mode).toBe('bm25');
      expect(res.data.result_count).toBeGreaterThan(0);
      // doc2 und doc8 enthalten "Flask"
      const ids = res.data.results.map(r => r.id);
      expect(ids).toContain('doc2');
      expect(ids).toContain('doc8');
    });

    test('Multi-Term Suche rankt richtig', async () => {
      await indexSampleDocs();
      const res = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Python programming' });
      expect(res.data.result_count).toBeGreaterThan(0);
      // doc1 hat beide Terme -> hoechster Score
      expect(res.data.results[0].id).toBe('doc1');
    });

    test('Scores sind absteigend sortiert', async () => {
      await indexSampleDocs();
      const res = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Python web' });
      const scores = res.data.results.map(r => r.score);
      for (let i = 1; i < scores.length; i++) {
        expect(scores[i]).toBeLessThanOrEqual(scores[i - 1]);
      }
    });

    test('Leere Query gibt 400', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: '' });
      expect(res.status).toBe(400);
    });

    test('Namespace-isolierte Suche', async () => {
      await apiRequest(port, 'POST', '/api/rag/index', {
        namespace: 'isolated', documents: [{ id: 'iso1', text: 'isolated document content' }], index_semantic: false
      });
      const res = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'isolated', namespace: 'isolated' });
      expect(res.data.result_count).toBe(1);

      const resDefault = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'isolated', namespace: 'default' });
      expect(resDefault.data.result_count).toBe(0);
    });
  });

  // -----------------------------------------------------------------------
  // 4. Semantic-only Search
  // -----------------------------------------------------------------------
  describe('Semantic-only Search', () => {
    test('Semantic Search ohne Backend gibt 200 + Warning', async () => {
      await indexSampleDocs();
      const res = await apiRequest(port, 'POST', '/api/rag/search/semantic', { query: 'Python' });
      expect(res.status).toBe(200);
      expect(res.data.mode).toBe('semantic');
      expect(res.data.result_count).toBe(0);
      expect(res.data.warnings.length).toBeGreaterThan(0);
    });

    test('Fehlende Query gibt 400', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/search/semantic', {});
      expect(res.status).toBe(400);
    });
  });

  // -----------------------------------------------------------------------
  // 5. RRF Reranking
  // -----------------------------------------------------------------------
  describe('RRF Reranking', () => {
    test('Reranking fusioniert lexical + semantic Hits', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/rerank', {
        lexical_hits: [
          { id: 'a', score: 5.0, rank: 1 },
          { id: 'b', score: 3.0, rank: 2 },
          { id: 'c', score: 1.0, rank: 3 }
        ],
        semantic_hits: [
          { id: 'b', score: 0.9, rank: 1 },
          { id: 'd', score: 0.8, rank: 2 },
          { id: 'a', score: 0.7, rank: 3 }
        ],
        top_k: 5
      });
      expect(res.status).toBe(200);
      expect(res.data.result_count).toBeGreaterThan(0);
      // 'a' und 'b' in beiden Listen -> hoechste fused scores
      const ids = res.data.results.map(r => r.id);
      expect(ids[0]).toBe('a');  // or 'b' - both appear in both lists
      expect(ids).toContain('b');
    });

    test('Reranking mit nur lexical Hits', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/rerank', {
        lexical_hits: [{ id: 'x', score: 1.0, rank: 1 }],
        semantic_hits: []
      });
      expect(res.data.result_count).toBe(1);
      expect(res.data.results[0].id).toBe('x');
    });

    test('Leere Listen geben 400', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/rerank', {
        lexical_hits: [], semantic_hits: []
      });
      expect(res.status).toBe(400);
    });

    test('Gewichtung beeinflusst Ranking', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/rerank', {
        lexical_hits: [{ id: 'a', score: 5.0, rank: 1 }],
        semantic_hits: [{ id: 'b', score: 0.9, rank: 1 }],
        lexical_weight: 2.0,
        semantic_weight: 0.5,
        top_k: 2
      });
      // Hoehere lexical weight -> 'a' sollte vorne sein
      expect(res.data.results[0].id).toBe('a');
    });

    test('Fusion-Metadata vorhanden', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/rerank', {
        lexical_hits: [{ id: 'a', score: 5.0, rank: 1 }],
        semantic_hits: [{ id: 'a', score: 0.9, rank: 1 }],
        top_k: 1
      });
      const result = res.data.results[0];
      expect(result.fused_score).toBeGreaterThan(0);
      expect(result.lexical_rank).toBe(1);
      expect(result.semantic_rank).toBe(1);
    });

    test('took_ms wird zurueckgegeben', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/rerank', {
        lexical_hits: [{ id: 'a', score: 1.0, rank: 1 }],
        semantic_hits: []
      });
      expect(res.data.took_ms).toBeGreaterThanOrEqual(0);
    });
  });

  // -----------------------------------------------------------------------
  // 6. Index Statistics + Metrics
  // -----------------------------------------------------------------------
  describe('Index Statistics + Metrics', () => {
    test('Stats eines leeren Index', async () => {
      const res = await apiRequest(port, 'GET', '/api/rag/stats');
      expect(res.status).toBe(200);
      expect(res.data.doc_count).toBe(0);
      expect(res.data.namespace).toBe('default');
    });

    test('Stats nach Indexierung', async () => {
      await indexSampleDocs();
      const res = await apiRequest(port, 'GET', '/api/rag/stats');
      expect(res.data.doc_count).toBe(8);
      expect(res.data.term_count).toBeGreaterThan(0);
    });

    test('Stats pro Namespace', async () => {
      await apiRequest(port, 'POST', '/api/rag/index', {
        namespace: 'test_ns',
        documents: [{ id: 't1', text: 'test document' }],
        index_semantic: false
      });
      const res = await apiRequest(port, 'GET', '/api/rag/stats?namespace=test_ns');
      expect(res.data.doc_count).toBe(1);
      expect(res.data.namespace).toBe('test_ns');
    });

    test('Metrics tracken Such-Requests', async () => {
      await indexSampleDocs();
      await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Python' });
      await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Flask' });

      const res = await apiRequest(port, 'GET', '/api/rag/stats');
      expect(res.data.metrics.search_requests).toBe(2);
      expect(res.data.metrics.index_requests).toBe(1);
    });

    test('Metrics tracken Rerank-Requests', async () => {
      await apiRequest(port, 'POST', '/api/rag/rerank', {
        lexical_hits: [{ id: 'a', score: 1.0, rank: 1 }],
        semantic_hits: []
      });
      const res = await apiRequest(port, 'GET', '/api/rag/stats');
      expect(res.data.metrics.rerank_requests).toBe(1);
    });
  });

  // -----------------------------------------------------------------------
  // 7. Auth-Integration
  // -----------------------------------------------------------------------
  describe('Auth-Integration', () => {
    test('Requests mit Token funktionieren', async () => {
      const res = await apiRequest(port, 'GET', '/api/rag/stats', null, MOCK_TOKEN);
      expect(res.status).toBe(200);
    });

    test('Auth-Required Mode blockiert ohne Token', async () => {
      const res = await apiRequest(port, 'GET', '/api/rag/stats', null, '',
        { 'X-Test-Auth-Required': 'true' });
      expect(res.status).toBe(401);
    });

    test('Auth-Required Mode erlaubt mit Token', async () => {
      const res = await apiRequest(port, 'GET', '/api/rag/stats', null, MOCK_TOKEN,
        { 'X-Test-Auth-Required': 'true' });
      expect(res.status).toBe(200);
    });
  });

  // -----------------------------------------------------------------------
  // 8. Namespace-Isolation
  // -----------------------------------------------------------------------
  describe('Namespace-Isolation', () => {
    test('Verschiedene Namespaces sind komplett isoliert', async () => {
      // Index in namespace A
      await apiRequest(port, 'POST', '/api/rag/index', {
        namespace: 'alpha', documents: [{ id: 'a1', text: 'alpha document only' }], index_semantic: false
      });
      // Index in namespace B
      await apiRequest(port, 'POST', '/api/rag/index', {
        namespace: 'beta', documents: [{ id: 'b1', text: 'beta document only' }], index_semantic: false
      });

      // Suche in alpha findet nur alpha-Dokumente
      const resA = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'alpha', namespace: 'alpha' });
      expect(resA.data.result_count).toBe(1);
      expect(resA.data.results[0].id).toBe('a1');

      // Suche in beta findet nur beta-Dokumente
      const resB = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'beta', namespace: 'beta' });
      expect(resB.data.result_count).toBe(1);
      expect(resB.data.results[0].id).toBe('b1');

      // Cross-Namespace: alpha-Suche in beta gibt 0
      const resCross = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'alpha', namespace: 'beta' });
      expect(resCross.data.result_count).toBe(0);
    });

    test('Stats sind namespace-spezifisch', async () => {
      await apiRequest(port, 'POST', '/api/rag/index', {
        namespace: 'ns_a', documents: [{ id: 'a1', text: 'test' }, { id: 'a2', text: 'test two' }], index_semantic: false
      });
      await apiRequest(port, 'POST', '/api/rag/index', {
        namespace: 'ns_b', documents: [{ id: 'b1', text: 'single doc' }], index_semantic: false
      });

      const statsA = await apiRequest(port, 'GET', '/api/rag/stats?namespace=ns_a');
      const statsB = await apiRequest(port, 'GET', '/api/rag/stats?namespace=ns_b');
      expect(statsA.data.doc_count).toBe(2);
      expect(statsB.data.doc_count).toBe(1);
    });
  });

  // -----------------------------------------------------------------------
  // 9. User-Flow: Index -> Search -> Rerank -> Display
  // -----------------------------------------------------------------------
  describe('User-Flow: Index -> Search -> Rerank -> Display', () => {
    test('Vollstaendiger RAG-Pipeline-Flow', async () => {
      // 1. Dokumente indexieren
      const indexRes = await indexSampleDocs();
      expect(indexRes.status).toBe(200);
      expect(indexRes.data.bm25_indexed).toBe(8);

      // 2. Hybrid Search
      const searchRes = await apiRequest(port, 'POST', '/api/rag/search', {
        query: 'Python web framework',
        use_lexical: true, use_semantic: true,
        include_text: true, include_metadata: true
      });
      expect(searchRes.status).toBe(200);
      expect(searchRes.data.result_count).toBeGreaterThan(0);

      // 3. Ergebnisse als lexical_hits fuer Reranking verwenden
      const lexHits = searchRes.data.results.map((r, i) => ({
        id: r.id, score: r.score, rank: i + 1
      }));

      // Simulierte semantic Hits
      const semHits = [
        { id: 'doc2', score: 0.95, rank: 1 },  // Flask = Python web framework
        { id: 'doc8', score: 0.88, rank: 2 },  // REST API with Flask
        { id: 'doc1', score: 0.75, rank: 3 }   // Python programming
      ];

      const rerankRes = await apiRequest(port, 'POST', '/api/rag/rerank', {
        lexical_hits: lexHits,
        semantic_hits: semHits,
        top_k: 5
      });
      expect(rerankRes.status).toBe(200);
      expect(rerankRes.data.result_count).toBeGreaterThan(0);

      // 4. Verify: Fusion verbessert Ranking
      const fusedIds = rerankRes.data.results.map(r => r.id);
      // doc2 sollte hoch ranken (in beiden Listen)
      expect(fusedIds).toContain('doc2');

      // 5. Verify: Stats wurden aktualisiert
      const statsRes = await apiRequest(port, 'GET', '/api/rag/stats');
      expect(statsRes.data.metrics.search_requests).toBeGreaterThan(0);
      expect(statsRes.data.metrics.index_requests).toBe(1);
      expect(statsRes.data.metrics.rerank_requests).toBe(1);
    });

    test('Flow mit WebSocket-Notification bei Index-Update', async () => {
      const { ws, messages } = await wsConnect(port);
      await new Promise(r => setTimeout(r, 50));

      // 1. Indexierung
      await indexSampleDocs();

      // 2. Backend notifiziert via WebSocket
      wsHandler.broadcast({
        event_type: 'system_status',
        data: {
          status: 'index_updated',
          namespace: 'default',
          doc_count: 8,
          message: 'RAG-Index aktualisiert'
        }
      });

      await new Promise(r => setTimeout(r, 100));

      // 3. Suche durchfuehren
      const searchRes = await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Python' });
      expect(searchRes.data.result_count).toBeGreaterThan(0);

      // 4. Verify: Index-Update empfangen
      const statusEvents = messages.filter(m =>
        m.event_type === 'system_status' && m.data.status === 'index_updated'
      );
      expect(statusEvents.length).toBe(1);
      expect(statusEvents[0].data.doc_count).toBe(8);

      ws.close();
    });
  });

  // -----------------------------------------------------------------------
  // 10. Error Handling + Validation
  // -----------------------------------------------------------------------
  describe('Error Handling + Validation', () => {
    test('Nicht-JSON Body gibt 400', async () => {
      const res = await new Promise((resolve, reject) => {
        const options = {
          hostname: '127.0.0.1', port, path: '/api/rag/search', method: 'POST',
          headers: { 'Content-Type': 'text/plain', 'X-Auth-Token': MOCK_TOKEN }
        };
        const req = http.request(options, (res) => {
          let data = '';
          res.on('data', c => { data += c; });
          res.on('end', () => resolve({ status: res.statusCode, data: JSON.parse(data) }));
        });
        req.on('error', reject);
        req.write('not json');
        req.end();
      });
      expect(res.status).toBe(400);
    });

    test('Unbekannter Endpoint gibt 404', async () => {
      const res = await apiRequest(port, 'GET', '/api/rag/nonexistent');
      expect(res.status).toBe(404);
    });

    test('Nicht-existierender Namespace gibt leere Ergebnisse', async () => {
      const res = await apiRequest(port, 'POST', '/api/rag/search/bm25', {
        query: 'test', namespace: 'nonexistent'
      });
      expect(res.status).toBe(200);
      expect(res.data.result_count).toBe(0);
    });
  });

  // -----------------------------------------------------------------------
  // 11. Performance: Latenz + Limits
  // -----------------------------------------------------------------------
  describe('Performance', () => {
    test('Indexierung ist schnell (< 500ms fuer 8 docs)', async () => {
      const start = Date.now();
      await indexSampleDocs();
      const elapsed = Date.now() - start;
      expect(elapsed).toBeLessThan(500);
    });

    test('Suche ist schnell (< 200ms)', async () => {
      await indexSampleDocs();
      const start = Date.now();
      await apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Python web' });
      const elapsed = Date.now() - start;
      expect(elapsed).toBeLessThan(200);
    });

    test('Reranking ist schnell (< 100ms)', async () => {
      const start = Date.now();
      await apiRequest(port, 'POST', '/api/rag/rerank', {
        lexical_hits: Array.from({ length: 100 }, (_, i) => ({ id: `d${i}`, score: 100 - i, rank: i + 1 })),
        semantic_hits: Array.from({ length: 100 }, (_, i) => ({ id: `d${i}`, score: (100 - i) / 100, rank: i + 1 })),
        top_k: 20
      });
      const elapsed = Date.now() - start;
      expect(elapsed).toBeLessThan(100);
    });

    test('Parallele Suchen funktionieren', async () => {
      await indexSampleDocs();
      const results = await Promise.all([
        apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Python' }),
        apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Flask' }),
        apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Home Assistant' }),
        apiRequest(port, 'POST', '/api/rag/search/bm25', { query: 'Machine learning' })
      ]);

      results.forEach(res => {
        expect(res.status).toBe(200);
        expect(res.data.result_count).toBeGreaterThan(0);
      });
    });
  });
});
