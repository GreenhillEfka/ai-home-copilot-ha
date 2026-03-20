"""
PilotSuite Styx Dashboard API v1
Zonenzentriertes Dashboard mit Habituszonen-Endpoints.

Fetches live data from PilotSuite Core API (port 8909) with
graceful fallback to default configuration when Core is unavailable.

Zone-IDs sind synchron mit pilotsuite-styx-core:
  living, kitchen, bath, hallway, bedroom, office,
  room_mira, room_paul, terrace, outside

Features:
  - 10 Habituszonen mit vollstaendigem Entity-Mapping
  - Controls (switches, fans, locks, covers) pro Zone
  - Musik/Playlists (Sonos-Integration, Favoriten)
  - Nachrichten/Notifications pro Zone
  - Geburtstage/Haushalt
  - Todos pro Zone
  - Energie-Sensoren pro Zone
  - Kameras pro Zone
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, date, timezone
import threading
import time
import logging
import requests

_LOGGER = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard_v1', __name__, url_prefix='/api/v1/dashboard')

# In-Memory Storage fuer Zone-Daten (aktualisiert durch Core-API oder HA-Integration)
zone_data_store = {}
zone_lock = threading.Lock()

# Cache fuer Core-API Antworten (TTL-basiert)
_core_cache = {}
_core_cache_lock = threading.Lock()
_CACHE_TTL_SECONDS = 30  # 30s Cache fuer Core-Daten


# ═══════════════════════════════════════════════════════════════════════════
# Core API Client
# ═══════════════════════════════════════════════════════════════════════════

def _get_core_url():
    """Resolve Core API base URL from app config or env."""
    try:
        return current_app.config.get('CORE_API_URL', 'http://localhost:8909')
    except RuntimeError:
        import os
        return os.environ.get('CORE_API_URL', 'http://localhost:8909')


def _get_core_headers():
    """Build auth headers for Core API requests."""
    try:
        token = current_app.config.get('CORE_AUTH_TOKEN', '')
    except RuntimeError:
        import os
        token = os.environ.get('COPILOT_AUTH_TOKEN', '')

    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
        headers['X-Auth-Token'] = token
    return headers


def _core_get(path, timeout=5):
    """
    GET request to Core API with caching and error handling.

    Args:
        path: API path (e.g. '/api/v1/zone/dashboard')
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON dict on success, None on failure
    """
    cache_key = path
    now = time.time()

    # Check cache
    with _core_cache_lock:
        cached = _core_cache.get(cache_key)
        if cached and (now - cached['ts']) < _CACHE_TTL_SECONDS:
            return cached['data']

    base_url = _get_core_url()
    url = f"{base_url}{path}"

    try:
        resp = requests.get(url, headers=_get_core_headers(), timeout=timeout)
        if resp.status_code < 400:
            data = resp.json()
            with _core_cache_lock:
                _core_cache[cache_key] = {'data': data, 'ts': now}
            return data
        _LOGGER.debug("Core API %s returned status %d", path, resp.status_code)
    except requests.exceptions.ConnectionError:
        _LOGGER.debug("Core API not reachable at %s", base_url)
    except requests.exceptions.Timeout:
        _LOGGER.debug("Core API timeout for %s", path)
    except Exception as e:
        _LOGGER.debug("Core API error for %s: %s", path, e)

    return None


def _core_post(path, data, timeout=5):
    """POST request to Core API."""
    base_url = _get_core_url()
    url = f"{base_url}{path}"
    try:
        resp = requests.post(url, json=data, headers=_get_core_headers(), timeout=timeout)
        if resp.status_code < 400:
            return resp.json() if resp.content else {'success': True}
        _LOGGER.debug("Core POST %s returned status %d", path, resp.status_code)
    except requests.exceptions.ConnectionError:
        _LOGGER.debug("Core POST not reachable at %s", base_url)
    except requests.exceptions.Timeout:
        _LOGGER.debug("Core POST timeout for %s", path)
    except Exception as e:
        _LOGGER.debug("Core POST error for %s: %s", path, e)
    return None


def _core_put(path, data, timeout=5):
    """PUT request to Core API."""
    base_url = _get_core_url()
    url = f"{base_url}{path}"
    try:
        resp = requests.put(url, json=data, headers=_get_core_headers(), timeout=timeout)
        if resp.status_code < 400:
            return resp.json() if resp.content else {'success': True}
        _LOGGER.debug("Core PUT %s returned status %d", path, resp.status_code)
    except requests.exceptions.ConnectionError:
        _LOGGER.debug("Core PUT not reachable at %s", base_url)
    except requests.exceptions.Timeout:
        _LOGGER.debug("Core PUT timeout for %s", path)
    except Exception as e:
        _LOGGER.debug("Core PUT error for %s: %s", path, e)
    return None


def _core_delete(path, timeout=5):
    """DELETE request to Core API."""
    base_url = _get_core_url()
    url = f"{base_url}{path}"
    try:
        resp = requests.delete(url, headers=_get_core_headers(), timeout=timeout)
        if resp.status_code < 400:
            return resp.json() if resp.content else {'success': True}
        _LOGGER.debug("Core DELETE %s returned status %d", path, resp.status_code)
    except requests.exceptions.ConnectionError:
        _LOGGER.debug("Core DELETE not reachable at %s", base_url)
    except requests.exceptions.Timeout:
        _LOGGER.debug("Core DELETE timeout for %s", path)
    except Exception as e:
        _LOGGER.debug("Core DELETE error for %s: %s", path, e)
    return None


def _invalidate_cache(path=None):
    """Invalidate Core cache, optionally for a specific path."""
    with _core_cache_lock:
        if path:
            _core_cache.pop(path, None)
        else:
            _core_cache.clear()


# ═══════════════════════════════════════════════════════════════════════════
# Live Data Fetchers (Core API first, fallback to defaults)
# ═══════════════════════════════════════════════════════════════════════════

def _fetch_zones_config():
    """
    Fetch zone configurations from Core zone-editor API.
    Returns list of zone config dicts.
    """
    # Try Core zone-editor API
    data = _core_get('/api/v1/zone-editor/zones')
    if data and isinstance(data, dict):
        zones_raw = data.get('zones', [])
        if zones_raw:
            zones = []
            for z in zones_raw:
                zones.append({
                    'id': z.get('zone_id', z.get('id', '')),
                    'name': z.get('name', ''),
                    'icon': z.get('icon', 'mdi-home'),
                    'color': z.get('color', _FALLBACK_ZONE_COLORS.get(
                        z.get('zone_id', z.get('id', '')), '#888')),
                    'enabled': z.get('enabled', True),
                    'priority': z.get('priority', 10),
                    'entities': z.get('entities', {}),
                    'mode': z.get('mode', 'auto'),
                    'rooms': z.get('rooms', []),
                })
            return zones

    # Try Core zone dashboard (alternative source)
    data = _core_get('/api/v1/zone/dashboard')
    if data and isinstance(data, dict):
        zones_raw = data.get('zones', [])
        if zones_raw:
            zones = []
            for z in zones_raw:
                zone_id = z.get('zone_id', z.get('id', ''))
                zones.append({
                    'id': zone_id,
                    'name': z.get('name', z.get('name_de', '')),
                    'icon': z.get('icon', 'mdi-home'),
                    'color': _FALLBACK_ZONE_COLORS.get(zone_id, '#888'),
                    'enabled': z.get('status', 'active') != 'disabled',
                    'priority': z.get('priority', 10),
                    'entities': z.get('entities', {}),
                })
            return zones

    # Fallback to default config
    return FALLBACK_ZONES_CONFIG


def _fetch_household():
    """Fetch household data from Core haushalt API."""
    data = _core_get('/api/v1/haushalt/overview')
    if data and isinstance(data, dict):
        members = []
        # Extract household members from overview
        household_raw = data.get('household', data.get('members', []))
        if household_raw:
            return household_raw

        # Try to build from birthday data
        birthdays = data.get('upcoming_birthdays_7d', [])
        birthday_today = data.get('birthday_today', [])
        # If we have birthday data, return the overview dict directly
        if birthdays or birthday_today:
            return data

    # Try presence API for person data
    data = _core_get('/api/v1/presence/status')
    if data and isinstance(data, dict):
        persons = data.get('persons', data.get('users', []))
        if persons:
            members = []
            for p in persons:
                members.append({
                    'person_id': p.get('person_id', p.get('entity_id', '')),
                    'name': p.get('name', p.get('friendly_name', '')),
                    'role': p.get('role', 'unknown'),
                    'birthday': p.get('birthday', ''),
                    'device_trackers': p.get('device_trackers', []),
                    'preferred_zones': p.get('preferred_zones', []),
                    'state': p.get('state', 'unknown'),
                })
            return members

    return FALLBACK_HOUSEHOLD


def _fetch_playlists(zone_id=None):
    """Fetch playlists from Core Musikwolke API."""
    data = _core_get('/api/v1/musikwolke/status')
    if data and isinstance(data, dict):
        # Try to get playlist data from musikwolke status
        playlists = data.get('playlists', [])
        if playlists:
            if zone_id:
                return [p for p in playlists
                        if zone_id in p.get('zone_affinity', [])]
            return playlists

    # Try zone dashboard for playlist module data
    if zone_id:
        data = _core_get(f'/api/v1/zone/dashboard/{zone_id}')
        if data and isinstance(data, dict):
            modules = data.get('modules', {})
            pl_mod = modules.get('playlists', modules.get('musikwolke', {}))
            if isinstance(pl_mod, dict):
                items = pl_mod.get('playlists', pl_mod.get('items', []))
                if items:
                    return items
    else:
        data = _core_get('/api/v1/zone/dashboard')
        if data and isinstance(data, dict):
            all_playlists = []
            seen_ids = set()
            gl = data.get('global', {})
            mw = gl.get('musikwolke', {})
            if isinstance(mw, dict):
                items = mw.get('playlists', [])
                for p in items:
                    pid = p.get('id', p.get('name', ''))
                    if pid not in seen_ids:
                        seen_ids.add(pid)
                        all_playlists.append(p)
            if all_playlists:
                return all_playlists

    # Fallback
    result = FALLBACK_PLAYLISTS
    if zone_id:
        result = [p for p in result if zone_id in p.get('zone_affinity', [])]
    return result


def _fetch_todos(zone_id=None):
    """Fetch todos/reminders from Core API."""
    data = _core_get('/api/v1/reminders?completed=0')
    if data and isinstance(data, dict):
        reminders = data.get('reminders', data.get('items', []))
        if reminders:
            todos = []
            for r in reminders:
                todos.append({
                    'id': str(r.get('id', '')),
                    'title': r.get('title', r.get('name', '')),
                    'zone_id': r.get('zone_id', ''),
                    'priority': r.get('priority', 'medium'),
                    'due_date': r.get('due_at', r.get('due_date', '')),
                    'category': r.get('category', 'reminder'),
                    'status': 'pending' if not r.get('completed') else 'completed',
                    'description': r.get('description', ''),
                })
            if zone_id:
                todos = [t for t in todos if t.get('zone_id') == zone_id]
            return todos

    # Try shopping list as additional source
    shopping_data = _core_get('/api/v1/shopping?completed=0')
    if shopping_data and isinstance(shopping_data, dict):
        items = shopping_data.get('items', [])
        if items:
            todos = []
            for item in items:
                todos.append({
                    'id': str(item.get('id', '')),
                    'title': item.get('name', item.get('title', '')),
                    'zone_id': item.get('zone_id', 'kitchen'),
                    'priority': 'medium',
                    'due_date': '',
                    'category': 'shopping',
                    'status': 'pending',
                })
            if zone_id:
                todos = [t for t in todos if t.get('zone_id') == zone_id]
            return todos

    # Try zone dashboard for todos module
    data = _core_get('/api/v1/zone/dashboard')
    if data and isinstance(data, dict):
        gl = data.get('global', {})
        todos_mod = gl.get('todos', {})
        if isinstance(todos_mod, dict):
            items = todos_mod.get('items', [])
            if items:
                if zone_id:
                    items = [t for t in items if t.get('zone_id') == zone_id]
                return items

    # Fallback
    result = FALLBACK_TODOS
    if zone_id:
        result = [t for t in result if t.get('zone_id') == zone_id]
    return [t for t in result if t.get('status') != 'completed']


def _fetch_notifications(zone_id=None):
    """Fetch notifications from Core notifications API."""
    data = _core_get('/notifications')
    if data and isinstance(data, dict):
        notifications = data.get('notifications', [])
        if notifications:
            result = []
            for n in notifications:
                result.append({
                    'id': str(n.get('id', '')),
                    'title': n.get('title', n.get('message', '')),
                    'zone_id': n.get('zone_id', ''),
                    'severity': n.get('priority', n.get('severity', 'info')),
                    'acknowledged': n.get('read', n.get('acknowledged', False)),
                    'created_at': n.get('created_at', ''),
                })
            if zone_id:
                result = [n for n in result
                          if n.get('zone_id') == zone_id and not n.get('acknowledged')]
            return result

    # Try zone dashboard for notification data
    data = _core_get('/api/v1/zone/dashboard')
    if data and isinstance(data, dict):
        gl = data.get('global', {})
        notif_mod = gl.get('notifications', {})
        if isinstance(notif_mod, dict):
            items = notif_mod.get('items', notif_mod.get('notifications', []))
            if items:
                if zone_id:
                    items = [n for n in items
                             if n.get('zone_id') == zone_id
                             and not n.get('acknowledged')]
                return items

    # Fallback
    result = FALLBACK_NOTIFICATIONS
    if zone_id:
        result = [n for n in result
                  if n.get('zone_id') == zone_id and not n.get('acknowledged')]
    return result


def _fetch_zone_live_data(zone_id):
    """
    Fetch live sensor/state data for a zone from Core zone dashboard.
    Returns dict with temperature, humidity, brightness, etc.
    """
    # Try per-zone dashboard endpoint
    data = _core_get(f'/api/v1/zone/dashboard/{zone_id}')
    if data and isinstance(data, dict):
        modules = data.get('modules', {})
        live = {}

        # Temperature from heiz module
        heiz = modules.get('heiz', {})
        if isinstance(heiz, dict):
            temp = heiz.get('current_temp', heiz.get('temperature'))
            if temp is not None:
                live['temperature'] = temp
            hum = heiz.get('humidity')
            if hum is not None:
                live['humidity'] = hum

        # Brightness from helligkeit module
        hell = modules.get('helligkeit', {})
        if isinstance(hell, dict):
            br = hell.get('brightness', hell.get('level'))
            if br is not None:
                live['brightness'] = br

        # Light count from licht module
        licht = modules.get('licht', {})
        if isinstance(licht, dict):
            live['lights_on'] = licht.get('on_count', 0)
            live['lights_total'] = licht.get('total', 0)

        # Presence from praesenz/bewegung module
        praesenz = modules.get('praesenz', modules.get('bewegung', {}))
        if isinstance(praesenz, dict):
            live['presence'] = praesenz.get('detected', False)
            live['person_count'] = praesenz.get('person_count',
                                                 data.get('person_count', 0))

        # Media from media module
        media = modules.get('media', {})
        if isinstance(media, dict):
            live['media_playing'] = media.get('state') == 'playing'

        if live:
            live['last_update'] = datetime.now(timezone.utc).isoformat()
            return live

    return None


# ═══════════════════════════════════════════════════════════════════════════
# Fallback-Konfiguration (wenn Core nicht erreichbar)
# ═══════════════════════════════════════════════════════════════════════════

_FALLBACK_ZONE_COLORS = {
    'living': '#4fc3f7', 'kitchen': '#ffb74d', 'bath': '#81c784',
    'office': '#4dd0e1', 'hallway': '#ce93d8', 'bedroom': '#7986cb',
    'room_mira': '#f48fb1', 'room_paul': '#90caf9', 'terrace': '#a5d6a7',
    'outside': '#c5e1a5',
}

FALLBACK_ZONES_CONFIG = [
    {
        'id': 'living', 'name': 'Wohnbereich', 'icon': 'mdi-sofa',
        'color': '#4fc3f7', 'enabled': True, 'priority': 10,
        'entities': {
            'temperature': 'sensor.wohnzimmer_temperatur',
            'humidity': 'sensor.wohnzimmer_luftfeuchtigkeit',
            'lights': ['light.wohnzimmer_decke', 'light.wohnzimmer_stehlampe',
                       'light.wohnzimmer_tv_hintergrund', 'light.esstisch_pendel'],
            'motion': ['binary_sensor.wohnzimmer_praesenz', 'binary_sensor.wohnzimmer_bewegung'],
            'media': ['media_player.sonos_wohnzimmer', 'media_player.sonos_sub_wohnzimmer',
                      'media_player.tv_wohnzimmer'],
            'climate': ['climate.wohnzimmer_thermostat'],
            'switches': ['switch.wohnzimmer_steckdose_tv', 'switch.wohnzimmer_steckdose_stehlampe'],
            'covers': ['cover.wohnzimmer_rollladen_links', 'cover.wohnzimmer_rollladen_rechts'],
            'sensors': ['sensor.wohnzimmer_co2', 'sensor.wohnzimmer_helligkeit',
                        'binary_sensor.wohnzimmer_fenster'],
            'energy': ['sensor.wohnzimmer_verbrauch_kwh', 'sensor.tv_verbrauch_watt'],
            'cameras': ['camera.wohnzimmer_overview'],
        }
    },
    {
        'id': 'kitchen', 'name': 'Kochbereich', 'icon': 'mdi-stove',
        'color': '#ffb74d', 'enabled': True, 'priority': 10,
        'entities': {
            'temperature': 'sensor.kueche_temperatur',
            'humidity': 'sensor.kueche_luftfeuchtigkeit',
            'lights': ['light.kueche_decke', 'light.kueche_arbeitsplatte', 'light.kueche_essbar'],
            'motion': ['binary_sensor.kueche_bewegung'],
            'media': ['media_player.sonos_kueche'],
            'climate': ['climate.kueche_thermostat'],
            'switches': ['switch.kaffeemaschine', 'switch.spuelmaschine',
                         'switch.kueche_steckdose_arbeitsplatte'],
            'sensors': ['sensor.kueche_helligkeit', 'binary_sensor.kueche_fenster',
                        'sensor.kueche_luftqualitaet'],
            'energy': ['sensor.spuelmaschine_verbrauch', 'sensor.kuehlschrank_verbrauch',
                       'sensor.kaffeemaschine_verbrauch', 'sensor.kueche_gesamt_kwh'],
        }
    },
    {
        'id': 'bath', 'name': 'Badbereich', 'icon': 'mdi-shower',
        'color': '#81c784', 'enabled': True, 'priority': 10,
        'entities': {
            'temperature': 'sensor.bad_temperatur',
            'humidity': 'sensor.bad_luftfeuchtigkeit',
            'lights': ['light.bad_decke', 'light.bad_spiegel'],
            'motion': ['binary_sensor.bad_praesenz'],
            'media': ['media_player.sonos_bad'],
            'climate': ['climate.bad_fussbodenheizung'],
            'switches': ['switch.bad_luefter', 'switch.bad_handtuchheizung'],
            'fans': ['fan.bad_abluft'],
            'sensors': ['binary_sensor.bad_fenster', 'binary_sensor.bad_wassermelder'],
        }
    },
    {
        'id': 'office', 'name': 'Buerobereich', 'icon': 'mdi-desk',
        'color': '#4dd0e1', 'enabled': True, 'priority': 8,
        'entities': {
            'temperature': 'sensor.buero_temperatur',
            'humidity': 'sensor.buero_luftfeuchtigkeit',
            'lights': ['light.buero_decke', 'light.buero_schreibtisch', 'light.buero_bildschirm_bias'],
            'motion': ['binary_sensor.buero_praesenz'],
            'media': ['media_player.sonos_buero'],
            'climate': ['climate.buero_thermostat'],
            'switches': ['switch.buero_monitor', 'switch.buero_drucker',
                         'switch.buero_steckdose_schreibtisch'],
            'sensors': ['sensor.buero_helligkeit', 'binary_sensor.buero_fenster',
                        'sensor.buero_co2'],
            'energy': ['sensor.buero_pc_verbrauch_watt', 'sensor.buero_gesamt_kwh'],
        }
    },
    {
        'id': 'hallway', 'name': 'Gangbereich', 'icon': 'mdi-door-open',
        'color': '#ce93d8', 'enabled': True, 'priority': 5,
        'entities': {
            'temperature': 'sensor.gang_temperatur',
            'lights': ['light.flur_decke', 'light.flur_garderobe', 'light.treppenhaus'],
            'motion': ['binary_sensor.flur_bewegung', 'binary_sensor.eingang_bewegung'],
            'sensors': ['binary_sensor.haustuer'],
            'locks': ['lock.haustuer_schloss'],
            'switches': ['switch.flur_steckdose'],
            'cameras': ['camera.eingang_klingel'],
        }
    },
    {
        'id': 'bedroom', 'name': 'Schlafbereich', 'icon': 'mdi-bed',
        'color': '#7986cb', 'enabled': True, 'priority': 12,
        'entities': {
            'temperature': 'sensor.schlafzimmer_temperatur',
            'humidity': 'sensor.schlafzimmer_luftfeuchtigkeit',
            'lights': ['light.schlafzimmer_decke', 'light.schlafzimmer_nachttisch_links',
                       'light.schlafzimmer_nachttisch_rechts'],
            'motion': ['binary_sensor.schlafzimmer_praesenz'],
            'media': ['media_player.sonos_schlafzimmer'],
            'climate': ['climate.schlafzimmer_thermostat'],
            'switches': ['switch.schlafzimmer_steckdose_links', 'switch.schlafzimmer_steckdose_rechts'],
            'covers': ['cover.schlafzimmer_rollladen'],
            'fans': ['fan.schlafzimmer_ventilator'],
            'sensors': ['sensor.schlafzimmer_co2'],
        }
    },
    {
        'id': 'room_mira', 'name': 'Zimmer Mira', 'icon': 'mdi-account-child',
        'color': '#f48fb1', 'enabled': True, 'priority': 20,
        'entities': {
            'temperature': 'sensor.mira_temperatur',
            'lights': ['light.mira_decke', 'light.mira_nachtlicht', 'light.mira_schreibtisch'],
            'motion': ['binary_sensor.mira_bewegung'],
            'media': ['media_player.sonos_mira'],
            'climate': ['climate.mira_thermostat'],
            'covers': ['cover.mira_rollladen'],
            'switches': ['switch.mira_steckdose'],
        }
    },
    {
        'id': 'room_paul', 'name': 'Zimmer Paul', 'icon': 'mdi-account-child',
        'color': '#90caf9', 'enabled': True, 'priority': 20,
        'entities': {
            'temperature': 'sensor.paul_temperatur',
            'lights': ['light.paul_decke', 'light.paul_nachtlicht', 'light.paul_schreibtisch'],
            'motion': ['binary_sensor.paul_bewegung'],
            'media': ['media_player.sonos_paul'],
            'climate': ['climate.paul_thermostat'],
            'covers': ['cover.paul_rollladen'],
            'switches': ['switch.paul_steckdose', 'switch.paul_gaming_pc'],
            'energy': ['sensor.paul_pc_verbrauch_watt'],
        }
    },
    {
        'id': 'terrace', 'name': 'Terrassenbereich', 'icon': 'mdi-flower',
        'color': '#a5d6a7', 'enabled': True, 'priority': 8,
        'entities': {
            'temperature': 'sensor.terrasse_temperatur',
            'lights': ['light.terrasse_aussen', 'light.terrasse_lichterkette',
                       'light.terrasse_spots'],
            'motion': ['binary_sensor.terrasse_bewegung'],
            'media': ['media_player.sonos_terrasse'],
            'sensors': ['sensor.terrasse_helligkeit', 'binary_sensor.terrasse_tuer'],
            'switches': ['switch.terrasse_markise', 'switch.terrasse_heizstrahler'],
            'covers': ['cover.terrasse_markise'],
        }
    },
    {
        'id': 'outside', 'name': 'Aussenbereich', 'icon': 'mdi-tree',
        'color': '#c5e1a5', 'enabled': True, 'priority': 5,
        'entities': {
            'temperature': 'sensor.wetter_temperatur',
            'humidity': 'sensor.wetter_luftfeuchtigkeit',
            'lights': ['light.garten_einfahrt', 'light.garten_weg', 'light.garten_terrassenrand'],
            'motion': ['binary_sensor.einfahrt_bewegung', 'binary_sensor.garten_bewegung'],
            'sensors': ['sensor.wetter_wind', 'sensor.wetter_regen_mm', 'sensor.wetter_uv_index'],
            'switches': ['switch.garagentor', 'switch.bewaesserung', 'switch.pool_pumpe'],
            'cameras': ['camera.garten_uebersicht', 'camera.einfahrt'],
            'energy': ['sensor.pv_erzeugung_watt', 'sensor.pv_einspeisung_kwh',
                       'sensor.pv_eigenverbrauch_kwh', 'sensor.hausstrom_verbrauch_watt',
                       'sensor.batterie_ladezustand_pct'],
        }
    }
]

FALLBACK_HOUSEHOLD = [
    {
        'person_id': 'person.papa', 'name': 'Papa', 'role': 'adult',
        'birthday': '1985-06-14',
        'device_trackers': ['device_tracker.papa_iphone', 'device_tracker.papa_watch'],
        'preferred_zones': ['office', 'living'],
    },
    {
        'person_id': 'person.mama', 'name': 'Mama', 'role': 'adult',
        'birthday': '1987-03-22',
        'device_trackers': ['device_tracker.mama_iphone'],
        'preferred_zones': ['kitchen', 'living'],
    },
    {
        'person_id': 'person.mira', 'name': 'Mira', 'role': 'child',
        'birthday': '2015-11-08',
        'device_trackers': ['device_tracker.mira_tablet'],
        'preferred_zones': ['room_mira', 'living'],
    },
    {
        'person_id': 'person.paul', 'name': 'Paul', 'role': 'child',
        'birthday': '2018-04-25',
        'device_trackers': ['device_tracker.paul_tablet'],
        'preferred_zones': ['room_paul', 'living'],
    },
]

FALLBACK_PLAYLISTS = [
    {'id': 'pl_morgen', 'name': 'Morgen-Energie', 'icon': 'mdi-weather-sunny',
     'zone_affinity': ['kitchen', 'bath'], 'time_affinity': 'morning'},
    {'id': 'pl_focus', 'name': 'Deep Focus', 'icon': 'mdi-head-lightbulb',
     'zone_affinity': ['office'], 'time_affinity': 'day'},
    {'id': 'pl_chill', 'name': 'Abend Chill', 'icon': 'mdi-candle',
     'zone_affinity': ['living', 'bedroom'], 'time_affinity': 'evening'},
    {'id': 'pl_kinder', 'name': 'Kinder-Hits', 'icon': 'mdi-music-note-eighth',
     'zone_affinity': ['room_mira', 'room_paul'], 'time_affinity': 'day'},
    {'id': 'pl_party', 'name': 'Gartenparty', 'icon': 'mdi-grill',
     'zone_affinity': ['terrace', 'outside'], 'time_affinity': 'day'},
    {'id': 'pl_einschlaf', 'name': 'Einschlafmusik', 'icon': 'mdi-weather-night',
     'zone_affinity': ['bedroom', 'room_mira', 'room_paul'], 'time_affinity': 'night'},
    {'id': 'pl_radio', 'name': 'SWR3 Radio', 'icon': 'mdi-radio',
     'zone_affinity': ['kitchen', 'bath'], 'time_affinity': 'morning'},
    {'id': 'pl_kochen', 'name': 'Kochen & Geniessen', 'icon': 'mdi-pot-steam',
     'zone_affinity': ['kitchen'], 'time_affinity': 'evening'},
]

FALLBACK_TODOS = [
    {'id': 'todo_001', 'title': 'Rauchmelder Batterie pruefen', 'zone_id': 'hallway',
     'priority': 'high', 'due_date': '2026-04-01', 'category': 'maintenance', 'status': 'pending'},
    {'id': 'todo_002', 'title': 'Filter Dunstabzugshaube wechseln', 'zone_id': 'kitchen',
     'priority': 'medium', 'due_date': '2026-03-20', 'category': 'maintenance', 'status': 'pending'},
    {'id': 'todo_003', 'title': 'Rollladen Service', 'zone_id': 'living',
     'priority': 'low', 'due_date': '2026-06-15', 'category': 'maintenance', 'status': 'pending'},
    {'id': 'todo_004', 'title': 'Garten winterfest machen', 'zone_id': 'outside',
     'priority': 'medium', 'due_date': '2026-10-30', 'category': 'seasonal', 'status': 'pending'},
    {'id': 'todo_006', 'title': 'Terrasse Lichterkette reparieren', 'zone_id': 'terrace',
     'priority': 'medium', 'due_date': '2026-04-15', 'category': 'maintenance', 'status': 'pending'},
    {'id': 'todo_007', 'title': 'Kinderzimmer aufraeumen (Mira)', 'zone_id': 'room_mira',
     'priority': 'medium', 'due_date': '2026-03-15', 'category': 'household', 'status': 'pending'},
    {'id': 'todo_008', 'title': 'PV-Anlage Reinigung', 'zone_id': 'outside',
     'priority': 'low', 'due_date': '2026-05-01', 'category': 'maintenance', 'status': 'pending'},
]

FALLBACK_NOTIFICATIONS = [
    {'id': 'n001', 'title': 'Fenster offen bei Regen', 'zone_id': 'kitchen',
     'severity': 'warning', 'acknowledged': False},
    {'id': 'n002', 'title': 'Heizung Eco-Modus', 'zone_id': 'bedroom',
     'severity': 'info', 'acknowledged': True},
    {'id': 'n003', 'title': 'Wassermelder Bad', 'zone_id': 'bath',
     'severity': 'critical', 'acknowledged': False},
    {'id': 'n004', 'title': 'PV-Ueberschuss', 'zone_id': 'outside',
     'severity': 'info', 'acknowledged': False},
    {'id': 'n006', 'title': 'CO2-Warnung Buero', 'zone_id': 'office',
     'severity': 'warning', 'acknowledged': False},
]


# ═══════════════════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════════════════

def _get_zones_config():
    """Get current zones config (cached fetch from Core)."""
    return _fetch_zones_config()


def _get_zone_by_id():
    """Build zone lookup map from current config."""
    return {z['id']: z for z in _get_zones_config()}


def _get_zone_playlists(zone_id):
    """Playlists fuer eine Zone."""
    return _fetch_playlists(zone_id=zone_id)


def _get_zone_todos(zone_id):
    """Offene Todos fuer eine Zone."""
    return _fetch_todos(zone_id=zone_id)


def _get_zone_notifications(zone_id):
    """Aktive Notifications fuer eine Zone."""
    return _fetch_notifications(zone_id=zone_id)


def _get_upcoming_birthdays():
    """Geburtstage in den naechsten 30 Tagen."""
    # Try Core haushalt API first
    data = _core_get('/api/v1/haushalt/overview')
    if data and isinstance(data, dict):
        # Core returns upcoming birthdays directly
        upcoming = data.get('upcoming_birthdays_7d', [])
        if upcoming:
            return upcoming
        # Also check birthday_today
        today_bdays = data.get('birthday_today', [])
        if today_bdays:
            return today_bdays

    # Try birthday status API
    data = _core_get('/api/v1/birthday/status')
    if data and isinstance(data, dict):
        upcoming = data.get('upcoming', data.get('birthdays', []))
        if upcoming:
            return upcoming

    # Fallback: compute from FALLBACK_HOUSEHOLD
    today = date.today()
    upcoming = []
    household = _fetch_household()
    if isinstance(household, list):
        for person in household:
            bday_str = person.get('birthday', '')
            if not bday_str:
                continue
            try:
                bday = date.fromisoformat(bday_str)
            except (ValueError, TypeError):
                continue
            next_bday = bday.replace(year=today.year)
            if next_bday < today:
                next_bday = next_bday.replace(year=today.year + 1)
            days_until = (next_bday - today).days
            if days_until <= 30:
                upcoming.append({
                    'name': person.get('name', ''),
                    'date': next_bday.isoformat(),
                    'days_until': days_until,
                    'age': next_bday.year - bday.year,
                })
    return sorted(upcoming, key=lambda x: x['days_until'])


def _count_entities(entities):
    """Entity-Counts nach Kategorie."""
    counts = {}
    for role, items in entities.items():
        if isinstance(items, list):
            counts[role] = len(items)
        elif isinstance(items, str):
            counts[role] = 1
    return counts


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@dashboard_bp.route('/config', methods=['GET'])
def get_dashboard_config():
    """Dashboard-Konfiguration mit Habituszonen-Metadaten."""
    zones_config = _get_zones_config()
    household = _fetch_household()

    config = {
        'version': '13.0.4',
        'zones': zones_config,
        'theme_support': ['light', 'dark'],
        'features': {
            'tabs': True,
            'websocket': True,
            'alerts': True,
            'responsive': True,
            'modules': True,
            'controls': True,
            'playlists': True,
            'notifications': True,
            'todos': True,
            'birthdays': True,
            'energy': True,
            'cameras': True,
        },
        'layout': {
            'tab_height': 56,
            'header_height': 64,
            'footer_height': 48
        },
        'household': household if isinstance(household, list) else FALLBACK_HOUSEHOLD,
        'data_source': 'core_api' if zones_config is not FALLBACK_ZONES_CONFIG else 'fallback',
    }
    return jsonify(config)


@dashboard_bp.route('/zones', methods=['GET'])
def get_zones():
    """Alle Habituszonen mit Live-Daten, Playlists, Todos, Notifications."""
    zones_config = _get_zones_config()
    zones = []

    with zone_lock:
        for zone_config in zones_config:
            zone_id = zone_config['id']

            # Try Core live data first, then local store
            live_data = _fetch_zone_live_data(zone_id)
            zone_data = live_data if live_data else zone_data_store.get(zone_id, {})

            # Update local store with live data
            if live_data:
                zone_data_store[zone_id] = {
                    **zone_data_store.get(zone_id, {}),
                    **live_data,
                }

            playlists = _get_zone_playlists(zone_id)
            todos = _get_zone_todos(zone_id)
            notifications = _get_zone_notifications(zone_id)

            zones.append({
                'id': zone_id,
                'name': zone_config['name'],
                'icon': zone_config['icon'],
                'color': zone_config.get('color', '#888'),
                'enabled': zone_config.get('enabled', True),
                'priority': zone_config.get('priority', 10),
                'entity_counts': _count_entities(zone_config.get('entities', {})),
                'data': zone_data,
                'alert_count': zone_data.get('alert_count', 0),
                'playlist_count': len(playlists),
                'todo_count': len(todos),
                'notification_count': len(notifications),
                'last_update': zone_data.get('last_update')
            })

    return jsonify({
        'zones': zones,
        'total': len(zones),
        'active_alerts': sum(z['alert_count'] for z in zones),
        'total_notifications': sum(z['notification_count'] for z in zones),
        'total_todos': sum(z['todo_count'] for z in zones),
        'upcoming_birthdays': _get_upcoming_birthdays(),
    })


@dashboard_bp.route('/zones/<zone_id>', methods=['GET'])
def get_zone(zone_id):
    """Daten einer spezifischen Habituszone mit allen Modulen."""
    zone_by_id = _get_zone_by_id()
    zone_config = zone_by_id.get(zone_id)

    if not zone_config:
        return jsonify({'error': 'Zone not found'}), 404

    # Try live data from Core
    live_data = _fetch_zone_live_data(zone_id)

    with zone_lock:
        zone_data = live_data if live_data else zone_data_store.get(zone_id, {})
        if live_data:
            zone_data_store[zone_id] = {
                **zone_data_store.get(zone_id, {}),
                **live_data,
            }

    return jsonify({
        'id': zone_id,
        'name': zone_config['name'],
        'icon': zone_config['icon'],
        'color': zone_config.get('color', '#888'),
        'enabled': zone_config.get('enabled', True),
        'priority': zone_config.get('priority', 10),
        'entities': zone_config.get('entities', {}),
        'entity_counts': _count_entities(zone_config.get('entities', {})),
        'data': zone_data,
        'playlists': _get_zone_playlists(zone_id),
        'todos': _get_zone_todos(zone_id),
        'notifications': _get_zone_notifications(zone_id),
        'alert_count': zone_data.get('alert_count', 0),
        'last_update': zone_data.get('last_update')
    })


# ── Zone-Editor CRUD Proxy (forwards to Core zone-editor API) ──────────────

@dashboard_bp.route('/zone-editor/zones', methods=['POST'])
def create_zone():
    """Create a new zone via Core zone-editor API."""
    payload = request.get_json() or {}
    result = _core_post('/api/v1/zone-editor/zones', payload)
    if result is None:
        return jsonify({'error': 'Core not reachable or zone creation failed'}), 502
    _invalidate_cache('/api/v1/zone-editor/zones')
    return jsonify(result), 201


@dashboard_bp.route('/zone-editor/zones/<zone_id>', methods=['PUT', 'PATCH'])
def update_zone(zone_id):
    """Update an existing zone via Core zone-editor API."""
    payload = request.get_json() or {}
    result = _core_put(f'/api/v1/zone-editor/zones/{zone_id}', payload)
    if result is None:
        return jsonify({'error': 'Core not reachable or zone update failed'}), 502
    _invalidate_cache('/api/v1/zone-editor/zones')
    return jsonify(result)


@dashboard_bp.route('/zone-editor/zones/<zone_id>', methods=['DELETE'])
def delete_zone(zone_id):
    """Delete a zone via Core zone-editor API."""
    result = _core_delete(f'/api/v1/zone-editor/zones/{zone_id}')
    if result is None:
        return jsonify({'error': 'Core not reachable or zone deletion failed'}), 502
    _invalidate_cache('/api/v1/zone-editor/zones')
    return jsonify(result)


@dashboard_bp.route('/zone-editor/zones/<zone_id>/rooms', methods=['POST'])
def add_room_to_zone(zone_id):
    """Add a room to a zone via Core zone-editor API."""
    payload = request.get_json() or {}
    result = _core_post(f'/api/v1/zone-editor/zones/{zone_id}/rooms', payload)
    if result is None:
        return jsonify({'error': 'Core not reachable or room creation failed'}), 502
    _invalidate_cache('/api/v1/zone-editor/zones')
    return jsonify(result), 201


@dashboard_bp.route('/zone-editor/zones/<zone_id>/rooms/<room_id>', methods=['DELETE'])
def remove_room_from_zone(zone_id, room_id):
    """Remove a room from a zone via Core zone-editor API."""
    result = _core_delete(f'/api/v1/zone-editor/zones/{zone_id}/rooms/{room_id}')
    if result is None:
        return jsonify({'error': 'Core not reachable or room removal failed'}), 502
    _invalidate_cache('/api/v1/zone-editor/zones')
    return jsonify(result)


@dashboard_bp.route('/zone-editor/rooms', methods=['GET'])
def list_rooms():
    """List all rooms via Core zone-editor API."""
    result = _core_get('/api/v1/zone-editor/rooms')
    if result is None:
        return jsonify({'error': 'Core not reachable'}), 502
    return jsonify(result)


@dashboard_bp.route('/zone-editor/templates', methods=['GET'])
def list_templates():
    """List available zone templates via Core zone-editor API."""
    result = _core_get('/api/v1/zone-editor/templates')
    if result is None:
        return jsonify({'error': 'Core not reachable'}), 502
    return jsonify(result)


@dashboard_bp.route('/zones/<zone_id>/data', methods=['PUT'])
def update_zone_data(zone_id):
    """Daten einer Habituszone aktualisieren (fuer HA-Integration)."""
    zone_by_id = _get_zone_by_id()
    zone_config = zone_by_id.get(zone_id)

    if not zone_config:
        return jsonify({'error': 'Zone not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    with zone_lock:
        zone_data_store[zone_id] = {
            **zone_data_store.get(zone_id, {}),
            **data,
            'last_update': datetime.now(timezone.utc).isoformat()
        }

    # Invalidate cache so next GET picks up fresh data
    _invalidate_cache()

    # WebSocket-Benachrichtigung ausloesen
    if hasattr(current_app, 'socketio'):
        current_app.socketio.emit('zone_update', {
            'zoneId': zone_id,
            'data': zone_data_store[zone_id]
        })

    return jsonify({
        'success': True,
        'zone_id': zone_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@dashboard_bp.route('/zones/<zone_id>/alerts', methods=['GET'])
def get_zone_alerts(zone_id):
    """Alerts einer spezifischen Zone."""
    zone_by_id = _get_zone_by_id()
    zone_config = zone_by_id.get(zone_id)

    if not zone_config:
        return jsonify({'error': 'Zone not found'}), 404

    with zone_lock:
        zone_data = zone_data_store.get(zone_id, {})

    alerts = zone_data.get('alerts', [])

    return jsonify({
        'zone_id': zone_id,
        'zone_name': zone_config['name'],
        'alert_count': len(alerts),
        'alerts': alerts
    })


@dashboard_bp.route('/zones/<zone_id>/alerts', methods=['POST'])
def add_zone_alert(zone_id):
    """Neuer Alert fuer eine Zone."""
    zone_by_id = _get_zone_by_id()
    zone_config = zone_by_id.get(zone_id)

    if not zone_config:
        return jsonify({'error': 'Zone not found'}), 404

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message required'}), 400

    alert = {
        'id': f'alert_{zone_id}_{int(time.time())}',
        'message': data['message'],
        'severity': data.get('severity', 'info'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'acknowledged': False
    }

    # Try to forward to Core notifications API
    _core_post_alert(zone_id, alert)

    with zone_lock:
        if zone_id not in zone_data_store:
            zone_data_store[zone_id] = {}

        if 'alerts' not in zone_data_store[zone_id]:
            zone_data_store[zone_id]['alerts'] = []

        zone_data_store[zone_id]['alerts'].append(alert)
        zone_data_store[zone_id]['alert_count'] = len(zone_data_store[zone_id]['alerts'])
        zone_data_store[zone_id]['last_update'] = datetime.now(timezone.utc).isoformat()

    # WebSocket-Benachrichtigung
    if hasattr(current_app, 'socketio'):
        current_app.socketio.emit('alert_update', {
            'zoneId': zone_id,
            'alertCount': zone_data_store[zone_id]['alert_count'],
            'alert': alert
        })

    return jsonify({
        'success': True,
        'alert': alert,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


def _core_post_alert(zone_id, alert):
    """Forward alert to Core notifications API."""
    base_url = _get_core_url()
    try:
        requests.post(
            f"{base_url}/notifications",
            json={
                'title': alert.get('message', ''),
                'message': alert.get('message', ''),
                'priority': alert.get('severity', 'info'),
                'zone_id': zone_id,
            },
            headers=_get_core_headers(),
            timeout=3,
        )
    except Exception:
        pass  # Best-effort forwarding


@dashboard_bp.route('/zones/<zone_id>/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(zone_id, alert_id):
    """Alert bestaetigen."""
    zone_by_id = _get_zone_by_id()
    zone_config = zone_by_id.get(zone_id)

    if not zone_config:
        return jsonify({'error': 'Zone not found'}), 404

    # Try to mark as read in Core
    base_url = _get_core_url()
    try:
        requests.post(
            f"{base_url}/notifications/{alert_id}/read",
            headers=_get_core_headers(),
            timeout=3,
        )
    except Exception as exc:
        _LOGGER.debug("Failed to forward alert ack to Core: %s", exc)

    with zone_lock:
        zone_data = zone_data_store.get(zone_id, {})
        alerts = zone_data.get('alerts', [])

        for alert in alerts:
            if alert.get('id') == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now(timezone.utc).isoformat()
                break

        # Bestaetigte Alerts entfernen
        zone_data['alerts'] = [a for a in alerts if not a.get('acknowledged', False)]
        zone_data['alert_count'] = len(zone_data['alerts'])
        zone_data_store[zone_id] = zone_data

    return jsonify({
        'success': True,
        'zone_id': zone_id,
        'alert_id': alert_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Dashboard-Statistiken."""
    zones_config = _get_zones_config()
    todos = _fetch_todos()
    notifications = _fetch_notifications()

    with zone_lock:
        total_zones = len(zones_config)
        enabled_zones = sum(1 for z in zones_config if z.get('enabled', True))
        total_alerts = sum(
            zone_data_store.get(z['id'], {}).get('alert_count', 0)
            for z in zones_config
        )

        zones_with_data = sum(
            1 for z in zones_config
            if zone_data_store.get(z['id'], {}).get('last_update')
        )

    total_entities = sum(
        sum(len(v) if isinstance(v, list) else 1
            for v in z.get('entities', {}).values())
        for z in zones_config
    )

    household = _fetch_household()
    household_count = len(household) if isinstance(household, list) else 0

    total_todos = sum(1 for t in todos if t.get('status') != 'completed')
    total_notifications = sum(1 for n in notifications if not n.get('acknowledged'))

    return jsonify({
        'total_zones': total_zones,
        'enabled_zones': enabled_zones,
        'zones_with_data': zones_with_data,
        'total_alerts': total_alerts,
        'total_entities': total_entities,
        'total_todos': total_todos,
        'total_notifications': total_notifications,
        'household_members': household_count,
        'upcoming_birthdays': _get_upcoming_birthdays(),
        'last_update': datetime.now(timezone.utc).isoformat()
    })


