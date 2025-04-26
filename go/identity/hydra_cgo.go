// Package identity implements CGO bindings to the Hydra cryptographic library
package identity

/*
#cgo CFLAGS: -I../../c/include
#cgo LDFLAGS: -L../../c/lib -lhydracrypto -lcrypto -lssl

#include "hydra_cgo.h"
#include <stdlib.h>
*/
import "C"
import (
	"errors"
	"fmt"
	"runtime"
	"unsafe"
)

// Initialize the Hydra crypto system
func init() {
	result := C.hydra_init()
	if result != 0 {
		fmt.Printf("Warning: Failed to initialize Hydra crypto system: error code %d\n", result)
		fmt.Printf("Using fallback implementation\n")
		return
	}
	
	// Register cleanup function to run on finalization
	runtime.SetFinalizer(&struct{}{}, func(_ interface{}) {
		C.hydra_cleanup()
	})
}

// HydraCrypto provides access to the C cryptographic primitives
type HydraCrypto struct{}

// NewHydraCrypto creates a new Hydra crypto instance
func NewHydraCrypto() *HydraCrypto {
	return &HydraCrypto{}
}

// CreateGeolocationCommitment creates a commitment to geolocation data
func (h *HydraCrypto) CreateGeolocationCommitment(
	latitude, longitude float64,
	countryCode, regionCode string,
) ([]byte, error) {
	// Convert Go strings to C strings
	cCountryCode := C.CString(countryCode)
	defer C.free(unsafe.Pointer(cCountryCode))
	
	cRegionCode := C.CString(regionCode)
	defer C.free(unsafe.Pointer(cRegionCode))
	
	// Create output buffer
	commitment := make([]byte, 32)
	
	// Call C function
	result := C.hydra_create_geolocation_commitment(
		C.double(latitude),
		C.double(longitude),
		cCountryCode,
		cRegionCode,
		(*C.uint8_t)(unsafe.Pointer(&commitment[0])),
	)
	
	if result != 0 {
		return nil, fmt.Errorf("failed to create geolocation commitment: error code %d", result)
	}
	
	return commitment, nil
}

// GenerateKyberKey generates a new Kyber key pair
func (h *HydraCrypto) GenerateKyberKey() (publicKey, privateKey []byte, err error) {
	// Create output buffers
	publicKey = make([]byte, C.HYDRA_KYBER_PUBLIC_KEY_BYTES)
	privateKey = make([]byte, C.HYDRA_KYBER_SECRET_KEY_BYTES)
	
	// Call C function
	result := C.hydra_generate_kyber_key(
		(*C.uint8_t)(unsafe.Pointer(&publicKey[0])),
		(*C.uint8_t)(unsafe.Pointer(&privateKey[0])),
	)
	
	if result != 0 {
		return nil, nil, fmt.Errorf("failed to generate Kyber key: error code %d", result)
	}
	
	return publicKey, privateKey, nil
}

// GenerateFalconKey generates a new Falcon key pair
func (h *HydraCrypto) GenerateFalconKey() (publicKey, privateKey []byte, err error) {
	// Create output buffers
	publicKey = make([]byte, C.HYDRA_FALCON_PUBLIC_KEY_BYTES)
	privateKey = make([]byte, C.HYDRA_FALCON_SECRET_KEY_BYTES)
	
	// Call C function
	result := C.hydra_generate_falcon_key(
		(*C.uint8_t)(unsafe.Pointer(&publicKey[0])),
		(*C.uint8_t)(unsafe.Pointer(&privateKey[0])),
	)
	
	if result != 0 {
		return nil, nil, fmt.Errorf("failed to generate Falcon key: error code %d", result)
	}
	
	return publicKey, privateKey, nil
}

