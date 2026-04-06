# PilotSuite Multi-Home Sync Bridge

Secure state and learning cluster synchronization between PilotSuite instances via mutual TLS.

## Quick Start

### 1. Generate Certificates

```bash
./scripts/gen-certs.sh
```

### 2. Configure Homes

Create `config.yaml`:

```yaml
home_id: "home-001"
port: 8443
trusted_clients:
  - "home-002"
  - "home-003"
```

### 3. Start Bridge

```bash
go run cmd/bridge/main.go -config config.yaml
```

### 4. Connect Client

```go
client, _ := sync.NewClient(cfg)
client.Connect("remote.home:8443", "certs/client.crt", "certs/client.key", "certs/ca.crt")

// Send state delta
deltas := []crdt.StateVector{crdt.NewStateVector("home-001", "entity", data)}
client.SendStateDelta(deltas)

// Send learning cluster
cluster := crdt.LearningCluster{...}
client.SendLearningClusters([]crdt.LearningCluster{cluster})
```

## Architecture

```
┌─────────────┐     TLS 1.3 + mTLS      ┌─────────────┐
│  Home 001   │◄─────────────────────►│  Home 002   │
│  (Server)   │                         │  (Client)   │
└──────┬──────┘                         └──────┬──────┘
       │                                       │
  ┌────┴────┐                              ┌───┴────┐
  │  CRDT   │                              │  CRDT  │
  │ State   │                              │ State  │
  │ Manager │                              │Manager │
  └────┬────┘                              └───┬────┘
       │                                       │
  ┌────┴──────────┐                    ┌──────┴───────┐
  │Learning       │                    │ Learning     │
  │Cluster        │                    │ Cluster      │
  │Exchange       │                    │ Exchange     │
  └───────────────┘                    └──────────────┘
```

## Protocol

### Message Types

- `Heartbeat` - Keepalive
- `StateDelta` - Entity state updates (CRDT-based)
- `ClusterExchange` - Learning pattern sharing
- `RequestSync` - Trigger full sync
- `Ack` - Acknowledgment

### Conflict Resolution

- Lamport timestamps for partial ordering
- Last-write-wins for state vectors
- Pattern merging with frequency-based prioritization

## Security

- TLS 1.3 with mutual authentication
- Certificate-based identity
- Client whitelist validation
- Encrypted transport
