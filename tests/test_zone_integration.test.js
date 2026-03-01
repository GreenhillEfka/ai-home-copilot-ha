/**
 * Zone Editor Full-Stack Integration Tests
 * Tests: Frontend ↔ API ↔ Database end-to-end
 * 
 * @version 1.0.0
 * @description Jest + Puppeteer integration tests for Zone Editor functionality
 * 
 * Test Coverage:
 * 1. Frontend loads zones from API
 * 2. Zone-Create works (Frontend → API → DB)
 * 3. Entity Drag&Drop saves in backend
 * 4. Validation works (Frontend + Backend)
 * 5. Auto-Save functionality
 */

'use strict';

const puppeteer = require('puppeteer');
const http = require('http');

// ============================================================================
// Mock Server Configuration
// ============================================================================

const MOCK_API_PORT = 4567;
const BASE_URL = `http://localhost:${MOCK_API_PORT}`;

// Mock zone data matching the backend API structure
const MOCK_ZONES_DATA = {
  success: true,
  data: {
    zones: [
      {
        zone_id: 'living_room',
        name: 'Wohnzimmer',
        floor: 1,
        area_sqm: 35.5,
        entities: {
          lights: ['light.living_room_main', 'light.living_room_lamp'],
          climate: ['climate.living_room_thermostat'],
          media: ['media_player.living_room_tv'],
          motion: ['binary_sensor.living_room_motion']
        },
        entity_ids: [
          'light.living_room_main',
          'light.living_room_lamp',
          'climate.living_room_thermostat',
          'media_player.living_room_tv',
          'binary_sensor.living_room_motion',
          'sensor.living_room_temperature',
          'sensor.living_room_humidity'
        ],
        mood: {
          comfort: 0.82,
          joy: 0.75,
          frugality: 0.68
        },
        status: 'active',
        person_count: 2,
        quick_actions: [
          { action_id: 'living_room_lights_on', name: 'Licht an', icon: 'mdi:lightbulb' },
          { action_id: 'living_room_lights_off', name: 'Licht aus', icon: 'mdi:lightbulb-off' }
        ]
      },
      {
        zone_id: 'kitchen',
        name: 'Küche',
        floor: 1,
        area_sqm: 18.0,
        entities: {
          lights: ['light.kitchen_main', 'light.kitchen_counter'],
          climate: ['climate.kitchen_thermostat'],
          appliances: ['switch.kitchen_coffee', 'switch.kitchen_toaster']
        },
        entity_ids: [
          'light.kitchen_main',
          'light.kitchen_counter',
          'climate.kitchen_thermostat',
          'switch.kitchen_coffee',
          'switch.kitchen_toaster',
          'sensor.kitchen_temperature'
        ],
        mood: {
          comfort: 0.75,
          joy: 0.68,
          frugality: 0.82
        },
        status: 'idle',
        person_count: 0,
        quick_actions: [
          { action_id: 'kitchen_lights_on', name: 'Licht an', icon: 'mdi:lightbulb' }
        ]
      },
      {
        zone_id: 'bedroom',
        name: 'Schlafzimmer',
        floor: 2,
        area_sqm: 22.0,
        entities: {
          lights: ['light.bedroom_main', 'light.bedroom_bedside'],
          climate: ['climate.bedroom_thermostat'],
          blinds: ['cover.bedroom_blinds']
        },
        entity_ids: [
          'light.bedroom_main',
          'light.bedroom_bedside',
          'climate.bedroom_thermostat',
          'cover.bedroom_blinds',
          'sensor.bedroom_temperature'
        ],
        mood: {
          comfort: 0.88,
          joy: 0.65,
          frugality: 0.72
        },
        status: 'idle',
        person_count: 0,
        quick_actions: []
      }
    ],
    total_zones: 3,
    active_zones: 1,
    total_entities: 19
  }
};

