// RAG Search Card for Lovelace - Search UI with autocomplete, results, and filters
import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { HomeAssistant } from 'custom-card-helpers';

export interface RAGSearchResult {
  id: string;
  text: string;
  score: number;
  rank: number;
  metadata?: {
    source?: string;
    category?: string;
    zone?: string;
    title?: string;
    timestamp?: string;
  };
}

export interface RAGSearchConfig {
  entity?: string;
  title?: string;
  placeholder?: string;
  max_results?: number;
  show_filters?: boolean;
  zones?: string[];
  categories?: string[];
  default_zone?: string;
  default_category?: string;
  api_endpoint?: string;
}

@customElement('ha-copilot-rag-search-card')
export class HaCopilotRAGSearchCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property() public config!: RAGSearchConfig;
  
  @state() private query: string = '';
  @state() private results: RAGSearchResult[] = [];
  @state() private loading: boolean = false;
  @state() private error?: string;
  @state() private suggestions: string[] = [];
  @state() private showSuggestions: boolean = false;
  @state() private selectedZone?: string;
  @state() private selectedCategory?: string;
  @state() private searchHistory: string[] = [];

  public setConfig(config: RAGSearchConfig): void {
    if (!config) {
      throw new Error('RAG Search card requires configuration');
    }
    this.config = {
      placeholder: config.placeholder || 'Search knowledge base...',
      max_results: config.max_results || 10,
      show_filters: config.show_filters !== false,
      zones: config.zones || [],
      categories: config.categories || [],
      default_zone: config.default_zone,
      default_category: config.default_category,
      api_endpoint: config.api_endpoint || '/api/rag/search',
      ...config
    };
    
    this.selectedZone = config.default_zone;
    this.selectedCategory = config.default_category;
    this._loadHistory();
  }

  public static getStubConfig(_hass: HomeAssistant, _entities: string[]): RAGSearchConfig {
    return {
      title: 'Knowledge Search',
      placeholder: 'Search documentation, runbooks, FAQs...',
      max_results: 10,
      show_filters: true,
      zones: ['home', 'work', 'automation'],
      categories: ['documentation', 'runbook', 'faq', 'troubleshooting']
    };
  }

  protected firstUpdated(): void {
    this._setupKeyboardNavigation();
  }

  private _loadHistory(): void {
    try {
      const stored = localStorage.getItem('rag_search_history');
      if (stored) {
        this.searchHistory = JSON.parse(stored);
      }
    } catch (e) {
      this.searchHistory = [];
    }
  }

  private _saveHistory(query: string): void {
    if (!query.trim()) return;
    
    const history = this.searchHistory.filter(h => h !== query);
    history.unshift(query);
    this.searchHistory = history.slice(0, 10);
    
    try {
      localStorage.setItem('rag_search_history', JSON.stringify(this.searchHistory));
    } catch (e) {
      // Ignore storage errors
    }
  }

  private _setupKeyboardNavigation(): void {
    this.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        this.showSuggestions = false;
      }
    });
  }

  private _handleInput(e: Event): void {
    const input = e.target as HTMLInputElement;
    this.query = input.value;
    this._updateSuggestions();
  }

  private _updateSuggestions(): void {
    if (!this.query.trim()) {
      this.suggestions = this.searchHistory.slice(0, 5);
      this.showSuggestions = this.suggestions.length > 0;
      return;
    }

    // Generate suggestions based on query
    const queryLower = this.query.toLowerCase();
    const suggestionsSet = new Set<string>();
    
    // Add matching history items
    for (const item of this.searchHistory) {
      if (item.toLowerCase().includes(queryLower)) {
        suggestionsSet.add(item);
      }
    }
    
    // Add common search suggestions based on query
    const commonSuggestions: Record<string, string[]> = {
      'how': ['how to configure', 'how to troubleshoot', 'how to restart'],
      'what': ['what is the status', 'what entities are available', 'what automations'],
      'error': ['error handling', 'error codes', 'error recovery'],
      'auto': ['automation', 'automations', 'automatic mode'],
      'light': ['lights', 'light control', 'light automation'],
      'sensor': ['sensors', 'sensor data', 'sensor configuration'],
      'zone': ['zones', 'zone control', 'zone configuration']
    };

    for (const [prefix, suggestions] of Object.entries(commonSuggestions)) {
      if (queryLower.startsWith(prefix)) {
        suggestions.forEach(s => suggestionsSet.add(s));
      }
    }

    this.suggestions = Array.from(suggestionsSet).slice(0, 8);
    this.showSuggestions = this.suggestions.length > 0;
  }

  private _selectSuggestion(suggestion: string): void {
    this.query = suggestion;
    this.showSuggestions = false;
    this._performSearch();
  }

  private async _handleKeyDown(e: KeyboardEvent): Promise<void> {
    if (e.key === 'Enter') {
      e.preventDefault();
      this.showSuggestions = false;
      await this._performSearch();
    }
  }

  private async _performSearch(): Promise<void> {
    if (!this.query.trim()) {
      this.error = 'Please enter a search query';
      return;
    }

    this.loading = true;
    this.error = undefined;
    this.results = [];

    try {
      const apiEndpoint = this.config.api_endpoint || '/api/rag/search';
      
      const payload: any = {
        query: this.query,
        top_k: this.config.max_results || 10,
        use_lexical: true,
        use_semantic: true,
        include_text: true,
        include_metadata: true
      };

      // Add filters
      if (this.selectedZone) {
        payload.zone = this.selectedZone;
      }
      if (this.selectedCategory) {
        payload.category = this.selectedCategory;
      }

      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      this.results = (data.results || []).map((r: any, index: number) => ({
        id: r.id,
        text: r.text,
        score: r.score || r.fused_score || 0,
        rank: r.rank || index + 1,
        metadata: r.metadata || {}
      }));

      if (this.results.length === 0) {
        this.error = 'No results found. Try different keywords.';
      } else {
        this._saveHistory(this.query);
      }
    } catch (err: any) {
      this.error = err.message || 'Search failed';
      console.error('RAG Search error:', err);
    } finally {
      this.loading = false;
    }
  }

  private _handleZoneChange(e: Event): void {
    const select = e.target as HTMLSelectElement;
    this.selectedZone = select.value || undefined;
    if (this.query) {
      this._performSearch();
    }
  }

  private _handleCategoryChange(e: Event): void {
    const select = e.target as HTMLSelectElement;
    this.selectedCategory = select.value || undefined;
    if (this.query) {
      this._performSearch();
    }
  }

  private _clearFilters(): void {
    this.selectedZone = undefined;
    this.selectedCategory = undefined;
    if (this.query) {
      this._performSearch();
    }
  }

  private _highlightMatch(text: string, query: string): string {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  private _getSourceIcon(source?: string): string {
    const icons: Record<string, string> = {
      'documentation': '📖',
      'runbook': '📋',
      'faq': '❓',
      'troubleshooting': '🔧',
      'automation': '⚙️',
      'sensor': '📡',
      'light': '💡',
      'default': '📄'
    };
    return icons[source || 'default'] || icons['default'];
  }

  protected render(): any {
    const hasFilters = this.config.show_filters && 
      (this.config.zones?.length > 0 || this.config.categories?.length > 0);

    return html`
      <div class="card">
        <ha-card .header="${this.config.title || 'Knowledge Search'}">
          <div class="content">
            <!-- Search Input -->
            <div class="search-container">
              <div class="search-input-wrapper">
                <span class="search-icon">🔍</span>
                <input
                  type="text"
                  class="search-input"
                  placeholder="${this.config.placeholder || 'Search...'}"
                  .value="${this.query}"
                  @input="${this._handleInput}"
                  @keydown="${this._handleKeyDown}"
                  @focus="${() => this._updateSuggestions()}"
                  @blur="${() => setTimeout(() => this.showSuggestions = false, 200)}"
                />
                ${this.loading ? html`
                  <span class="loading-spinner">⏳</span>
                ` : nothing}
              </div>
              
              <!-- Suggestions Dropdown -->
              ${this.showSuggestions ? html`
                <div class="suggestions-dropdown">
                  ${this.suggestions.map(suggestion => html`
                    <div 
                      class="suggestion-item"
                      @click="${() => this._selectSuggestion(suggestion)}"
                    >
                      <span class="suggestion-icon">🕐</span>
                      <span class="suggestion-text">${suggestion}</span>
                    </div>
                  `)}
                </div>
              ` : nothing}
            </div>

            <!-- Filters -->
            ${hasFilters ? html`
              <div class="filters-row">
                ${this.config.zones?.length > 0 ? html`
                  <div class="filter-group">
                    <label>Zone</label>
                    <select 
                      .value="${this.selectedZone || ''}"
                      @change="${this._handleZoneChange}"
                    >
                      <option value="">All Zones</option>
                      ${this.config.zones.map(zone => html`
                        <option value="${zone}">${zone}</option>
                      `)}
                    </select>
                  </div>
                ` : nothing}
                
                ${this.config.categories?.length > 0 ? html`
                  <div class="filter-group">
                    <label>Category</label>
                    <select 
                      .value="${this.selectedCategory || ''}"
                      @change="${this._handleCategoryChange}"
                    >
                      <option value="">All Categories</option>
                      ${this.config.categories.map(cat => html`
                        <option value="${cat}">${cat}</option>
                      `)}
                    </select>
                  </div>
                ` : nothing}

                ${this.selectedZone || this.selectedCategory ? html`
                  <button class="clear-filters-btn" @click="${this._clearFilters}">
                    ✕ Clear
                  </button>
                ` : nothing}
              </div>
            ` : nothing}

            <!-- Error Message -->
            ${this.error ? html`
              <div class="error-message">
                <span class="error-icon">⚠️</span>
                <span>${this.error}</span>
              </div>
            ` : nothing}

            <!-- Results -->
            <div class="results-container">
              ${this.results.length > 0 ? html`
                <div class="results-header">
                  <span class="results-count">${this.results.length} results found</span>
                </div>
                <div class="results-list">
                  ${this.results.map(result => html`
                    <div class="result-item">
                      <div class="result-header">
                        <span class="result-icon">${this._getSourceIcon(result.metadata?.source)}</span>
                        <span class="result-rank">#${result.rank}</span>
                        <span class="result-score">${(result.score * 100).toFixed(1)}%</span>
                        ${result.metadata?.title ? html`
                          <span class="result-title">${result.metadata.title}</span>
                        ` : nothing}
                      </div>
                      <div class="result-text">
                        ${this._highlightMatch(this._truncateText(result.text, 200), this.query)}
                      </div>
                      <div class="result-meta">
                        ${result.metadata?.source ? html`
                          <span class="meta-item">
                            <span class="meta-label">Source:</span>
                            <span class="meta-value">${result.metadata.source}</span>
                          </span>
                        ` : nothing}
                        ${result.metadata?.zone ? html`
                          <span class="meta-item">
                            <span class="meta-label">Zone:</span>
                            <span class="meta-value">${result.metadata.zone}</span>
                          </span>
                        ` : nothing}
                        ${result.metadata?.timestamp ? html`
                          <span class="meta-item">
                            <span class="meta-label">Updated:</span>
                            <span class="meta-value">${new Date(result.metadata.timestamp).toLocaleDateString()}</span>
                          </span>
                        ` : nothing}
                      </div>
                    </div>
                  `)}
                </div>
              ` : this.query && !this.loading && !this.error ? html`
                <div class="no-results">
                  <span>No results found for "${this.query}"</span>
                </div>
              ` : nothing}
            </div>
          </div>
        </ha-card>
      </div>
    `;
  }

  private _truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  }

  static get styles(): any {
    return css`
      .card {
        width: 100%;
      }
      
      .content {
        padding: 16px;
      }
      
      /* Search Input Styles */
      .search-container {
        position: relative;
        margin-bottom: 16px;
      }
      
      .search-input-wrapper {
        display: flex;
        align-items: center;
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 8px 12px;
        transition: border-color 0.2s ease;
      }
      
      .search-input-wrapper:focus-within {
        border-color: var(--primary-color);
      }
      
      .search-icon {
        font-size: 16px;
        margin-right: 8px;
        opacity: 0.7;
      }
      
      .search-input {
        flex: 1;
        border: none;
        background: transparent;
        font-size: 14px;
        color: var(--primary-text-color);
        outline: none;
      }
      
      .search-input::placeholder {
        color: var(--secondary-text-color);
      }
      
      .loading-spinner {
        font-size: 16px;
        animation: spin 1s linear infinite;
      }
      
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      
      /* Suggestions Dropdown */
      .suggestions-dropdown {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-top: none;
        border-radius: 0 0 8px 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        z-index: 100;
        max-height: 240px;
        overflow-y: auto;
      }
      
      .suggestion-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 12px;
        cursor: pointer;
        transition: background-color 0.2s ease;
      }
      
      .suggestion-item:hover {
        background: rgba(var(--primary-color-rgb, 76, 175, 80), 0.1);
      }
      
      .suggestion-icon {
        font-size: 14px;
        opacity: 0.6;
      }
      
      .suggestion-text {
        font-size: 14px;
        color: var(--primary-text-color);
      }
      
      /* Filters */
      .filters-row {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 16px;
        padding: 12px;
        background: var(--card-background-color);
        border-radius: 8px;
      }
      
      .filter-group {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      
      .filter-group label {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      
      .filter-group select {
        padding: 6px 10px;
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        font-size: 13px;
        cursor: pointer;
        min-width: 120px;
      }
      
      .clear-filters-btn {
        align-self: flex-end;
        padding: 6px 12px;
        background: transparent;
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        color: var(--secondary-text-color);
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
      }
      
      .clear-filters-btn:hover {
        border-color: var(--error-color);
        color: var(--error-color);
      }
      
      /* Error Message */
      .error-message {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px;
        background: rgba(244, 67, 54, 0.1);
        border: 1px solid var(--error-color);
        border-radius: 8px;
        color: var(--error-color);
        font-size: 14px;
        margin-bottom: 16px;
      }
      
      .error-icon {
        font-size: 16px;
      }
      
      /* Results */
      .results-container {
        margin-top: 8px;
      }
      
      .results-header {
        margin-bottom: 12px;
      }
      
      .results-count {
        font-size: 13px;
        color: var(--secondary-text-color);
      }
      
      .results-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      
      .result-item {
        padding: 12px;
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        transition: border-color 0.2s ease;
      }
      
      .result-item:hover {
        border-color: var(--primary-color);
      }
      
      .result-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      
      .result-icon {
        font-size: 16px;
      }
      
      .result-rank {
        font-size: 12px;
        color: var(--secondary-text-color);
        font-weight: 500;
      }
      
      .result-score {
        font-size: 12px;
        color: var(--success-color);
        font-weight: 500;
        padding: 2px 6px;
        background: rgba(76, 175, 80, 0.1);
        border-radius: 4px;
      }
      
      .result-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--primary-text-color);
        margin-left: auto;
      }
      
      .result-text {
        font-size: 13px;
        line-height: 1.5;
        color: var(--primary-text-color);
        margin-bottom: 8px;
      }
      
      .result-text mark {
        background: rgba(255, 235, 59, 0.3);
        color: inherit;
        padding: 1px 2px;
        border-radius: 2px;
      }
      
      .result-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
      }
      
      .meta-item {
        display: flex;
        gap: 4px;
        font-size: 12px;
      }
      
      .meta-label {
        color: var(--secondary-text-color);
      }
      
      .meta-value {
        color: var(--primary-text-color);
      }
      
      .no-results {
        text-align: center;
        padding: 24px;
        color: var(--secondary-text-color);
        font-size: 14px;
      }
    `;
  }
}

// Register the custom element
declare global {
  interface HTMLElementTagNameMap {
    'ha-copilot-rag-search-card': HaCopilotRAGSearchCard;
  }
}
