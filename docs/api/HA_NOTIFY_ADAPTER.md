# HomeAssistant Notify Adapter Documentation

**Version:** 1.0  
**Module:** `copilot_core.notifications.ha_notify_adapter`  
**Integration:** HomeAssistant Core

---

## Overview

The HANotifyAdapter provides seamless integration between PilotSuite and HomeAssistant's notification services. It enables unified notification delivery across multiple platforms through HA's `notify.*` entities.

### Supported Services

| Service Type | Entity Pattern | Use Case |
|--------------|----------------|----------|
| Mobile App | `notify.mobile_app_*` | iOS/Android Companion Apps |
| Telegram | `notify.telegram` | Telegram Bot Messages |
| WhatsApp | `notify.whatsapp` | WhatsApp Messages |
| Pushover | `notify.pushover` | Pushover Push Notifications |
| Email | `notify.email` | Email Notifications |
| Signal | `notify.signal` | Signal Messenger |
| Slack | `notify.slack` | Slack Workspace |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PilotSuite Core                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              HANotifyAdapter                        │    │
│  │  - Device Registration                              │    │
│  │  - Priority Mapping                                 │    │
│  │  - Category Mapping                                 │    │
│  │  - Payload Construction                             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 HomeAssistant Core                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              notify.* Services                      │    │
│  │  - notify.mobile_app_iphone                         │    │
│  │  - notify.mobile_app_android                        │    │
│  │  - notify.telegram                                  │    │
│  │  - notify.whatsapp                                  │    │
│  │  - notify.pushover                                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Services                          │
│  [Apple Push] [FCM] [Telegram API] [WhatsApp] [Pushover]   │
└─────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Class: `HANotifyAdapter`

#### Constructor

```python
def __init__(self, hass: HomeAssistant | None = None) -> None
```

**Parameters:**
- `hass`: Optional HomeAssistant instance (can be set later via `set_hass()`)

**Example:**
```python
from copilot_core.notifications.ha_notify_adapter import HANotifyAdapter

# With HA instance
adapter = HANotifyAdapter(hass)

# Without HA instance (set later)
adapter = HANotifyAdapter()
adapter.set_hass(hass)
```

---

#### Method: `set_hass()`

Set HomeAssistant instance for service calls.

```python
def set_hass(self, hass: HomeAssistant) -> None
```

**Example:**
```python
adapter = HANotifyAdapter()
adapter.set_hass(hass)
```

---

#### Method: `register_ha_device()`

Register a notification device for a user.

```python
def register_ha_device(
    self,
    user_id: str,
    ha_entity_id: str,
    device_name: str = None,
    device_type: str = "mobile"
) -> HADevice
```

**Parameters:**
- `user_id`: Unique user identifier
- `ha_entity_id`: HA notify entity (e.g., `notify.mobile_app_iphone`)
- `device_name`: Optional friendly device name
- `device_type`: Device type (`mobile`, `telegram`, `whatsapp`, etc.)

**Returns:** `HADevice` object

**Example:**
```python
device = adapter.register_ha_device(
    user_id="user_123",
    ha_entity_id="notify.mobile_app_iphone",
    device_name="John's iPhone",
    device_type="mobile"
)
print(f"Registered device: {device.id}")
```

---

#### Method: `send_to_ha_service()`

Send notification to a registered HA notify service.

```python
def send_to_ha_service(
    self,
    device_id: str,
    title: str,
    message: str,
    priority: str = "normal",
    category: str = None,
    data: dict = None
) -> bool
```

**Parameters:**
- `device_id`: Registered device ID or HA entity ID
- `title`: Notification title
- `message`: Notification message body
- `priority`: Priority level (`low`, `normal`, `high`, `urgent`)
- `category`: Notification category (`mood_change`, `alert`, `suggestion`, `system`)
- `data`: Optional additional payload data

**Returns:** `bool` (True if successful)

**Example:**
```python
success = adapter.send_to_ha_service(
    device_id="device_abc123",
    title="Mood Change Detected",
    message="Living room mood changed to 'Relaxing Evening'",
    priority="normal",
    category="mood_change"
)
```

---



---

#### Method: `get_ha_devices()`

Get all registered devices for a user.

```python
def get_ha_devices(self, user_id: str) -> list[HADevice]
```

