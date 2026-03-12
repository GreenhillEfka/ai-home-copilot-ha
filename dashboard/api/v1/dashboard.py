"""
PilotSuite Styx Dashboard API v1
Zonenzentriertes Dashboard mit Habituszonen-Endpoints.

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

dashboard_bp = Blueprint('dashboard_v1', __name__, url_prefix='/api/v1/dashboard')

# In-Memory Storage fuer Zone-Daten (wird durch HA-Integration ersetzt)
zone_data_store = {}
zone_lock = threading.Lock()

# ═══════════════════════════════════════════════════════════════════════════
# Standard-Konfiguration fuer Habituszonen (synchron mit Core Zone-IDs)
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_ZONES_CONFIG = [
    {
        'id': 'living',
        'name': 'Wohnbereich',
        'icon': 'mdi-sofa',
        'color': '#4fc3f7',
        'enabled': True,
        'priority': 10,
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
        'id': 'kitchen',
        'name': 'Kochbereich',
        'icon': 'mdi-stove',
        'color': '#ffb74d',
        'enabled': True,
        'priority': 10,
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
        'id': 'bath',
        'name': 'Badbereich',
        'icon': 'mdi-shower',
        'color': '#81c784',
        'enabled': True,
        'priority': 10,
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
        'id': 'office',
        'name': 'Buerobereich',
        'icon': 'mdi-desk',
        'color': '#4dd0e1',
        'enabled': True,
        'priority': 8,
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
        'id': 'hallway',
        'name': 'Gangbereich',
        'icon': 'mdi-door-open',
        'color': '#ce93d8',
        'enabled': True,
        'priority': 5,
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
        'id': 'bedroom',
        'name': 'Schlafbereich',
        'icon': 'mdi-bed',
        'color': '#7986cb',
        'enabled': True,
        'priority': 12,
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
        'id': 'room_mira',
        'name': 'Zimmer Mira',
        'icon': 'mdi-account-child',
        'color': '#f48fb1',
        'enabled': True,
        'priority': 20,
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
        'id': 'room_paul',
        'name': 'Zimmer Paul',
        'icon': 'mdi-account-child',
        'color': '#90caf9',
        'enabled': True,
        'priority': 20,
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
        'id': 'terrace',
        'name': 'Terrassenbereich',
        'icon': 'mdi-flower',
        'color': '#a5d6a7',
        'enabled': True,
        'priority': 8,
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
        'id': 'outside',
        'name': 'Aussenbereich',
        'icon': 'mdi-tree',
        'color': '#c5e1a5',
        'enabled': True,
        'priority': 5,
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

# ═══════════════════════════════════════════════════════════════════════════
# Haushalt / Personen / Geburtstage
# ═══════════════════════════════════════════════════════════════════════════

HOUSEHOLD = [
    {
        'person_id': 'person.papa',
        'name': 'Papa',
        'role': 'adult',
        'birthday': '1985-06-14',
        'device_trackers': ['device_tracker.papa_iphone', 'device_tracker.papa_watch'],
        'preferred_zones': ['office', 'living'],
    },
    {
        'person_id': 'person.mama',
        'name': 'Mama',
        'role': 'adult',
        'birthday': '1987-03-22',
        'device_trackers': ['device_tracker.mama_iphone'],
        'preferred_zones': ['kitchen', 'living'],
    },
    {
        'person_id': 'person.mira',
        'name': 'Mira',
        'role': 'child',
        'birthday': '2015-11-08',
        'device_trackers': ['device_tracker.mira_tablet'],
        'preferred_zones': ['room_mira', 'living'],
    },
    {
        'person_id': 'person.paul',
        'name': 'Paul',
        'role': 'child',
        'birthday': '2018-04-25',
        'device_trackers': ['device_tracker.paul_tablet'],
        'preferred_zones': ['room_paul', 'living'],
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# Playlists / Sonos-Favoriten
# ═══════════════════════════════════════════════════════════════════════════

PLAYLISTS = [
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

# ═══════════════════════════════════════════════════════════════════════════
# Todos
# ═══════════════════════════════════════════════════════════════════════════

TODOS = [
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

# ═══════════════════════════════════════════════════════════════════════════
# Notifications
# ═══════════════════════════════════════════════════════════════════════════

NOTIFICATIONS = [
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


# Lookup-Map fuer schnellen Zugriff
_ZONE_BY_ID = {z['id']: z for z in DEFAULT_ZONES_CONFIG}


def _get_zone_playlists(zone_id):
    """Playlists fuer eine Zone."""
    return [p for p in PLAYLISTS if zone_id in p.get('zone_affinity', [])]


def _get_zone_todos(zone_id):
    """Offene Todos fuer eine Zone."""
    return [t for t in TODOS if t.get('zone_id') == zone_id and t.get('status') != 'completed']


def _get_zone_notifications(zone_id):
    """Aktive Notifications fuer eine Zone."""
    return [n for n in NOTIFICATIONS if n.get('zone_id') == zone_id and not n.get('acknowledged')]


def _get_upcoming_birthdays():
    """Geburtstage in den naechsten 30 Tagen."""
    today = date.today()
    upcoming = []
    for person in HOUSEHOLD:
        bday_str = person.get('birthday', '')
        if not bday_str:
            continue
        bday = date.fromisoformat(bday_str)
        next_bday = bday.replace(year=today.year)
        if next_bday < today:
            next_bday = next_bday.replace(year=today.year + 1)
        days_until = (next_bday - today).days
        if days_until <= 30:
            upcoming.append({
                'name': person['name'],
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
    config = {
        'version': '13.0.4',
        'zones': DEFAULT_ZONES_CONFIG,
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
        'household': HOUSEHOLD,
    }
    return jsonify(config)


@dashboard_bp.route('/zones', methods=['GET'])
def get_zones():
    """Alle Habituszonen mit Live-Daten, Playlists, Todos, Notifications."""
    zones = []
    with zone_lock:
        for zone_config in DEFAULT_ZONES_CONFIG:
            zone_id = zone_config['id']
            zone_data = zone_data_store.get(zone_id, {})
            playlists = _get_zone_playlists(zone_id)
            todos = _get_zone_todos(zone_id)
            notifications = _get_zone_notifications(zone_id)

            zones.append({
                'id': zone_id,
                'name': zone_config['name'],
                'icon': zone_config['icon'],
                'color': zone_config.get('color', '#888'),
                'enabled': zone_config['enabled'],
                'priority': zone_config['priority'],
                'entity_counts': _count_entities(zone_config['entities']),
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
    zone_config = _ZONE_BY_ID.get(zone_id)

    if not zone_config:
        return jsonify({'error': 'Zone not found'}), 404

    with zone_lock:
        zone_data = zone_data_store.get(zone_id, {})

    return jsonify({
        'id': zone_id,
        'name': zone_config['name'],
        'icon': zone_config['icon'],
        'color': zone_config.get('color', '#888'),
        'enabled': zone_config['enabled'],
        'priority': zone_config['priority'],
        'entities': zone_config['entities'],
        'entity_counts': _count_entities(zone_config['entities']),
        'data': zone_data,
        'playlists': _get_zone_playlists(zone_id),
        'todos': _get_zone_todos(zone_id),
        'notifications': _get_zone_notifications(zone_id),
        'alert_count': zone_data.get('alert_count', 0),
        'last_update': zone_data.get('last_update')
    })


@dashboard_bp.route('/zones/<zone_id>/data', methods=['PUT'])
def update_zone_data(zone_id):
    """Daten einer Habituszone aktualisieren (fuer HA-Integration)."""
    zone_config = _ZONE_BY_ID.get(zone_id)

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
    zone_config = _ZONE_BY_ID.get(zone_id)

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
    zone_config = _ZONE_BY_ID.get(zone_id)

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


@dashboard_bp.route('/zones/<zone_id>/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(zone_id, alert_id):
    """Alert bestaetigen."""
    zone_config = _ZONE_BY_ID.get(zone_id)

    if not zone_config:
        return jsonify({'error': 'Zone not found'}), 404

    with zone_lock:
        zone_data = zone_data_store.get(zone_id, {})
        alerts = zone_data.get('alerts', [])

        for alert in alerts:
            if alert['id'] == alert_id:
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
    with zone_lock:
        total_zones = len(DEFAULT_ZONES_CONFIG)
        enabled_zones = sum(1 for z in DEFAULT_ZONES_CONFIG if z['enabled'])
        total_alerts = sum(
            zone_data_store.get(z['id'], {}).get('alert_count', 0)
            for z in DEFAULT_ZONES_CONFIG
        )

        zones_with_data = sum(
            1 for z in DEFAULT_ZONES_CONFIG
            if zone_data_store.get(z['id'], {}).get('last_update')
        )

    total_entities = sum(
        sum(len(v) if isinstance(v, list) else 1
            for v in z['entities'].values())
        for z in DEFAULT_ZONES_CONFIG
    )

    total_todos = sum(1 for t in TODOS if t.get('status') != 'completed')
    total_notifications = sum(1 for n in NOTIFICATIONS if not n.get('acknowledged'))

    return jsonify({
        'total_zones': total_zones,
        'enabled_zones': enabled_zones,
        'zones_with_data': zones_with_data,
        'total_alerts': total_alerts,
        'total_entities': total_entities,
        'total_todos': total_todos,
        'total_notifications': total_notifications,
        'household_members': len(HOUSEHOLD),
        'upcoming_birthdays': _get_upcoming_birthdays(),
        'last_update': datetime.now(timezone.utc).isoformat()
    })


@dashboard_bp.route('/household', methods=['GET'])
def get_household():
    """Haushaltsmitglieder und Geburtstage."""
    return jsonify({
        'household': HOUSEHOLD,
        'upcoming_birthdays': _get_upcoming_birthdays(),
        'total_members': len(HOUSEHOLD),
    })


@dashboard_bp.route('/playlists', methods=['GET'])
def get_playlists():
    """Alle Playlists, optional gefiltert nach Zone."""
    zone_id = request.args.get('zone_id')
    if zone_id:
        result = _get_zone_playlists(zone_id)
    else:
        result = PLAYLISTS
    return jsonify({'playlists': result, 'total': len(result)})


@dashboard_bp.route('/todos', methods=['GET'])
def get_todos():
    """Alle Todos, optional gefiltert nach Zone."""
    zone_id = request.args.get('zone_id')
    status = request.args.get('status', 'pending')
    result = TODOS
    if zone_id:
        result = [t for t in result if t.get('zone_id') == zone_id]
    if status:
        result = [t for t in result if t.get('status') == status]
    return jsonify({'todos': result, 'total': len(result)})


@dashboard_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Alle Notifications, optional gefiltert nach Zone."""
    zone_id = request.args.get('zone_id')
    result = NOTIFICATIONS
    if zone_id:
        result = [n for n in result if n.get('zone_id') == zone_id]
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
    """Initiale Zonendaten setzen (fuer Demo-Zwecke)."""
    for zone in DEFAULT_ZONES_CONFIG:
        entities = zone['entities']
        light_count = len(entities.get('lights', []))
        switch_count = len(entities.get('switches', []))
        zone_data_store[zone['id']] = {
            'temperature': 21.5,
            'humidity': 45,
            'lights': light_count,
            'switches': switch_count,
            'brightness': 60,
            'alert_count': 0,
            'alerts': [],
            'last_update': datetime.now(timezone.utc).isoformat()
        }


# Initiale Daten beim Modul-Import
initialize_zone_data()
