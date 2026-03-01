# Phase 7 Feature Proposals

**Created:** 2026-03-01  
**Author:** @cowdya (via @clawdya orchestration)  
**Status:** Draft for Review  
**Target Version:** 12.0.0 (MAJOR release)

---

## Executive Summary

Phase 7 focuses on transforming PilotSuite from a feature-complete backend into a production-ready, user-friendly smart home orchestration platform. Building on Phase 6's ML foundations (RAG, Collective Intelligence, Neuron Visualization), Phase 7 delivers the UX, performance, and documentation needed for real-world deployment.

**Three Pillars:**
1. **UX Dashboard v2** — Zero-config installation, intuitive zone management, live system visualization
2. **Performance Optimization** — Caching, query optimization, sub-100ms response times
3. **OpenAPI Specification** — Complete API documentation, SDK generation, developer onboarding

---

## Priority 1: UX Dashboard v2 & Zone Editor Improvements

### Problem Statement
Current PilotSuite requires manual configuration and lacks visual feedback. Users need:
- Installation in < 5 minutes without technical knowledge
- Visual understanding of what Styx is doing (neuron activity, mood states)
- Easy zone/entity management without YAML editing

### Proposed Features

#### 1.1 Zero-Config Installation Wizard
**Status:** P0 — Critical for adoption

**Features:**
- **Auto-Discovery:** Zeroconf/mDNS detection of Home Assistant instances
- **Smart Auto-Tagging:** ML-based entity classification using:
  - Entity domain patterns (light.*, switch.*, climate.*)
  - Attribute analysis (friendly_name, device_class, icons)
  - Usage patterns (frequency, time-of-day, co-occurrence)
- **Zone Suggestions:** Automatic zone creation based on:
  - Entity naming conventions ("Wohnzimmer Licht" → Wohnzimmer zone)
  - Spatial clustering (entities in same area)
  - Functional grouping (all lights, all climate controls)
- **Example Config Generator:** Pre-populated configuration based on detected HA setup
- **Progressive Disclosure:** Show only essential options first, advanced settings on-demand

**Technical Implementation:**
```python
# Auto-tagger service
class EntityAutoTagger:
    def classify_entity(self, entity: Entity) -> List[Tag]:
        # Pattern matching + heuristics
        # ML model (trained on common HA setups)
        # User override capability
        pass
    
    def suggest_zones(self, entities: List[Entity]) -> List[Zone]:
        # Clustering algorithm (DBSCAN or K-Means)
        # Naming from entity patterns
        # Confidence scoring
        pass
```

**UI Components:**
- Step-by-step wizard (7 steps, < 5 min total)
- Real-time preview of detected entities and zones
- One-click correction interface
- Import/Export configuration

**Success Metrics:**
- Installation time: < 5 minutes (target: 3 min average)
- Manual corrections: < 3 per setup
- First-time success rate: > 95%

#### 1.2 Zone Editor v2
**Status:** P1 — High priority for usability

**Features:**
- **Drag & Drop Interface:** Visual entity assignment to zones
- **Tag-Based Filtering:** Show/hide entities by tag (light, climate, sensor)
- **Bulk Operations:** Multi-select for batch assignments
- **Zone Templates:** Pre-defined zone types (Living Room, Bedroom, Kitchen)
- **Conflict Detection:** Warn if entity assigned to multiple zones
- **Undo/Redo:** Full history of zone changes

**Technical Implementation:**
- Backend: Zone Store v2 with tag indexing
- Frontend: React/Vue component with dnd-kit or similar
- API: RESTful endpoints for zone CRUD operations

