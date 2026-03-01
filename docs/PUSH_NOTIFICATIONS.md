# Push Notifications API Documentation

**Phase 6 Feature** | **Version:** 1.0.0 | **Last Updated:** 2026-03-01

Comprehensive API documentation for the Push Notification system supporting multiple channels (Mobile, Telegram, Email) with templates, scheduling, and priority levels.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Data Types](#data-types)
- [Endpoints](#endpoints)
  - [POST /api/v1/notifications/send](#post-apiv1notificationssend)
  - [GET /api/v1/notifications](#get-apiv1notifications)
  - [POST /api/v1/notifications/subscribe](#post-apiv1notificationssubscribe)
  - [POST /api/v1/notifications/unsubscribe](#post-apiv1notificationsunsubscribe)
  - [GET /api/v1/notifications/subscriptions](#get-apiv1notificationssubscriptions)
  - [PUT /api/v1/notifications/subscriptions/:device_id](#put-apiv1notificationssubscriptionsdevice_id)
  - [POST /api/v1/notifications/:id/read](#post-apiv1notificationsidread)
  - [DELETE /api/v1/notifications/:id](#delete-apiv1notificationsid)
  - [POST /api/v1/notifications/clear](#post-apiv1notificationsclear)
  - [GET /api/v1/notifications/templates](#get-apiv1notificationstemplates)
  - [GET /api/v1/notifications/templates/:id](#get-apiv1notificationstemplatesid)
  - [POST /api/v1/notifications/templates](#post-apiv1notificationstemplates)
  - [DELETE /api/v1/notifications/templates/:id](#delete-apiv1notificationstemplatesid)
  - [POST /api/v1/notifications/send-with-template](#post-apiv1notificationssend-with-template)
  - [POST /api/v1/notifications/schedule](#post-apiv1notificationsschedule)
  - [GET /api/v1/notifications/scheduled](#get-apiv1notificationsscheduled)
  - [DELETE /api/v1/notifications/scheduled/:id](#delete-apiv1notificationsscheduledid)
- [Error Codes](#error-codes)
- [Python SDK Examples](#python-sdk-examples)

---

## Overview

The Push Notifications API provides a unified interface for sending notifications across multiple channels with advanced features like templates, scheduling, and device management.

### Supported Channels

| Channel | Description | Status |
|---------|-------------|--------|
| **Mobile** | HA Companion App push notifications | ✅ Always available |
| **Telegram** | Telegram Bot messages | ⚙️ Configurable |
| **Email** | SMTP email notifications | ⚙️ Configurable |

### Priority Levels

| Priority | Use Case | Notification Behavior |
|----------|----------|----------------------|
| `low` | Info updates, non-urgent | Silent, no sound |
| `medium` | Standard notifications | Normal sound |
| `high` | Important alerts | Loud sound, vibration |
| `critical` | Emergency alerts | Maximum volume, bypass DND |

### Notification Types

| Type | Description | Example |
|------|-------------|---------|
| `mood_change` | Mood transition notifications | "Mood changed from relax to focus" |
| `alert` | System alerts | "Energy anomaly detected" |
| `suggestion` | AI suggestions | "Consider lowering heating" |
| `system` | System messages | "Backup completed" |
| `info` | General information | "New device connected" |
| `warning` | Warnings | "Low battery" |

---

## Authentication

All endpoints require authentication via:

### Header Authentication

```http
X-Auth-Token: your-api-token-here
```

or

```http
Authorization: Bearer your-api-token-here
```

### Authentication Failure Response

```json
{
  "error": "unauthorized",
  "message": "Valid X-Auth-Token or Bearer token required"
}
```

**HTTP Status:** `401 Unauthorized`

---

## Data Types

### Notification Object

```json
{
  "id": "notif_abc123",
  "title": "Energy Alert",
  "message": "High consumption detected",
  "priority": "high",
  "type": "alert",
  "timestamp": "2026-03-01T14:30:00Z",
  "action_data": {"entity_id": "sensor.energy"},
  "action_url": "/lovelace/energy",
  "target_devices": ["device_001"],
  "target_users": ["user_andreas"],
  "read": false,
  "dismissed": false,
  "sent": true,
  "source": "copilot",
  "tags": ["energy", "alert"]
}
```

### Device Subscription Object

```json
{
  "id": "sub_xyz789",
  "device_id": "iphone_andreas",
  "device_name": "Andreas iPhone",
  "device_type": "mobile",
  "push_token": "abcd1234...",
  "enabled": true,
  "preferences": {
    "notify_mood": true,
    "notify_alerts": true,
    "notify_suggestions": true,
    "notify_system": false
  },
  "ha_entity_id": "notify.mobile_app_iphone",
  "last_seen": "2026-03-01T14:30:00Z",
  "created_at": "2026-01-15T10:00:00Z"
}
```

### Template Object

```json
{
  "id": "tpl-energy-anomaly",
  "name": "Energy Anomaly Alert",
  "title_template": "⚡ Energie-Anomalie erkannt",
  "message_template": "Verbrauch von {consumption} kWh um {time} - {deviation}% über dem Durchschnitt",
  "default_priority": "high",
  "tags": ["energy", "anomaly"],
  "created_at": "2026-03-01T10:00:00Z"
}
```

### Scheduled Notification Object

```json
{
  "id": "sched_abc123xyz",
  "title": "Meeting Reminder",
  "message": "Team meeting in 15 minutes",
  "deliver_at": "2026-03-01T15:00:00Z",
  "priority": "medium",
  "channel": "mobile",
  "template_id": "tpl-reminder",
  "created_at": "2026-03-01T14:00:00Z",
  "delivered": false,
  "cancelled": false
}
```

---

## Endpoints

### POST /api/v1/notifications/send

Send a notification immediately.

#### Description

Creates and sends a notification through all configured channels.

#### Request Format

**Endpoint:** `POST /api/v1/notifications/send`

**Headers:**
```http
Content-Type: application/json
X-Auth-Token: your-api-token
```

**Body:**
```json
{
  "title": "⚠️ Energy Alert",
  "message": "Unusual consumption detected: 2.5 kWh in last hour",
  "priority": "high",
  "type": "alert",
  "action_data": {
    "entity_id": "sensor.energy_consumption",
    "action": "view_details"
  },
  "action_url": "/lovelace/energy",
  "target_devices": ["iphone_andreas", "ipad_tablet"],
  "target_users": ["user_andreas"],
  "tags": ["energy", "anomaly", "urgent"]
}
```

**Request Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `title` | string | ✅ Yes | - | Notification title |
| `message` | string | ✅ Yes | - | Notification message body |
| `priority` | string | ❌ No | "normal" | `low`, `normal`, `high`, `urgent` |
| `type` | string | ❌ No | "info" | `mood_change`, `alert`, `suggestion`, `system`, `info`, `warning` |
| `action_data` | object | ❌ No | {} | Action payload for interactive notifications |
| `action_url` | string | ❌ No | "" | URL to open on notification tap |
| `target_devices` | array | ❌ No | [] | Device IDs to target (empty = all) |
| `target_users` | array | ❌ No | [] | User IDs to target (empty = all) |
| `tags` | array | ❌ No | [] | Tags for categorization |

#### Response Format

**Success Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "notification_id": "notif_abc123xyz",
    "timestamp": "2026-03-01T14:30:00Z"
  }
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `400` | Bad Request - Missing required fields |
| `401` | Unauthorized - Invalid or missing token |
| `403` | Forbidden - Insufficient permissions |
| `500` | Internal Server Error - Failed to send |

#### Python Code Example

```python
import requests
from typing import List, Dict, Any, Optional


class PushNotificationClient:
    """Client for Push Notifications API."""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            'X-Auth-Token': api_token,
            'Content-Type': 'application/json'
        })
    
    def send(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        notification_type: str = "info",
        action_data: Dict[str, Any] = None,
        action_url: str = "",
        target_devices: List[str] = None,
        target_users: List[str] = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send a notification.
        
        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (low/normal/high/urgent)
            notification_type: Type (alert/info/warning/etc.)
            action_data: Action payload
            action_url: URL to open on tap
            target_devices: Target device IDs
            target_users: Target user IDs
            tags: Categorization tags
            
        Returns:
            Response with notification ID
        """
        payload = {
            'title': title,
            'message': message,
            'priority': priority,
            'type': notification_type,
            'action_data': action_data or {},
            'action_url': action_url,
            'target_devices': target_devices or [],
            'target_users': target_users or [],
            'tags': tags or []
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/notifications/send',
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            raise ValueError(f"Bad request: {response.json().get('error')}")
        elif response.status_code == 401:
            raise PermissionError("Invalid API token")
        else:
            response.raise_for_status()


# Usage Example
if __name__ == '__main__':
    client = PushNotificationClient(
        base_url='http://localhost:8123',
        api_token='your-api-token-here'
    )
    
    # Send alert notification
    result = client.send(
        title="⚠️ Security Alert",
        message="Motion detected at front door",
        priority="high",
        notification_type="alert",
        action_data={"camera_id": "front_door", "snapshot": "url_to_image"},
        action_url="/lovelace/security",
        tags=["security", "motion"]
    )
    
    print(f"✅ Notification sent: {result['data']['notification_id']}")
```

---

### GET /api/v1/notifications

List recent notifications with optional filtering.

#### Description

Retrieves notifications from history with support for filtering by read status and type.

#### Request Format

**Endpoint:** `GET /api/v1/notifications`

**Headers:**
```http
X-Auth-Token: your-api-token
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `unread_only` | boolean | ❌ No | false | Return only unread notifications |
| `type` | string | ❌ No | - | Filter by notification type |
| `limit` | integer | ❌ No | 20 | Maximum results (max: 100) |

#### Response Format

**Success Response (200 OK):**

```json
{
  "ok": true,
  "count": 5,
  "notifications": [
    {
      "id": "notif_001",
      "title": "Mood Changed",
      "message": "Stimmung gewechselt von relax zu focus (85%)",
      "priority": "low",
      "type": "mood_change",
      "timestamp": "2026-03-01T14:30:00Z",
      "read": false,
      "dismissed": false,
      "sent": true,
      "tags": ["mood", "mood_change"]
    }
  ]
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `401` | Unauthorized |
| `403` | Forbidden |
| `500` | Internal Server Error |

#### Python Code Example

```python
def list_notifications_example(client: PushNotificationClient):
    """Example: List recent notifications."""
    
    # Get unread alerts only
    response = client.session.get(
        f'{client.base_url}/api/v1/notifications',
        headers=client.session.headers,
        params={
            'unread_only': 'true',
            'type': 'alert',
            'limit': '10'
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"📬 Unread alerts: {data['count']}")
        
        for notif in data['notifications']:
            print(f"  • {notif['title']}: {notif['message']}")
    else:
        print(f"❌ Failed: {response.status_code}")
```

---

### POST /api/v1/notifications/subscribe

Register a device for push notifications.

#### Description

Subscribes a device to receive push notifications with customizable preferences.

#### Request Format

**Endpoint:** `POST /api/v1/notifications/subscribe`

**Headers:**
```http
Content-Type: application/json
X-Auth-Token: your-api-token
```

**Body:**
```json
{
  "device_id": "iphone_andreas",
  "device_name": "Andreas iPhone 15",
  "device_type": "mobile",
  "push_token": "abcd1234efgh5678...",
  "ha_entity_id": "notify.mobile_app_iphone_andreas",
  "preferences": {
    "notify_mood": true,
    "notify_alerts": true,
    "notify_suggestions": true,
    "notify_system": false
  }
}
```

**Request Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `device_id` | string | ✅ Yes | - | Unique device identifier |
| `device_name` | string | ❌ No | "" | Human-readable device name |
| `device_type` | string | ❌ No | "mobile" | `mobile`, `tablet`, `watch`, `speaker` |
| `push_token` | string | ❌ No | "" | Platform-specific push token |
| `ha_entity_id` | string | ❌ No | "" | HA notify service entity ID |
| `preferences` | object | ❌ No | {} | Notification preferences |

#### Response Format

**Success Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "sub_xyz789",
    "device_id": "iphone_andreas",
    "device_name": "Andreas iPhone 15",
    "device_type": "mobile",
    "push_token": "abcd1234...",
    "enabled": true,
    "preferences": {
      "notify_mood": true,
      "notify_alerts": true,
      "notify_suggestions": true,
      "notify_system": false
    },
    "ha_entity_id": "notify.mobile_app_iphone_andreas",
    "last_seen": "2026-03-01T14:30:00Z",
    "created_at": "2026-01-15T10:00:00Z"
  }
}
```

#### Python Code Example

```python
def subscribe_device_example(client: PushNotificationClient):
    """Example: Subscribe a device."""
    
    payload = {
        'device_id': 'ipad_tablet',
        'device_name': 'iPad Pro',
        'device_type': 'tablet',
        'ha_entity_id': 'notify.mobile_app_ipad',
        'preferences': {
            'notify_mood': False,
            'notify_alerts': True,
            'notify_suggestions': True,
            'notify_system': False
        }
    }
    
    response = client.session.post(
        f'{client.base_url}/api/v1/notifications/subscribe',
        headers=client.session.headers,
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()['data']
        print(f"✅ Device subscribed: {data['device_name']}")
        print(f"   Subscription ID: {data['id']}")
    else:
        print(f"❌ Failed: {response.status_code}")
```

---

### POST /api/v1/notifications/unsubscribe

Unsubscribe a device from push notifications.

#### Request Format

**Body:**
```json
{
  "device_id": "iphone_andreas"
}
```

#### Python Code Example

```python
def unsubscribe_device_example(client: PushNotificationClient, device_id: str):
    """Example: Unsubscribe a device."""
    
    response = client.session.post(
        f'{client.base_url}/api/v1/notifications/unsubscribe',
        headers=client.session.headers,
        json={'device_id': device_id}
    )
    
    if response.status_code == 200:
        print(f"✅ Device unsubscribed: {device_id}")
    elif response.status_code == 404:
        print(f"⚠️  Device not found: {device_id}")
```

---

### GET /api/v1/notifications/subscriptions

List all device subscriptions.

#### Response Format

```json
{
  "success": true,
  "data": {
    "subscriptions": [
      {
        "id": "sub_001",
        "device_id": "iphone_andreas",
        "device_name": "Andreas iPhone",
        "device_type": "mobile",
        "enabled": true,
        "preferences": {...}
      }
    ],
    "count": 2
  }
}
```

---

### PUT /api/v1/notifications/subscriptions/:device_id

Update subscription preferences.

#### Request Format

**Body:**
```json
{
  "enabled": true,
  "preferences": {
    "notify_mood": false,
    "notify_alerts": true,
    "notify_suggestions": true,
    "notify_system": false
  }
}
```

---

### POST /api/v1/notifications/:id/read

Mark a notification as read.

#### Request Format

**Endpoint:** `POST /api/v1/notifications/:notification_id/read`

#### Response Format

```json
{
  "success": true,
  "data": {
    "notification_id": "notif_001"
  }
}
```

---

### DELETE /api/v1/notifications/:id

Dismiss/delete a notification.

#### Response Format

```json
{
  "success": true,
  "data": {
    "notification_id": "notif_001"
  }
}
```

---

### POST /api/v1/notifications/clear

Clear notifications from history.

#### Request Format

**Body (optional):**
```json
{
  "type": "alert"
}
```

#### Response Format

```json
{
  "success": true,
  "data": {
    "cleared_count": 15
  }
}
```

---

### GET /api/v1/notifications/templates

List all notification templates.

#### Description

Retrieves available notification templates with optional tag filtering.

#### Request Format

**Endpoint:** `GET /api/v1/notifications/templates`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tag` | string | Filter by tag |

#### Response Format

```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "id": "tpl-energy-anomaly",
        "name": "Energy Anomaly Alert",
        "title_template": "⚡ Energie-Anomalie erkannt",
        "message_template": "Verbrauch von {consumption} kWh um {time} - {deviation}% über dem Durchschnitt",
        "default_priority": "high",
        "tags": ["energy", "anomaly"]
      }
    ],
    "count": 4
  }
}
```

#### Python Code Example

```python
def list_templates_example(client: PushNotificationClient):
    """Example: List notification templates."""
    
    response = client.session.get(
        f'{client.base_url}/api/v1/notifications/templates',
        headers=client.session.headers,
        params={'tag': 'alert'}
    )
    
    if response.status_code == 200:
        templates = response.json()['data']['templates']
        print(f"📋 Found {len(templates)} templates:")
        for tpl in templates:
            print(f"  • {tpl['id']}: {tpl['name']}")
```

---

### GET /api/v1/notifications/templates/:id

Get a specific template by ID.

#### Response Format

```json
{
  "success": true,
  "data": {
    "id": "tpl-energy-anomaly",
    "name": "Energy Anomaly Alert",
    "title_template": "⚡ Energie-Anomalie erkannt",
    "message_template": "Verbrauch von {consumption} kWh um {time} - {deviation}% über dem Durchschnitt",
    "default_priority": "high",
    "tags": ["energy", "anomaly"]
  }
}
```

---

### POST /api/v1/notifications/templates

Create a new notification template.

#### Request Format

**Body:**
```json
{
  "id": "tpl-custom-alert",
  "name": "Custom Alert Template",
  "title_template": "🚨 {alert_type} detected",
  "message_template": "{description} at {location} - {severity}",
  "default_priority": "high",
  "tags": ["custom", "alert"]
}
```

#### Response Format

```json
{
  "success": true,
  "data": {
    "id": "tpl-custom-alert",
    "name": "Custom Alert Template",
    "title_template": "🚨 {alert_type} detected",
    "message_template": "{description} at {location} - {severity}",
    "default_priority": "high",
    "tags": ["custom", "alert"],
    "created_at": "2026-03-01T14:30:00Z"
  }
}
```

---

### DELETE /api/v1/notifications/templates/:id

Delete a notification template.

---

### POST /api/v1/notifications/send-with-template

Send a notification using a template.

#### Description

Sends a notification by rendering a template with provided variables.

#### Request Format

**Body:**
```json
{
  "template_id": "tpl-energy-anomaly",
  "variables": {
    "consumption": "2.5",
    "time": "14:30",
    "deviation": "45"
  },
  "priority": "high",
  "channel": "mobile",
  "target_devices": ["iphone_andreas"]
}
```

#### Response Format

```json
{
  "success": true,
  "data": {
    "notification_id": "notif_abc123",
    "template_id": "tpl-energy-anomaly"
  }
}
```

#### Python Code Example

```python
def send_with_template_example(client: PushNotificationClient):
    """Example: Send notification using template."""
    
    payload = {
        'template_id': 'tpl-energy-anomaly',
        'variables': {
            'consumption': '3.2',
            'time': '15:45',
            'deviation': '67'
        },
        'priority': 'high',
        'target_devices': ['iphone_andreas']
    }
    
    response = client.session.post(
        f'{client.base_url}/api/v1/notifications/send-with-template',
        headers=client.session.headers,
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Template notification sent: {data['data']['notification_id']}")
```

---

### POST /api/v1/notifications/schedule

Schedule a notification for future delivery.

#### Description

Creates a scheduled notification that will be delivered at a specified time.

#### Request Format

**Body:**
```json
{
  "title": "Meeting Reminder",
  "message": "Team standup in 15 minutes",
  "deliver_at": "2026-03-01T15:00:00Z",
  "priority": "medium",
  "channel": "mobile"
}
```

**OR using delay:**

```json
{
  "title": "Break Reminder",
  "message": "Time for a short break!",
  "delay_minutes": 30,
  "priority": "low"
}
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ Yes | Notification title |
| `message` | string | ✅ Yes | Notification message |
| `deliver_at` | string | ❌ No | ISO 8601 datetime (use OR delay_minutes) |
| `delay_minutes` | integer | ❌ No | Minutes from now (use OR deliver_at) |
| `priority` | string | ❌ No | Priority level |
| `channel` | string | ❌ No | Target channel |
| `template_id` | string | ❌ No | Template to use |

#### Response Format

```json
{
  "success": true,
  "data": {
    "id": "sched_abc123xyz",
    "title": "Meeting Reminder",
    "message": "Team standup in 15 minutes",
    "deliver_at": "2026-03-01T15:00:00Z",
    "priority": "medium",
    "channel": "mobile",
    "created_at": "2026-03-01T14:30:00Z",
    "delivered": false,
    "cancelled": false
  }
}
```

#### Python Code Example

```python
def schedule_notification_example(client: PushNotificationClient):
    """Example: Schedule a notification."""
    
    from datetime import datetime, timedelta, timezone
    
    # Schedule for specific time
    deliver_at = datetime.now(timezone.utc) + timedelta(hours=2)
    
    payload = {
        'title': '💧 Water Plants',
        'message': 'Don\'t forget to water the plants!',
        'deliver_at': deliver_at.isoformat(),
        'priority': 'low'
    }
    
    response = client.session.post(
        f'{client.base_url}/api/v1/notifications/schedule',
        headers=client.session.headers,
        json=payload
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Notification scheduled: {data['data']['id']}")
        print(f"   Delivery: {data['data']['deliver_at']}")
```

---

### GET /api/v1/notifications/scheduled

List scheduled notifications.

#### Request Format

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_delivered` | boolean | false | Include already delivered |
| `include_cancelled` | boolean | false | Include cancelled |

#### Response Format

```json
{
  "success": true,
  "data": {
    "scheduled": [
      {
        "id": "sched_001",
        "title": "Meeting Reminder",
        "deliver_at": "2026-03-01T15:00:00Z",
        "delivered": false,
        "cancelled": false
      }
    ],
    "count": 1
  }
}
```

---

### DELETE /api/v1/notifications/scheduled/:id

Cancel a scheduled notification.

#### Response Format

```json
{
  "success": true,
  "data": {
    "scheduled_id": "sched_001"
  }
}
```

---

## Error Codes

### Standard HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Template/schedule created |
| `400` | Bad Request | Invalid request format |
| `401` | Unauthorized | Invalid authentication |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Template ID exists |
| `500` | Internal Server Error | Server error |

---

## Python SDK Examples

### Complete Usage Example

```python
#!/usr/bin/env python3
"""
Push Notifications API - Complete Usage Examples
"""

import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional


class PushNotificationsClient:
    """Complete client for Push Notifications API."""
    
    def __init__(self, base_url: str, api_token: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.timeout = timeout
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-Auth-Token': api_token,
            'Content-Type': 'application/json'
        })
    
    # ==================== Send Notifications ====================
    
    def send(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        notification_type: str = "info",
        action_data: Dict[str, Any] = None,
        action_url: str = "",
        target_devices: List[str] = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Send a notification."""
        payload = {
            'title': title,
            'message': message,
            'priority': priority,
            'type': notification_type,
            'action_data': action_data or {},
            'action_url': action_url,
            'target_devices': target_devices or [],
            'tags': tags or []
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/notifications/send',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def send_with_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        priority: str = None,
        target_devices: List[str] = None
    ) -> Dict[str, Any]:
        """Send notification using a template."""
        payload = {
            'template_id': template_id,
            'variables': variables,
            'priority': priority,
            'target_devices': target_devices or []
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/notifications/send-with-template',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Device Management ====================
    
    def subscribe_device(
        self,
        device_id: str,
        device_name: str = "",
        device_type: str = "mobile",
        push_token: str = "",
        ha_entity_id: str = "",
        preferences: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """Subscribe a device."""
        payload = {
            'device_id': device_id,
            'device_name': device_name,
            'device_type': device_type,
            'push_token': push_token,
            'ha_entity_id': ha_entity_id,
            'preferences': preferences or {}
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/notifications/subscribe',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def unsubscribe_device(self, device_id: str) -> Dict[str, Any]:
        """Unsubscribe a device."""
        response = self.session.post(
            f'{self.base_url}/api/v1/notifications/unsubscribe',
            json={'device_id': device_id},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_subscriptions(self) -> Dict[str, Any]:
        """Get all device subscriptions."""
        response = self.session.get(
            f'{self.base_url}/api/v1/notifications/subscriptions',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Templates ====================
    
    def list_templates(self, tag: str = None) -> Dict[str, Any]:
        """List notification templates."""
        params = {'tag': tag} if tag else {}
        response = self.session.get(
            f'{self.base_url}/api/v1/notifications/templates',
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def create_template(
        self,
        name: str,
        title_template: str,
        message_template: str,
        default_priority: str = "medium",
        tags: List[str] = None,
        template_id: str = None
    ) -> Dict[str, Any]:
        """Create a notification template."""
        payload = {
            'id': template_id,
            'name': name,
            'title_template': title_template,
            'message_template': message_template,
            'default_priority': default_priority,
            'tags': tags or []
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/notifications/templates',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Scheduling ====================
    
    def schedule(
        self,
        title: str,
        message: str,
        deliver_at: datetime = None,
        delay_minutes: int = None,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """Schedule a notification."""
        payload = {
            'title': title,
            'message': message,
            'priority': priority
        }
        
        if deliver_at:
            payload['deliver_at'] = deliver_at.isoformat()
        elif delay_minutes:
            payload['delay_minutes'] = delay_minutes
        else:
            raise ValueError("Either deliver_at or delay_minutes required")
        
        response = self.session.post(
            f'{self.base_url}/api/v1/notifications/schedule',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_scheduled(
        self,
        include_delivered: bool = False,
        include_cancelled: bool = False
    ) -> Dict[str, Any]:
        """Get scheduled notifications."""
        response = self.session.get(
            f'{self.base_url}/api/v1/notifications/scheduled',
            params={
                'include_delivered': str(include_delivered).lower(),
                'include_cancelled': str(include_cancelled).lower()
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def cancel_scheduled(self, scheduled_id: str) -> Dict[str, Any]:
        """Cancel a scheduled notification."""
        response = self.session.delete(
            f'{self.base_url}/api/v1/notifications/scheduled/{scheduled_id}',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()


# ==================== Example Usage ====================

if __name__ == '__main__':
    BASE_URL = 'http://localhost:8123'
    API_TOKEN = 'your-api-token-here'
    
    client = PushNotificationsClient(BASE_URL, API_TOKEN)
    
    print("=" * 60)
    print("Push Notifications API - Usage Examples")
    print("=" * 60)
    
    # 1. Send immediate notification
    print("\n1. 📬 Send Immediate Notification")
    print("-" * 40)
    result = client.send(
        title="🧘 Mood Changed",
        message="Stimmung gewechselt zu 'focus'",
        priority="low",
        notification_type="mood_change",
        tags=["mood"]
    )
    print(f"✅ Sent: {result['data']['notification_id']}")
    
    # 2. Send with template
    print("\n2. 📋 Send with Template")
    print("-" * 40)
    result = client.send_with_template(
        template_id='tpl-energy-anomaly',
        variables={
            'consumption': '2.8',
            'time': '15:30',
            'deviation': '52'
        },
        priority='high'
    )
    print(f"✅ Template sent: {result['data']['notification_id']}")
    
    # 3. Schedule notification
    print("\n3. ⏰ Schedule Notification")
    print("-" * 40)
    deliver_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    result = client.schedule(
        title="💧 Plant Reminder",
        message="Time to water the plants!",
        deliver_at=deliver_at,
        priority="low"
    )
    print(f"✅ Scheduled: {result['data']['id']} for {result['data']['deliver_at']}")
    
    # 4. List templates
    print("\n4. 📑 List Templates")
    print("-" * 40)
    templates = client.list_templates()
    for tpl in templates['data']['templates']:
        print(f"  • {tpl['id']}: {tpl['name']}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
```

---

**Documentation Version:** 1.0.0  
**Last Updated:** 2026-03-01  
**Maintained By:** PilotSuite Core Team