// SignMessage signs a message using a Falcon key
func (h *HydraCrypto) SignMessage(message, privateKey []byte) ([]byte, error) {
	if len(message) == 0 {
		return nil, errors.New("message cannot be empty")
	}
	
	// Create output buffer
	signature := make([]byte, C.HYDRA_FALCON_SIGNATURE_MAX_BYTES)
	var signatureLen C.size_t = C.HYDRA_FALCON_SIGNATURE_MAX_BYTES
	
	// Call C function
	result := C.hydra_sign_message(
		(*C.uint8_t)(unsafe.Pointer(&message[0])),
		C.size_t(len(message)),
		(*C.uint8_t)(unsafe.Pointer(&privateKey[0])),
		(*C.uint8_t)(unsafe.Pointer(&signature[0])),
		&signatureLen,
	)
	
	if result != 0 {
		return nil, fmt.Errorf("failed to sign message: error code %d", result)
	}
	
	// Return only the actual signature bytes
	return signature[:signatureLen], nil
}

// VerifySignature verifies a message signature
func (h *HydraCrypto) VerifySignature(message, signature, publicKey []byte) (bool, error) {
	if len(message) == 0 {
		return false, errors.New("message cannot be empty")
	}
	
	if len(signature) == 0 {
		return false, errors.New("signature cannot be empty")
	}
	
	// Call C function
	result := C.hydra_verify_signature(
		(*C.uint8_t)(unsafe.Pointer(&message[0])),
		C.size_t(len(message)),
		(*C.uint8_t)(unsafe.Pointer(&signature[0])),
		C.size_t(len(signature)),
		(*C.uint8_t)(unsafe.Pointer(&publicKey[0])),
	)
	
	// C API returns 1 for valid, 0 for invalid, negative for errors
	if result < 0 {
		return false, fmt.Errorf("signature verification error: code %d", result)
	}
	
	return result == 1, nil
}

// EstablishSharedKey creates a shared key using Kyber
func (h *HydraCrypto) EstablishSharedKey(recipientPublicKey []byte) ([]byte, []byte, error) {
	// Create output buffers
	sharedSecret := make([]byte, C.HYDRA_KYBER_SHARED_SECRET_BYTES)
	ciphertext := make([]byte, C.HYDRA_KYBER_CIPHERTEXT_BYTES)
	
	// Call C function
	result := C.hydra_establish_shared_key(
		(*C.uint8_t)(unsafe.Pointer(&recipientPublicKey[0])),
		(*C.uint8_t)(unsafe.Pointer(&sharedSecret[0])),
		(*C.uint8_t)(unsafe.Pointer(&ciphertext[0])),
	)
	
	if result != 0 {
		return nil, nil, fmt.Errorf("failed to establish shared key: error code %d", result)
	}
	
	return sharedSecret, ciphertext, nil
}

// ReceiveSharedKey decapsulates a shared key
func (h *HydraCrypto) ReceiveSharedKey(ciphertext, recipientPrivateKey []byte) ([]byte, error) {
	// Create output buffer
	sharedSecret := make([]byte, C.HYDRA_KYBER_SHARED_SECRET_BYTES)
	
	// Call C function
	result := C.hydra_receive_shared_key(
		(*C.uint8_t)(unsafe.Pointer(&recipientPrivateKey[0])),
		(*C.uint8_t)(unsafe.Pointer(&ciphertext[0])),
		(*C.uint8_t)(unsafe.Pointer(&sharedSecret[0])),
	)
	
	if result != 0 {
		return nil, fmt.Errorf("failed to receive shared key: error code %d", result)
	}
	
	return sharedSecret, nil
}

// GenerateZKProof generates a zero-knowledge proof
func (h *HydraCrypto) GenerateZKProof(secret, publicInput []byte) ([]byte, error) {
	if len(secret) == 0 {
		return nil, errors.New("secret cannot be empty")
	}
	
	// Initial buffer size - we might need to resize
	proofLen := C.size_t(1024)
	proof := make([]byte, proofLen)
	
	// Call C function
	result := C.hydra_generate_zkproof(
		(*C.uint8_t)(unsafe.Pointer(&secret[0])),
		C.size_t(len(secret)),
		(*C.uint8_t)(unsafe.Pointer(&publicInput[0])),
		C.size_t(len(publicInput)),
		(*C.uint8_t)(unsafe.Pointer(&proof[0])),
		&proofLen,
	)
	
	if result == -3 {
		// Buffer too small, resize and try again
		proof = make([]byte, proofLen)
		
		result = C.hydra_generate_zkproof(
			(*C.uint8_t)(unsafe.Pointer(&secret[0])),
			C.size_t(len(secret)),
			(*C.uint8_t)(unsafe.Pointer(&publicInput[0])),
			C.size_t(len(publicInput)),
			(*C.uint8_t)(unsafe.Pointer(&proof[0])),
			&proofLen,
		)
	}
	
	if result != 0 {
		return nil, fmt.Errorf("failed to generate ZK proof: error code %d", result)
	}
	
	// Return only the actual proof bytes
	return proof[:proofLen], nil
}