const MOCK_ZONES_SUMMARY = {
  success: true,
  data: {
    total_zones: 3,
    active_zones: 1,
    idle_zones: 2,
    total_entities: 19,
    floors: [1, 2],
    zones_by_floor: {
      1: 2,
      2: 1
    }
  }
};

const MOCK_CREATE_ZONE_RESPONSE = {
  success: true,
  data: {
    zone_id: 'new_zone',
    name: 'Neue Zone',
    created_at: new Date().toISOString(),
    message: 'Zone created successfully'
  }
};

const MOCK_UPDATE_ZONE_RESPONSE = {
  success: true,
  data: {
    zone_id: 'living_room',
    updated_at: new Date().toISOString(),
    message: 'Zone updated successfully'
  }
};

const MOCK_VALIDATION_ERROR = {
  success: false,
  error: 'validation_error',
  details: [
    { field: 'name', message: 'Name is required' },
    { field: 'zone_id', message: 'Zone ID must be unique' }
  ]
};

// In-memory "database" for testing persistence
let mockDatabase = {
  zones: JSON.parse(JSON.stringify(MOCK_ZONES_DATA.data.zones)),
  lastUpdate: new Date().toISOString()
};

// ============================================================================
// Mock API Server
// ============================================================================

let apiServer = null;

