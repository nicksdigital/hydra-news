/**
 * TypeScript interface definitions for Hydra News content structures
 */

// Entity extracted from content
export interface ContentEntity {
  name: string;
  type: string;
  context: string;
  confidence: number;
  position: {
    start: number;
    end: number;
  };
}

// Factual claim extracted from content
export interface ContentClaim {
  id: string;
  text: string;
  entities: ContentEntity[];
  source_text: string;
  confidence: number;
  type: string;
  position: {
    start: number;
    end: number;
  };
}

// Cross-reference information
export interface CrossReference {
  url: string;
  title: string;
  source: string;
  content_hash: string;
  support_score?: number;
  dispute_score?: number;
}

// Verification status for a claim
export interface VerifiedClaim {
  claim_id: string;
  text: string;
  score: number;
  supporting_references?: CrossReference[];
  disputed_by?: CrossReference[];
}

// Verification result from the consensus network
export interface VerificationResult {
  content_hash: string;
  verification_score: number;
  verified_claims: VerifiedClaim[];
  disputed_claims: VerifiedClaim[];
  references: CrossReference[];
  timestamp: string;
}

// News content item
export interface NewsContent {
  title: string;
  content: string;
  source: string;
  url?: string;
  author?: string;
  publish_date?: string;
  content_hash: string;
  entities?: ContentEntity[];
  claims?: ContentClaim[];
  entanglement_hash?: string;
  processed: boolean;
  verification_result?: VerificationResult;
  verification_level?: number;
}

// Verification levels
export enum VerificationLevel {
  None = 0,
  Minimal = 1,
  Standard = 2,
  High = 3,
  Maximum = 4
}

// Verification level details
export interface VerificationLevelInfo {
  level: VerificationLevel;
  name: string;
  color: string;
  description: string;
}

export const verificationLevels: VerificationLevelInfo[] = [
  { 
    level: VerificationLevel.None, 
    name: 'None', 
    color: '#e74c3c', 
    description: 'This content has not been verified' 
  },
  { 
    level: VerificationLevel.Minimal, 
    name: 'Minimal', 
    color: '#e67e22', 
    description: 'Basic verification with limited cross-referencing' 
  },
  { 
    level: VerificationLevel.Standard, 
    name: 'Standard', 
    color: '#f1c40f', 
    description: 'Standard verification with multiple sources' 
  },
  { 
    level: VerificationLevel.High, 
    name: 'High', 
    color: '#2ecc71', 
    description: 'High level of verification with extensive cross-referencing' 
  },
  { 
    level: VerificationLevel.Maximum, 
    name: 'Maximum', 
    color: '#27ae60', 
    description: 'Maximum verification with cryptographic proof and multiple trusted sources' 
  }
];
