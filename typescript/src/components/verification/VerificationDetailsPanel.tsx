import React, { useState } from 'react';
import './VerificationDetailsPanel.css';
import VerificationScore from './VerificationScore';
import { Verification, Article, Reference } from '../../types/article';

interface VerificationDetailsPanelProps {
  article: Article;
  verification: Verification;
  onClose?: () => void;
}

/**
 * Component to display detailed verification information
 */
const VerificationDetailsPanel: React.FC<VerificationDetailsPanelProps> = ({
  article,
  verification,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'claims' | 'sources'>('overview');
  
  // Format date for display
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };
  
  // Get color based on score
  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return '#4CAF50'; // Green
    if (score >= 0.6) return '#8BC34A'; // Light Green
    if (score >= 0.4) return '#FFC107'; // Amber
    if (score >= 0.2) return '#FF9800'; // Orange
    return '#F44336'; // Red
  };
  
  // Get percentage from score
  const getPercentage = (score: number): string => {
    return `${Math.round(score * 100)}%`;
  };
  
  // Render source item
  const renderSourceItem = (reference: Reference, index: number) => {
    const isSupporting = reference.support_score !== undefined && reference.support_score > 0.5;
    const isDisputing = reference.dispute_score !== undefined && reference.dispute_score > 0.5;
    
    return (
      <div key={`source-${index}`} className={`source-item ${isSupporting ? 'supporting' : ''} ${isDisputing ? 'disputing' : ''}`}>
        <div className="source-header">
          <h4 className="source-title">{reference.title}</h4>
          <div className="source-meta">
            <span className="source-name">{reference.source}</span>
            {reference.support_score !== undefined && (
              <span className="source-score supporting">
                Supports: {getPercentage(reference.support_score)}
              </span>
            )}
            {reference.dispute_score !== undefined && (
              <span className="source-score disputing">
                Disputes: {getPercentage(reference.dispute_score)}
              </span>
            )}
          </div>
        </div>
        <div className="source-actions">
          <a href={reference.url} target="_blank" rel="noopener noreferrer" className="source-link">
            View Source
          </a>
        </div>
      </div>
    );
  };
  
  return (
    <div className="verification-details-panel">
      <div className="verification-details-header">
        <h2>Verification Details</h2>
        {onClose && (
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        )}
      </div>
      
      <div className="verification-details-tabs">
        <button 
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab-button ${activeTab === 'claims' ? 'active' : ''}`}
          onClick={() => setActiveTab('claims')}
        >
          Claims ({verification.verified_claims.length + verification.disputed_claims.length})
        </button>
        <button 
          className={`tab-button ${activeTab === 'sources' ? 'active' : ''}`}
          onClick={() => setActiveTab('sources')}
        >
          Sources ({verification.references.length})
        </button>
      </div>
      
      <div className="verification-details-content">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="tab-content">
            <div className="overview-header">
              <div className="score-display">
                <VerificationScore 
                  score={verification.verification_score}
                  size="large"
                />
              </div>
              
              <div className="overview-stats">
                <div className="stat-item">
                  <div className="stat-value">{verification.verified_claims.length}</div>
                  <div className="stat-label">Verified Claims</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{verification.disputed_claims.length}</div>
                  <div className="stat-label">Disputed Claims</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{verification.references.length}</div>
                  <div className="stat-label">Sources</div>
                </div>
              </div>
            </div>
            
            <div className="overview-details">
              <div className="detail-item">
                <div className="detail-label">Content Hash:</div>
                <div className="detail-value">{verification.content_hash}</div>
              </div>
              <div className="detail-item">
                <div className="detail-label">Verification Time:</div>
                <div className="detail-value">{formatDate(verification.timestamp)}</div>
              </div>
              {article.entanglement_hash && (
                <div className="detail-item">
                  <div className="detail-label">Entanglement Hash:</div>
                  <div className="detail-value">{article.entanglement_hash}</div>
                </div>
              )}
            </div>
            
            <div className="verification-summary">
              <h3>Verification Summary</h3>
              <p>
                {verification.verification_score >= 0.8 ? (
                  'This content has been highly verified with multiple trusted sources supporting the claims.'
                ) : verification.verification_score >= 0.6 ? (
                  'Most of the claims in this content are supported by trusted sources.'
                ) : verification.verification_score >= 0.4 ? (
                  'This content contains a mix of verified and disputed claims.'
                ) : verification.verification_score >= 0.2 ? (
                  'Several claims in this content have been disputed by trusted sources.'
                ) : (
                  'Most claims in this content have been disputed or could not be verified.'
                )}
              </p>
            </div>
          </div>
        )}
        
        {/* Claims Tab */}
        {activeTab === 'claims' && (
          <div className="tab-content">
            {verification.verified_claims.length > 0 && (
              <div className="claims-section">
                <h3>Verified Claims</h3>
                <div className="claims-list">
                  {verification.verified_claims.map((claim, index) => (
                    <div key={`verified-${index}`} className="claim-item verified">
                      <div className="claim-header">
                        <div className="claim-text">{claim.text}</div>
                        <div className="claim-score" style={{ color: getScoreColor(claim.score) }}>
                          {getPercentage(claim.score)}
                        </div>
                      </div>
                      
                      {claim.supporting_references && claim.supporting_references.length > 0 && (
                        <div className="claim-references">
                          <h4>Supporting Sources:</h4>
                          <ul>
                            {claim.supporting_references.map((ref, refIndex) => (
                              <li key={`support-${refIndex}`}>
                                <a href={ref.url} target="_blank" rel="noopener noreferrer">
                                  {ref.title} ({ref.source})
                                </a>
                                {ref.support_score && (
                                  <span className="reference-score">
                                    {getPercentage(ref.support_score)}
                                  </span>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {verification.disputed_claims.length > 0 && (
              <div className="claims-section">
                <h3>Disputed Claims</h3>
                <div className="claims-list">
                  {verification.disputed_claims.map((claim, index) => (
                    <div key={`disputed-${index}`} className="claim-item disputed">
                      <div className="claim-header">
                        <div className="claim-text">{claim.text}</div>
                        <div className="claim-score" style={{ color: getScoreColor(claim.score) }}>
                          {getPercentage(claim.score)}
                        </div>
                      </div>
                      
                      {claim.disputed_by && claim.disputed_by.length > 0 && (
                        <div className="claim-references">
                          <h4>Disputing Sources:</h4>
                          <ul>
                            {claim.disputed_by.map((ref, refIndex) => (
                              <li key={`dispute-${refIndex}`}>
                                <a href={ref.url} target="_blank" rel="noopener noreferrer">
                                  {ref.title} ({ref.source})
                                </a>
                                {ref.dispute_score && (
                                  <span className="reference-score">
                                    {getPercentage(ref.dispute_score)}
                                  </span>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {verification.verified_claims.length === 0 && verification.disputed_claims.length === 0 && (
              <div className="no-claims">
                <p>No claims have been verified or disputed in this content.</p>
              </div>
            )}
          </div>
        )}
        
        {/* Sources Tab */}
        {activeTab === 'sources' && (
          <div className="tab-content">
            <div className="sources-list">
              {verification.references.length > 0 ? (
                verification.references.map((reference, index) => renderSourceItem(reference, index))
              ) : (
                <div className="no-sources">
                  <p>No reference sources are available for this content.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerificationDetailsPanel;
