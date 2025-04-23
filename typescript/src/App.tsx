import React, { useState, useEffect } from 'react';
import VerifiedNewsCard from './components/VerifiedNewsCard';
import VerificationDetails from './components/VerificationDetails';
import ContentSubmissionForm from './components/ContentSubmissionForm';
import { getRecentContent, verifyContent, getVerification } from './services/ApiService';
import { NewsContent, VerificationResult } from './types/NewsContent';
import './App.css';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'browse' | 'submit'>('browse');
  const [newsItems, setNewsItems] = useState<NewsContent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedContent, setSelectedContent] = useState<NewsContent | null>(null);
  const [selectedVerification, setSelectedVerification] = useState<VerificationResult | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Load recent content on initial render
  useEffect(() => {
    const loadRecentContent = async () => {
      try {
        setLoading(true);
        setError(null);
        const recentContent = await getRecentContent(10);
        setNewsItems(recentContent);
      } catch (err) {
        setError('Failed to load recent content. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadRecentContent();
  }, []);

  // Handle new content submission
  const handleContentSubmission = (content: NewsContent) => {
    setNewsItems((prev) => [content, ...prev]);
    setActiveTab('browse');
  };

  // Handle view details button click
  const handleViewDetails = async (content: NewsContent) => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch verification result if not already available
      let verificationResult: VerificationResult;
      
      if (content.verification_result) {
        verificationResult = content.verification_result;
      } else {
        verificationResult = await getVerification(content.content_hash);
      }
      
      setSelectedContent(content);
      setSelectedVerification(verificationResult);
      setShowDetails(true);
    } catch (err) {
      setError('Failed to load verification details. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Close verification details modal
  const handleCloseDetails = () => {
    setShowDetails(false);
    setSelectedContent(null);
    setSelectedVerification(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo-container">
          <h1 className="app-title">Hydra News</h1>
          <div className="app-subtitle">Untamperable News Verification System</div>
        </div>
        
        <nav className="app-nav">
          <button 
            className={`nav-button ${activeTab === 'browse' ? 'active' : ''}`}
            onClick={() => setActiveTab('browse')}
          >
            Browse Verified News
          </button>
          <button 
            className={`nav-button ${activeTab === 'submit' ? 'active' : ''}`}
            onClick={() => setActiveTab('submit')}
          >
            Submit Content
          </button>
        </nav>
      </header>
      
      <main className="app-content">
        {activeTab === 'browse' ? (
          <div className="news-browser">
            <h2 className="section-title">Recently Verified News</h2>
            
            {loading && <div className="loading-indicator">Loading content...</div>}
            
            {error && <div className="error-message">{error}</div>}
            
            {!loading && !error && newsItems.length === 0 && (
              <div className="empty-state">
                <p>No verified news content available yet.</p>
                <button 
                  className="action-button"
                  onClick={() => setActiveTab('submit')}
                >
                  Submit Your First Article
                </button>
              </div>
            )}
            
            <div className="news-items-list">
              {newsItems.map((item) => (
                <VerifiedNewsCard
                  key={item.content_hash}
                  title={item.title}
                  content={item.content}
                  source={item.source}
                  author={item.author}
                  publishDate={item.publish_date}
                  verificationLevel={item.verification_level || 0}
                  trustScore={item.verification_result?.verification_score || 0}
                  contentHash={item.content_hash}
                  entities={item.entities}
                  claims={item.claims}
                  entanglementHash={item.entanglement_hash}
                  onViewDetails={() => handleViewDetails(item)}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="content-submission">
            <ContentSubmissionForm onSubmissionComplete={handleContentSubmission} />
          </div>
        )}
      </main>
      
      {showDetails && selectedContent && selectedVerification && (
        <VerificationDetails
          newsContent={selectedContent}
          verificationResult={selectedVerification}
          onClose={handleCloseDetails}
        />
      )}
      
      <footer className="app-footer">
        <div className="footer-content">
          <div className="copyright">© 2025 Hydra News - Untamperable News Verification System</div>
          <div className="footer-links">
            <a href="/about" className="footer-link">About</a>
            <a href="/privacy" className="footer-link">Privacy</a>
            <a href="/terms" className="footer-link">Terms</a>
            <a href="/developers" className="footer-link">API</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
