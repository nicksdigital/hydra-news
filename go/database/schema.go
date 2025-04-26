package database

// Database schema definitions for Hydra News system

// Schema versioning information
const (
	SchemaVersion = "1.0.0"
)

// Database tables
const (
	// News content and verification
	TableNewsContent   = "news_content"
	TableVerification  = "verification"
	TableEntities      = "entities"
	TableClaims        = "claims"
	TableReferences    = "references"
	
	// User and source management
	TableUsers         = "users"
	TableSources       = "sources"
	TableCredentials   = "credentials"
	
	// System and consensus
	TableNodes         = "nodes"
	TableConsensusLogs = "consensus_logs"
	TableSystemEvents  = "system_events"
)

// Content table schema
var ContentTableSchema = `
CREATE TABLE IF NOT EXISTS news_content (
    content_hash      TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    content           TEXT NOT NULL,
    source            TEXT NOT NULL,
    author            TEXT,
    publish_date      TIMESTAMP,
    url               TEXT,
    entanglement_hash TEXT NOT NULL,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    submission_ip     TEXT,
    submitter_id      TEXT,
    is_verified       BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_content_source ON news_content(source);
CREATE INDEX IF NOT EXISTS idx_content_author ON news_content(author);
CREATE INDEX IF NOT EXISTS idx_content_created ON news_content(created_at);
`

// Verification table schema
var VerificationTableSchema = `
CREATE TABLE IF NOT EXISTS verification (
    verification_id     TEXT PRIMARY KEY,
    content_hash        TEXT NOT NULL,
    verification_score  REAL NOT NULL DEFAULT 0.0,
    verification_time   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verifier_node_id    TEXT NOT NULL,
    consensus_round_id  TEXT,
    verification_status TEXT NOT NULL,
    FOREIGN KEY (content_hash) REFERENCES news_content(content_hash)
);

CREATE INDEX IF NOT EXISTS idx_verification_content ON verification(content_hash);
CREATE INDEX IF NOT EXISTS idx_verification_score ON verification(verification_score);
CREATE INDEX IF NOT EXISTS idx_verification_time ON verification(verification_time);
`

// Entities table schema
var EntitiesTableSchema = `
CREATE TABLE IF NOT EXISTS entities (
    entity_id       TEXT PRIMARY KEY,
    content_hash    TEXT NOT NULL,
    entity_name     TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    confidence      REAL NOT NULL,
    context         TEXT,
    position_start  INTEGER,
    position_end    INTEGER,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_hash) REFERENCES news_content(content_hash)
);

CREATE INDEX IF NOT EXISTS idx_entity_content ON entities(content_hash);
CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(entity_name);
CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type);
`

// Claims table schema
var ClaimsTableSchema = `
CREATE TABLE IF NOT EXISTS claims (
    claim_id        TEXT PRIMARY KEY,
    content_hash    TEXT NOT NULL,
    claim_text      TEXT NOT NULL,
    source_text     TEXT,
    confidence      REAL NOT NULL,
    claim_type      TEXT NOT NULL,
    position_start  INTEGER,
    position_end    INTEGER,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_hash) REFERENCES news_content(content_hash)
);

CREATE INDEX IF NOT EXISTS idx_claim_content ON claims(content_hash);
`

// Claim-Entity relationship table schema
var ClaimEntityTableSchema = `
CREATE TABLE IF NOT EXISTS claim_entity (
    claim_id        TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    relationship    TEXT NOT NULL,
    PRIMARY KEY (claim_id, entity_id),
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id),
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);
`

// References table schema
var ReferencesTableSchema = `
CREATE TABLE IF NOT EXISTS references (
    reference_id      TEXT PRIMARY KEY,
    verification_id   TEXT NOT NULL,
    content_hash      TEXT NOT NULL,
    reference_url     TEXT NOT NULL,
    reference_title   TEXT,
    reference_source  TEXT,
    reference_hash    TEXT,
    support_score     REAL,
    dispute_score     REAL,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (verification_id) REFERENCES verification(verification_id),
    FOREIGN KEY (content_hash) REFERENCES news_content(content_hash)
);

CREATE INDEX IF NOT EXISTS idx_reference_verification ON references(verification_id);
CREATE INDEX IF NOT EXISTS idx_reference_content ON references(content_hash);
`

