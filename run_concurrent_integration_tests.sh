#!/bin/bash

# Script to run integration tests concurrently against AWS and Azure
# Usage: ./run_concurrent_integration_tests.sh

set -e

echo "🚀 Starting concurrent integration tests..."
echo "AWS Profile: e2demo-aws"
echo "Azure Profile: e2demo-azure"
echo ""

# Activate virtual environment
source test-env/bin/activate

# Function to run AWS tests
run_aws_tests() {
    echo "[AWS] 🔧 Starting AWS integration tests..."
    DATABRICKS_CONFIG_PROFILE=e2demo-aws \
    DATABRICKS_CLOUD=aws \
    TEST_CATALOG_NAME=jas_test_mlops \
    TEST_SCHEMA_NAME=test \
    python -m pytest tests/integration/test_workspace_integration.py -v --integration -s \
        --tb=short 2>&1 | sed 's/^/[AWS] /'
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "[AWS] ✅ AWS integration tests completed successfully!"
    else
        echo "[AWS] ❌ AWS integration tests failed!"
        return 1
    fi
}

# Function to run Azure tests  
run_azure_tests() {
    echo "[AZURE] 🔧 Starting Azure integration tests..."
    DATABRICKS_CONFIG_PROFILE=e2demo-azure \
    DATABRICKS_CLOUD=azure \
    TEST_CATALOG_NAME=jas_bali_btw6_da \
    TEST_SCHEMA_NAME=test \
    python -m pytest tests/integration/test_workspace_integration.py -v --integration -s \
        --tb=short 2>&1 | sed 's/^/[AZURE] /'
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "[AZURE] ✅ Azure integration tests completed successfully!"
    else
        echo "[AZURE] ❌ Azure integration tests failed!"
        return 1
    fi
}

# Run tests concurrently
echo "🏃‍♂️ Running tests in parallel..."
echo "==============================================="

# Start both test suites in background
run_aws_tests &
AWS_PID=$!

run_azure_tests &
AZURE_PID=$!

# Wait for both to complete
wait $AWS_PID
AWS_RESULT=$?

wait $AZURE_PID  
AZURE_RESULT=$?

echo ""
echo "==============================================="
echo "📊 FINAL RESULTS:"
echo "==============================================="

if [ $AWS_RESULT -eq 0 ]; then
    echo "AWS Tests: ✅ PASSED"
else
    echo "AWS Tests: ❌ FAILED"
fi

if [ $AZURE_RESULT -eq 0 ]; then
    echo "Azure Tests: ✅ PASSED"  
else
    echo "Azure Tests: ❌ FAILED"
fi

echo ""

# Overall result
if [ $AWS_RESULT -eq 0 ] && [ $AZURE_RESULT -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED! Both AWS and Azure integration tests successful!"
    exit 0
else
    echo "💥 SOME TESTS FAILED! Check the logs above for details."
    exit 1
fi