@dashboard_bp.route('/household', methods=['GET'])
def get_household():
    """Haushaltsmitglieder und Geburtstage."""
    household = _fetch_household()
    if isinstance(household, list):
        return jsonify({
            'household': household,
            'upcoming_birthdays': _get_upcoming_birthdays(),
            'total_members': len(household),
        })
    # If household is a dict (from haushalt/overview), return it enriched
    result = household if isinstance(household, dict) else {}
    result['upcoming_birthdays'] = _get_upcoming_birthdays()
    return jsonify(result)


@dashboard_bp.route('/playlists', methods=['GET'])
def get_playlists():
    """Alle Playlists, optional gefiltert nach Zone."""
    zone_id = request.args.get('zone_id')
    result = _fetch_playlists(zone_id=zone_id)
    return jsonify({'playlists': result, 'total': len(result)})


@dashboard_bp.route('/todos', methods=['GET'])
def get_todos():
    """Alle Todos, optional gefiltert nach Zone."""
    zone_id = request.args.get('zone_id')
    status = request.args.get('status', 'pending')
    result = _fetch_todos(zone_id=zone_id)
    if status:
        result = [t for t in result if t.get('status') == status]
    return jsonify({'todos': result, 'total': len(result)})


@dashboard_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Alle Notifications, optional gefiltert nach Zone."""
    zone_id = request.args.get('zone_id')
    result = _fetch_notifications(zone_id=zone_id)
    return jsonify({'notifications': result, 'total': len(result)})


@dashboard_bp.route('/theme', methods=['GET', 'PUT'])
def theme_management():
    """Theme-Einstellungen verwalten."""
    if request.method == 'GET':
        return jsonify({
            'themes': ['light', 'dark'],
            'default': 'light',
            'auto_detect': True
        })

    elif request.method == 'PUT':
        data = request.get_json()
        theme = data.get('theme')

        if theme not in ['light', 'dark']:
            return jsonify({'error': 'Invalid theme'}), 400

        return jsonify({
            'success': True,
            'theme': theme,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })


def initialize_zone_data():
    """
    Initialize zone data by fetching live data from Core API.
    Falls back to basic defaults if Core is unavailable.
    """
    zones_config = FALLBACK_ZONES_CONFIG  # Use fallback at init (no app context yet)

    for zone in zones_config:
        zone_id = zone['id']
        entities = zone.get('entities', {})
        light_count = len(entities.get('lights', []))
        switch_count = len(entities.get('switches', []))

        # Set basic structure; live data will be fetched on first request
        zone_data_store[zone_id] = {
            'lights': light_count,
            'switches': switch_count,
            'alert_count': 0,
            'alerts': [],
            'last_update': datetime.now(timezone.utc).isoformat()
        }


def refresh_zone_data_from_core():
    """
    Background refresh: fetch live data from Core for all zones.
    Called periodically or on demand.
    """
    zones_config = _fetch_zones_config()
    for zone in zones_config:
        zone_id = zone['id']
        live_data = _fetch_zone_live_data(zone_id)
        if live_data:
            with zone_lock:
                zone_data_store[zone_id] = {
                    **zone_data_store.get(zone_id, {}),
                    **live_data,
                }


# Initiale Grundstruktur beim Modul-Import
initialize_zone_data()
