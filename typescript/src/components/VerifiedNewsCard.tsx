import React, { useState, useEffect } from 'react';
import './VerifiedNewsCard.css';

// Types for content entities and claims
interface ContentEntity {
  name: string;
  type: string;
  context: string;
  confidence: number;
  position: {
    start: number;
    end: number;
  };
}

interface ContentClaim {
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

// Verification level details
interface VerificationLevel {
  level: number;
  name: string;
  color: string;
  description: string;
}

const verificationLevels: VerificationLevel[] = [
  { 
    level: 0, 
    name: 'None', 
    color: '#e74c3c', 
    description: 'This content has not been verified' 
  },
  { 
    level: 1, 
    name: 'Minimal', 
    color: '#e67e22', 
    description: 'Basic verification with limited cross-referencing' 
  },
  { 
    level: 2, 
    name: 'Standard', 
    color: '#f1c40f', 
    description: 'Standard verification with multiple sources' 
  },
  { 
    level: 3, 
    name: 'High', 
    color: '#2ecc71', 
    description: 'High level of verification with extensive cross-referencing' 
  },
  { 
    level: 4, 
    name: 'Maximum', 
    color: '#27ae60', 
    description: 'Maximum verification with cryptographic proof and multiple trusted sources' 
  }
];

// Props for the NewsCard component
interface VerifiedNewsCardProps {
  title: string;
  content: string;
  source: string;
  author?: string;
  publishDate?: string;
  verificationLevel: number;
  trustScore: number;
  contentHash: string;
  entities?: ContentEntity[];
  claims?: ContentClaim[];
  entanglementHash?: string;
  onViewDetails?: () => void;
}

// Formats a hash for display by truncating and adding ellipsis
const formatHash = (hash: string): string => {
  if (!hash) return '';
  return `${hash.substring(0, 8)}...${hash.substring(hash.length - 8)}`;
};

// Component for highlighting entities in the text
const HighlightedText: React.FC<{ 
  text: string; 
  entities: ContentEntity[]; 
  showHighlights: boolean;
}> = ({ text, entities, showHighlights }) => {
  if (!showHighlights || !entities || entities.length === 0) {
    return <p>{text}</p>;
  }

  // Sort entities by position
  const sortedEntities = [...entities].sort((a, b) => a.position.start - b.position.start);
  
  // Create segments with highlighted parts
  const segments: JSX.Element[] = [];
  let lastEnd = 0;
  
  sortedEntities.forEach((entity, index) => {
    // Add text before the entity
    if (entity.position.start > lastEnd) {
      segments.push(
        <span key={`text-${index}`}>
          {text.substring(lastEnd, entity.position.start)}
        </span>
      );
    }
    
    // Add the highlighted entity
    segments.push(
      <span 
        key={`entity-${index}`} 
        className={`entity entity-${entity.type.toLowerCase()}`}
        title={`${entity.type}: ${entity.name} (Confidence: ${(entity.confidence * 100).toFixed(0)}%)`}
      >
        {text.substring(entity.position.start, entity.position.end)}
      </span>
    );
    
    lastEnd = entity.position.end;
  });
  
  // Add any remaining text after the last entity
  if (lastEnd < text.length) {
    segments.push(
      <span key="text-end">
        {text.substring(lastEnd)}
      </span>
    );
  }
  
  return <p>{segments}</p>;
};

// Main VerifiedNewsCard component
const VerifiedNewsCard: React.FC<VerifiedNewsCardProps> = ({ 
  title,
  content,
  source,
  author,
  publishDate,
  verificationLevel,
  trustScore,
  contentHash,
  entities = [],
  claims = [],
  entanglementHash,
  onViewDetails
}) => {
  const [showHighlights, setShowHighlights] = useState<boolean>(true);
  const [showClaims, setShowClaims] = useState<boolean>(false);
  const [expandedClaimId, setExpandedClaimId] = useState<string | null>(null);
  
  // Get verification level details
  const level = verificationLevels.find(l => l.level === verificationLevel) || verificationLevels[0];
  
  // Format trust score as percentage
  const formattedTrustScore = `${(trustScore * 100).toFixed(0)}%`;
  
  // Toggle expanded claim
  const toggleClaim = (claimId: string) => {
    if (expandedClaimId === claimId) {
      setExpandedClaimId(null);
    } else {
      setExpandedClaimId(claimId);
    }
  };
  
  return (
    <div className="verified-news-card">
      {/* Header with verification level */}
      <div className="card-header" style={{ backgroundColor: level.color }}>
        <div className="verification-badge">
          <span className="verification-level">{level.name}</span>
          <span className="verification-score">{formattedTrustScore}</span>
        </div>
      </div>
      
      {/* Content area */}
      <div className="card-content">
        <h2 className="card-title">{title}</h2>
        
        <div className="card-metadata">
          <span className="source">{source}</span>
          {author && <span className="author">By {author}</span>}
          {publishDate && <span className="date">{publishDate}</span>}
        </div>
        
        <div className="content-area">
          <HighlightedText 
            text={content} 
            entities={entities} 
            showHighlights={showHighlights} 
          />
        </div>
        
        {/* Controls for entity highlighting and claims */}
        <div className="content-controls">
          <label>
            <input 
              type="checkbox" 
              checked={showHighlights} 
              onChange={() => setShowHighlights(!showHighlights)} 
            />
            Show Entity Highlights
          </label>
          
          <label>
            <input 
              type="checkbox" 
              checked={showClaims} 
              onChange={() => setShowClaims(!showClaims)} 
            />
            Show Claims Analysis
          </label>
        </div>
        
        {/* Claims section */}
        {showClaims && claims.length > 0 && (
          <div className="claims-section">
            <h3>Claims Analysis</h3>
            <ul className="claims-list">
              {claims.map(claim => (
                <li key={claim.id} className="claim-item">
                  <div 
                    className="claim-header" 
                    onClick={() => toggleClaim(claim.id)}
                  >
                    <span className="claim-text">{claim.text}</span>
                    <span className={`claim-confidence confidence-${Math.floor(claim.confidence * 5)}`}>
                      {(claim.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  
                  {expandedClaimId === claim.id && (
                    <div className="claim-details">
                      <h4>Associated Entities:</h4>
                      <ul className="claim-entities">
                        {claim.entities.map((entity, idx) => (
                          <li key={idx} className={`entity-item entity-${entity.type.toLowerCase()}`}>
                            <strong>{entity.name}</strong> ({entity.type})
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      {/* Footer with verification details */}
      <div className="card-footer">
        <div className="hash-info">
          <span className="hash-label">Content Hash:</span>
          <span className="hash-value">{formatHash(contentHash)}</span>
          
          {entanglementHash && (
            <>
              <span className="hash-label">Entanglement:</span>
              <span className="hash-value">{formatHash(entanglementHash)}</span>
            </>
          )}
        </div>
        
        <button 
          className="details-button" 
          onClick={onViewDetails}
        >
          View Verification Details
        </button>
      </div>
    </div>
  );
};

export default VerifiedNewsCard;
