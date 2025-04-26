import React, { useState } from 'react';
import './ClaimVerification.css';
import VerificationScore from './VerificationScore';
import { Article, VerifiedClaim, DisputedClaim } from '../../types/article';

interface ClaimVerificationProps {
  claim: VerifiedClaim | DisputedClaim;
  isVerified: boolean;
  article: Article;
}

/**
 * Component to display a verified or disputed claim
 */
const ClaimVerification: React.FC<ClaimVerificationProps> = ({
  claim,
  isVerified,
  article,
}) => {
  const [expanded, setExpanded] = useState(false);
  
  // Find the original claim in the article if possible
  const findOriginalClaim = () => {
    if (!article.claims) return null;
    return article.claims.find(c => c.id === claim.claim_id);
  };
  
  const originalClaim = findOriginalClaim();
  
  // Helper function to render source references
  const renderSources = () => {
    if (isVerified && 'supporting_references' in claim) {
      return claim.supporting_references.map((ref, index) => (
        <div key={`supporting-${index}`} className="claim-source">
          <div className="source-info">
            <span className="source-name">{ref.source}</span>
            <span className="source-title">{ref.title}</span>
          </div>
          <div className="source-score">
            Support: {Math.round(ref.support_score * 100)}%
          </div>
          {ref.url && (
            <a 
              href={ref.url}
              target="_blank"
              rel="noopener noreferrer"
              className="source-link"
            >
              View Source
            </a>
          )}
        </div>
      ));
    } else if (!isVerified && 'disputed_by' in claim) {
      return claim.disputed_by.map((ref, index) => (
        <div key={`disputing-${index}`} className="claim-source disputing">
          <div className="source-info">
            <span className="source-name">{ref.source}</span>
            <span className="source-title">{ref.title}</span>
          </div>
          <div className="source-score">
            Dispute: {Math.round(ref.dispute_score * 100)}%
          </div>
          {ref.url && (
            <a 
              href={ref.url}
              target="_blank"
              rel="noopener noreferrer"
              className="source-link"
            >
              View Source
            </a>
          )}
        </div>
      ));
    }
    return null;
  };
  
  return (
    <div className={`claim-verification ${isVerified ? 'verified' : 'disputed'}`}>
      <div className="claim-header" onClick={() => setExpanded(!expanded)}>
        <div className="claim-score">
          <VerificationScore 
            score={claim.score}
            size="small"
            showLabel={false}
          />
        </div>
        <div className="claim-text">{claim.text}</div>
        <div className="claim-expand-icon">
          {expanded ? '−' : '+'}
        </div>
      </div>
      
      {expanded && (
        <div className="claim-details">
          <div className="claim-score-details">
            <div className="score-label">
              {isVerified ? 'Verification Score:' : 'Dispute Score:'}
            </div>
            <div className="score-value">
              {Math.round(claim.score * 100)}%
            </div>
          </div>
          
          {originalClaim && originalClaim.entities && originalClaim.entities.length > 0 && (
            <div className="claim-entities">
              <div className="entities-label">Entities:</div>
              <div className="entities-list">
                {originalClaim.entities.map((entity, index) => (
                  <span 
                    key={`entity-${index}`} 
                    className={`entity-badge ${entity.type.toLowerCase()}`}
                  >
                    {entity.name}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          <div className="claim-sources">
            <div className="sources-label">
              {isVerified ? 'Supporting Sources:' : 'Disputing Sources:'}
            </div>
            <div className="sources-list">
              {renderSources()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClaimVerification;
