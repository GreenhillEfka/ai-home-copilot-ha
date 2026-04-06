package auth

import (
	"crypto/tls"
	"crypto/x509"
	"errors"
	"net"
)

type Authenticator struct {
	trustedClients map[string]bool
}

func NewAuthenticator(trustedClients []string) *Authenticator {
	tc := make(map[string]bool)
	for _, client := range trustedClients {
		tc[client] = true
	}
	return &Authenticator{trustedClients: tc}
}

func (a *Authenticator) Authenticate(conn net.Conn) (string, error) {
	tlsConn, ok := conn.(*tls.Conn)
	if !ok {
		return "", errors.New("not a TLS connection")
	}

	// Perform handshake to verify client certificate
	if err := tlsConn.Handshake(); err != nil {
		return "", err
	}

	// Get client certificates
 certs := tlsConn.ConnectionState().PeerCertificates
	if len(certs) == 0 {
		return "", errors.New("no client certificate provided")
	}

	// Extract client ID from certificate (using Common Name for simplicity)
	clientID := certs[0].Subject.CommonName

	// Verify client is trusted
	if !a.trustedClients[clientID] {
		return "", errors.New("client not trusted")
	}

	return clientID, nil
}