**Example:**
```python
devices = adapter.get_ha_devices("user_123")
for device in devices:
    print(f"{device.device_name}: {device.ha_entity_id}")
```

---

#### Method: `unregister_ha_device()`

Remove a registered device.

```python
def unregister_ha_device(self, device_id: str) -> bool
```

**Example:**
```python
removed = adapter.unregister_ha_device("device_abc123")
```

---

#### Method: `test_ha_connection()`

Test connection to HomeAssistant and notify services.

```python
def test_ha_connection(self) -> dict
```

**Returns:**
```python
{
    "success": True,
    "hass_connected": True,
    "notify_services_available": True,
    "services_count": 3,
    "services": ["mobile_app_iphone", "telegram", "whatsapp"],
    "error": None
}
```

---

## Priority Mapping

PilotSuite priority levels are mapped to HomeAssistant payload:

| PilotSuite | HA Priority | HA Urgency | Use Case |
|------------|-------------|------------|----------|
| `low` | 0 | `low` | Background updates |
| `normal` | 1 | `normal` | Standard notifications |
| `high` | 2 | `high` | Important alerts |
| `urgent` | 3 | `emergency` | Critical warnings |
| `CRITICAL` | 3 | `emergency` | System emergencies |

**Example:**
```python
# High priority notification
adapter.send_to_ha_service(
    device_id="device_123",
    title="Motion Detected",
    message="Front door motion detected at 2:00 AM",
    priority="high"  # Maps to priority=2, urgency=high
)
```

---

## Category Mapping

Categories help mobile apps group and display notifications:

| Category | HA Category | Mobile App Behavior |
|----------|-------------|---------------------|
| `mood_change` | `mood` | Grouped under mood updates |
| `alert` | `alert` | Immediate display with sound |
| `suggestion` | `suggestion` | Actionable suggestions |
| `system` | `system` | System status updates |
| `info` | `info` | Informational messages |
| `warning` | `warning` | Warning indicators |
| `error` | `error` | Error notifications |

---

## Data Class: `HADevice`

Represents a registered notification device.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique device identifier (auto-generated) |
| `user_id` | str | Associated user ID |
| `ha_entity_id` | str | HA notify entity ID |
| `device_name` | str | Friendly device name |
| `device_type` | str | Type: `mobile`, `telegram`, `whatsapp`, etc. |
| `enabled` | bool | Device enabled status |
| `created_at` | str | ISO timestamp of registration |
| `last_used` | str | ISO timestamp of last notification |

### Methods

#### `to_dict()`

Convert device to dictionary representation.

```python
device_dict = device.to_dict()
# Returns:
# {
#   "id": "1709283600.123",
#   "user_id": "user_123",
#   "ha_entity_id": "notify.mobile_app_iphone",
#   "device_name": "John's iPhone",
#   "device_type": "mobile",
#   "enabled": True,
#   "created_at": "2026-03-01T09:00:00+00:00",
#   "last_used": "2026-03-01T09:15:00+00:00"
# }
```

---

## Module Functions

### `get_ha_notify_adapter()`

Get or create singleton HANotifyAdapter instance.

```python
from copilot_core.notifications.ha_notify_adapter import get_ha_notify_adapter

adapter = get_ha_notify_adapter(hass)
```

### `reset_ha_notify_adapter()`

Reset the singleton instance (useful for testing).

```python
from copilot_core.notifications.ha_notify_adapter import reset_ha_notify_adapter

reset_ha_notify_adapter()
```

---

## Usage Examples

### Basic Setup

```python
from copilot_core.notifications.ha_notify_adapter import HANotifyAdapter

# Initialize adapter
adapter = HANotifyAdapter(hass)

# Register user devices
adapter.register_ha_device(
    user_id="alice",
    ha_entity_id="notify.mobile_app_iphone",
    device_name="Alice's iPhone"
)

adapter.register_ha_device(
    user_id="alice",
    ha_entity_id="notify.telegram",
    device_name="Alice's Telegram",
    device_type="telegram"
)

# Send notification
adapter.send_to_ha_service(
    device_id="alice",
    title="Welcome Home",
    message="Arrival detected. Turning on lights.",
    priority="normal",
    category="system"
)
```

### Multi-User Notifications