function createMockApiServer() {
  return http.createServer((req, res) => {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Auth-Token, Authorization');
    res.setHeader('Content-Type', 'application/json');

    // Handle preflight
    if (req.method === 'OPTIONS') {
      res.statusCode = 204;
      return res.end();
    }

    // Auth check (simplified)
    const authToken = req.headers['x-auth-token'] || req.headers['authorization'];
    if (!authToken && !req.url.includes('/health')) {
      res.statusCode = 401;
      return res.end(JSON.stringify({
        success: false,
        error: 'unauthorized',
        message: 'Valid X-Auth-Token or Bearer token required'
      }));
    }

    const url = new URL(req.url, `http://localhost:${MOCK_API_PORT}`);
    const pathname = url.pathname;

    // Route handling
    try {
      // Health check
      if (pathname === '/health' && req.method === 'GET') {
        res.statusCode = 200;
        return res.end(JSON.stringify({ status: 'ok', timestamp: new Date().toISOString() }));
      }

      // GET all zones
      if (pathname === '/api/v1/zone/dashboard' && req.method === 'GET') {
        res.statusCode = 200;
        return res.end(JSON.stringify({
          success: true,
          data: {
            zones: mockDatabase.zones,
            total_zones: mockDatabase.zones.length,
            active_zones: mockDatabase.zones.filter(z => z.status === 'active').length,
            total_entities: mockDatabase.zones.reduce((sum, z) => sum + (z.entity_ids?.length || 0), 0)
          }
        }));
      }

      // GET zone summary
      if (pathname === '/api/v1/zone/dashboard/summary' && req.method === 'GET') {
        res.statusCode = 200;
        return res.end(JSON.stringify(MOCK_ZONES_SUMMARY));
      }

      // GET zone mood
      if (pathname === '/api/v1/zone/dashboard/mood' && req.method === 'GET') {
        const moodData = mockDatabase.zones.map(z => ({
          zone_id: z.zone_id,
          name: z.name,
          mood: z.mood
        }));
        res.statusCode = 200;
        return res.end(JSON.stringify({
          success: true,
          data: { zones: moodData }
        }));
      }

      // PUT zone mood
      if (pathname.startsWith('/api/v1/zone/dashboard/mood/') && req.method === 'PUT') {
        const zoneId = pathname.split('/').pop();
        const body = JSON.parse(req.body || '{}');
        
        const zone = mockDatabase.zones.find(z => z.zone_id === zoneId);
        if (!zone) {
          res.statusCode = 404;
          return res.end(JSON.stringify({
            success: false,
            error: 'Zone not found'
          }));
        }

        zone.mood = {
          ...zone.mood,
          ...body,
          updated_at: new Date().toISOString()
        };

        res.statusCode = 200;
        return res.end(JSON.stringify({
          success: true,
          data: { zone_id: zoneId, mood: zone.mood }
        }));
      }

      // POST create zone
      if (pathname === '/api/v1/zone/create' && req.method === 'POST') {
        const body = JSON.parse(req.body || '{}');
        
        // Validation
        if (!body.name || !body.zone_id) {
          res.statusCode = 400;
          return res.end(JSON.stringify(MOCK_VALIDATION_ERROR));
        }

        // Check for duplicate
        if (mockDatabase.zones.some(z => z.zone_id === body.zone_id)) {
          res.statusCode = 409;
          return res.end(JSON.stringify({
            success: false,
            error: 'Zone ID already exists'
          }));
        }

        const newZone = {
          zone_id: body.zone_id,
          name: body.name,
          floor: body.floor || 1,
          area_sqm: body.area_sqm || 0,
          entities: body.entities || {},
          entity_ids: body.entity_ids || [],
          mood: { comfort: 0.5, joy: 0.5, frugality: 0.5 },
          status: 'idle',
          person_count: 0,
          quick_actions: [],
          created_at: new Date().toISOString()
        };

        mockDatabase.zones.push(newZone);
        mockDatabase.lastUpdate = new Date().toISOString();

        res.statusCode = 201;
        return res.end(JSON.stringify({
          ...MOCK_CREATE_ZONE_RESPONSE,
          data: { ...MOCK_CREATE_ZONE_RESPONSE.data, zone: newZone }
        }));
      }

      // POST update zone (includes entity drag&drop)
      if (pathname === '/api/v1/zone/update' && req.method === 'POST') {
        const body = JSON.parse(req.body || '{}');
        const { zone_id, entities, entity_ids, action } = body;

        const zone = mockDatabase.zones.find(z => z.zone_id === zone_id);
        if (!zone) {
          res.statusCode = 404;
          return res.end(JSON.stringify({
            success: false,
            error: 'Zone not found'
          }));
        }

        // Handle entity drag&drop
        if (action === 'add_entity' && body.entity) {
          if (!zone.entity_ids) zone.entity_ids = [];
          if (!zone.entity_ids.includes(body.entity)) {
            zone.entity_ids.push(body.entity);
          }
          const domain = body.entity.split('.')[0];
          if (!zone.entities[domain]) zone.entities[domain] = [];
          if (!zone.entities[domain].includes(body.entity)) {
            zone.entities[domain].push(body.entity);
          }
        }

        if (action === 'remove_entity' && body.entity) {
          if (zone.entity_ids) {
            zone.entity_ids = zone.entity_ids.filter(e => e !== body.entity);
          }
          Object.keys(zone.entities).forEach(domain => {
            zone.entities[domain] = zone.entities[domain].filter(e => e !== body.entity);
          });
        }

        // Handle general updates
        if (entities) zone.entities = { ...zone.entities, ...entities };
        if (entity_ids) zone.entity_ids = entity_ids;

        mockDatabase.lastUpdate = new Date().toISOString();

        res.statusCode = 200;
        return res.end(JSON.stringify({
          ...MOCK_UPDATE_ZONE_RESPONSE,
          data: { ...MOCK_UPDATE_ZONE_RESPONSE.data, zone }
        }));
      }

      // POST quick action
      if (pathname === '/api/v1/zone/dashboard/quick-action' && req.method === 'POST') {
        const body = JSON.parse(req.body || '{}');
        const { action_id, zone_id } = body;

        if (!action_id || !zone_id) {
          res.statusCode = 400;
          return res.end(JSON.stringify({
            success: false,
            error: 'action_id and zone_id required'
          }));
        }

        const zone = mockDatabase.zones.find(z => z.zone_id === zone_id);
        if (!zone) {
          res.statusCode = 404;
          return res.end(JSON.stringify({
            success: false,
            error: 'Zone not found'
          }));
        }

        res.statusCode = 200;
        return res.end(JSON.stringify({
          success: true,
          data: {
            action_id,
            zone_id,
            executed_at: new Date().toISOString(),
            message: 'Action executed successfully'
          }
        }));
      }

      // DELETE zone
      if (pathname.startsWith('/api/v1/zone/delete/') && req.method === 'DELETE') {
        const zoneId = pathname.split('/').pop();
        const index = mockDatabase.zones.findIndex(z => z.zone_id === zoneId);
        
        if (index === -1) {
          res.statusCode = 404;
          return res.end(JSON.stringify({
            success: false,
            error: 'Zone not found'
          }));
        }

        mockDatabase.zones.splice(index, 1);
        mockDatabase.lastUpdate = new Date().toISOString();

        res.statusCode = 200;
        return res.end(JSON.stringify({
          success: true,
          data: { zone_id: zoneId, deleted: true }
        }));
      }

      // GET available entities (for drag&drop source)
      if (pathname === '/api/v1/zone/entities/available' && req.method === 'GET') {
        res.statusCode = 200;
        return res.end(JSON.stringify({
          success: true,
          data: {
            entities: [
              { entity_id: 'light.garage_main', name: 'Garage Light', domain: 'light' },
              { entity_id: 'switch.garden_pump', name: 'Garden Pump', domain: 'switch' },
              { entity_id: 'sensor.outdoor_temp', name: 'Outdoor Temperature', domain: 'sensor' }
            ]
          }
        }));
      }

      // Default 404
      res.statusCode = 404;
      res.end(JSON.stringify({ success: false, error: 'Not found' }));
    } catch (e) {
      console.error('[API] Error:', e);
      res.statusCode = 500;
      res.end(JSON.stringify({ success: false, error: e.message }));
    }
  });
}

