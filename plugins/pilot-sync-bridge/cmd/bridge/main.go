package main

import (
	"crypto/tls"
	"flag"
	"fmt"
	"log"
	"net"

	"github.com/pilotsuite/sync-bridge/internal/auth"
	"github.com/pilotsuite/sync-bridge/internal/config"
	"github.com/pilotsuite/sync-bridge/internal/sync"
)

func main() {
	configPath := flag.String("config", "config.yaml", "Path to configuration file")
	flag.Parse()

	cfg, err := config.Load(*configPath)
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Setup TLS configuration with mutual authentication
	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cfg.ServerCert},
		ClientAuth:   tls.RequireAndVerifyClientCert,
		ClientCAs:    cfg.ClientCAs,
	}

	listener, err := tls.Listen("tcp", fmt.Sprintf(":%d", cfg.Port), tlsConfig)
	if err != nil {
		log.Fatalf("Failed to start TLS listener: %v", err)
	}
	defer listener.Close()

	log.Printf("PilotSuite Sync Bridge listening on :%d", cfg.Port)

	// Initialize authenticator
	authenticator := auth.NewAuthenticator(cfg.TrustedClients)

	// Start accepting connections
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Failed to accept connection: %v", err)
			continue
		}

		// Handle each connection in a separate goroutine
		go handleConnection(conn, authenticator, cfg)
	}
}

func handleConnection(conn net.Conn, authenticator *auth.Authenticator, cfg *config.Config) {
	defer conn.Close()

	clientID, err := authenticator.Authenticate(conn)
	if err != nil {
		log.Printf("Authentication failed: %v", err)
		return
	}

	log.Printf("Client %s authenticated successfully", clientID)

	// Start sync session
	session := sync.NewSession(clientID, conn, cfg)
	session.Start()
}