"""RAG Search Lovelace Card — Slice 154.

Interactive search interface for PilotSuite RAG (Retrieval-Augmented Generation).

Features:
- Hybrid search (BM25 + Semantic)
- Real-time results with relevance scores
- Namespace filtering
- Result expansion with metadata
- Search history
- One-click copy results

Architecture:
- Card calls /api/v1/rag/search endpoint
- Uses OllamaRAGClient hybrid search
- Displays fused results with lexical + semantic ranks
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)


def rag_search_card() -> Dict[str, Any]:
    """RAG Search Card with hybrid search UI.
    
    Features:
    - Search input with autocomplete
    - Namespace selector (ha_docs, user_notes, automation_rules, etc.)
    - Top-K slider (1-20 results)
    - Toggle: hybrid vs BM25-only vs semantic-only
    - Results list with scores, ranks, metadata
    - Expandable result details
    - Search history (last 10 queries)
    - Copy to clipboard button
    """
    return {
        "type": "custom:mod-card",
        "card_mod": {
            "style": """
                ha-card {
                    padding: 20px;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    border-radius: 16px;
                }
                .search-container {
                    margin-bottom: 20px;
                }
                .search-input {
                    width: 100%;
                    padding: 12px 16px;
                    background: rgba(255,255,255,0.1);
                    border: 2px solid #3498db;
                    border-radius: 8px;
                    color: #fff;
                    font-size: 16px;
                }
                .search-input:focus {
                    outline: none;
                    border-color: #2ecc71;
                }
                .controls {
                    display: flex;
                    gap: 10px;
                    margin-top: 12px;
                    flex-wrap: wrap;
                }
                .namespace-select, .topk-select, .mode-select {
                    padding: 8px 12px;
                    background: rgba(255,255,255,0.1);
                    border: 1px solid #4a5568;
                    border-radius: 6px;
                    color: #fff;
                    font-size: 14px;
                }
                .search-btn {
                    background: linear-gradient(135deg, #3498db, #2ecc71);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    font-weight: 600;
                }
                .search-btn:hover {
                    opacity: 0.9;
                    transform: translateY(-2px);
                }
                .search-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                .results-container {
                    margin-top: 20px;
                }
                .result-item {
                    background: rgba(255,255,255,0.05);
                    border-left: 4px solid #3498db;
                    padding: 16px;
                    margin: 12px 0;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .result-item:hover {
                    background: rgba(255,255,255,0.1);
                    transform: translateX(4px);
                }
                .result-item.expanded {
                    border-left-color: #2ecc71;
                }
                .result-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                }
                .result-score {
                    background: linear-gradient(135deg, #3498db, #2ecc71);
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                }
                .result-text {
                    color: #eee;
                    font-size: 14px;
                    line-height: 1.6;
                }
                .result-meta {
                    margin-top: 12px;
                    padding-top: 12px;
                    border-top: 1px solid rgba(255,255,255,0.1);
                    font-size: 12px;
                    color: #aaa;
                }
                .result-meta.hidden {
                    display: none;
                }
                .meta-row {
                    display: flex;
                    justify-content: space-between;
                    margin: 4px 0;
                }
                .history-container {
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 2px solid rgba(255,255,255,0.1);
                }
                .history-title {
                    font-size: 14px;
                    color: #aaa;
                    margin-bottom: 10px;
                }
                .history-item {
                    background: rgba(255,255,255,0.05);
                    padding: 8px 12px;
                    margin: 6px 0;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 13px;
                    display: flex;
                    justify-content: space-between;
                }
                .history-item:hover {
                    background: rgba(255,255,255,0.1);
                }
                .loading {
                    text-align: center;
                    padding: 40px;
                    color: #aaa;
                }
                .spinner {
                    border: 3px solid rgba(255,255,255,0.1);
                    border-top-color: #3498db;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 16px;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                .no-results {
                    text-align: center;
                    padding: 40px;
                    color: #aaa;
                }
                .copy-btn {
                    background: rgba(52, 152, 219, 0.3);
                    border: 1px solid #3498db;
                    color: #3498db;
                    padding: 4px 8px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                }
                .copy-btn:hover {
                    background: rgba(52, 152, 219, 0.5);
                }
            """
        },
        "card": {
            "type": "vertical-stack",
            "cards": [
                {
                    "type": "custom:template-entity-row",
                    "entity": "sensor.rag_search_status",
                    "name": "RAG Search",
                    "icon": "mdi:magnify"
                }
            ]
        }
    }


def _generate_rag_search_html() -> str:
    """Generate full RAG Search Card HTML/JS."""
    return """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>RAG Search</title>
  <style>
    :root {
      --bg-primary: #1a1a2e;
      --bg-secondary: #16213e;
      --bg-card: #0f3460;
      --text-primary: #eee;
      --text-secondary: #aaa;
      --accent-blue: #3498db;
      --accent-green: #2ecc71;
      --accent-purple: #9b59b6;
    }
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      padding: 20px;
    }
    
    .search-box {
      max-width: 800px;
      margin: 0 auto;
    }
    
    .search-input {
      width: 100%;
      padding: 16px 20px;
      background: rgba(255,255,255,0.1);
      border: 2px solid var(--accent-blue);
      border-radius: 12px;
      color: #fff;
      font-size: 18px;
      margin-bottom: 16px;
    }
    
    .search-input:focus {
      outline: none;
      border-color: var(--accent-green);
      box-shadow: 0 0 20px rgba(46, 204, 113, 0.3);
    }
    
    .controls {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }
    
    select, button {
      padding: 10px 16px;
      background: rgba(255,255,255,0.1);
      border: 1px solid #4a5568;
      border-radius: 8px;
      color: #fff;
      font-size: 14px;
    }
    
    button {
      background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
      border: none;
      cursor: pointer;
      font-weight: 600;
    }
    
    button:hover { opacity: 0.9; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    
    .results { margin-top: 24px; }
    
    .result {
      background: rgba(255,255,255,0.05);
      border-left: 4px solid var(--accent-blue);
      padding: 16px;
      margin: 12px 0;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .result:hover {
      background: rgba(255,255,255,0.1);
      transform: translateX(4px);
    }
    
    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    
    .score-badge {
      background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
    }
    
    .result-text {
      color: #eee;
      line-height: 1.6;
      font-size: 14px;
    }
    
    .result-meta {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid rgba(255,255,255,0.1);
      font-size: 12px;
      color: #aaa;
      display: none;
    }
    
    .result.expanded .result-meta { display: block; }
    
    .history {
      margin-top: 32px;
      padding-top: 20px;
      border-top: 2px solid rgba(255,255,255,0.1);
    }
    
    .history-title {
      font-size: 14px;
      color: #aaa;
      margin-bottom: 12px;
    }
    
    .history-item {
      background: rgba(255,255,255,0.05);
      padding: 10px 14px;
      margin: 6px 0;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
    }
    
    .history-item:hover { background: rgba(255,255,255,0.1); }
    
    .loading {
      text-align: center;
      padding: 40px;
    }
    
    .spinner {
      border: 3px solid rgba(255,255,255,0.1);
      border-top-color: var(--accent-blue);
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 0 auto 16px;
    }
    
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="search-box">
    <h1 style="margin-bottom: 20px; text-align: center;">🔍 RAG Search</h1>
    
    <input type="text" class="search-input" id="searchInput" placeholder="Suche in Dokumenten..." />
    
    <div class="controls">
      <select id="namespace">
        <option value="default">Alle</option>
        <option value="ha_docs">HA Docs</option>
        <option value="user_notes">User Notes</option>
        <option value="automation_rules">Automation Rules</option>
        <option value="zone_configs">Zone Configs</option>
      </select>
      
      <select id="searchMode">
        <option value="hybrid">Hybrid (BM25 + Semantic)</option>
        <option value="bm25">BM25 Only</option>
        <option value="semantic">Semantic Only</option>
      </select>
      
      <select id="topK">
        <option value="5">5 Results</option>
        <option value="10" selected>10 Results</option>
        <option value="20">20 Results</option>
      </select>
      
      <button onclick="performSearch()">🔍 Search</button>
    </div>
    
    <div class="results" id="results"></div>
    
    <div class="history" id="history"></div>
  </div>
  
  <script>
    const API_BASE = '/api/v1/rag';
    let searchHistory = [];
    
    async function performSearch() {
      const query = document.getElementById('searchInput').value.trim();
      if (!query) return;
      
      const namespace = document.getElementById('namespace').value;
      const mode = document.getElementById('searchMode').value;
      const topK = parseInt(document.getElementById('topK').value);
      
      // Show loading
      document.getElementById('results').innerHTML = `
        <div class="loading">
          <div class="spinner"></div>
          <div>Searching...</div>
        </div>
      `;
      
      try {
        const response = await fetch(`${API_BASE}/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, namespace, top_k: topK, mode })
        });
        
        const data = await response.json();
        displayResults(data.results || []);
        addToHistory(query);
      } catch (error) {
        document.getElementById('results').innerHTML = `
          <div class="no-results">
            <div>❌ Search failed: ${error.message}</div>
          </div>
        `;
      }
    }
    
    function displayResults(results) {
      if (!results || results.length === 0) {
        document.getElementById('results').innerHTML = `
          <div class="no-results">
            <div>🤷 No results found</div>
          </div>
        `;
        return;
      }
      
      const html = results.map((r, i) => `
        <div class="result" onclick="toggleResult(this)" data-index="${i}">
          <div class="result-header">
            <span>#${i + 1} — ${r.doc_id || 'Result ' + (i + 1)}</span>
            <span class="score-badge">Score: ${(r.score || 0).toFixed(3)}</span>
          </div>
          <div class="result-text">${escapeHtml(r.text || '').substring(0, 200)}${(r.text || '').length > 200 ? '...' : ''}</div>
          <div class="result-meta">
            <div class="meta-row"><span>Lexical Rank:</span><span>${r.lexical_rank || 'N/A'}</span></div>
            <div class="meta-row"><span>Semantic Rank:</span><span>${r.semantic_rank || 'N/A'}</span></div>
            <div class="meta-row"><span>Metadata:</span><span>${JSON.stringify(r.metadata || {})}</span></div>
            <button class="copy-btn" onclick="event.stopPropagation(); copyText('${escapeHtml(r.text || '').replace(/'/g, "\\'")}')">📋 Copy</button>
          </div>
        </div>
      `).join('');
      
      document.getElementById('results').innerHTML = html;
    }
    
    function toggleResult(el) {
      el.classList.toggle('expanded');
    }
    
    function addToHistory(query) {
      if (!searchHistory.includes(query)) {
        searchHistory.unshift(query);
        if (searchHistory.length > 10) searchHistory.pop();
        renderHistory();
      }
    }
    
    function renderHistory() {
      const html = searchHistory.map(q => `
        <div class="history-item" onclick="document.getElementById('searchInput').value='${escapeHtml(q)}'; performSearch()">
          <span>🔍 ${escapeHtml(q)}</span>
          <span>↻</span>
        </div>
      `).join('');
      
      document.getElementById('history').innerHTML = searchHistory.length ? `
        <div class="history-title">Recent Searches</div>
        ${html}
      ` : '';
    }
    
    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    function copyText(text) {
      navigator.clipboard.writeText(text).then(() => {
        alert('✅ Copied to clipboard');
      });
    }
    
    // Enter key to search
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') performSearch();
    });
    
    // Load history from localStorage
    try {
      searchHistory = JSON.parse(localStorage.getItem('ragSearchHistory') || '[]');
      renderHistory();
    } catch (e) {}
    
    // Save history to localStorage
    const originalAddToHistory = addToHistory;
    addToHistory = (query) => {
      originalAddToHistory(query);
      localStorage.setItem('ragSearchHistory', JSON.stringify(searchHistory));
    };
  </script>
</body>
</html>"""


async def async_publish_rag_search_panel(hass, core_url: str, api_token: str):
    """Publish RAG Search panel to /config/www."""
    from pathlib import Path
    
    html = _generate_rag_search_html()
    panel_path = Path("/config/www/copilot_ha/rag_search.html")
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    
    await hass.async_add_executor_job(panel_path.write_text, html, "utf-8")
    
    # Register with HA Lovelace if needed
    # This can be added to lovelace resources automatically
    
    return panel_path
