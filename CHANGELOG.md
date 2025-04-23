# Hydra News Changelog

## [Unreleased]

### Added
- Created comprehensive memory.json knowledge base documenting system architecture and components
- Added anonymity tests in C to verify core cryptographic primitives
- Created testing documentation in tests/ANONYMITY_TESTING.md

### Fixed
- Enhanced probabilistic encoding algorithm in quantum_zkp.c to use true randomness
- Fixed issue where probabilistic encoding produced identical outputs for the same input
- Added random nonce generation using RAND_bytes to ensure encoding varies across multiple calls

### Changed
- Updated test suite to verify proper randomness in probabilistic encoding
- Improved Makefile to properly link against OpenSSL crypto library

## [0.1.0] - Initial Version

### Added
- Implemented core quantum-inspired zero-knowledge proof system
- Created logical entanglement mechanism for tamper-evident content
- Developed Byzantine Fault Tolerance consensus mechanism
- Implemented privacy-preserving geolocation verification
- Developed content processing and natural language analysis components
