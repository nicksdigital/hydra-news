import React, { useState } from 'react';
import { 
  VerificationScore, 
  VerificationStatusIndicator, 
  VerificationDetailsPanel 
} from './verification';
import { VerificationLevel } from '../types/NewsContent';

// Mock data for demonstration
const mockArticle = {
  id: 'article-1',
  title: 'Example News Article',
  content: 'This is an example news article content that demonstrates the verification system.',
  source: 'Example News Source',
  author: 'John Doe',
  url: 'https://example.com/article',
  content_hash: 'abcdef1234567890',
  entanglement_hash: 'entgl-abcdef1234567890',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockVerification = {
  content_hash: 'abcdef1234567890',
  verification_score: 0.85,
  verified_claims: [
    {
      claim_id: 'claim1',
      text: 'This is a verified claim from the article.',
      score: 0.92,
      supporting_references: [
        {
          url: 'https://example.com/reference1',
          title: 'Supporting Reference 1',
          source: 'Trusted Source A',
          content_hash: 'ref1hash',
          support_score: 0.9,
        },
      ],
    },
    {
      claim_id: 'claim2',
      text: 'This is another verified claim with strong supporting evidence.',
      score: 0.88,
      supporting_references: [
        {
          url: 'https://example.com/reference2',
          title: 'Supporting Reference 2',
          source: 'Trusted Source B',
          content_hash: 'ref2hash',
          support_score: 0.85,
        },
      ],
    },
  ],
  disputed_claims: [
    {
      claim_id: 'claim3',
      text: 'This is a disputed claim that has contradicting evidence.',
      score: 0.3,
      disputed_by: [
        {
          url: 'https://example.com/disputing-source',
          title: 'Contradicting Evidence',
          source: 'Fact-Check Organization',
          content_hash: 'disphash',
          dispute_score: 0.75,
        },
      ],
    },
  ],
  references: [
    {
      url: 'https://example.com/reference1',
      title: 'Supporting Reference 1',
      source: 'Trusted Source A',
      content_hash: 'ref1hash',
      support_score: 0.9,
    },
    {
      url: 'https://example.com/reference2',
      title: 'Supporting Reference 2',
      source: 'Trusted Source B',
      content_hash: 'ref2hash',
      support_score: 0.85,
    },
    {
      url: 'https://example.com/disputing-source',
      title: 'Contradicting Evidence',
      source: 'Fact-Check Organization',
      content_hash: 'disphash',
      dispute_score: 0.75,
    },
  ],
  timestamp: new Date().toISOString(),
};

/**
 * Component to demonstrate verification components
 */
const VerificationDemo: React.FC = () => {
  const [showDetails, setShowDetails] = useState(false);
  
  return (
    <div className="verification-demo" style={{ padding: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      <h1>Verification Components Demo</h1>
      
      <section style={{ marginBottom: '32px' }}>
        <h2>Verification Scores</h2>
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          <VerificationScore score={0.95} size="small" />
          <VerificationScore score={0.75} size="medium" />
          <VerificationScore score={0.5} size="large" />
          <VerificationScore score={0.25} size="medium" />
          <VerificationScore score={0.1} size="small" />
        </div>
      </section>
      
      <section style={{ marginBottom: '32px' }}>
        <h2>Verification Status Indicators</h2>
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          <VerificationStatusIndicator score={0.95} size="small" />
          <VerificationStatusIndicator score={0.75} size="medium" />
          <VerificationStatusIndicator score={0.5} size="medium" />
          <VerificationStatusIndicator score={0.25} size="medium" />
          <VerificationStatusIndicator score={0.1} size="small" />
        </div>
        
        <h3 style={{ marginTop: '24px' }}>By Verification Level</h3>
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          <VerificationStatusIndicator level={VerificationLevel.None} size="small" />
          <VerificationStatusIndicator level={VerificationLevel.Minimal} size="small" />
          <VerificationStatusIndicator level={VerificationLevel.Standard} size="small" />
          <VerificationStatusIndicator level={VerificationLevel.High} size="small" />
          <VerificationStatusIndicator level={VerificationLevel.Maximum} size="small" />
        </div>
      </section>
      
      <section style={{ marginBottom: '32px' }}>
        <h2>Interactive Verification Status</h2>
        <VerificationStatusIndicator 
          score={0.85} 
          size="medium" 
          onClick={() => setShowDetails(true)}
          className="clickable"
        />
        <p style={{ marginTop: '8px', color: '#666' }}>
          Click on the status indicator above to see detailed verification information.
        </p>
      </section>
      
      {showDetails && (
        <section>
          <h2>Verification Details Panel</h2>
          <VerificationDetailsPanel 
            article={mockArticle} 
            verification={mockVerification}
            onClose={() => setShowDetails(false)}
          />
        </section>
      )}
    </div>
  );
};

export default VerificationDemo;
