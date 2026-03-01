#!/bin/bash
# =============================================================================
# PilotSuite Styx Core - Test Runner Script
# =============================================================================
# Usage:
#   ./scripts/run_tests.sh [options]
#
# Options:
#   --all           Run all tests (default)
#   --unit          Run only unit tests
#   --integration   Run only integration tests
#   --coverage      Generate coverage report
#   --parallel      Run tests in parallel (requires pytest-xdist)
#   --verbose       Verbose output
#   --help          Show this help message
#
# Examples:
#   ./scripts/run_tests.sh --all --coverage --parallel
#   ./scripts/run_tests.sh --integration --verbose
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APP_DIR="$PROJECT_ROOT/copilot_core/rootfs/usr/src/app"
TESTS_DIR="$APP_DIR/tests"
COVERAGE_DIR="$APP_DIR/htmlcov"
COVERAGE_FILE="$APP_DIR/coverage.xml"

# Default options
RUN_ALL=true
RUN_UNIT=false
RUN_INTEGRATION=false
GENERATE_COVERAGE=false
RUN_PARALLEL=false
VERBOSE=false
COVERAGE_TARGET=90
PYTEST_OPTS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            RUN_ALL=true
            shift
            ;;
        --unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        --coverage)
            GENERATE_COVERAGE=true
            shift
            ;;
        --parallel)
            RUN_PARALLEL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            PYTEST_OPTS="$PYTEST_OPTS -v"
            shift
            ;;
        --coverage-target=*)
            COVERAGE_TARGET="${1#*=}"
            shift
            ;;
        --help)
            echo -e "${BLUE}PilotSuite Styx Core - Test Runner${NC}"
            echo ""
            head -20 "$0" | tail -15
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_dependencies() {
    print_header "Checking Dependencies"
    
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check pytest
    if ! python3 -m pytest --version &> /dev/null; then
        missing_deps+=("pytest")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_warning "Missing dependencies: ${missing_deps[*]}"
        echo "Install with: pip install ${missing_deps[*]}"
        exit 1
    fi
    
    print_success "All dependencies available"
}

setup_environment() {
    print_header "Setting Up Environment"
    
    cd "$APP_DIR"
    
    # Set environment variables for testing
    export PYTHONPATH="$APP_DIR:$PYTHONPATH"
    export PYTHONDONTWRITEBYTECODE=1
    export NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
    export NEO4J_USER="${NEO4J_USER:-neo4j}"
    export NEO4J_PASSWORD="${NEO4J_PASSWORD:-testpassword123}"
    
    print_success "Environment configured"
}

run_unit_tests() {
    print_header "Running Unit Tests"
    
    local pytest_cmd="python3 -m pytest"
    
    # Add parallel execution if requested
    if [ "$RUN_PARALLEL" = true ]; then
        pytest_cmd="$pytest_cmd -n auto"
        print_success "Parallel execution enabled"
    fi
    
    # Add coverage if requested
    if [ "$GENERATE_COVERAGE" = true ]; then
        pytest_cmd="$pytest_cmd --cov=copilot_core --cov-report=html --cov-report=term-missing --cov-fail-under=$COVERAGE_TARGET"
        print_success "Coverage reporting enabled (target: ${COVERAGE_TARGET}%)"
    fi
    
    # Add verbose if requested
    if [ "$VERBOSE" = true ]; then
        pytest_cmd="$pytest_cmd -v"
    fi
    
    # Run tests (exclude integration tests)
    $pytest_cmd tests/ --ignore=tests/integration/ -x
    
    if [ $? -eq 0 ]; then
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed"
        return 1
    fi
}

run_integration_tests() {
    print_header "Running Integration Tests"
    
    if [ ! -d "tests/integration" ]; then
        print_warning "Integration tests directory not found"
        return 0
    fi
    
    local pytest_cmd="python3 -m pytest"
    
    # Add parallel execution if requested
    if [ "$RUN_PARALLEL" = true ]; then
        pytest_cmd="$pytest_cmd -n auto"
        print_success "Parallel execution enabled"
    fi
    
    # Add coverage if requested
    if [ "$GENERATE_COVERAGE" = true ]; then
        pytest_cmd="$pytest_cmd --cov=copilot_core --cov-report=html --cov-report=term-missing --cov-append"
        print_success "Coverage reporting enabled"
    fi
    
    # Add verbose if requested
    if [ "$VERBOSE" = true ]; then
        pytest_cmd="$pytest_cmd -v"
    fi
    
    # Run integration tests
    $pytest_cmd tests/integration/ -x
    
    if [ $? -eq 0 ]; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        return 1
    fi
}

run_all_tests() {
    print_header "Running All Tests"
    
    local pytest_cmd="python3 -m pytest"
    
    # Add parallel execution if requested
    if [ "$RUN_PARALLEL" = true ]; then
        pytest_cmd="$pytest_cmd -n auto"
        print_success "Parallel execution enabled (pytest-xdist)"
    fi
    
    # Add coverage if requested
    if [ "$GENERATE_COVERAGE" = true ]; then
        pytest_cmd="$pytest_cmd --cov=copilot_core --cov-report=html --cov-report=xml --cov-report=term-missing --cov-fail-under=$COVERAGE_TARGET"
        print_success "Coverage reporting enabled (target: ${COVERAGE_TARGET}%)"
    fi
    
    # Add verbose if requested
    if [ "$VERBOSE" = true ]; then
        pytest_cmd="$pytest_cmd -v"
    fi
    
    # Run all tests
    $pytest_cmd tests/ -x
    
    if [ $? -eq 0 ]; then
        print_success "All tests passed"
    else
        print_error "Some tests failed"
        return 1
    fi
}

show_coverage_report() {
    if [ "$GENERATE_COVERAGE" = true ]; then
        print_header "Coverage Report"
        
        if [ -f "$COVERAGE_FILE" ]; then
            print_success "Coverage XML report: $COVERAGE_FILE"
        fi
        
        if [ -d "$COVERAGE_DIR" ]; then
            print_success "Coverage HTML report: $COVERAGE_DIR/index.html"
            echo "Open in browser: file://$COVERAGE_DIR/index.html"
        fi
    fi
}

cleanup() {
    print_header "Cleanup"
    
    # Remove Python cache files
    find "$APP_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$APP_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
    
    print_success "Cleanup complete"
}

# Main execution
main() {
    print_header "PilotSuite Styx Core - Test Runner"
    echo "Project Root: $PROJECT_ROOT"
    echo "App Directory: $APP_DIR"
    echo ""
    
    check_dependencies
    setup_environment
    
    local exit_code=0
    
    if [ "$RUN_ALL" = true ]; then
        run_all_tests || exit_code=$?
    else
        if [ "$RUN_UNIT" = true ]; then
            run_unit_tests || exit_code=$?
        fi
        
        if [ "$RUN_INTEGRATION" = true ]; then
            run_integration_tests || exit_code=$?
        fi
    fi
    
    show_coverage_report
    cleanup
    
    if [ $exit_code -eq 0 ]; then
        print_header "Test Run Complete"
        print_success "All tests passed successfully! 🎉"
    else
        print_header "Test Run Failed"
        print_error "Some tests failed. Please review the output above."
    fi
    
    exit $exit_code
}

# Run main function
main
