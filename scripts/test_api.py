#!/usr/bin/env python3
"""Enhanced API test for ReskPoints with new services validation."""

import json
import requests
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"

def test_health_endpoint():
    """Test health endpoint with service status."""
    response = requests.get(f"{BASE_URL}/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.1.0"
    assert "services" in data
    
    # Check that we have status for all expected services
    expected_services = ["api", "database", "timescale", "cache", "clickhouse"]
    for service in expected_services:
        assert service in data["services"]
    
    print("✅ Enhanced health endpoint test passed")
    return data

def test_metric_submission():
    """Test metric submission with enhanced validation."""
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
    print("✅ Enhanced metric submission test passed")

def test_error_submission():
    """Test error submission with enhanced validation."""
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
    print("✅ Enhanced error submission test passed")

def test_cost_transaction():
    """Test cost transaction with enhanced cost tracking."""
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
    print("✅ Enhanced cost transaction test passed")

def test_cost_summary():
    """Test cost summary endpoint."""
    response = requests.get(f"{BASE_URL}/cost/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_cost" in data
    assert "total_transactions" in data
    assert "period_start" in data
    assert "period_end" in data
    print("✅ Cost summary test passed")

def test_model_metrics():
    """Test model metrics endpoint."""
    response = requests.get(f"{BASE_URL}/metrics/models/openai/gpt-3.5-turbo")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert data["model_name"] == "gpt-3.5-turbo"
    assert "time_window_start" in data
    assert "time_window_end" in data
    print("✅ Model metrics test passed")

def test_budget_alert():
    """Test budget alert creation."""
    alert_data = {
        "budget_name": "Test Budget",
        "budget_limit": 100.0,
        "threshold_percentage": 80.0,
        "user_id": "test_user",
        "alert_message": "Budget threshold reached",
        "period_start": "2025-01-01T00:00:00",
        "period_end": "2025-01-31T23:59:59"
    }
    
    response = requests.post(f"{BASE_URL}/cost/budget/alerts", json=alert_data)
    assert response.status_code == 200
    data = response.json()
    assert data["budget_name"] == "Test Budget"
    assert data["budget_limit"] == 100.0
    assert "id" in data
    print("✅ Budget alert creation test passed")

def test_optimization_recommendations():
    """Test cost optimization recommendations."""
    response = requests.get(f"{BASE_URL}/cost/optimization/recommendations?user_id=test_user&days=30")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "potential_total_savings" in data
    assert "analysis_period_days" in data
    print("✅ Optimization recommendations test passed")

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
    print("✅ Enhanced incident ticket test passed")

def main():
    """Run all enhanced tests."""
    print("🚀 Starting ReskPoints Enhanced API tests...")
    
    try:
        # Test basic functionality
        health_data = test_health_endpoint()
        test_metric_submission()
        test_error_submission()
        test_cost_transaction()
        test_incident_ticket()
        
        # Test new enhanced features
        test_cost_summary()
        test_model_metrics()
        test_budget_alert()
        test_optimization_recommendations()
        
        print(f"\n🎉 All enhanced tests passed successfully!")
        print("📊 ReskPoints API with advanced services is fully functional!")
        
        # Print service status summary
        print(f"\n📈 Service Status Summary:")
        for service, status in health_data["services"].items():
            status_emoji = "✅" if status == "healthy" else "⚠️" if status == "unknown" else "❌"
            print(f"  {status_emoji} {service}: {status}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())