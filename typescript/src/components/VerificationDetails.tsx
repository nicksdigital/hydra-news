import React, { useState } from 'react';
import { NewsContent, VerificationResult, CrossReference } from '../types/NewsContent';
import './VerificationDetails.css';

interface VerificationDetailsProps {
  newsContent: NewsContent;
  verificationResult: VerificationResult;
  onClose: () => void;
}

const VerificationDetails: React.FC<VerificationDetailsProps> = ({
  newsContent,
  verificationResult,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'claims' | 'sources' | 'technical'>('overview');
  
  // Format a timestamp string
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Format a hash for display by truncating
  const formatHash = (hash: string): string => {
    if (!hash) return '-';
    if (hash.length <= 16) return hash;
    return `${hash.substring(0, 8)}...${hash.substring(hash.length - 8)}`;
  };

  // Get percentage from a 0-1 score
  const getPercentage = (score: number): string => {
    return `${Math.round(score * 100)}%`;
  };

  // Format verification score with color
  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return '#27ae60';
    if (score >= 0.6) return '#2ecc71';
    if (score >= 0.4) return '#f1c40f';
    if (score >= 0.2) return '#e67e22';
    return '#e74c3c';
  };

  // Render references list
  const renderReferences = (references: CrossReference[]): JSX.Element => {
    if (!references || references.length === 0) {
      return <p className="no-data">No reference sources available.</p>;
    }

    return (
      <ul className="reference-list">
        {references.map((ref, index) => (
          <li key={index} className="reference-item">
            <a href={ref.url} target="_blank" rel="noopener noreferrer" className="reference-title">
              {ref.title || 'Untitled Reference'}
            </a>
            <div className="reference-source">{ref.source}</div>
            {(ref.support_score || ref.dispute_score) && (
              <div className="reference-score">
                {ref.support_score && (
                  <span className="support-score" style={{ color: getScoreColor(ref.support_score) }}>
                    Support: {getPercentage(ref.support_score)}
                  </span>
                )}
                {ref.dispute_score && (
                  <span className="dispute-score" style={{ color: getScoreColor(1 - ref.dispute_score) }}>
                    Dispute: {getPercentage(ref.dispute_score)}
                  </span>
                )}
              </div>
            )}
            <div className="reference-hash">
              <span className="hash-label">Hash:</span>
              <span className="hash-value">{formatHash(ref.content_hash)}</span>
            </div>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="verification-details-overlay">
      <div className="verification-details-container">
        <div className="verification-details-header">
          <h2>Verification Details</h2>
          <button className="close-button" onClick={onClose}>×</button>
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
            Claims
          </button>
          <button 
            className={`tab-button ${activeTab === 'sources' ? 'active' : ''}`}
            onClick={() => setActiveTab('sources')}
          >
            Sources
          </button>
          <button 
            className={`tab-button ${activeTab === 'technical' ? 'active' : ''}`}
            onClick={() => setActiveTab('technical')}
          >
            Technical
          </button>
        </div>
        
        <div className="verification-details-content">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="tab-content">
              <div className="overview-header">
                <div className="score-display">
                  <div 
                    className="score-circle" 
                    style={{ 
                      backgroundColor: getScoreColor(verificationResult.verification_score),
                    }}
                  >
                    {getPercentage(verificationResult.verification_score)}
                  </div>
                  <div className="score-label">Verification Score</div>
                </div>
                
                <div className="verification-summary">
                  <div className="summary-item">
                    <span className="summary-label">Verified Claims:</span>
                    <span className="summary-value">{verificationResult.verified_claims.length}</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Disputed Claims:</span>
                    <span className="summary-value">{verificationResult.disputed_claims.length}</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Reference Sources:</span>
                    <span className="summary-value">{verificationResult.references.length}</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Verification Time:</span>
                    <span className="summary-value">{formatTimestamp(verificationResult.timestamp)}</span>
                  </div>
                </div>
              </div>
              
              <div className="content-preview">
                <h3>{newsContent.title}</h3>
                <div className="content-metadata">
                  <span className="source">{newsContent.source}</span>
                  {newsContent.author && <span className="author">By {newsContent.author}</span>}
                  {newsContent.publish_date && <span className="date">{newsContent.publish_date}</span>}
                </div>
                <p className="content-excerpt">{newsContent.content.substring(0, 300)}...</p>
              </div>
            </div>
          )}
          
          {/* Claims Tab */}
          {activeTab === 'claims' && (
            <div className="tab-content">
              <div className="claims-sections">
                <div className="verified-claims-section">
                  <h3>Verified Claims ({verificationResult.verified_claims.length})</h3>
                  {verificationResult.verified_claims.length === 0 ? (
                    <p className="no-data">No verified claims found.</p>
                  ) : (
                    <ul className="claims-list">
                      {verificationResult.verified_claims.map((claim) => (
                        <li key={claim.claim_id} className="claim-item">
                          <div className="claim-header">
                            <span className="claim-text">{claim.text}</span>
                            <span 
                              className="claim-score" 
                              style={{ color: getScoreColor(claim.score) }}
                            >
                              {getPercentage(claim.score)}
                            </span>
                          </div>
                          {claim.supporting_references && claim.supporting_references.length > 0 && (
                            <div className="claim-references">
                              <h4>Supporting References:</h4>
                              {renderReferences(claim.supporting_references)}
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                
                <div className="disputed-claims-section">
                  <h3>Disputed Claims ({verificationResult.disputed_claims.length})</h3>
                  {verificationResult.disputed_claims.length === 0 ? (
                    <p className="no-data">No disputed claims found.</p>
                  ) : (
                    <ul className="claims-list">
                      {verificationResult.disputed_claims.map((claim) => (
                        <li key={claim.claim_id} className="claim-item disputed">
                          <div className="claim-header">
                            <span className="claim-text">{claim.text}</span>
                            <span 
                              className="claim-score" 
                              style={{ color: getScoreColor(claim.score) }}
                            >
                              {getPercentage(claim.score)}
                            </span>
                          </div>
                          {claim.disputed_by && claim.disputed_by.length > 0 && (
                            <div className="claim-references">
                              <h4>Disputed By:</h4>
                              {renderReferences(claim.disputed_by)}
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {/* Sources Tab */}
          {activeTab === 'sources' && (
            <div className="tab-content">
              <h3>Reference Sources ({verificationResult.references.length})</h3>
              {renderReferences(verificationResult.references)}
            </div>
          )}
          
          {/* Technical Tab */}
          {activeTab === 'technical' && (
            <div className="tab-content">
              <div className="technical-details">
                <div className="technical-section">
                  <h3>Content Identification</h3>
                  <div className="technical-item">
                    <span className="technical-label">Content Hash:</span>
                    <span className="technical-value monospace">{newsContent.content_hash}</span>
                  </div>
                  {newsContent.entanglement_hash && (
                    <div className="technical-item">
                      <span className="technical-label">Entanglement Hash:</span>
                      <span className="technical-value monospace">{newsContent.entanglement_hash}</span>
                    </div>
                  )}
                </div>
                
                <div className="technical-section">
                  <h3>Entities Detected</h3>
                  {!newsContent.entities || newsContent.entities.length === 0 ? (
                    <p className="no-data">No entities detected.</p>
                  ) : (
                    <table className="entities-table">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Type</th>
                          <th>Confidence</th>
                          <th>Position</th>
                        </tr>
                      </thead>
                      <tbody>
                        {newsContent.entities.map((entity, index) => (
                          <tr key={index}>
                            <td>{entity.name}</td>
                            <td>{entity.type}</td>
                            <td>{getPercentage(entity.confidence)}</td>
                            <td>{entity.position.start}-{entity.position.end}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
                
                <div className="technical-section">
                  <h3>Verification Metadata</h3>
                  <div className="technical-item">
                    <span className="technical-label">Processed:</span>
                    <span className="technical-value">{newsContent.processed ? 'Yes' : 'No'}</span>
                  </div>
                  <div className="technical-item">
                    <span className="technical-label">Verification Time:</span>
                    <span className="technical-value">{formatTimestamp(verificationResult.timestamp)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerificationDetails;
