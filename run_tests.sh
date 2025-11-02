#!/bin/bash

# Script to run all tests
# Usage: ./run_tests.sh [pytest|cypress|all]

set -e

echo "🧪 Running Tests"
echo "=================="

# Check if server is running
check_server() {
    if curl -s http://localhost:4000 > /dev/null; then
        echo "✅ Server is running"
        return 0
    else
        echo "⚠️  Server is not running"
        echo "Please start the server first:"
        echo "  python -m uvicorn api.app:app --reload"
        return 1
    fi
}

# Run Pytest tests
run_pytest() {
    echo ""
    echo "📋 Running Pytest Tests..."
    echo "---------------------------"
    pytest -v --tb=short
    echo ""
}

# Run Cypress tests
run_cypress() {
    echo ""
    echo "🌲 Running Cypress Tests..."
    echo "---------------------------"
    
    if ! check_server; then
        echo "❌ Cannot run Cypress tests - server is not running"
        return 1
    fi
    
    if command -v npx &> /dev/null; then
        npx cypress run
    else
        echo "❌ Cypress is not installed. Run: npm install"
        return 1
    fi
    echo ""
}

# Run all tests
run_all() {
    echo ""
    echo "🚀 Running All Tests..."
    echo "========================"
    
    run_pytest
    
    if [ $? -eq 0 ]; then
        run_cypress
    else
        echo "❌ Pytest tests failed. Skipping Cypress tests."
        exit 1
    fi
    
    echo ""
    echo "✅ All tests completed!"
}

# Main
case "${1:-all}" in
    pytest)
        run_pytest
        ;;
    cypress)
        run_cypress
        ;;
    all)
        run_all
        ;;
    *)
        echo "Usage: $0 [pytest|cypress|all]"
        exit 1
        ;;
esac

