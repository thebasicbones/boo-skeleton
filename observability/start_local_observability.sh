#!/bin/bash
# Script to start local observability stack

set -e

echo "=========================================="
echo "Starting Local Observability Stack"
echo "=========================================="
echo ""

# Check if Prometheus is installed
if ! command -v prometheus &> /dev/null; then
    echo "❌ Prometheus not found. Installing..."
    brew install prometheus
fi

# Check if Grafana is installed
if ! command -v grafana-server &> /dev/null; then
    echo "❌ Grafana not found. Installing..."
    brew install grafana
fi

# Check if OTEL Collector is installed
# if ! command -v otelcol-cpp &> /dev/null; then
#     echo "❌ OpenTelemetry Collector not found. Installing..."
#     brew install opentelemetry-collector-cpp
# fi

echo "Step 1: Starting Prometheus"
echo "------------------------------------------"
# Copy prometheus config to Homebrew location
PROM_CONFIG_DIR="/opt/homebrew/etc"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$PROM_CONFIG_DIR" ]; then
    cp "$SCRIPT_DIR/prometheus.yml" "$PROM_CONFIG_DIR/prometheus.yml"
    echo "✓ Copied prometheus.yml to $PROM_CONFIG_DIR"
fi

brew services start prometheus
echo "✓ Prometheus started on http://localhost:9090"
echo ""

echo "Step 2: Starting Grafana"
echo "------------------------------------------"
brew services start grafana
echo "✓ Grafana started on http://localhost:3000"
echo "  Default login: admin/admin"
echo ""

echo "Step 3: Starting OpenTelemetry Collector"
echo "------------------------------------------"
if [ ! -f "$SCRIPT_DIR/otel-collector-config.yaml" ]; then
    echo "❌ otel-collector-config.yaml not found!"
    exit 1
fi

echo "Starting OTEL Collector in background..."
cd "$SCRIPT_DIR"
nohup ./otelcol-contrib --config=otel-collector-config.yaml > otel-collector.log 2>&1 &
OTEL_PID=$!
echo $OTEL_PID > otel-collector.pid
cd - > /dev/null
echo "✓ OTEL Collector started (PID: $OTEL_PID)"
echo "  Logs: tail -f observability/otel-collector.log"
echo "  Metrics endpoint: http://localhost:8889/metrics"
echo ""

echo "Step 4: Waiting for services to be ready..."
echo "------------------------------------------"
sleep 3

# Check services
echo "Checking Prometheus..."
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus is healthy"
else
    echo "⚠️  Prometheus may not be ready yet"
fi

echo "Checking Grafana..."
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✅ Grafana is healthy"
else
    echo "⚠️  Grafana may not be ready yet"
fi

echo "Checking OTEL Collector..."
if curl -s http://localhost:8889/metrics > /dev/null; then
    echo "✅ OTEL Collector is healthy"
else
    echo "⚠️  OTEL Collector may not be ready yet"
fi

echo ""
echo "=========================================="
echo "✅ Observability Stack Started!"
echo "=========================================="
echo ""
echo "Services:"
echo "  Prometheus:      http://localhost:9090"
echo "  Grafana:         http://localhost:3000 (admin/admin)"
echo "  OTEL Collector:  http://localhost:4317 (gRPC)"
echo "                   http://localhost:4318 (HTTP)"
echo ""
echo "Next Steps:"
echo "  1. Test the setup:"
echo "     python observability/test_metrics_endpoint.py"
echo ""
echo "  2. Configure Grafana data source:"
echo "     - Go to http://localhost:3000"
echo "     - Login with admin/admin"
echo "     - Add Prometheus data source: http://localhost:9090"
echo ""
echo "  3. Start your FastAPI app:"
echo "     python src/main.py"
echo ""
echo "To stop services:"
echo "  ./observability/stop_local_observability.sh"
echo ""