// Users table schema
var UsersTableSchema = `
CREATE TABLE IF NOT EXISTS users (
    user_id         TEXT PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    email           TEXT UNIQUE,
    role            TEXT NOT NULL,
    display_name    TEXT,
    reputation      REAL NOT NULL DEFAULT 0.0,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login      TIMESTAMP,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    public_key      TEXT
);

CREATE INDEX IF NOT EXISTS idx_user_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
`

// Sources table schema
var SourcesTableSchema = `
CREATE TABLE IF NOT EXISTS sources (
    source_id       TEXT PRIMARY KEY,
    source_name     TEXT NOT NULL,
    domain          TEXT,
    trust_score     REAL NOT NULL DEFAULT 0.5,
    verified        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_source_name ON sources(source_name);
CREATE INDEX IF NOT EXISTS idx_source_domain ON sources(domain);
CREATE INDEX IF NOT EXISTS idx_source_trust ON sources(trust_score);
`

// Credentials table schema
var CredentialsTableSchema = `
CREATE TABLE IF NOT EXISTS credentials (
    credential_id   TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    qzkp_proof      TEXT NOT NULL,
    issued_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP NOT NULL,
    credential_type TEXT NOT NULL,
    is_revoked      BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_credential_user ON credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_credential_expires ON credentials(expires_at);
`

// Nodes table schema
var NodesTableSchema = `
CREATE TABLE IF NOT EXISTS nodes (
    node_id         TEXT PRIMARY KEY,
    node_address    TEXT NOT NULL,
    qzkp_address    TEXT NOT NULL,
    public_key      TEXT NOT NULL,
    reputation      REAL NOT NULL DEFAULT 0.5,
    first_seen      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          TEXT NOT NULL,
    geo_region      TEXT,
    node_version    TEXT,
    is_bootstrap    BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_node_address ON nodes(node_address);
CREATE INDEX IF NOT EXISTS idx_node_qzkp ON nodes(qzkp_address);
CREATE INDEX IF NOT EXISTS idx_node_reputation ON nodes(reputation);
CREATE INDEX IF NOT EXISTS idx_node_last_seen ON nodes(last_seen);
`

// Consensus logs table schema
var ConsensusLogsTableSchema = `
CREATE TABLE IF NOT EXISTS consensus_logs (
    log_id          TEXT PRIMARY KEY,
    round_id        TEXT NOT NULL,
    node_id         TEXT NOT NULL,
    log_time        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action          TEXT NOT NULL,
    status          TEXT NOT NULL,
    details         TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id)
);

CREATE INDEX IF NOT EXISTS idx_consensus_round ON consensus_logs(round_id);
CREATE INDEX IF NOT EXISTS idx_consensus_node ON consensus_logs(node_id);
CREATE INDEX IF NOT EXISTS idx_consensus_time ON consensus_logs(log_time);
`

// System events table schema
var SystemEventsTableSchema = `
CREATE TABLE IF NOT EXISTS system_events (
    event_id        TEXT PRIMARY KEY,
    event_type      TEXT NOT NULL,
    event_time      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    severity        TEXT NOT NULL,
    details         TEXT,
    node_id         TEXT
);

CREATE INDEX IF NOT EXISTS idx_event_type ON system_events(event_type);
CREATE INDEX IF NOT EXISTS idx_event_time ON system_events(event_time);
CREATE INDEX IF NOT EXISTS idx_event_severity ON system_events(severity);
`

// GetAllSchemas returns all table schemas
func GetAllSchemas() []string {
	return []string{
		ContentTableSchema,
		VerificationTableSchema,
		EntitiesTableSchema,
		ClaimsTableSchema,
		ClaimEntityTableSchema,
		ReferencesTableSchema,
		UsersTableSchema,
		SourcesTableSchema,
		CredentialsTableSchema,
		NodesTableSchema,
		ConsensusLogsTableSchema,
		SystemEventsTableSchema,
	}
}
