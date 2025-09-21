"""Test metrics API endpoints."""

import pytest
from datetime import datetime


def test_submit_metric(client, sample_ai_metric):
    """Test metric submission endpoint."""
    response = client.post(
        "/api/v1/metrics/submit",
        json=sample_ai_metric.dict(),
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["metric_type"] == "latency"
    assert data["value"] == 150.5
    assert data["unit"] == "ms"
    assert data["provider"] == "openai"
    assert data["model_name"] == "gpt-3.5-turbo"
    assert "id" in data  # Should have generated an ID


def test_list_metrics(client):
    """Test metrics listing endpoint."""
    response = client.get("/api/v1/metrics/")
    assert response.status_code == 200
    
    data = response.json()
    assert "metrics" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert data["page"] == 1
    assert data["per_page"] == 50


def test_list_metrics_with_filters(client):
    """Test metrics listing with filters."""
    response = client.get(
        "/api/v1/metrics/",
        params={
            "metric_type": "latency",
            "provider": "openai",
            "page": 2,
            "per_page": 25,
        }
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["page"] == 2
    assert data["per_page"] == 25


def test_get_metric_not_found(client):
    """Test getting non-existent metric."""
    response = client.get("/api/v1/metrics/nonexistent")
    assert response.status_code == 404


def test_submit_error(client, sample_ai_error):
    """Test error submission endpoint."""
    response = client.post(
        "/api/v1/metrics/errors",
        json=sample_ai_error.dict(),
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["severity"] == "high"
    assert data["category"] == "rate_limit"
    assert data["message"] == "Rate limit exceeded"
    assert data["provider"] == "openai"
    assert "id" in data  # Should have generated an ID


def test_list_errors(client):
    """Test errors listing endpoint."""
    response = client.get("/api/v1/metrics/errors")
    assert response.status_code == 200
    
    data = response.json()
    assert "errors" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


def test_get_model_metrics(client):
    """Test model metrics endpoint."""
    response = client.get("/api/v1/metrics/models/openai/gpt-3.5-turbo")
    assert response.status_code == 200
    
    data = response.json()
    assert data["provider"] == "openai"
    assert data["model_name"] == "gpt-3.5-turbo"
    assert "time_window_start" in data
    assert "time_window_end" in data
    assert "total_requests" in data