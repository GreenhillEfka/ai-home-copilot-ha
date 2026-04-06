package crdt

import (
	"encoding/json"
	"sync"
	"time"

	"github.com/google/uuid"
)

// StateVector represents a CRDT-based state update
type StateVector struct {
	ID        string                 `json:"id"`
	HomeID    string                 `json:"home_id"`
	Timestamp int64                  `json:"timestamp"`
	Version   int64                  `json:"version"`
	Delta     map[string]interface{} `json:"delta"`
	Type      string                 `json:"type"` // "entity", "automation", "learning_cluster"
}

// StateManager manages distributed state across homes
type StateManager struct {
	mu       sync.RWMutex
	states   map[string]StateVector       // key: entity_id
	versions map[string]int64             // key: home_id:entity_id, value: version
	vector   map[string]int64             // Lamport clock per home
	clusters map[string]LearningCluster   // Learning clusters by ID
}

// LearningCluster represents a group of related learning patterns
type LearningCluster struct {
	ID          string            `json:"id"`
	HomeID      string            `json:"home_id"`
	Name        string            `json:"name"`
	Patterns    []Pattern         `json:"patterns"`
	Confidence  float64           `json:"confidence"`
	LastUpdated int64             `json:"last_updated"`
	Version     int64             `json:"version"`
	Metadata    map[string]string `json:"metadata"`
}

// Pattern represents a learned behavioral pattern
type Pattern struct {
	ID          string            `json:"id"`
	Type        string            `json:"type"` // "time", "sensor", "manual"
	Trigger     TriggerConfig     `json:"trigger"`
	Conditions  []Condition       `json:"conditions"`
	Actions     []Action          `json:"actions"`
	Frequency   int               `json:"frequency"`
	LastSeen    int64             `json:"last_seen"`
}

// TriggerConfig defines when a pattern activates
type TriggerConfig struct {
	Time     string            `json:"time,omitempty"`
	Sensors  map[string]any    `json:"sensors,omitempty"`
	Days     []string          `json:"days,omitempty"`
	Interval int               `json:"interval,omitempty"`
}

// Condition represents a state condition
type Condition struct {
	EntityID   string `json:"entity_id"`
	Attribute  string `json:"attribute"`
	Operator   string `json:"operator"` // eq, ne, gt, lt, contains
	Value      any    `json:"value"`
}

// Action represents an automation action
type Action struct {
	Type       string            `json:"type"` // service_call, scene, notify
	Target     string            `json:"target"`
	Service    string            `json:"service,omitempty"`
	Payload    map[string]any    `json:"payload,omitempty"`
	Delay      int               `json:"delay,omitempty"`
}

// NewStateManager creates a new CRDT state manager
func NewStateManager() *StateManager {
	return &StateManager{
		states:   make(map[string]StateVector),
		versions: make(map[string]int64),
		vector:   make(map[string]int64),
		clusters: make(map[string]LearningCluster),
	}
}

// UpdateState merges a new state vector into local state
func (sm *StateManager) UpdateState(sv StateVector) bool {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	key := sv.HomeID + ":" + sv.ID

	// Check if this is a newer version
	if current, exists := sm.states[key]; exists {
		if current.Version >= sv.Version {
			return false // Ignore stale updates
		}
	}

	sm.states[key] = sv
	sm.versions[key] = sv.Version

	// Update Lamport clock
	if sv.Timestamp > sm.vector[sv.HomeID] {
		sm.vector[sv.HomeID] = sv.Timestamp
	}

	return true
}

// GetState returns the current state for an entity
func (sm *StateManager) GetState(homeID, entityID string) (StateVector, bool) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	sv, ok := sm.states[homeID+":"+entityID]
	return sv, ok
}

// MergeLearningCluster merges a learning cluster from remote
func (sm *StateManager) MergeLearningCluster(lc LearningCluster) (bool, error) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	key := lc.HomeID + ":" + lc.ID

	if current, exists := sm.clusters[key]; exists {
		if current.Version >= lc.Version {
			return false, nil // Remote version is stale
		}
		// Merge patterns from both clusters
		lc.Patterns = sm.mergePatterns(current.Patterns, lc.Patterns)
	}

	lc.LastUpdated = time.Now().UnixNano()
	sm.clusters[key] = lc

	return true, nil
}

// mergePatterns combines patterns, keeping highest frequency ones
func (sm *StateManager) mergePatterns(local, remote []Pattern) []Pattern {
	patternMap := make(map[string]Pattern)

	// Add local patterns
	for _, p := range local {
		patternMap[p.ID] = p
	}

	// Merge with remote
	for _, p := range remote {
		if existing, ok := patternMap[p.ID]; ok {
			if p.Frequency > existing.Frequency {
				patternMap[p.ID] = p
			}
		} else {
			patternMap[p.ID] = p
		}
	}

	// Convert back to slice
	merged := make([]Pattern, 0, len(patternMap))
	for _, p := range patternMap {
		merged = append(merged, p)
	}

	return merged
}

// GetCluster retrieves a learning cluster
func (sm *StateManager) GetCluster(homeID, clusterID string) (LearningCluster, bool) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	lc, ok := sm.clusters[homeID+":"+clusterID]
	return lc, ok
}

// GetAllClusters returns all learning clusters for a home
func (sm *StateManager) GetAllClusters(homeID string) []LearningCluster {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	var clusters []LearningCluster
	prefix := homeID + ":"
	for key, lc := range sm.clusters {
		if len(key) > len(prefix) && key[:len(prefix)] == prefix {
			clusters = append(clusters, lc)
		}
	}

	return clusters
}

// CreateDelta generates a delta update from local to remote state
func (sm *StateManager) CreateDelta(since map[string]int64) []StateVector {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	var deltas []StateVector
	for key, sv := range sm.states {
		remoteVersion := since[sv.HomeID]
		if sv.Timestamp > remoteVersion {
			deltas = append(deltas, sv)
		}
	}

	return deltas
}

// ToJSON serializes the state manager to JSON
func (sm *StateManager) ToJSON() ([]byte, error) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	return json.Marshal(map[string]interface{}{
		"states":   sm.states,
		"clusters": sm.clusters,
		"vector":   sm.vector,
	})
}

// NewStateVector creates a new state vector
func NewStateVector(homeID, entityType string, delta map[string]interface{}) StateVector {
	return StateVector{
		ID:        uuid.New().String(),
		HomeID:    homeID,
		Timestamp: time.Now().UnixNano(),
		Version:   1,
		Delta:     delta,
		Type:      entityType,
	}
}