**UI Mockup:**
```
┌─────────────────────────────────────────────────────┐
│  Zone Editor                              [+ Add]   │
├─────────────────────────────────────────────────────┤
│  Filters: [All] [Lights] [Climate] [Sensors] [...]  │
├──────────────┬──────────────────────────────────────┤
│              │  Wohnzimmer                          │
│  Entities    │  ┌────────────────────────────────┐  │
│  ┌────────┐  │  │ 💡 Deckenlicht                 │  │
│  │ Licht  │──┼──│ 🌡️ Heizung                     │  │
│  ├────────┤  │  │ 📺 TV                          │  │
│  │ Klima  │  │  └────────────────────────────────┘  │
│  ├────────┤  │                                      │
│  │ Sensor │  │  Schlafzimmer                        │
│  └────────┘  │  ┌────────────────────────────────┐  │
│              │  │ 💡 Nachttischlinks             │  │
│              │  │ 💡 Nachttischrechts            │  │
│              │  │ 🌡️ Heizung                     │  │
│              │  └────────────────────────────────┘  │
└──────────────┴──────────────────────────────────────┘
```

**Success Metrics:**
- Zone setup time: < 2 minutes
- User satisfaction: > 85%
- Error rate (misassignments): < 2%

#### 1.3 Styx Dashboard Tab — Live System Visualization
**Status:** P1 — Differentiator for user trust

**Features:**
- **Active Neuron Brain:** Real-time visualization of which neurons are firing
  - Color-coded by neuron type (Comfort, Energy, Security, etc.)
  - Animation for activation patterns
  - Click to inspect neuron state and weights
- **Communication Pipeline:** Visual flow diagram
  - HA → Core → Webhook → HA
  - Live event stream with timestamps
  - Error highlighting (failed webhooks, timeouts)
- **System States Panel:**
  - Current Mood (Comfort/Joy/Frugality/Security)
  - Confidence score (0-100%)
  - Active automations count
  - Last decision timestamp
- **Live Events Feed:**
  - Scrollable event log
  - Filter by type (trigger, action, decision)
  - Search functionality

**Technical Implementation:**
- WebSocket connection for real-time updates
- Canvas/SVG rendering for neuron visualization
- D3.js or similar for pipeline diagrams
- Event buffering (last 1000 events)

