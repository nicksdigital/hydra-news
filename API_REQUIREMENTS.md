# Hydra News API Requirements

## Overview

This document outlines the API requirements for the Hydra News system, providing decentralized news verification with source protection through cryptographic methods. The APIs outlined here cover all components of the system, with special emphasis on the GDELT integration which is nearly complete.

## Core API Categories

1. Content Submission and Verification
2. Source Protection and Authentication
3. Byzantine Consensus
4. GDELT Data Integration
5. Cryptographic Operations

## 1. Content Submission and Verification API

### Submit Content

```
POST /api/content/submit
```

**Request Body:**
```json
{
  "title": "string",
  "content": "string",
  "source": "string",
  "author": "string",
  "location": "string (optional)",
  "publish_date": "datetime (optional)"
}
```

**Response:**
```json
{
  "content_hash": "string",
  "submission_id": "string",
  "timestamp": "datetime",
  "verification_status": "string (pending)",
  "entanglement_hash": "string"
}
```

### Verify Content

```
POST /api/content/verify
```

**Request Body:**
```json
{
  "content_hash": "string",
  "reference_urls": ["string"]
}
```

**Response:**
```json
{
  "verification_id": "string",
  "content_hash": "string",
  "verification_score": "float",
  "verification_level": "integer",
  "verified_by": ["string"],
  "disputed": "boolean",
  "dispute_reasons": ["string"],
  "timestamp": "datetime",
  "references": [
    {
      "url": "string",
      "title": "string",
      "source": "string",
      "support_score": "float"
    }
  ]
}
```

### Get Content Status

```
GET /api/content/{content_hash}
```

**Response:**
```json
{
  "content_hash": "string",
  "title": "string",
  "source": "string", 
  "author": "string",
  "submission_timestamp": "datetime",
  "verification_status": "string",
  "verification_score": "float",
  "verification_level": "integer",
  "entanglement_status": {
    "hash": "string",
    "intact": "boolean",
    "timestamp": "datetime"
  },
  "verified_by": ["string"],
  "disputed": "boolean",
  "dispute_reasons": ["string"]
}
```

### Entangle Content

```
POST /api/content/entangle
```

**Request Body:**
```json
{
  "content_parts": ["string"]
}
```

**Response:**
```json
{
  "entanglement_hash": "string",
  "timestamp": "datetime"
}
```

### Verify Entanglement

```
POST /api/content/verify_entanglement
```

**Request Body:**
```json
{
  "entanglement_hash": "string",
  "content_parts": ["string"]
}
```

**Response:**
```json
{
  "intact": "boolean",
  "timestamp": "datetime",
  "tampered_sections": ["integer"] // Indices of tampered sections, if any
}
```

## 2. Source Protection and Authentication API

### Verify Source Identity

```
POST /api/source/verify
```

**Request Body:**
```json
{
  "proof_data": "string (base64 encoded)",
  "public_info": "string",
  "claimed_location": "string"
}
```

**Response:**
```json
{
  "source_verification": "boolean",
  "verification_timestamp": "datetime",
  "verification_level": "integer",
  "verified_attributes": ["string"],
  "location_verified": "boolean",
  "location_region": "string"
}
```

### Generate Source Credentials

```
POST /api/source/generate_credentials
```

**Request Body:**
```json
{
  "source_id": "string",
  "organization": "string",
  "region": "string",
  "role": "string"
}
```

**Response:**
```json
{
  "credential_id": "string",
  "public_key": "string",
  "encrypted_private_key": "string",
  "recovery_code": "string"
}
```

## 3. Byzantine Consensus API

### Submit Verification

```
POST /api/verification/submit
```

**Request Body:**
```json
{
  "node_id": "string",
  "content_hash": "string",
  "verification_level": "integer",
  "cross_references": ["string"],
  "disputed": "boolean",
  "dispute_reasons": ["string"]
}
```

**Response:**
```json
{
  "verification_id": "string",
  "acceptance_status": "string",
  "consensus_status": "string"
}
```

### Get Verification Status

```
GET /api/verification/status/{content_hash}
```

**Response:**
```json
{
  "content_hash": "string",
  "verification_level": "integer",
  "verified_by": ["string"],
  "verification_score": "float",
  "dispute_status": {
    "disputed": "boolean",
    "dispute_reasons": ["string"],
    "dispute_resolution_status": "string"
  },
  "consensus": {
    "reached": "boolean",
    "consensus_timestamp": "datetime",
    "participating_nodes": "integer",
    "byzantine_detected": "boolean"
  }
}
```

### Register Verification Node

```
POST /api/verification/register_node
```

**Request Body:**
```json
{
  "node_id": "string",
  "public_key": "string",
  "specialties": ["string"],
  "capacity": "integer"
}
```

**Response:**
```json
{
  "registration_status": "string",
  "network_position": "string",
  "authorization_token": "string"
}
```

## 4. GDELT Data Integration API

### Get GDELT Events

```
GET /api/gdelt/events
```