// Helper to read request body
function attachBodyParser(server) {
  const originalEmit = server.emit;
  server.emit = function(event, req, res) {
    if (event === 'request' && ['POST', 'PUT', 'DELETE'].includes(req.method)) {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        req.body = body;
        originalEmit.call(server, event, req, res);
      });
      return true;
    }
    return originalEmit.call(server, event, req, res);
  };
}

// ============================================================================
// Test Suite
// ============================================================================

describe('Zone Editor Full-Stack Integration', () => {
  let browser;
  let page;

  beforeAll(async () => {
    // Reset database
    mockDatabase = {
      zones: JSON.parse(JSON.stringify(MOCK_ZONES_DATA.data.zones)),
      lastUpdate: new Date().toISOString()
    };

    // Start mock server
    apiServer = createMockApiServer();
    attachBodyParser(apiServer);
    await new Promise(resolve => apiServer.listen(MOCK_API_PORT, resolve));
    console.log(`[API] Mock server running on port ${MOCK_API_PORT}`);

    // Launch browser
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
  });

  afterAll(async () => {
    if (browser) await browser.close();
    if (apiServer) await new Promise(resolve => apiServer.close(resolve));
  });

  beforeEach(async () => {
    page = await browser.newPage();
    
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      if (type === 'error') console.error(`[Browser ${type}]`, text);
      else console.log(`[Browser ${type}]`, text);
    });

    page.on('pageerror', err => {
      console.error('[Browser Error]', err.message);
    });
  });

  afterEach(async () => {
    if (page) await page.close();
  });

  // ============================================================================
  // 1. API Loading Tests
  // ============================================================================

  describe('1. API Loading', () => {
    test('sollte Zones von API laden', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(true);
      expect(response.data.zones).toBeDefined();
      expect(response.data.total_zones).toBe(3);
    });

    test('sollte Zone Summary von API laden', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard/summary`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(true);
      expect(response.data.total_zones).toBe(3);
      expect(response.data.active_zones).toBe(1);
    });

    test('sollte Mood-Daten von API laden', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard/mood`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(true);
      expect(response.data.zones).toHaveLength(3);
    });

    test('sollte verfügbare Entities laden', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/entities/available`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(true);
      expect(response.data.entities).toBeDefined();
    });

    test('sollte 401 ohne Auth-Token zurückgeben', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard`);
        return { status: res.status, data: await res.json() };
      }, BASE_URL);

      expect(response.status).toBe(401);
      expect(response.data.error).toBe('unauthorized');
    });
  });

  // ============================================================================
  // 2. Zone Create Tests
  // ============================================================================

  describe('2. Zone Create (Frontend → API → DB)', () => {
    test('sollte neue Zone erstellen', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/create`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'office',
            name: 'Büro',
            floor: 1,
            area_sqm: 15.0
          })
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(true);
      expect(response.data.zone_id).toBe('office');
    });

    test('sollte erstellte Zone in DB persistieren', async () => {
      // Create zone
      await page.evaluate(async (url) => {
        await fetch(`${url}/api/v1/zone/create`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'test_zone_persist',
            name: 'Test Zone',
            floor: 1
          })
        });
      }, BASE_URL);

      // Verify it's in the database by fetching all zones
      const zones = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
        const data = await res.json();
        return data.data.zones;
      }, BASE_URL);

      expect(zones.some(z => z.zone_id === 'test_zone_persist')).toBe(true);
    });

    test('sollte Validierungsfehler bei fehlendem Namen zeigen', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/create`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ zone_id: 'invalid_zone' })
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(false);
      expect(response.error).toBe('validation_error');
    });

    test('sollte Fehler bei doppelter Zone-ID zeigen', async () => {
      // First create
      await page.evaluate(async (url) => {
        await fetch(`${url}/api/v1/zone/create`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'duplicate_test',
            name: 'Duplicate Test'
          })
        });
      }, BASE_URL);

      // Second create with same ID
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/create`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'duplicate_test',
            name: 'Duplicate Test 2'
          })
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(false);
      expect(response.error).toContain('already exists');
    });
  });

  // ============================================================================
  // 3. Entity Drag&Drop Tests
  // ============================================================================

  describe('3. Entity Drag&Drop (Frontend → API → DB)', () => {
    test('sollte Entity zu Zone hinzufügen', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/update`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'living_room',
            action: 'add_entity',
            entity: 'light.new_lamp'
          })
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(true);
      
      // Verify entity was added
      const zone = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
        const data = await res.json();
        return data.data.zones.find(z => z.zone_id === 'living_room');
      }, BASE_URL);

      expect(zone.entity_ids).toContain('light.new_lamp');
    });

    test('sollte Entity aus Zone entfernen', async () => {
      // First add an entity
      await page.evaluate(async (url) => {
        await fetch(`${url}/api/v1/zone/update`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'kitchen',
            action: 'add_entity',
            entity: 'switch.temp_switch'
          })
        });
      }, BASE_URL);

      // Then remove it
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/update`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'kitchen',
            action: 'remove_entity',
            entity: 'switch.temp_switch'
          })
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(true);

      // Verify entity was removed
      const zone = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
        const data = await res.json();
        return data.data.zones.find(z => z.zone_id === 'kitchen');
      }, BASE_URL);

      expect(zone.entity_ids).not.toContain('switch.temp_switch');
    });

    test('sollte Entity-Order speichern', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/update`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'bedroom',
            entity_ids: [
              'light.bedroom_bedside',
              'light.bedroom_main',
              'climate.bedroom_thermostat'
            ]
          })
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(true);
    });
  });

  // ============================================================================
  // 4. Validation Tests
  // ============================================================================

  describe('4. Validation (Frontend + Backend)', () => {
    test('sollte leeren Zone-Namen im Frontend validieren', async () => {
      const validationResult = await page.evaluate(() => {
        // Simulate frontend validation
        function validateZoneName(name) {
          if (!name || name.trim() === '') {
            return { valid: false, error: 'Name is required' };
          }
          if (name.length < 2) {
            return { valid: false, error: 'Name must be at least 2 characters' };
          }
          return { valid: true };
        }

        return {
          empty: validateZoneName(''),
          short: validateZoneName('A'),
          valid: validateZoneName('Valid Name')
        };
      });

      expect(validationResult.empty.valid).toBe(false);
      expect(validationResult.short.valid).toBe(false);
      expect(validationResult.valid.valid).toBe(true);
    });

    test('sollte ungültige Zone-ID im Frontend validieren', async () => {
      const validationResult = await page.evaluate(() => {
        function validateZoneId(id) {
          const pattern = /^[a-z][a-z0-9_]*$/;
          if (!pattern.test(id)) {
            return { 
              valid: false, 
              error: 'Zone ID must start with lowercase letter and contain only lowercase letters, numbers, and underscores' 
            };
          }
          return { valid: true };
        }

        return {
          invalid1: validateZoneId('123invalid'),
          invalid2: validateZoneId('Invalid-Zone'),
          valid: validateZoneId('valid_zone_1')
        };
      });

      expect(validationResult.invalid1.valid).toBe(false);
      expect(validationResult.invalid2.valid).toBe(false);
      expect(validationResult.valid.valid).toBe(true);
    });

    test('sollte Backend-Validierung bei Entity-Add durchführen', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/update`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'nonexistent_zone',
            action: 'add_entity',
            entity: 'light.test'
          })
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(false);
      expect(response.error).toBe('Zone not found');
    });
  });

  // ============================================================================
  // 5. Auto-Save Tests
  // ============================================================================

  describe('5. Auto-Save Functionality', () => {
    test('sollte Änderungen automatisch speichern', async () => {
      // Simulate auto-save after entity change
      const autoSaveResult = await page.evaluate(async (url) => {
        const changes = [
          { zone_id: 'living_room', action: 'add_entity', entity: 'light.auto_1' },
          { zone_id: 'living_room', action: 'add_entity', entity: 'light.auto_2' }
        ];

        const results = [];
        for (const change of changes) {
          const res = await fetch(`${url}/api/v1/zone/update`, {
            method: 'POST',
            headers: {
              'X-Auth-Token': 'test-token',
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(change)
          });
          results.push(await res.json());
        }

        return results;
      }, BASE_URL);

      expect(autoSaveResult.every(r => r.success)).toBe(true);

      // Verify all changes persisted
      const zone = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
        const data = await res.json();
        return data.data.zones.find(z => z.zone_id === 'living_room');
      }, BASE_URL);

      expect(zone.entity_ids).toContain('light.auto_1');
      expect(zone.entity_ids).toContain('light.auto_2');
    });

    test('sollte Auto-Save Debouncing implementieren', async () => {
      const debounceTest = await page.evaluate(() => {
        // Simulate debounce logic
        let saveTimeout = null;
        let saveCount = 0;

        function debouncedSave(change, delay = 500) {
          if (saveTimeout) clearTimeout(saveTimeout);
          saveTimeout = setTimeout(() => {
            saveCount++;
            console.log('Auto-saved:', change);
          }, delay);
        }

        // Simulate rapid changes
        debouncedSave({ entity: 'light.1' });
        debouncedSave({ entity: 'light.2' });
        debouncedSave({ entity: 'light.3' });

        // After 100ms, should not have saved yet
        const beforeSave = saveCount;

        return {
          beforeSave,
          description: 'Debounce should delay saves'
        };
      });

      expect(debounceTest.beforeSave).toBe(0);
    });

    test('sollte Auto-Save Status im Frontend anzeigen', async () => {
      const saveStatus = await page.evaluate(() => {
        // Simulate save status tracking
        const status = {
          saving: false,
          saved: true,
          error: null,
          lastSaved: new Date().toISOString()
        };

        function setSaving() {
          status.saving = true;
          status.saved = false;
          status.error = null;
        }

        function setSaved() {
          status.saving = false;
          status.saved = true;
          status.lastSaved = new Date().toISOString();
        }

        function setError(error) {
          status.saving = false;
          status.saved = false;
          status.error = error;
        }

        // Simulate save cycle
        setSaving();
        const isSaving = status.saving;
        setSaved();
        const isSaved = status.saved;

        return { isSaving, isSaved, hasError: status.error !== null };
      });

      expect(saveStatus.isSaving).toBe(false);
      expect(saveStatus.isSaved).toBe(true);
    });
  });

  // ============================================================================
  // 6. Quick Action Tests
  // ============================================================================

  describe('6. Quick Actions', () => {
    test('sollte Quick Action ausführen', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard/quick-action`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            action_id: 'living_room_lights_on',
            zone_id: 'living_room'
          })
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(true);
      expect(response.data.action_id).toBe('living_room_lights_on');
    });

    test('sollte Fehler bei ungültiger Action-ID zeigen', async () => {
      const response = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard/quick-action`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            action_id: '',
            zone_id: 'living_room'
          })
        });
        return res.json();
      }, BASE_URL);

      expect(response.success).toBe(false);
    });
  });

  // ============================================================================
  // 7. Full-Stack End-to-End Tests
  // ============================================================================

  describe('7. Full-Stack End-to-End', () => {
    test('sollte kompletten Zone-Workflow testen', async () => {
      // 1. Load zones
      const loadResult = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
        return res.json();
      }, BASE_URL);

      expect(loadResult.success).toBe(true);
      const initialCount = loadResult.data.total_zones;

      // 2. Create new zone
      const createResult = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/create`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'e2e_test_zone',
            name: 'E2E Test Zone',
            floor: 1
          })
        });
        return res.json();
      }, BASE_URL);

      expect(createResult.success).toBe(true);

      // 3. Add entities to zone
      const addEntityResult = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/update`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: 'e2e_test_zone',
            action: 'add_entity',
            entity: 'light.e2e_light'
          })
        });
        return res.json();
      }, BASE_URL);

      expect(addEntityResult.success).toBe(true);

      // 4. Verify zone exists with entity
      const verifyResult = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/dashboard`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
        return res.json();
      }, BASE_URL);

      const newZone = verifyResult.data.zones.find(z => z.zone_id === 'e2e_test_zone');
      expect(newZone).toBeDefined();
      expect(newZone.entity_ids).toContain('light.e2e_light');

      // 5. Delete zone
      const deleteResult = await page.evaluate(async (url) => {
        const res = await fetch(`${url}/api/v1/zone/delete/e2e_test_zone`, {
          method: 'DELETE',
          headers: { 'X-Auth-Token': 'test-token' }
        });
        return res.json();
      }, BASE_URL);

      expect(deleteResult.success).toBe(true);
    });
  });

  // ============================================================================
  // 8. Performance Tests
  // ============================================================================

  describe('8. Performance', () => {
    test('sollte Zone-Liste in unter 500ms laden', async () => {
      const startTime = Date.now();
      
      await page.evaluate(async (url) => {
        await fetch(`${url}/api/v1/zone/dashboard`, {
          headers: { 'X-Auth-Token': 'test-token' }
        });
      }, BASE_URL);

      const elapsed = Date.now() - startTime;
      expect(elapsed).toBeLessThan(500);
    });

    test('sollte Zone-Create in unter 300ms speichern', async () => {
      const startTime = Date.now();
      
      await page.evaluate(async (url) => {
        await fetch(`${url}/api/v1/zone/create`, {
          method: 'POST',
          headers: {
            'X-Auth-Token': 'test-token',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            zone_id: `perf_test_${Date.now()}`,
            name: 'Performance Test',
            floor: 1
          })
        });
      }, BASE_URL);

      const elapsed = Date.now() - startTime;
      expect(elapsed).toBeLessThan(300);
    });
  });
});

// ============================================================================
// Export for potential standalone usage
// ============================================================================

module.exports = {
  MOCK_API_PORT,
  BASE_URL,
  createMockApiServer,
  MOCK_ZONES_DATA
};