**UI Components:**
```
┌─────────────────────────────────────────────────────┐
│  Styx Dashboard                          [Live ●]   │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │   Neuron Brain  │  │   System Status          │  │
│  │                 │  │   Mood: Comfort 😌       │  │
│  │    (●) (●)      │  │   Confidence: 87%        │  │
│  │   (●)   (●)     │  │   Active: 12 automations │  │
│  │      (●)        │  │   Last: 2s ago           │  │
│  │                 │  └──────────────────────────┘  │
│  └─────────────────┘                                 │
│  ┌────────────────────────────────────────────────┐  │
│  │  Communication Pipeline                        │  │
│  │  [HA] → [Core] → [Webhook] → [HA]             │  │
│  │   14:32    14:32    14:32    14:32            │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │  Live Events                          [Filter] │  │
│  │  14:32:45 | Trigger | Wohnzimmer motion        │  │
│  │  14:32:46 | Decision| Turn on lights           │  │
│  │  14:32:47 | Action  | light.wohnzimmer = on    │  │
│  │  ...                                           │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Success Metrics:**
- Dashboard load time: < 2 seconds
- WebSocket reconnection rate: < 1% per hour
- User engagement: > 60% check dashboard daily

#### 1.4 Chat Interface v1
**Status:** P2 — Enhanced user interaction

**Features:**
- **Conversation History:** Searchable chat log with Styx
- **Context Display:** Show which entities/zones were referenced
- **Tool-Calling Visualization:** Display actions Styx took
- **Quick Actions:** Pre-defined commands (e.g., "Show energy usage")
- **Natural Language Input:** "Turn off all lights in bedroom"

**Technical Implementation:**
- Integration with existing LLM provider (Ollama/Cloud)
- Context window management (last 50 messages)
- Entity resolution from natural language
- Action confirmation for destructive operations

**Success Metrics:**
- Command success rate: > 90%
- Average response time: < 3 seconds
- User satisfaction: > 80%

#### 1.5 Action Recommendations Panel
**Status:** P2 — Proactive assistance

**Features:**
- **Phase 1 (v12.0.0):** Automation error detection
  - Identify broken automations (entities no longer exist)
  - Detect conflicting automations
  - Suggest fixes
- **Phase 2 (v12.1.0):** Optimization suggestions
  - Energy savings opportunities
  - Comfort improvements
  - Security enhancements
- **Phase 3 (v12.2.0):** Habitus-based recommendations
  - Personalized suggestions based on user behavior
  - Seasonal adjustments
  - Predictive automation timing

**UI Design:**
- Side panel with expandable recommendations
- Each recommendation includes:
  - Problem description
  - Proposed solution
  - Expected impact (energy, comfort, cost)
  - Accept/Reject buttons
  - "Ask why" explanation

**Success Metrics:**
- Recommendation acceptance rate: > 40%
- False positive rate: < 10%
- User trust score: > 75%

---

## Priority 2: Performance Optimization & Caching

### Problem Statement
As PilotSuite scales to hundreds of entities and multiple homes, performance becomes critical. Current architecture lacks:
- Query caching for frequently-accessed data
- Connection pooling for database operations
- Response time optimization for real-time features

### Proposed Features

#### 2.1 Hybrid Search Caching Layer
**Status:** P1 — Critical for RAG performance

**Features:**
- **Multi-Level Cache:**
  - L1: In-memory cache (Redis or in-process) for hot queries
  - L2: Persistent cache (SQLite/PostgreSQL) for common searches
  - L3: Vector index cache (FAISS/Chroma) for embedding similarity
- **Cache Invalidation Strategies:**
  - Time-based expiry (TTL: 5 min for queries, 1 hour for embeddings)
  - Event-based invalidation (entity update → invalidate related queries)
  - Manual invalidation API endpoint
- **Query Optimization:**
  - Query result deduplication
  - Batch query processing
  - Lazy loading for large result sets

**Technical Implementation:**
```python
class HybridSearchCache:
    def __init__(self):
        self.l1_cache = LRUCache(maxsize=1000)  # In-memory
        self.l2_cache = SQLiteCache(db_path)     # Persistent
        self.vector_cache = FAISSIndex(dim=768)  # Vector store
    
    async def search(self, query: str, config: HybridSearchConfig) -> List[Result]:
        # Check L1 cache
        if result := self.l1_cache.get(query):
            return result
        
        # Check L2 cache
        if result := await self.l2_cache.get(query):
            self.l1_cache.set(query, result)
            return result
        
        # Execute search
        result = await self._execute_search(query, config)
        
        # Populate caches
        self.l1_cache.set(query, result)
        await self.l2_cache.set(query, result)
        
        return result
```

**Performance Targets:**
- Cached query response: < 50ms (currently ~200ms)
- Cache hit rate: > 80% for common queries
- Memory usage: < 500MB for L1 cache

#### 2.2 Database Query Optimization
**Status:** P1 — Foundation for scalability

**Features:**
- **Index Optimization:**
  - Add composite indexes for common query patterns
  - Partial indexes for filtered queries (e.g., active zones only)
  - Covering indexes for frequently-selected columns
- **Query Refactoring:**
  - Replace N+1 queries with JOINs or batch loading
  - Use EXISTS instead of COUNT for existence checks
  - Implement cursor-based pagination
- **Connection Pooling:**
  - SQLAlchemy connection pool (size: 10-20)
  - Async connection support for high concurrency
  - Connection health checks and automatic recovery

**Technical Implementation:**
```sql
-- Example index additions
CREATE INDEX idx_entities_zone_active ON entities(zone_id, active);
CREATE INDEX idx_notifications_created_desc ON notifications(created_at DESC);
CREATE INDEX idx_zone_entities_composite ON zone_entities(zone_id, entity_id);