// VerifyZKProof verifies a zero-knowledge proof
func (h *HydraCrypto) VerifyZKProof(proofData, publicInput []byte) (bool, error) {
	if len(proofData) == 0 {
		return false, errors.New("proof cannot be empty")
	}
	
	// Call C function
	result := C.hydra_verify_zkproof(
		(*C.uint8_t)(unsafe.Pointer(&proofData[0])),
		C.size_t(len(proofData)),
		(*C.uint8_t)(unsafe.Pointer(&publicInput[0])),
		C.size_t(len(publicInput)),
	)
	
	// C API returns 1 for valid, 0 for invalid, negative for errors
	if result < 0 {
		return false, fmt.Errorf("proof verification error: code %d", result)
	}
	
	return result == 1, nil
}

// CreateEntanglement creates an entanglement hash
func (h *HydraCrypto) CreateEntanglement(dataItems [][]byte) ([]byte, error) {
	if len(dataItems) == 0 {
		return nil, errors.New("no data items provided")
	}
	
	// Create arrays for C parameters
	cDataItems := make([]unsafe.Pointer, len(dataItems))
	cDataLengths := make([]C.size_t, len(dataItems))
	
	for i, item := range dataItems {
		if len(item) == 0 {
			return nil, fmt.Errorf("data item %d is empty", i)
		}
		cDataItems[i] = unsafe.Pointer(&item[0])
		cDataLengths[i] = C.size_t(len(item))
	}
	
	// Create output buffer
	entanglementHash := make([]byte, 32)
	
	// Call C function
	result := C.hydra_create_entanglement(
		(**C.uint8_t)(unsafe.Pointer(&cDataItems[0])),
		(*C.size_t)(unsafe.Pointer(&cDataLengths[0])),
		C.size_t(len(dataItems)),
		(*C.uint8_t)(unsafe.Pointer(&entanglementHash[0])),
	)
	
	if result != 0 {
		return nil, fmt.Errorf("failed to create entanglement: error code %d", result)
	}
	
	return entanglementHash, nil
}

// VerifyEntanglement verifies an entanglement hash
func (h *HydraCrypto) VerifyEntanglement(dataItems [][]byte, entanglementHash []byte) (bool, error) {
	if len(dataItems) == 0 {
		return false, errors.New("no data items provided")
	}
	
	if len(entanglementHash) != 32 {
		return false, fmt.Errorf("invalid entanglement hash length: expected 32, got %d", 
			len(entanglementHash))
	}
	
	// Create arrays for C parameters
	cDataItems := make([]unsafe.Pointer, len(dataItems))
	cDataLengths := make([]C.size_t, len(dataItems))
	
	for i, item := range dataItems {
		if len(item) == 0 {
			return false, fmt.Errorf("data item %d is empty", i)
		}
		cDataItems[i] = unsafe.Pointer(&item[0])
		cDataLengths[i] = C.size_t(len(item))
	}
	
	// Call C function
	result := C.hydra_verify_entanglement(
		(**C.uint8_t)(unsafe.Pointer(&cDataItems[0])),
		(*C.size_t)(unsafe.Pointer(&cDataLengths[0])),
		C.size_t(len(dataItems)),
		(*C.uint8_t)(unsafe.Pointer(&entanglementHash[0])),
	)
	
	// C API returns 1 for valid, 0 for invalid, negative for errors
	if result < 0 {
		return false, fmt.Errorf("entanglement verification error: code %d", result)
	}
	
	return result == 1, nil
}
