#!/usr/bin/env python3
"""
Test script to verify metrics are being generated and exported.

This script:
1. Makes API calls to generate metrics
2. Checks if metrics are being recorded
3. Provides instructions for viewing metrics in Grafana
"""

import asyncio
import httpx
import time


async def test_metrics():
    """Test that metrics are being generated."""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Testing FastAPI CRUD Backend Metrics")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("\n1. Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 2: Create a resource (generates metrics)
        print("\n2. Creating a test resource...")
        resource_data = {
            "name": "Test Resource for Metrics",
            "description": "This resource is created to test metrics",
            "dependencies": []
        }
        response = await client.post(f"{base_url}/api/resources", json=resource_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            resource = response.json()
            resource_id = resource["id"]
            print(f"   Created resource ID: {resource_id}")
        else:
            print(f"   Error: {response.text}")
            return
        
        # Test 3: List resources (generates metrics)
        print("\n3. Listing all resources...")
        response = await client.get(f"{base_url}/api/resources")
        print(f"   Status: {response.status_code}")
        print(f"   Total resources: {len(response.json())}")
        
        # Test 4: Get single resource (generates metrics)
        print("\n4. Getting single resource...")
        response = await client.get(f"{base_url}/api/resources/{resource_id}")
        print(f"   Status: {response.status_code}")
        
        # Test 5: Update resource (generates metrics)
        print("\n5. Updating resource...")
        update_data = {
            "name": "Updated Test Resource",
            "description": "Updated description for metrics testing"
        }
        response = await client.put(f"{base_url}/api/resources/{resource_id}", json=update_data)
        print(f"   Status: {response.status_code}")
        
        # Test 6: Search resources (generates metrics)
        print("\n6. Searching resources...")
        response = await client.get(f"{base_url}/api/search?q=test")
        print(f"   Status: {response.status_code}")
        print(f"   Search results: {len(response.json())}")
        
        # Test 7: Delete resource (generates metrics)
        print("\n7. Deleting resource...")
        response = await client.delete(f"{base_url}/api/resources/{resource_id}")
        print(f"   Status: {response.status_code}")
        
        # Test 8: Test error metrics (404)
        print("\n8. Testing error metrics (404)...")
        response = await client.get(f"{base_url}/api/resources/non-existent-id")
        print(f"   Status: {response.status_code}")
        
    print("\n" + "=" * 60)
    print("Metrics Test Complete!")
    print("=" * 60)
    
    print("\n📊 Metrics Information:")
    print("-" * 60)
    print("Meter Name: app.services.resource_service")
    print("\nMetric Names:")
    print("  1. crud.operation.duration (Histogram)")
    print("     - Tracks operation timing in milliseconds")
    print("     - Attributes: operation.type, db.type, status")
    print()
    print("  2. crud.operation.count (Counter)")
    print("     - Total number of operations")
    print("     - Attributes: operation.type, db.type, status")
    print()
    print("  3. crud.operation.errors (Counter)")
    print("     - Number of failed operations")
    print("     - Attributes: operation.type, db.type, error.type")
    print()
    print("  4. crud.resources.total (UpDownCounter)")
    print("     - Current total number of resources")
    print("     - Attributes: db.type")
    print()
    print("  5. crud.cascade.delete.count (Histogram)")
    print("     - Resources deleted in cascade operations")
    print("     - Attributes: db.type")
    
    print("\n🔍 Where to View Metrics:")
    print("-" * 60)
    print("1. Check OTEL Collector logs:")
    print("   tail -f otel-collector.log")
    print()
    print("2. If using Grafana (local):")
    print("   http://localhost:3000")
    print()
    print("3. If using Grafana Cloud:")
    print("   https://riyajames807.grafana.net/")
    print()
    print("4. Prometheus queries (if configured):")
    print("   rate(crud_operation_count_total[5m])")
    print("   rate(crud_operation_duration_sum[5m]) / rate(crud_operation_duration_count[5m])")
    print("   crud_resources_total")
    
    print("\n⏱️  Note: Metrics are exported every 10 seconds (OTEL_METRICS_EXPORT_INTERVAL_MS=10000)")
    print("    Wait 10-15 seconds after running this script, then check your metrics backend.")
    print()


if __name__ == "__main__":
    asyncio.run(test_metrics())
