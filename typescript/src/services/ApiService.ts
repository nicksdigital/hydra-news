/**
 * API Service for Hydra News
 * 
 * This service handles all communication with the backend API,
 * including content submission, verification, and retrieval.
 */

import { NewsContent, VerificationResult } from '../types/NewsContent';

// API endpoints
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';
const ENDPOINTS = {
  SUBMIT_CONTENT: `${API_BASE_URL}/api/content/submit`,
  VERIFY_CONTENT: `${API_BASE_URL}/api/content/verify`,
  GET_CONTENT: `${API_BASE_URL}/api/content`,
  GET_VERIFICATION: `${API_BASE_URL}/api/verification`,
  CROSS_REFERENCE: `${API_BASE_URL}/api/content/cross-reference`,
};

/**
 * Submit news content for processing and verification
 * @param content The news content to submit
 * @returns The processed content with hash and entanglement
 */
export const submitContent = async (content: Partial<NewsContent>): Promise<NewsContent> => {
  try {
    const response = await fetch(ENDPOINTS.SUBMIT_CONTENT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(content),
    });

    if (!response.ok) {
      throw new Error(`Error submitting content: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error submitting content:', error);
    throw error;
  }
};

/**
 * Request verification for a content item
 * @param contentHash The hash of the content to verify
 * @param crossReferenceUrls Optional URLs to use for cross-referencing
 * @returns The verification result
 */
export const verifyContent = async (
  contentHash: string,
  crossReferenceUrls?: string[]
): Promise<VerificationResult> => {
  try {
    const response = await fetch(ENDPOINTS.VERIFY_CONTENT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content_hash: contentHash,
        reference_urls: crossReferenceUrls || [],
      }),
    });

    if (!response.ok) {
      throw new Error(`Error verifying content: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error verifying content:', error);
    throw error;
  }
};

/**
 * Get content by hash
 * @param contentHash The hash of the content to retrieve
 * @returns The content item
 */
export const getContent = async (contentHash: string): Promise<NewsContent> => {
  try {
    const response = await fetch(`${ENDPOINTS.GET_CONTENT}/${contentHash}`);

    if (!response.ok) {
      throw new Error(`Error retrieving content: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error retrieving content:', error);
    throw error;
  }
};

/**
 * Get verification result for content
 * @param contentHash The hash of the content to get verification for
 * @returns The verification result
 */
export const getVerification = async (contentHash: string): Promise<VerificationResult> => {
  try {
    const response = await fetch(`${ENDPOINTS.GET_VERIFICATION}/${contentHash}`);

    if (!response.ok) {
      throw new Error(`Error retrieving verification: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error retrieving verification:', error);
    throw error;
  }
};

/**
 * Cross-reference content with other sources
 * @param contentHash The hash of the content to cross-reference
 * @param urls URLs to use for cross-referencing
 * @returns The verification result with cross-references
 */
export const crossReferenceContent = async (
  contentHash: string,
  urls: string[]
): Promise<VerificationResult> => {
  try {
    const response = await fetch(ENDPOINTS.CROSS_REFERENCE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content_hash: contentHash,
        reference_urls: urls,
      }),
    });

    if (!response.ok) {
      throw new Error(`Error cross-referencing content: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error cross-referencing content:', error);
    throw error;
  }
};

/**
 * Get recent news content items
 * @param limit Maximum number of items to return
 * @returns Array of news content items
 */
export const getRecentContent = async (limit: number = 10): Promise<NewsContent[]> => {
  try {
    const response = await fetch(`${ENDPOINTS.GET_CONTENT}?limit=${limit}`);

    if (!response.ok) {
      throw new Error(`Error retrieving recent content: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error retrieving recent content:', error);
    throw error;
  }
};

/**
 * Search for content by keywords
 * @param query The search query
 * @param limit Maximum number of items to return
 * @returns Array of matching news content items
 */
export const searchContent = async (
  query: string,
  limit: number = 10
): Promise<NewsContent[]> => {
  try {
    const response = await fetch(
      `${ENDPOINTS.GET_CONTENT}/search?q=${encodeURIComponent(query)}&limit=${limit}`
    );

    if (!response.ok) {
      throw new Error(`Error searching content: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error searching content:', error);
    throw error;
  }
};

/**
 * Upload a file URL for content extraction
 * @param url The URL to extract content from
 * @returns The extracted content
 */
export const extractContentFromUrl = async (url: string): Promise<Partial<NewsContent>> => {
  try {
    const response = await fetch(`${ENDPOINTS.SUBMIT_CONTENT}/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      throw new Error(`Error extracting content: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error extracting content:', error);
    throw error;
  }
};

/**
 * Get trust score for a source
 * @param source The source name or domain
 * @returns The trust score (0-1)
 */
export const getSourceTrustScore = async (source: string): Promise<number> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sources/trust-score/${encodeURIComponent(source)}`);

    if (!response.ok) {
      throw new Error(`Error retrieving source trust score: ${response.statusText}`);
    }

    const data = await response.json();
    return data.score;
  } catch (error) {
    console.error('Error retrieving source trust score:', error);
    throw error;
  }
};

/**
 * Get the verification status of the system
 * @returns Object containing system status information
 */
export const getSystemStatus = async (): Promise<{
  activeNodes: number;
  verifiedContent: number;
  averageVerificationTime: number;
  systemHealth: string;
}> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/system/status`);

    if (!response.ok) {
      throw new Error(`Error retrieving system status: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error retrieving system status:', error);
    throw error;
  }
};

export default {
  submitContent,
  verifyContent,
  getContent,
  getVerification,
  crossReferenceContent,
  getRecentContent,
  searchContent,
  extractContentFromUrl,
  getSourceTrustScore,
  getSystemStatus,
};
