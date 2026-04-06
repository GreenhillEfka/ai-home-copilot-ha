package sync

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"sync"
	"time"

	"github.com/pilotsuite/sync-bridge/internal/config"
	"github.com/pilotsuite/sync-bridge/internal/crdt"
)

// MessageType defines the type of sync message
type MessageType int

const (
	MessageTypeHeartbeat MessageType = iota
	MessageTypeStateDelta
	MessageTypeClusterExchange
	MessageTypeRequestSync
	MessageTypeAck
	MessageTypeError
)

// Message represents a protocol message
type Message struct {
	Type      MessageType            `json:"type"`
	HomeID    string                 `json:"home_id"`
	Timestamp int64                  `json:"timestamp"`
	Payload   map[string]interface{} `json:"payload"`
	Vector    map[string]int64       `json:"vector"` // Lamport clock vector
}

// Session manages a synchronized connection with a remote home
type Session struct {
	clientID      string
	conn          net.Conn
	config        *config.Config
	stateManager  *crdt.StateManager
	localClock    int64
	remoteVector  map[string]int64
	mu            sync.RWMutex
	stopChan      chan struct{}
	encoder       *json.Encoder
	decoder       *json.Decoder
}

// NewSession creates a new sync session
func NewSession(clientID string, conn net.Conn, cfg *config.Config) *Session {
	return &Session{
		clientID:     clientID,
		conn:         conn,
		config:       cfg,
		stateManager: crdt.NewStateManager(),
		localClock:   time.Now().UnixNano(),
		remoteVector: make(map[string]int64),
		stopChan:     make(chan struct{}),
		encoder:      json.NewEncoder(conn),
		decoder:      json.NewDecoder(conn),
	}
}

// Start begins the sync session
func (s *Session) Start() {
	// Send greeting with our home ID
	s.sendMessage(Message{
		Type:      MessageTypeRequestSync,
		HomeID:    s.config.HomeID,
		Timestamp: s.localClock,
		Vector:    s.getVector(),
	})

	// Start goroutines for reading and heartbeat
	go s.readLoop()
	go s.heartbeatLoop()

	// Wait for stop signal
	<-s.stopChan
}

// Stop terminates the session
func (s *Session) Stop() {
	close(s.stopChan)
	s.conn.Close()
}

// readLoop processes incoming messages
func (s *Session) readLoop() {
	for {
		select {
		case <-s.stopChan:
			return
		default:
			var msg Message
			if err := s.decoder.Decode(&msg); err != nil {
				if err == io.EOF {
					log.Printf("Connection closed by %s", s.clientID)
					s.Stop()
					return
				}
				log.Printf("Error decoding message from %s: %v", s.clientID, err)
				continue
			}

			if err := s.handleMessage(msg); err != nil {
				log.Printf("Error handling message from %s: %v", s.clientID, err)
			}
		}
	}
}

// handleMessage processes a single message
func (s *Session) handleMessage(msg Message) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Update remote vector
	for home, timestamp := range msg.Vector {
		if timestamp > s.remoteVector[home] {
			s.remoteVector[home] = timestamp
		}
	}

	switch msg.Type {
	case MessageTypeHeartbeat:
		// Update clock on any message
		s.updateClock(msg.Timestamp)
		return s.sendMessage(Message{Type: MessageTypeAck, HomeID: s.config.HomeID})

	case MessageTypeRequestSync:
		// Send our current state deltas
		deltas := s.stateManager.CreateDelta(msg.Vector)
		return s.sendMessage(Message{
			Type:      MessageTypeStateDelta,
			HomeID:    s.config.HomeID,
			Timestamp: s.localClock,
			Payload: map[string]interface{}{
				"deltas": deltas,
			},
		})

	case MessageTypeStateDelta:
		// Process incoming state updates
		if deltas, ok := msg.Payload["deltas"].([]crdt.StateVector); ok {
			for _, sv := range deltas {
				if s.stateManager.UpdateState(sv) {
					log.Printf("Applied state update from %s: %s", s.clientID, sv.ID)
				}
			}
		}
		return s.sendMessage(Message{Type: MessageTypeAck, HomeID: s.config.HomeID})

	case MessageTypeClusterExchange:
		// Process incoming learning clusters
		if clusters, ok := msg.Payload["clusters"].([]crdt.LearningCluster); ok {
			for _, lc := range clusters {
				if _, err := s.stateManager.MergeLearningCluster(lc); err != nil {
					log.Printf("Failed to merge cluster %s: %v", lc.ID, err)
				}
			}
		}
		return s.sendMessage(Message{Type: MessageTypeAck, HomeID: s.config.HomeID})

	case MessageTypeAck:
		// Acknowledgment received, no action needed
		return nil

	default:
		return fmt.Errorf("unknown message type: %d", msg.Type)
	}
}

// heartbeatLoop sends periodic keepalive messages
func (s *Session) heartbeatLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-s.stopChan:
			return
		case <-ticker.C:
			s.mu.Lock()
			s.updateClock(0)
			err := s.sendMessage(Message{
				Type:      MessageTypeHeartbeat,
				HomeID:    s.config.HomeID,
				Timestamp: s.localClock,
				Vector:    s.getVector(),
			})
			s.mu.Unlock()

			if err != nil {
				log.Printf("Failed to send heartbeat: %v", err)
			}
		}
	}
}

// updateClock updates the Lamport clock
func (s *Session) updateClock(receivedTimestamp int64) {
	now := time.Now().UnixNano()
	if receivedTimestamp > now {
		s.localClock = receivedTimestamp + 1
	} else {
		s.localClock = now
	}
}

// getVector returns the current Lamport clock vector
func (s *Session) getVector() map[string]int64 {
	vector := make(map[string]int64)
	for k, v := range s.remoteVector {
		vector[k] = v
	}
	vector[s.config.HomeID] = s.localClock
	return vector
}

// sendMessage sends a message to the remote peer
func (s *Session) sendMessage(msg Message) error {
	return s.encoder.Encode(msg)
}

// ExchangeClusters sends learning clusters to remote
func (s *Session) ExchangeClusters(clusters []crdt.LearningCluster) error {
	s.mu.RLock()
	defer s.mu.RUnlock()

	return s.sendMessage(Message{
		Type:      MessageTypeClusterExchange,
		HomeID:    s.config.HomeID,
		Timestamp: s.localClock,
		Payload: map[string]interface{}{
			"clusters": clusters,
		},
	})
}

// RequestStateSync triggers a full state sync from remote
func (s *Session) RequestStateSync() error {
	s.mu.RLock()
	defer s.mu.RUnlock()

	return s.sendMessage(Message{
		Type:      MessageTypeRequestSync,
		HomeID:    s.config.HomeID,
		Timestamp: s.localClock,
		Vector:    s.getVector(),
	})
}
