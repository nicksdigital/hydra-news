/**
 * Types for article, entities, claims, and verification.
 */

/**
 * Entity extracted from content
 */
export interface Entity {
  name: string;
  type: string;
  context?: string;
  confidence: number;
  position: {
    start: number;
    end: number;
  };
}

/**
 * Claim extracted from content
 */
export interface Claim {
  id: string;
  text: string;
  entities: {
    name: string;
    type: string;
  }[];
  source_text: string;
  confidence: number;
  type: string;
  position: {
    start: number;
    end: number;
  };
}

/**
 * Multimedia content (image, video)
 */
export interface Multimedia {
  content_type: string;
  url: string;
  content_hash: string;
  caption?: string;
  metadata?: Record<string, any>;
  entities?: Entity[];
}

/**
 * Reference source for verification
 */
export interface Reference {
  url: string;
  title: string;
  source: string;
  content_hash: string;
  support_score?: number;
  dispute_score?: number;
  trust_score?: number;
}

/**
 * Verified claim with supporting references
 */
export interface VerifiedClaim {
  claim_id: string;
  text: string;
  score: number;
  supporting_references: Reference[];
}

/**
 * Disputed claim with disputing references
 */
export interface DisputedClaim {
  claim_id: string;
  text: string;
  score: number;
  disputed_by: Reference[];
}

/**
 * Verification result for an article
 */
export interface Verification {
  content_hash: string;
  verification_score: number;
  verified_claims: VerifiedClaim[];
  disputed_claims: DisputedClaim[];
  references: Reference[];
  timestamp: string;
  trusted_source_boost?: number;
}

/**
 * Complete article with content, metadata, and processing
 */
export interface Article {
  id: string;
  title: string;
  content: string;
  source: string;
  url?: string;
  author?: string;
  publish_date?: string;
  content_hash: string;
  entanglement_hash?: string;
  entities?: Entity[];
  claims?: Claim[];
  multimedia?: Multimedia[];
  keywords?: string[];
  summary?: string;
  topic_classification?: Record<string, number>;
  verification?: Verification;
  created_at: string;
  updated_at: string;
}

/**
 * Article list item (simplified article for listings)
 */
export interface ArticleListItem {
  id: string;
  title: string;
  source: string;
  author?: string;
  publish_date?: string;
  content_hash: string;
  verification_score?: number;
  summary?: string;
  created_at: string;
}