**Query Parameters:**
- `start_date`: Start date for filtering events (format: YYYY-MM-DD)
- `end_date`: End date for filtering events
- `entity_id`: Optional filter for specific entity
- `topic`: Optional filter for specific topic/theme
- `limit`: Maximum number of events to return (default: 100)
- `offset`: Pagination offset
- `significance`: Minimum significance score (0-1)

**Response:**
```json
{
  "events": [
    {
      "event_id": "string",
      "headline": "string",
      "description": "string",
      "source_url": "string",
      "event_date": "date",
      "significance_score": "float",
      "entities": [
        {
          "entity_id": "string",
          "name": "string",
          "type": "string",
          "confidence": "float"
        }
      ],
      "themes": ["string"],
      "sentiment_score": "float",
      "verification_status": "string"
    }
  ],
  "total_count": "integer",
  "pagination": {
    "limit": "integer",
    "offset": "integer",
    "has_more": "boolean"
  }
}
```

### Get GDELT Entities

```
GET /api/gdelt/entities
```

**Query Parameters:**
- `search`: Text search for entity name
- `type`: Entity type filter (PERSON, ORG, LOC, etc.)
- `min_mentions`: Minimum number of mentions
- `limit`: Maximum number of entities to return
- `offset`: Pagination offset

**Response:**
```json
{
  "entities": [
    {
      "entity_id": "string",
      "name": "string",
      "type": "string",
      "mention_count": "integer",
      "first_seen": "date",
      "last_seen": "date",
      "sentiment_trend": {
        "average": "float",
        "trend": "string",
        "history": [
          {
            "date": "date",
            "value": "float"
          }
        ]
      },
      "related_entities": [
        {
          "entity_id": "string",
          "name": "string",
          "type": "string",
          "relationship_strength": "float"
        }
      ]
    }
  ],
  "total_count": "integer",
  "pagination": {
    "limit": "integer",
    "offset": "integer",
    "has_more": "boolean"
  }
}
```

### Get GDELT Predictions

```
GET /api/gdelt/predictions
```

**Query Parameters:**
- `entity_id`: Entity to get predictions for
- `days`: Number of days to predict (default: 7)
- `models`: Comma-separated list of models to use (arima,prophet,etc.)

**Response:**
```json
{
  "entity": {
    "entity_id": "string",
    "name": "string",
    "type": "string"
  },
  "prediction_start_date": "date",
  "prediction_end_date": "date",
  "predictions": {
    "arima": {
      "2023-01-01": "float",
      "2023-01-02": "float"
    },
    "prophet": {
      "2023-01-01": "float",
      "2023-01-02": "float"
    },
    "ensemble": {
      "2023-01-01": "float",
      "2023-01-02": "float"
    }
  },
  "confidence_intervals": {
    "lower": {
      "2023-01-01": "float"
    },
    "upper": {
      "2023-01-01": "float"
    }
  },
  "predicted_events": [
    {
      "date": "date",
      "probability": "float",
      "significance": "float",
      "description": "string"
    }
  ]
}
```

### Verify Content with GDELT

```
POST /api/gdelt/verify
```

**Request Body:**
```json
{
  "content_hash": "string",
  "headline": "string",
  "content": "string",
  "source": "string",
  "publish_date": "date",
  "entities": [
    {
      "name": "string",
      "type": "string"
    }
  ]
}
```

**Response:**
```json
{
  "verification_id": "string",
  "verification_score": "float",
  "matched_events": [
    {
      "event_id": "string",
      "headline": "string",
      "match_score": "float",
      "source_url": "string"
    }
  ],
  "entity_verification": [
    {
      "entity_name": "string",
      "entity_type": "string",
      "verification_score": "float",
      "contradictions": [
        {
          "claim": "string", 
          "contradiction": "string",
          "source_url": "string"
        }
      ]
    }
  ],
  "fact_check_results": [
    {
      "claim": "string",
      "verdict": "string",
      "confidence": "float",
      "supporting_evidence": [
        {
          "source_url": "string",
          "excerpt": "string"
        }
      ]
    }
  ]
}
```

### Get GDELT Pipeline Status

```
GET /api/gdelt/pipeline/status
```

**Response:**
```json
{
  "status": "string",
  "last_fetch": "datetime",
  "last_analysis": "datetime",
  "articles_processed": "integer",
  "entities_extracted": "integer",
  "database_size_mb": "float",
  "next_scheduled_run": "datetime",
  "active_models": ["string"],
  "coverage_timespan": {
    "start": "date",
    "end": "date"
  },
  "pipeline_health": {
    "overall": "string",
    "fetch": "string",
    "process": "string",
    "analyze": "string",
    "predict": "string"
  }
}
```

## 5. Cryptographic Operations API

### Key Exchange

```
POST /api/crypto/exchange
```

**Request Body:**
```json
{
  "client_id": "string"
}
```

**Response:**
```json
{
  "session_id": "string",
  "public_key": "string",
  "algorithm": "string",
  "expiration": "datetime"
}
```

