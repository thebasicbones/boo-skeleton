#!/bin/bash
# Script to stop local observability stack

echo "=========================================="
echo "Stopping Local Observability Stack"
echo "=========================================="
echo ""

echo "Stopping Prometheus..."
brew services stop prometheus
echo "✓ Prometheus stopped"
echo ""

echo "Stopping Grafana..."
brew services stop grafana
echo "✓ Grafana stopped"
echo ""

echo "Stopping OpenTelemetry Collector..."
if [ -f "otel-collector.pid" ]; then
    PID=$(cat otel-collector.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "✓ OTEL Collector stopped (PID: $PID)"
        rm otel-collector.pid
    else
        echo "⚠️  OTEL Collector process not found"
        rm otel-collector.pid
    fi
else
    # Try to find and kill by process name
    pkill -f "otelcol-contrib" && echo "✓ OTEL Collector stopped" || echo "⚠️  OTEL Collector not running"
fi

echo ""
echo "=========================================="
echo "✅ All services stopped"
echo "=========================================="
