package sync

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"os"
	"sync"
	"time"

	"github.com/pilotsuite/sync-bridge/internal/config"
	"github.com/pilotsuite/sync-bridge/internal/crdt"
)

// Client represents a sync client for outbound connections
type Client struct {
	config  *config.Config
	conn    net.Conn
	encoder *json.Encoder
	decoder *json.Decoder
	mu      sync.RWMutex
	localClock int64
	remoteVector map[string]int64
	stateManager *crdt.StateManager
}

// NewClient creates a new sync client
func NewClient(cfg *config.Config) (*Client, error) {
	return &Client{
		config:       cfg,
		localClock:   time.Now().UnixNano(),
		remoteVector: make(map[string]int64),
		stateManager: crdt.NewStateManager(),
	}, nil
}

// Connect establishes a TLS connection to a remote home
func (c *Client) Connect(remoteAddr, clientCertPath, clientKeyPath, caCertPath string) error {
	// Load client certificate
	cert, err := tls.LoadX509KeyPair(clientCertPath, clientKeyPath)
	if err != nil {
		return fmt.Errorf("failed to load client certificate: %w", err)
	}

	// Load CA certificate
	caCert, err := os.ReadFile(caCertPath)
	if err != nil {
		return fmt.Errorf("failed to read CA certificate: %w", err)
	}

	caPool := x509.NewCertPool()
	caPool.AppendCertsFromPEM(caCert)

	// Configure TLS with mutual authentication
	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs:      caPool,
	}

	// Connect to remote
	conn, err := tls.Dial("tcp", remoteAddr, tlsConfig)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}

	c.conn = conn
	c.encoder = json.NewEncoder(conn)
	c.decoder = json.NewDecoder(conn)

	// Start read loop
	go c.readLoop()

	log.Printf("Connected to %s", remoteAddr)
	return nil
}

// readLoop processes incoming messages
func (c *Client) readLoop() {
	for {
		var msg Message
		if err := c.decoder.Decode(&msg); err != nil {
			log.Printf("Connection closed: %v", err)
			return
		}

		if err := c.handleMessage(msg); err != nil {
			log.Printf("Error handling message: %v", err)
		}
	}
}

// handleMessage processes a single message
func (c *Client) handleMessage(msg Message) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Update remote vector
	for home, timestamp := range msg.Vector {
		if timestamp > c.remoteVector[home] {
			c.remoteVector[home] = timestamp
		}
	}

	// Update clock
	if msg.Timestamp > c.localClock {
		c.localClock = msg.Timestamp + 1
	} else {
		c.localClock = time.Now().UnixNano()
	}

	switch msg.Type {
	case MessageTypeStateDelta:
		if deltas, ok := msg.Payload["deltas"].([]crdt.StateVector); ok {
			for _, sv := range deltas {
				c.stateManager.UpdateState(sv)
			}
		}
		log.Printf("Received state delta from %s", msg.HomeID)

	case MessageTypeClusterExchange:
		if clusters, ok := msg.Payload["clusters"].([]crdt.LearningCluster); ok {
			for _, lc := range clusters {
				c.stateManager.MergeLearningCluster(lc)
			}
		}
		log.Printf("Received learning clusters from %s", msg.HomeID)
	}

	return nil
}

// SendStateDelta sends state updates to the remote home
func (c *Client) SendStateDelta(deltas []crdt.StateVector) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.localClock = time.Now().UnixNano()
	return c.encoder.Encode(Message{
		Type:      MessageTypeStateDelta,
		HomeID:    c.config.HomeID,
		Timestamp: c.localClock,
		Payload: map[string]interface{}{
			"deltas": deltas,
		},
		Vector: c.getVector(),
	})
}

// SendLearningClusters sends learning clusters to the remote home
func (c *Client) SendLearningClusters(clusters []crdt.LearningCluster) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.localClock = time.Now().UnixNano()
	return c.encoder.Encode(Message{
		Type:      MessageTypeClusterExchange,
		HomeID:    c.config.HomeID,
		Timestamp: c.localClock,
		Payload: map[string]interface{}{
			"clusters": clusters,
		},
		Vector: c.getVector(),
	})
}

// getVector returns the current clock vector
func (c *Client) getVector() map[string]int64 {
	vector := make(map[string]int64)
	for k, v := range c.remoteVector {
		vector[k] = v
	}
	vector[c.config.HomeID] = c.localClock
	return vector
}

// Close terminates the client connection
func (c *Client) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}