### Complete Key Exchange

```
POST /api/crypto/complete_exchange
```

**Request Body:**
```json
{
  "client_id": "string",
  "client_ciphertext": "string"
}
```

**Response:**
```json
{
  "exchange_complete": "boolean",
  "session_id": "string",
  "expiration": "datetime"
}
```

### Generate Zero-Knowledge Proof

```
POST /api/crypto/generate_zkp
```

**Request Body:**
```json
{
  "secret_data": "string (encrypted)",
  "public_data": "string",
  "proof_type": "string"
}
```

**Response:**
```json
{
  "proof_id": "string",
  "proof_data": "string",
  "verification_key": "string",
  "expiration": "datetime"
}
```

### Verify Zero-Knowledge Proof

```
POST /api/crypto/verify_zkp
```

**Request Body:**
```json
{
  "proof_data": "string",
  "verification_key": "string",
  "public_data": "string"
}
```

**Response:**
```json
{
  "verification_result": "boolean",
  "verification_timestamp": "datetime",
  "confidence": "float"
}
```

## Database Schema Requirements

### 1. Articles Table
```sql
CREATE TABLE articles (
    article_id VARCHAR(64) PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_domain VARCHAR(255) NOT NULL,
    publish_date TIMESTAMP,
    fetch_date TIMESTAMP NOT NULL,
    language VARCHAR(10),
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    verification_status VARCHAR(32) DEFAULT 'pending',
    verification_score FLOAT DEFAULT 0.0,
    entanglement_hash VARCHAR(64)
);
```

### 2. Entities Table
```sql
CREATE TABLE entities (
    entity_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(32) NOT NULL,
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    mention_count INTEGER DEFAULT 1,
    average_sentiment FLOAT,
    UNIQUE (name, type)
);
```

### 3. Article_Entities Table
```sql
CREATE TABLE article_entities (
    article_id VARCHAR(64) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    mention_offset INTEGER,
    mention_context TEXT,
    confidence FLOAT NOT NULL,
    sentiment FLOAT,
    PRIMARY KEY (article_id, entity_id, mention_offset),
    FOREIGN KEY (article_id) REFERENCES articles(article_id),
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);
```

### 4. Events Table
```sql
CREATE TABLE events (
    event_id VARCHAR(64) PRIMARY KEY,
    headline TEXT NOT NULL,
    description TEXT,
    event_date TIMESTAMP NOT NULL,
    significance_score FLOAT NOT NULL,
    verification_status VARCHAR(32) DEFAULT 'pending',
    theme VARCHAR(64)
);
```

### 5. Event_Articles Table
```sql
CREATE TABLE event_articles (
    event_id VARCHAR(64) NOT NULL,
    article_id VARCHAR(64) NOT NULL,
    relation_type VARCHAR(32) DEFAULT 'SUPPORTS',
    confidence FLOAT NOT NULL,
    PRIMARY KEY (event_id, article_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
);
```

### 6. Verifications Table
```sql
CREATE TABLE verifications (
    verification_id VARCHAR(64) PRIMARY KEY,
    content_hash VARCHAR(64) NOT NULL,
    node_id VARCHAR(64) NOT NULL,
    verification_level INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    disputed BOOLEAN DEFAULT FALSE,
    dispute_reasons JSON,
    FOREIGN KEY (content_hash) REFERENCES articles(content_hash)
);
```

### 7. Predictions Table
```sql
CREATE TABLE predictions (
    prediction_id VARCHAR(64) PRIMARY KEY,
    entity_id VARCHAR(64) NOT NULL,
    prediction_date TIMESTAMP NOT NULL,
    target_date TIMESTAMP NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    predicted_value FLOAT NOT NULL,
    confidence_lower FLOAT,
    confidence_upper FLOAT,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);
```

### 8. Sources Table
```sql
CREATE TABLE sources (
    source_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255),
    organization VARCHAR(255),
    public_key TEXT NOT NULL,
    region VARCHAR(255),
    reputation_score FLOAT DEFAULT 0.5,
    verification_level INTEGER DEFAULT 0,
    registration_date TIMESTAMP NOT NULL
);
```

## Integration Requirements

1. The Go API service must communicate with the Python GDELT processing service through a REST API or gRPC.
2. The C cryptographic libraries must be accessible to both Go and Python components through a unified interface.
3. The Byzantine consensus network must have access to verification results from the GDELT system.
4. All services should share a common authentication mechanism with post-quantum security.
5. Database access should be coordinated to prevent race conditions and ensure ACID compliance.

## Implementation Notes

1. All API endpoints should implement rate limiting to prevent DoS attacks.
2. Sensitive endpoints should require authentication with post-quantum cryptography.
3. All data in transit must be encrypted with post-quantum algorithms.
4. Error responses should follow a consistent format with appropriate HTTP status codes.
5. All APIs should include comprehensive logging with tamper-evident mechanisms.
6. Documentation should be generated from these API definitions using OpenAPI/Swagger.
