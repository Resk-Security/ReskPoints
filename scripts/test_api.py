#!/usr/bin/env python3
"""Simple manual test for ReskPoints API functionality."""

import json
import requests
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"

def test_health_endpoint():
    """Test health endpoint."""
    response = requests.get(f"{BASE_URL}/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    print("✅ Health endpoint test passed")

def test_metric_submission():
    """Test metric submission."""
    metric_data = {
        "metric_type": "latency",
        "value": 150.5,
        "unit": "ms",
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "endpoint": "/v1/chat/completions",
        "user_id": "test_user",
        "project_id": "test_project"
    }
    
    response = requests.post(f"{BASE_URL}/metrics/submit", json=metric_data)
    assert response.status_code == 200
    data = response.json()
    assert data["metric_type"] == "latency"
    assert data["value"] == 150.5
    assert "id" in data
    print("✅ Metric submission test passed")

def test_error_submission():
    """Test error submission."""
    error_data = {
        "severity": "high",
        "category": "rate_limit",
        "message": "Rate limit exceeded",
        "code": "rate_limit_exceeded",
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "endpoint": "/v1/chat/completions",
        "user_id": "test_user"
    }
    
    response = requests.post(f"{BASE_URL}/metrics/errors", json=error_data)
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "high"
    assert data["category"] == "rate_limit"
    assert "id" in data
    print("✅ Error submission test passed")

def test_cost_transaction():
    """Test cost transaction submission."""
    transaction_data = {
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "endpoint": "/v1/chat/completions",
        "user_id": "test_user",
        "project_id": "test_project",
        "duration_ms": 1250.0,
        "status_code": 200,
        "success": True,
        "token_usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150
        },
        "cost_breakdown": {
            "input_cost": 0.002,
            "output_cost": 0.003,
            "total_cost": 0.005
        }
    }
    
    response = requests.post(f"{BASE_URL}/cost/transactions", json=transaction_data)
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert data["success"] == True
    assert "id" in data
    print("✅ Cost transaction test passed")

def test_incident_ticket():
    """Test incident ticket creation."""
    ticket_data = {
        "title": "High latency detected",
        "description": "API response times have increased significantly",
        "priority": "high",
        "category": "performance",
        "severity": "high",
        "provider": "openai",
        "model_name": "gpt-3.5-turbo"
    }
    
    response = requests.post(f"{BASE_URL}/incidents/tickets", json=ticket_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "High latency detected"
    assert data["priority"] == "high"
    assert "id" in data
    print("✅ Incident ticket test passed")

def main():
    """Run all tests."""
    print("🚀 Starting ReskPoints API tests...")
    
    try:
        test_health_endpoint()
        test_metric_submission()
        test_error_submission()
        test_cost_transaction()
        test_incident_ticket()
        
        print("\n🎉 All tests passed successfully!")
        print("📊 ReskPoints API is fully functional!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())