```python
# Send to all devices for a user
devices = adapter.get_ha_devices("alice")
for device in devices:
    adapter.send_to_ha_service(
        device_id=device.id,
        title="Evening Routine",
        message="Starting evening automation sequence",
        priority="low"
    )
```

### Priority-Based Routing

```python
def send_alert(message: str, is_critical: bool = False):
    priority = "urgent" if is_critical else "normal"
    category = "alert" if is_critical else "info"
    
    # Register device first if not already registered
    device = adapter.register_ha_device(
        user_id="user_123",
        ha_entity_id="notify.mobile_app_iphone",
        device_name="User iPhone"
    )
    
    adapter.send_to_ha_service(
        device_id=device.id,
        title="Security Alert" if is_critical else "Home Update",
        message=message,
        priority=priority,
        notification_type=category
    )
```

### Custom Payload Data

```python
# Mobile app with custom data
adapter.send_to_ha_service(
    device_id="device_123",
    title="New Automation",
    message="Suggested: Turn off lights when leaving",
    priority="normal",
    category="suggestion",
    data={
        "action_id": "suggestion_456",
        "actions": [
            {"title": "Accept", "action": "ACCEPT"},
            {"title": "Dismiss", "action": "DISMISS"}
        ],
        "image": "/local/images/suggestion.png"
    }
)
```

---

## Error Handling

### Connection Errors

```python
try:
    adapter.send_to_ha_service(...)
except Exception as e:
    logger.error(f"Notification failed: {e}")
    # Fallback to alternative notify service
```

### Service Discovery

```python
# Check available services
result = adapter.test_ha_connection()
if not result["success"]:
    logger.warning("HA connection not available")
    
available = result["services"]
if "telegram" not in available:
    logger.warning("Telegram notify service not configured")
```

---

## Testing

### Unit Test Example

```python
import pytest
from unittest.mock import Mock
from copilot_core.notifications.ha_notify_adapter import HANotifyAdapter

@pytest.fixture
def mock_hass():
    hass = Mock()
    hass.services.async_services = Mock(return_value={
        "notify": {
            "mobile_app_iphone": Mock(),
            "telegram": Mock()
        }
    })
    return hass

def test_send_notification(mock_hass):
    adapter = HANotifyAdapter(mock_hass)
    adapter._refresh_notify_services()
    
    device = adapter.register_ha_device(
        user_id="test_user",
        ha_entity_id="notify.mobile_app_iphone"
    )
    
    result = adapter.send_to_ha_service(
        device_id=device.id,
        title="Test",
        message="Test message",
        priority="normal"
    )
    
    assert result is True
    mock_hass.services.call.assert_called_once()
```

---

## Best Practices

### Device Registration

1. **Register once:** Call `register_ha_device()` during user setup
2. **Store device IDs:** Persist device IDs for future use
3. **Validate entity IDs:** Ensure `notify.*` entity exists before registering

### Notification Design

1. **Use appropriate priority:** Don't cry wolf with `urgent` priority
2. **Keep titles concise:** Mobile notifications show ~40 chars
3. **Include actionable data:** Add `data` for interactive notifications
4. **Respect categories:** Use consistent categorization

### Performance

1. **Batch notifications:** For multiple users, batch service calls
2. **Cache device lookups:** Store device-to-entity mappings
3. **Async where possible:** Use async service calls in async contexts

---

## Troubleshooting

### Issue: Notification not sent

**Check:**
1. HA instance is connected (`adapter.hass is not None`)
2. Entity ID exists in HA (`notify.*` service available)
3. Device is enabled (`device.enabled == True`)
4. HA services are accessible

### Issue: Wrong priority displayed

**Check:**
1. Priority string is valid (`low`, `normal`, `high`, `urgent`)
2. Mobile app supports priority levels
3. HA notify service respects priority field

### Issue: Category not working

**Check:**
1. Category is in `CATEGORY_MAP`
2. Mobile app supports notification categories
3. Platform supports category (iOS/Android differences)

---

## Related Documentation

- [Notifications API](./NOTIFICATIONS_API.md)
- [RAG Hybrid Search API](./RAG_HYBRID_SEARCH.md)
- [HomeAssistant Integration Guide](../integrations/HOMEASSISTANT.md)

---

**Last Updated:** 2026-03-01  
**Maintained by:** @cowdya  
**Test Coverage:** `tests/test_notifications_ha_adapter.py`
