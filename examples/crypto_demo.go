package main

import (
	"flag"
	"fmt"
	"hydranews/identity"
	"log"
	"os"
	"strings"
	"time"
)

func main() {
	// Initialize logging
	log.SetOutput(os.Stdout)
	log.SetFlags(log.LstdFlags | log.Lshortfile)

	// Parse command-line flags
	mode := flag.String("mode", "all", "Demo mode: all, source, content, channel")
	flag.Parse()

	// Initialize crypto provider
	log.Println("Initializing Hydra crypto system...")
	crypto, err := identity.NewCryptoProvider()
	if err != nil {
		log.Fatalf("Failed to initialize crypto provider: %v", err)
	}

	// Run appropriate demo based on mode
	switch strings.ToLower(*mode) {
	case "all":
		runSourceVerificationDemo(crypto)
		runContentEntanglementDemo(crypto)
		runSecureChannelDemo(crypto)
	case "source":
		runSourceVerificationDemo(crypto)
	case "content":
		runContentEntanglementDemo(crypto)
	case "channel":
		runSecureChannelDemo(crypto)
	default:
		log.Fatalf("Unknown mode: %s", *mode)
	}
}

// Source verification demo
func runSourceVerificationDemo(crypto *identity.CryptoProvider) {
	log.Println("\n=== Source Verification Demo ===")

	// Create source verification with location
	sourceID := "source_123"
	latitude := 37.7749
	longitude := -122.4194
	countryCode := "US"
	regionCode := "CA"

	log.Printf("Creating verification for source %s at location %f, %f (%s, %s)...",
		sourceID, latitude, longitude, countryCode, regionCode)

	verification, err := crypto.CreateSourceVerification(
		sourceID, latitude, longitude, countryCode, regionCode,
	)
	if err != nil {
		log.Fatalf("Failed to create source verification: %v", err)
	}

	log.Printf("Source verification created: %x... (%d bytes)",
		verification[:16], len(verification))

	// Verify source location
	log.Println("Verifying source location...")
	valid, err := crypto.VerifySourceLocation(
		sourceID, verification, latitude, longitude, countryCode, regionCode,
	)
	if err != nil {
		log.Fatalf("Failed to verify source location: %v", err)
	}

	log.Printf("Source location verification: %v", valid)

	// Try with incorrect location
	log.Println("Trying with incorrect location...")
	wrongLatitude := latitude + 1.0 // 1 degree off
	valid, err = crypto.VerifySourceLocation(
		sourceID, verification, wrongLatitude, longitude, countryCode, regionCode,
	)
	if err != nil {
		log.Printf("Verification error with wrong location: %v", err)
	} else {
		log.Printf("Verification with wrong location: %v (expected false)", valid)
	}
}

// Content entanglement demo
func runContentEntanglementDemo(crypto *identity.CryptoProvider) {
	log.Println("\n=== Content Entanglement Demo ===")

	// Create content
	title := "Breaking News: New Technology Unveiled"
	content := "Scientists have announced a breakthrough in quantum cryptography..."
	author := "John Smith"
	metadata := map[string]string{
		"published_date": time.Now().Format(time.RFC3339),
		"category":       "Technology",
		"tags":           "quantum,security,research",
	}

	log.Printf("Creating entanglement for content: %s by %s...", title, author)

	// Create entanglement
	entanglement, err := crypto.CreateContentEntanglement(
		title, content, author, metadata,
	)
	if err != nil {
		log.Fatalf("Failed to create content entanglement: %v", err)
	}

	log.Printf("Content entanglement created: %x (%d bytes)",
		entanglement, len(entanglement))

	// Verify content
	log.Println("Verifying content entanglement...")
	valid, err := crypto.VerifyContentEntanglement(
		entanglement, title, content, author, metadata,
	)
	if err != nil {
		log.Fatalf("Failed to verify content entanglement: %v", err)
	}

	log.Printf("Content entanglement verification: %v", valid)

	// Try with modified content
	log.Println("Trying with modified content...")
	modifiedContent := content + " This text was added."
	valid, err = crypto.VerifyContentEntanglement(
		entanglement, title, modifiedContent, author, metadata,
	)
	if err != nil {
		log.Printf("Verification error with modified content: %v", err)
	} else {
		log.Printf("Verification with modified content: %v (expected false)", valid)
	}
}

// Secure channel demo
func runSecureChannelDemo(crypto *identity.CryptoProvider) {
	log.Println("\n=== Secure Channel Demo ===")

	// Establish a secure channel
	receiverID := "node_456"
	log.Printf("Establishing secure channel with receiver %s...", receiverID)

	channelID, senderKey, err := crypto.EstablishSecureChannel(receiverID)
	if err != nil {
		log.Fatalf("Failed to establish secure channel: %v", err)
	}

	log.Printf("Secure channel established: %s", channelID)
	log.Printf("Sender session key: %x... (%d bytes)",
		senderKey[:8], len(senderKey))

	// Join the secure channel
	log.Printf("Receiver joining secure channel %s...", channelID)
	receiverKey, err := crypto.JoinSecureChannel(channelID)
	if err != nil {
		log.Fatalf("Failed to join secure channel: %v", err)
	}

	log.Printf("Receiver session key: %x... (%d bytes)",
		receiverKey[:8], len(receiverKey))

	// Verify keys match
	keysMatch := compareByteSlices(senderKey, receiverKey)
	log.Printf("Keys match: %v", keysMatch)
	if !keysMatch {
		log.Printf("  Sender key: %x", senderKey)
		log.Printf("Receiver key: %x", receiverKey)
	}

	// Simulate secure communication
	if keysMatch {
		message := "This is a secret message"
		log.Printf("Sender encrypting message: %s", message)

		// Simple XOR encryption with key for demonstration
		encrypted := encryptDemo([]byte(message), senderKey)
		log.Printf("Encrypted message: %x", encrypted)

		// Decrypt the message
		log.Printf("Receiver decrypting message...")
		decrypted := encryptDemo(encrypted, receiverKey) // XOR is symmetric
		log.Printf("Decrypted message: %s", string(decrypted))
	}
}

// Helper functions

// compareByteSlices compares two byte slices
func compareByteSlices(a, b []byte) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

// encryptDemo is a simple XOR encryption for demo purposes
func encryptDemo(data, key []byte) []byte {
	result := make([]byte, len(data))
	for i := 0; i < len(data); i++ {
		result[i] = data[i] ^ key[i%len(key)]
	}
	return result
}
