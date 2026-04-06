package config

import (
	"crypto/tls"
	"crypto/x509"
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Port           int             `yaml:"port"`
	HomeID         string          `yaml:"home_id"`
	ServerCert     tls.Certificate `yaml:"-"`
	ClientCAs      *x509.CertPool  `yaml:"-"`
	TrustedClients []string        `yaml:"trusted_clients"`
}

func Load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}

	// Load server certificate and key
	cert, err := tls.LoadX509KeyPair("certs/server.crt", "certs/server.key")
	if err != nil {
		return nil, err
	}
	cfg.ServerCert = cert

	// Load client CA pool
	caCert, err := os.ReadFile("certs/ca.crt")
	if err != nil {
		return nil, err
	}
	caPool := x509.NewCertPool()
	caPool.AppendCertsFromPEM(caCert)
	cfg.ClientCAs = caPool

	return &cfg, nil
}