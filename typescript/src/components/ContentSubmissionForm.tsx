import React, { useState } from 'react';
import { submitContent, extractContentFromUrl } from '../services/ApiService';
import { NewsContent } from '../types/NewsContent';
import './ContentSubmissionForm.css';

interface ContentSubmissionFormProps {
  onSubmissionComplete: (content: NewsContent) => void;
}

const ContentSubmissionForm: React.FC<ContentSubmissionFormProps> = ({ onSubmissionComplete }) => {
  const [submissionType, setSubmissionType] = useState<'manual' | 'url'>('manual');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    source: '',
    author: '',
    url: '',
  });

  // Handle form input changes
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
  };

  // Extract content from URL
  const handleUrlExtraction = async () => {
    if (!formData.url) {
      setError('Please enter a URL');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const extractedContent = await extractContentFromUrl(formData.url);
      
      setFormData({
        title: extractedContent.title || '',
        content: extractedContent.content || '',
        source: extractedContent.source || '',
        author: extractedContent.author || '',
        url: formData.url,
      });
      
      setSubmissionType('manual'); // Switch to manual mode to allow editing
    } catch (err) {
      setError('Failed to extract content from URL. Please check the URL or enter content manually.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }
    
    if (!formData.content.trim()) {
      setError('Content is required');
      return;
    }
    
    if (!formData.source.trim()) {
      setError('Source is required');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // Submit content to API
      const submittedContent = await submitContent({
        title: formData.title,
        content: formData.content,
        source: formData.source,
        author: formData.author || undefined,
        url: formData.url || undefined,
      });
      
      // Notify parent component about submission
      onSubmissionComplete(submittedContent);
      
      // Reset form
      setFormData({
        title: '',
        content: '',
        source: '',
        author: '',
        url: '',
      });
    } catch (err) {
      setError('Failed to submit content. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="content-submission-form">
      <h2>Submit News Content</h2>
      
      <div className="submission-type-selector">
        <button
          className={`selector-button ${submissionType === 'manual' ? 'active' : ''}`}
          onClick={() => setSubmissionType('manual')}
          disabled={loading}
        >
          Manual Entry
        </button>
        <button
          className={`selector-button ${submissionType === 'url' ? 'active' : ''}`}
          onClick={() => setSubmissionType('url')}
          disabled={loading}
        >
          From URL
        </button>
      </div>
      
      {submissionType === 'url' ? (
        <div className="url-extraction-form">
          <div className="form-group">
            <label htmlFor="url">URL to Extract Content From</label>
            <input
              type="url"
              id="url"
              name="url"
              value={formData.url}
              onChange={handleChange}
              placeholder="https://example.com/article"
              disabled={loading}
              required
            />
          </div>
          
          <button
            type="button"
            className="extract-button"
            onClick={handleUrlExtraction}
            disabled={loading || !formData.url}
          >
            {loading ? 'Extracting...' : 'Extract Content'}
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Title</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="Enter article title"
              disabled={loading}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="content">Content</label>
            <textarea
              id="content"
              name="content"
              value={formData.content}
              onChange={handleChange}
              placeholder="Enter article content"
              rows={10}
              disabled={loading}
              required
            />
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="source">Source</label>
              <input
                type="text"
                id="source"
                name="source"
                value={formData.source}
                onChange={handleChange}
                placeholder="News source (e.g., BBC News)"
                disabled={loading}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="author">Author (Optional)</label>
              <input
                type="text"
                id="author"
                name="author"
                value={formData.author}
                onChange={handleChange}
                placeholder="Author name"
                disabled={loading}
              />
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="url">Source URL (Optional)</label>
            <input
              type="url"
              id="url"
              name="url"
              value={formData.url}
              onChange={handleChange}
              placeholder="https://example.com/article"
              disabled={loading}
            />
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button type="submit" className="submit-button" disabled={loading}>
            {loading ? 'Submitting...' : 'Submit Content for Verification'}
          </button>
        </form>
      )}
    </div>
  );
};

export default ContentSubmissionForm;
