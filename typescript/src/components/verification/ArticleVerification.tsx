import React, { useState, useEffect } from 'react';
import './ArticleVerification.css';
import VerificationScore from './VerificationScore';
import ClaimVerification from './ClaimVerification';
import { Article, Verification, Claim, Entity } from '../../types/article';

interface ArticleVerificationProps {
  article: Article;
  verification?: Verification;
  isLoading?: boolean;
  onVerifyRequest?: () => void;
}

/**
 * Component to display article verification information
 */
const ArticleVerification: React.FC<ArticleVerificationProps> = ({
  article,
  verification,
  isLoading = false,
  onVerifyRequest,
}) => {
  const [activeTab, setActiveTab] = useState<'summary' | 'claims' | 'entities' | 'sources'>('summary');
  
  // Auto switch to claims tab when verification is available
  useEffect(() => {
    if (verification && !isLoading) {
      setActiveTab('claims');
    }
  }, [verification, isLoading]);
  
  // Handle verification request
  const handleVerifyClick = () => {
    if (onVerifyRequest) {
      onVerifyRequest();
    }
  };
  
  return (
    <div className="article-verification">
      <div className="verification-header">
        <h2>Verification Status</h2>
        {verification && !isLoading ? (
          <VerificationScore 
            score={verification.verification_score}
            size="large"
          />
        ) : (
          <div className="verification-status">
            {isLoading ? (
              <div className="verification-loading">
                <VerificationScore 
                  score={0.5}
                  size="large"
                  className="loading"
                />
                <p>Verifying article...</p>
              </div>
            ) : (
              <div className="verification-unavailable">
                <p>This article has not been verified yet.</p>
                <button 
                  className="verify-button"
                  onClick={handleVerifyClick}
                  disabled={isLoading}
                >
                  Verify Now
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      
      <div className="verification-content">
        <div className="verification-tabs">
          <button 
            className={`tab-button ${activeTab === 'summary' ? 'active' : ''}`}
            onClick={() => setActiveTab('summary')}
          >
            Summary
          </button>
          <button 
            className={`tab-button ${activeTab === 'claims' ? 'active' : ''}`}
            onClick={() => setActiveTab('claims')}
          >
            Claims {verification?.verified_claims.length + verification?.disputed_claims.length ? 
              `(${verification.verified_claims.length + verification.disputed_claims.length})` : ''}
          </button>
          <button 
            className={`tab-button ${activeTab === 'entities' ? 'active' : ''}`}
            onClick={() => setActiveTab('entities')}
          >
            Entities {article.entities?.length ? `(${article.entities.length})` : ''}
          </button>
          <button 
            className={`tab-button ${activeTab === 'sources' ? 'active' : ''}`}
            onClick={() => setActiveTab('sources')}
          >
            Sources {verification?.references?.length ? `(${verification.references.length})` : ''}
          </button>
        </div>
        
        <div className="tab-content">
          {activeTab === 'summary' && (
            <div className="summary-tab">
              <div className="summary-stats">
                <div className="stat-item">
                  <div className="stat-value">{article.entities?.length || 0}</div>
                  <div className="stat-label">Entities Detected</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{article.claims?.length || 0}</div>
                  <div className="stat-label">Claims Identified</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">
                    {verification ? verification.verified_claims.length : 0}
                  </div>
                  <div className="stat-label">Verified Claims</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">
                    {verification ? verification.disputed_claims.length : 0}
                  </div>
                  <div className="stat-label">Disputed Claims</div>
                </div>
              </div>
              
              <div className="verification-summary">
                <h3>Verification Summary</h3>
                {verification ? (
                  <p>
                    This article has been verified against {verification.references.length} sources. 
                    {verification.verification_score >= 0.8 ? (
                      ' The content has been highly verified with multiple trusted sources supporting the claims.'
                    ) : verification.verification_score >= 0.6 ? (
                      ' Most of the claims in this article are supported by trusted sources.'
                    ) : verification.verification_score >= 0.4 ? (
                      ' The article contains a mix of verified and disputed claims.'
                    ) : verification.verification_score >= 0.2 ? (
                      ' Several claims in this article have been disputed by trusted sources.'
                    ) : (
                      ' Most claims in this article have been disputed or could not be verified.'
                    )}
                  </p>
                ) : (
                  <p>No verification data is available for this article yet.</p>
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'claims' && (
            <div className="claims-tab">
              {verification && (
                <>
                  {verification.verified_claims.length > 0 && (
                    <div className="verified-claims">
                      <h3>Verified Claims</h3>
                      {verification.verified_claims.map((claim, index) => (
                        <ClaimVerification
                          key={`verified-${claim.claim_id || index}`}
                          claim={claim}
                          isVerified={true}
                          article={article}
                        />
                      ))}
                    </div>
                  )}
                  
                  {verification.disputed_claims.length > 0 && (
                    <div className="disputed-claims">
                      <h3>Disputed Claims</h3>
                      {verification.disputed_claims.map((claim, index) => (
                        <ClaimVerification
                          key={`disputed-${claim.claim_id || index}`}
                          claim={claim}
                          isVerified={false}
                          article={article}
                        />
                      ))}
                    </div>
                  )}
                  
                  {verification.verified_claims.length === 0 && verification.disputed_claims.length === 0 && (
                    <p className="no-claims">No claims have been verified or disputed in this article.</p>
                  )}
                </>
              )}
              
              {!verification && (
                <div className="claims-unavailable">
                  <p>Verification data is not available.</p>
                  {!isLoading && (
                    <button 
                      className="verify-button"
                      onClick={handleVerifyClick}
                    >
                      Verify Article
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
          
          {activeTab === 'entities' && (
            <div className="entities-tab">
              {article.entities && article.entities.length > 0 ? (
                <div className="entities-list">
                  {article.entities.map((entity: Entity, index) => (
                    <div key={`entity-${index}`} className="entity-item">
                      <div className="entity-header">
                        <span className="entity-name">{entity.name}</span>
                        <span className={`entity-type ${entity.type.toLowerCase()}`}>
                          {entity.type}
                        </span>
                      </div>
                      {entity.context && (
                        <div className="entity-context">
                          "{entity.context}"
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-entities">No entities have been identified in this article.</p>
              )}
            </div>
          )}
          
          {activeTab === 'sources' && (
            <div className="sources-tab">
              {verification && verification.references && verification.references.length > 0 ? (
                <div className="sources-list">
                  {verification.references.map((reference, index) => (
                    <div key={`source-${index}`} className="source-item">
                      <div className="source-header">
                        <span className="source-title">{reference.title}</span>
                        <span className="source-domain">{reference.source}</span>
                      </div>
                      <div className="source-meta">
                        {reference.support_score !== undefined && (
                          <div className="source-score">
                            <span className="score-label">Support Score:</span>
                            <span className="score-value">
                              {Math.round(reference.support_score * 100)}%
                            </span>
                          </div>
                        )}
                        {reference.dispute_score !== undefined && (
                          <div className="source-score dispute">
                            <span className="score-label">Dispute Score:</span>
                            <span className="score-value">
                              {Math.round(reference.dispute_score * 100)}%
                            </span>
                          </div>
                        )}
                        {reference.trust_score !== undefined && (
                          <div className="source-score trust">
                            <span className="score-label">Trust Score:</span>
                            <span className="score-value">
                              {Math.round(reference.trust_score * 100)}%
                            </span>
                          </div>
                        )}
                      </div>
                      {reference.url && (
                        <a 
                          href={reference.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="source-link"
                        >
                          View Source
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-sources">No reference sources available for this article.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArticleVerification;
