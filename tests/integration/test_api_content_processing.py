#!/usr/bin/env python3
"""
Integration tests for API security and content processing.

These tests verify that the Go API server and Python content processor
work together correctly, including authentication, rate limiting,
and content processing.
"""

import os
import sys
import unittest
import json
import time
import requests
import hashlib
import threading
import subprocess
from datetime import datetime

# Test configuration
API_SERVER_URL = "http://localhost:8080"
CONTENT_PROCESSOR_URL = "http://localhost:5000"
API_KEY = "test_api_key"  # For testing only

class TestAPIContentProcessing(unittest.TestCase):
    """Integration tests for API and content processing"""
    
    @classmethod
    def setUpClass(cls):
        """Start the necessary services for testing"""
        # Check if services are already running
        try:
            # Check API server
            response = requests.get(f"{API_SERVER_URL}/api/v1/health")
            api_running = response.status_code == 200
        except:
            api_running = False
            
        try:
            # Check content processor
            response = requests.get(f"{CONTENT_PROCESSOR_URL}/api/health")
            processor_running = response.status_code == 200
        except:
            processor_running = False
        
        # Start API server if needed
        if not api_running:
            print("Starting API server...")
            cls.api_server_process = subprocess.Popen(
                ["go", "run", "main.go"],
                cwd="../../go/src",
                env=dict(os.environ, PORT="8080")
            )
            # Wait for server to start
            time.sleep(2)
        else:
            cls.api_server_process = None
            print("API server already running")
        
        # Start content processor if needed
        if not processor_running:
            print("Starting content processor...")
            cls.processor_process = subprocess.Popen(
                ["python3", "content_processor_service.py", "--port", "5000"],
                cwd="../../python/src"
            )
            # Wait for processor to start
            time.sleep(2)
        else:
            cls.processor_process = None
            print("Content processor already running")
    
    @classmethod
    def tearDownClass(cls):
        """Stop the services after testing"""
        # Stop API server if we started it
        if cls.api_server_process:
            print("Stopping API server...")
            cls.api_server_process.terminate()
            cls.api_server_process.wait(timeout=5)
        
        # Stop content processor if we started it
        if cls.processor_process:
            print("Stopping content processor...")
            cls.processor_process.terminate()
            cls.processor_process.wait(timeout=5)
    
    def get_auth_token(self):
        """Get an authentication token for testing"""
        response = requests.post(
            f"{API_SERVER_URL}/api/v1/login",
            json={
                "username": "test_user",
                "password": "test_password"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get auth token: {response.text}")
        
        return response.json()["token"]
    
    def test_api_health(self):
        """Test API server health check endpoint"""
        response = requests.get(f"{API_SERVER_URL}/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
    
    def test_content_processor_health(self):
        """Test content processor health check endpoint"""
        response = requests.get(f"{CONTENT_PROCESSOR_URL}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
    
    def test_api_authentication(self):
        """Test API authentication"""
        # Try accessing protected endpoint without token
        response = requests.get(f"{API_SERVER_URL}/api/v1/articles")
        self.assertEqual(response.status_code, 401)
        
        # Get auth token
        token = self.get_auth_token()
        
        # Try accessing protected endpoint with token
        response = requests.get(
            f"{API_SERVER_URL}/api/v1/articles",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 200)
    
    def test_rate_limiting(self):
        """Test API rate limiting"""
        # Make multiple rapid requests to trigger rate limiting
        endpoint = f"{API_SERVER_URL}/api/v1/health"
        
        # Make 100 requests (should hit rate limit)
        responses = []
        for _ in range(100):
            response = requests.get(endpoint)
            responses.append(response.status_code)
            
        # At least one request should be rate limited (429)
        self.assertIn(429, responses)
    
    def test_input_validation(self):
        """Test API input validation"""
        # Get auth token
        token = self.get_auth_token()
        
        # Try to submit article with missing required fields
        response = requests.post(
            f"{API_SERVER_URL}/api/v1/articles",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "title": "Test Article"
                # Missing content and source
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("errors", data)
    
    def test_content_processing_flow(self):
        """Test full content processing flow"""
        # Get auth token
        token = self.get_auth_token()
        
        # Submit article
        article_data = {
            "title": "Test Integration Article",
            "content": "This is a test article for integration testing. " 
                      "John Smith has been appointed as the new CEO of Test Corp. "
                      "The announcement was made on Monday by the board of directors.",
            "source": "test-source.com",
            "author": "Integration Test"
        }
        
        response = requests.post(
            f"{API_SERVER_URL}/api/v1/articles",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=article_data
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("content_hash", data)
        
        article_id = data["id"]
        content_hash = data["content_hash"]
        
        # Verify content
        verification_request = {
            "content_hash": content_hash,
            "reference_urls": [
                "https://example.com/reference1",
                "https://example.com/reference2"
            ]
        }
        
        response = requests.post(
            f"{API_SERVER_URL}/api/v1/verification",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=verification_request
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("verification_score", data)
        self.assertIn("verified_claims", data)
        
        # Get article
        response = requests.get(
            f"{API_SERVER_URL}/api/v1/articles/{article_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], article_data["title"])
        self.assertEqual(data["content"], article_data["content"])
        self.assertIn("entities", data)
        self.assertIn("claims", data)
        
        # Check if entities were extracted
        self.assertGreater(len(data["entities"]), 0)
        
        # Check if claims were extracted
        self.assertGreater(len(data["claims"]), 0)


class TestConcurrentRequests(unittest.TestCase):
    """Test concurrent requests to API server"""
    
    def test_concurrent_requests(self):
        """Test making concurrent requests to API server"""
        # Number of concurrent requests
        num_requests = 20
        
        # Results container
        results = []
        
        # Request function
        def make_request():
            try:
                response = requests.get(f"{API_SERVER_URL}/api/v1/health")
                results.append(response.status_code)
            except Exception as e:
                results.append(str(e))
        
        # Create threads
        threads = []
        for _ in range(num_requests):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Count successful responses
        successful = results.count(200)
        
        # Some might be rate limited, but not all
        self.assertGreater(successful, 0)
        
        # Count rate limited responses
        rate_limited = results.count(429)
        
        # Print results
        print(f"Concurrent requests: {num_requests}")
        print(f"Successful responses: {successful}")
        print(f"Rate limited responses: {rate_limited}")
        print(f"Other responses: {num_requests - successful - rate_limited}")


class TestAPISecurityFeatures(unittest.TestCase):
    """Test API security features"""
    
    def test_request_id_tracking(self):
        """Test request ID generation and tracking"""
        response = requests.get(f"{API_SERVER_URL}/api/v1/health")
        self.assertEqual(response.status_code, 200)
        
        # Check if X-Request-ID header is present
        self.assertIn("X-Request-ID", response.headers)
        request_id = response.headers["X-Request-ID"]
        self.assertIsNotNone(request_id)
        self.assertNotEqual(request_id, "")
    
    def test_content_type_enforcement(self):
        """Test that the API enforces proper content type"""
        # Try to send JSON with wrong content type
        response = requests.post(
            f"{API_SERVER_URL}/api/v1/login",
            headers={"Content-Type": "text/plain"},
            data=json.dumps({
                "username": "test_user",
                "password": "test_password"
            })
        )
        
        self.assertEqual(response.status_code, 415)  # Unsupported Media Type
    
    def test_large_payload_handling(self):
        """Test handling of large request payloads"""
        # Create a large payload
        large_payload = {
            "username": "test_user",
            "password": "test_password",
            "large_data": "x" * (2 * 1024 * 1024)  # 2MB of data
        }
        
        # Send large payload
        response = requests.post(
            f"{API_SERVER_URL}/api/v1/login",
            headers={"Content-Type": "application/json"},
            json=large_payload
        )
        
        # Should be rejected (413 Payload Too Large)
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
