/**
 * API service for interacting with the Hydra News backend
 */

import { Article, ArticleListItem, Verification } from '../types/article';

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api/v1';

// Token storage key
const TOKEN_STORAGE_KEY = 'hydra_news_token';

/**
 * Get stored auth token
 */
const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
};

/**
 * Set auth token in storage
 */
const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
};

/**
 * Clear auth token from storage
 */
const clearToken = (): void => {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
};

/**
 * Create headers with auth token
 */
const createHeaders = (includeAuth: boolean = true): Headers => {
  const headers = new Headers({
    'Content-Type': 'application/json',
  });
  
  if (includeAuth) {
    const token = getToken();
    if (token) {
      headers.append('Authorization', `Bearer ${token}`);
    }
  }
  
  return headers;
};

/**
 * Login to the API
 */
export const login = async (username: string, password: string): Promise<{ token: string; user: any }> => {
  const response = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: createHeaders(false),
    body: JSON.stringify({ username, password }),
  });
  
  if (!response.ok) {
    throw new Error(`Login failed: ${response.status} ${response.statusText}`);
  }
  
  const data = await response.json();
  setToken(data.token);
  
  return data;
};

/**
 * Register a new user
 */
export const register = async (
  username: string,
  email: string,
  password: string
): Promise<{ token: string; user: any }> => {
  const response = await fetch(`${API_BASE_URL}/register`, {
    method: 'POST',
    headers: createHeaders(false),
    body: JSON.stringify({ username, email, password }),
  });
  
  if (!response.ok) {
    throw new Error(`Registration failed: ${response.status} ${response.statusText}`);
  }
  
  const data = await response.json();
  setToken(data.token);
  
  return data;
};

/**
 * Logout
 */
export const logout = (): void => {
  clearToken();
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  return getToken() !== null;
};

/**
 * Get list of articles
 */
export const getArticles = async (
  page: number = 1,
  limit: number = 10
): Promise<{ articles: ArticleListItem[]; total: number }> => {
  const response = await fetch(
    `${API_BASE_URL}/articles?page=${page}&limit=${limit}`,
    {
      headers: createHeaders(),
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to fetch articles: ${response.status} ${response.statusText}`);
  }
  
  return await response.json();
};

/**
 * Get single article by ID
 */
export const getArticle = async (id: string): Promise<Article> => {
  const response = await fetch(`${API_BASE_URL}/articles/${id}`, {
    headers: createHeaders(),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch article: ${response.status} ${response.statusText}`);
  }
  
  return await response.json();
};

/**
 * Create a new article
 */
export const createArticle = async (
  title: string,
  content: string,
  source: string,
  author?: string,
  url?: string
): Promise<Article> => {
  const response = await fetch(`${API_BASE_URL}/articles`, {
    method: 'POST',
    headers: createHeaders(),
    body: JSON.stringify({
      title,
      content,
      source,
      author,
      url,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create article: ${response.status} ${response.statusText}`);
  }
  
  return await response.json();
};

/**
 * Extract article from URL
 */
export const extractArticle = async (url: string): Promise<{
  title: string;
  content: string;
  source: string;
  author?: string;
}> => {
  const response = await fetch(`${API_BASE_URL}/extract`, {
    method: 'POST',
    headers: createHeaders(),
    body: JSON.stringify({ url }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to extract article: ${response.status} ${response.statusText}`);
  }
  
  return await response.json();
};

/**
 * Verify article content
 */
export const verifyArticle = async (
  contentHash: string,
  referenceUrls?: string[]
): Promise<Verification> => {
  const response = await fetch(`${API_BASE_URL}/verification`, {
    method: 'POST',
    headers: createHeaders(),
    body: JSON.stringify({
      content_hash: contentHash,
      reference_urls: referenceUrls || [],
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to verify article: ${response.status} ${response.statusText}`);
  }
  
  return await response.json();
};

/**
 * Get API health status
 */
export const getApiHealth = async (): Promise<{ status: string; time: string }> => {
  const response = await fetch(`${API_BASE_URL}/health`, {
    headers: createHeaders(false),
  });
  
  if (!response.ok) {
    throw new Error(`API health check failed: ${response.status} ${response.statusText}`);
  }
  
  return await response.json();
};

/**
 * Get user profile
 */
export const getUserProfile = async (): Promise<any> => {
  const response = await fetch(`${API_BASE_URL}/profile`, {
    headers: createHeaders(),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch user profile: ${response.status} ${response.statusText}`);
  }
  
  return await response.json();
};

// Export the API service
const apiService = {
  login,
  register,
  logout,
  isAuthenticated,
  getArticles,
  getArticle,
  createArticle,
  extractArticle,
  verifyArticle,
  getApiHealth,
  getUserProfile,
};

export default apiService;