-- Query optimization example
-- Before: N+1 query
for zone in zones:
    entities = session.query(Entity).filter_by(zone_id=zone.id).all()

-- After: Batch loading
zones = session.query(Zone).options(joinedload(Zone.entities)).all()
```

**Performance Targets:**
- Zone list query: < 100ms (currently ~500ms)
- Entity lookup by ID: < 10ms
- Notification history (100 items): < 200ms

#### 2.3 WebSocket Connection Optimization
**Status:** P2 — Real-time performance

**Features:**
- **Connection Pooling:** Reuse WebSocket connections
- **Message Batching:** Batch multiple events into single message
- **Compression:** Enable per-message compression (permessage-deflate)
- **Backpressure Handling:** Slow client detection and message dropping
- **Heartbeat Optimization:** Configurable ping/pong intervals

**Technical Implementation:**
- Use `aiohttp` or `FastAPI` WebSocket with compression
- Implement message queue with priority levels
- Add connection health monitoring

**Performance Targets:**
- WebSocket message latency: < 100ms
- Connection stability: > 99.9% uptime
- Memory per connection: < 1MB

---

## Priority 3: OpenAPI/Swagger Specification

### Problem Statement
PilotSuite lacks comprehensive API documentation, making it difficult for:
- Developers to integrate with PilotSuite
- Frontend teams to understand available endpoints
- Third-party tool creators to build extensions

### Proposed Features

#### 3.1 OpenAPI 3.0 Specification
**Status:** P1 — Developer experience

**Features:**
- **Complete API Coverage:**
  - All Phase 5 endpoints (Notifications, Sharing, Collective Intelligence)
  - All Phase 6 endpoints (RAG, Neuron Visualization, WebSocket)
  - All Phase 7 endpoints (Zone Management, Auto-Tagging)
- **Interactive Documentation:**
  - Swagger UI integration at `/api/docs`
  - Try-it-out functionality with auth support
  - Schema validation examples
- **Code Generation:**
  - Python SDK (async/sync clients)
  - TypeScript/JavaScript client
  - Postman collection
  - curl examples

**Technical Implementation:**
```python
# FastAPI example (auto-generates OpenAPI)
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

app = FastAPI(
    title="PilotSuite API",
    version="12.0.0",
    description="Smart home orchestration platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# For Flask, use flask-openapi3 or apispec
```

**Deliverables:**
- `openapi.yaml` — Complete OpenAPI 3.0 specification
- `/api/docs` — Interactive Swagger UI
- `/api/openapi.json` — Machine-readable spec
- SDK packages (Python, TypeScript)

#### 3.2 API Documentation Website
**Status:** P2 — User onboarding

**Features:**
- **Getting Started Guide:**
  - Authentication setup
  - First API call tutorial
  - Common use cases
- **Endpoint Reference:**
  - Request/response examples
  - Error code documentation
  - Rate limiting information
- **Integration Guides:**
  - Home Assistant integration
  - Custom dashboard integration
  - Mobile app development
- **Changelog:**
  - Version history
  - Breaking changes
  - Deprecation notices

**Technical Implementation:**
- Use Docusaurus, GitBook, or MkDocs
- Auto-generate from OpenAPI spec
- Versioned documentation (v11.x, v12.x)
- Search functionality

**Success Metrics:**
- Documentation completeness: 100% of endpoints
- Developer onboarding time: < 30 minutes
- Support ticket reduction: > 30%

#### 3.3 SDK Development
**Status:** P2 — Developer adoption

**Features:**
- **Python SDK:**
  - Async and sync clients
  - Type hints and IDE autocomplete
  - Automatic retry logic
  - Connection pooling
- **TypeScript SDK:**
  - Browser and Node.js support
  - React hooks for common operations
  - TypeScript types from OpenAPI spec
- **Example Projects:**
  - Custom dashboard example
  - Automation script examples
  - Mobile app starter template

**Technical Implementation:**
```python
# Python SDK example
from pilotsuite import PilotSuiteClient

async with PilotSuiteClient(base_url="http://localhost:8123", api_key="...") as client:
    # Get all zones
    zones = await client.zones.list()
    
    # Hybrid search
    results = await client.rag.hybrid_search(
        query="Turn off lights in living room",
        config={"top_k": 5}
    )
    
    # Send notification
    await client.notifications.send(
        title="Welcome",
        message="PilotSuite is ready!"
    )
```

**Success Metrics:**
- SDK download count: > 100 in first month
- GitHub stars: > 50
- Community contributions: > 5 PRs

---

## Implementation Timeline

### Phase 7.1 (v12.0.0 — MAJOR) — Q2 2026
**Duration:** 6 weeks  
**Focus:** UX Foundation

**Week 1-2:** Zero-Config Installation
- Auto-discovery service
- Entity auto-tagger
- Zone suggestion engine
- Installation wizard UI

**Week 3-4:** Zone Editor v2
- Drag & drop interface
- Tag-based filtering
- Bulk operations
- Zone templates

**Week 5-6:** Dashboard Tab v1
- Neuron visualization
- System status panel
- Live events feed
- WebSocket integration

**Deliverables:**
- Installation time: < 5 minutes
- Zone editor: Fully functional
- Dashboard: Live visualization

### Phase 7.2 (v12.1.0 — MINOR) — Q3 2026
**Duration:** 4 weeks  
**Focus:** Performance & Documentation

**Week 1-2:** Caching Layer
- Hybrid search cache (L1/L2)
- Query optimization
- Connection pooling

**Week 3-4:** OpenAPI Specification
- Complete OpenAPI 3.0 spec
- Swagger UI integration
- Python SDK v1

**Deliverables:**
- Query response: < 100ms (cached)
- API docs: 100% coverage
- Python SDK: Published to PyPI

### Phase 7.3 (v12.2.0 — MINOR) — Q4 2026
**Duration:** 6 weeks  
**Focus:** Advanced Features

**Week 1-2:** Chat Interface
- Conversation history
- Context display
- Natural language commands

**Week 3-4:** Action Recommendations
- Automation error detection
- Optimization suggestions
- Recommendation UI

**Week 5-6:** TypeScript SDK & Mobile
- TypeScript client
- React hooks
- Mobile app starter

**Deliverables:**
- Chat: Production-ready
- Recommendations: Phase 1 complete
- TypeScript SDK: Published to npm

---

## Success Criteria

### Quantitative Metrics
| Metric | Current | Phase 7 Target | Improvement |
|--------|---------|----------------|-------------|
| Installation Time | ~30 min | < 5 min | 83% faster |
| Query Response Time | ~200ms | < 50ms (cached) | 75% faster |
| API Documentation Coverage | 0% | 100% | Complete |
| Test Coverage | 98% | > 99% | +1% |
| User Satisfaction | N/A | > 85% | Baseline |
| Dashboard Load Time | N/A | < 2s | Target |
| Cache Hit Rate | 0% | > 80% | New feature |

### Qualitative Metrics
- **User Feedback:** Positive reviews on installation experience
- **Developer Adoption:** SDK downloads, GitHub stars, community contributions
- **Support Load:** Reduction in "how to setup" tickets
- **Trust:** Users understand what Styx is doing (dashboard transparency)

---

## Risks & Mitigations

### Risk 1: Auto-Tagging Accuracy
**Risk:** Incorrect entity classification frustrates users  
**Mitigation:**
- Provide easy manual override
- Show confidence scores
- Learn from user corrections (feedback loop)
- Start conservative (fewer auto-tags, more manual)

### Risk 2: Performance Regression
**Risk:** Caching adds complexity and potential bugs  
**Mitigation:**
- Extensive testing with load simulation
- Cache bypass option for debugging
- Monitoring and alerting on cache hit rates
- Gradual rollout (canary deployments)

### Risk 3: Documentation Drift
**Risk:** OpenAPI spec becomes outdated  
**Mitigation:**
- Auto-generate spec from code (FastAPI or decorators)
- CI/CD check: spec must match implementation
- Version-locked documentation
- Automated changelog generation

### Risk 4: Scope Creep
**Risk:** Phase 7 becomes too ambitious  
**Mitigation:**
- Strict prioritization (P0, P1, P2)
- Time-boxed iterations (2-week sprints)
- MVP approach for each feature
- Willingness to defer P2 features to Phase 8

---

## Resource Requirements

### Development Team
- **@cowdya:** Backend implementation (caching, OpenAPI, SDK)
- **@styx:** HA integration, auto-discovery, entity analysis
- **@groky:** Testing, UX review, installation validation
- **@viewona:** Dashboard visualization, neuron brain UI
- **@clawdya:** Orchestration, user feedback integration

### Infrastructure
- **CI/CD:** GitHub Actions for automated testing and deployment
- **Documentation Hosting:** GitHub Pages or Vercel
- **Package Registries:** PyPI, npm, Docker Hub
- **Monitoring:** Prometheus/Grafana for performance metrics

### Tools & Libraries
- **Caching:** Redis (optional), SQLite (built-in)
- **OpenAPI:** FastAPI or flask-openapi3
- **SDK Generation:** openapi-generator or custom
- **Visualization:** D3.js, Canvas API, or SVG
- **Testing:** pytest, pytest-asyncio, locust (load testing)

---

## Open Questions

1. **Dashboard Implementation:** Lovelace custom card vs. Custom Panel vs. standalone web app?
   - Recommendation: Custom Panel for tightest integration

2. **Cache Backend:** Redis vs. in-memory vs. SQLite?
   - Recommendation: SQLite for simplicity, Redis for multi-instance deployments

3. **SDK Priority:** Python first, then TypeScript, or parallel development?
   - Recommendation: Python first (internal dogfooding), TypeScript second

4. **Neuron Visualization:** Static diagram vs. interactive animation?
   - Recommendation: Interactive Canvas-based animation for engagement

5. **Auto-Tagging ML Model:** Train custom model or use heuristics only?
   - Recommendation: Heuristics first (v12.0.0), ML model later (v12.2.0)

---

## Next Steps

### Immediate (Week of 2026-03-01)
- [ ] Review this proposal with @clawdya and team
- [ ] Prioritize features for v12.0.0 MVP
- [ ] Create GitHub issues for Phase 7.1 tasks
- [ ] Set up project board for tracking

### Short-term (March 2026)
- [ ] Implement auto-discovery service
- [ ] Build entity auto-tagger
- [ ] Design zone editor UI mockups
- [ ] Set up OpenAPI spec scaffolding

### Mid-term (April-May 2026)
- [ ] Complete Phase 7.1 (v12.0.0 release)
- [ ] Begin Phase 7.2 development
- [ ] Gather user feedback on beta features
- [ ] Iterate based on feedback

---

## Appendix A: Related Documents

- **PHASE6_TODO.md** — Phase 6 completion status
- **UX_FRONTEND_PRIORITIES.md** — UX requirements and principles
- **docs/COLLECTIVE_INTELLIGENCE.md** — Neuron visualization background
- **docs/RAG_HYBRID_SEARCH.md** — RAG implementation details
- **docs/ZONE_EDITOR.md** — Zone editor technical spec

## Appendix B: Technical References

- **OpenAPI Specification:** https://swagger.io/specification/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Redis Caching Patterns:** https://redis.io/docs/manual/
- **D3.js Examples:** https://d3js.org/examples
- **Home Assistant API:** https://developers.home-assistant.io/docs/api/rest/

---

**Document Status:** Draft  
**Review Requested:** @clawdya, @styx, @groky  
**Target Approval:** 2026-03-01 14:00 CET  
**Implementation Start:** 2026-03-02 (pending approval)
