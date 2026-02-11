#!/bin/bash
# =============================================================================
# SEO Tool Framework - Bootstrap Script
# =============================================================================
# 
# Kör detta script för att sätta upp hela framework:et från scratch.
# 
# Usage:
#   chmod +x bootstrap.sh
#   ./bootstrap.sh
#
# Eller steg för steg:
#   ./bootstrap.sh setup      # Installera dependencies
#   ./bootstrap.sh test       # Testa med mock-verktyg  
#   ./bootstrap.sh start      # Starta servern
#   ./bootstrap.sh all        # Kör allt
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# =============================================================================
# Helper functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# =============================================================================
# Setup function
# =============================================================================

do_setup() {
    print_header "STEG 1: Setup Environment"
    
    # Check Python version
    print_info "Kontrollerar Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION hittad"
    else
        print_error "Python3 inte installerat!"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Skapar virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment skapad"
    else
        print_info "Virtual environment finns redan"
    fi
    
    # Activate virtual environment
    print_info "Aktiverar virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    print_info "Installerar dependencies..."
    pip install --upgrade pip -q
    pip install -r v2/requirements.txt -q
    print_success "Dependencies installerade"
    
    # Create necessary directories
    print_info "Skapar mappstruktur..."
    mkdir -p v2/tools/test_tools
    mkdir -p v2/manifests
    mkdir -p v2/logs
    print_success "Mappstruktur klar"
    
    # Copy test tools if they exist
    if [ -d "test_tools" ]; then
        print_info "Kopierar test-verktyg..."
        cp -r test_tools/* v2/tools/test_tools/
        print_success "Test-verktyg kopierade"
    fi
    
    # Copy test manifests if they exist
    if [ -d "test_manifests" ]; then
        print_info "Kopierar test-manifests..."
        cp -r test_manifests/* v2/manifests/
        print_success "Test-manifests kopierade"
    fi
    
    print_success "Setup klar!"
}

# =============================================================================
# Test function
# =============================================================================

do_test() {
    print_header "STEG 2: Testa Framework"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run the test script
    print_info "Kör framework-tester..."
    cd v2
    python -c "
import asyncio
import sys
sys.path.insert(0, '.')

from core.framework import ToolFramework

async def test():
    print('Initierar framework...')
    fw = ToolFramework()
    
    # Load manifests
    manifest_count = fw.load_manifests('manifests')
    print(f'Laddade {manifest_count} manifests')
    
    # Auto-discover tools
    discover_count = fw.auto_discover('tools/test_tools', 'tools.test_tools')
    print(f'Auto-upptäckte {discover_count} verktyg')
    
    # List all tools
    tools = fw.list_tools()
    print(f'\\nTotalt {len(tools)} verktyg registrerade:')
    for tool in tools:
        print(f'  - {tool[\"id\"]}: {tool[\"name\"]} ({tool[\"archetype\"]})')
    
    # Test execution if we have tools
    if tools:
        tool_id = tools[0]['id']
        print(f'\\nTestar körning av: {tool_id}')
        
        result = await fw.execute(tool_id, {'test': 'data'})
        
        if result.success:
            print(f'✓ Körning lyckades!')
            print(f'  Tid: {result.execution_time_ms:.1f}ms')
            print(f'  Data: {str(result.data)[:100]}...')
        else:
            print(f'✗ Körning misslyckades: {result.error}')
    
    await fw.shutdown()
    print('\\n✓ Alla tester passerade!')

asyncio.run(test())
"
    cd ..
    
    print_success "Tester klara!"
}

# =============================================================================
# Start server function
# =============================================================================

do_start() {
    print_header "STEG 3: Starta Server"
    
    # Activate virtual environment
    source venv/bin/activate
    
    print_info "Startar FastAPI server..."
    print_info "Öppna http://localhost:8000 i din webbläsare"
    print_info "Tryck Ctrl+C för att stoppa"
    echo ""
    
    cd v2
    
    # Set environment variables
    export MANIFEST_DIR="manifests"
    export TOOLS_DIR="tools/test_tools"
    export TOOLS_MODULE="tools.test_tools"
    export DEMO_MODE="false"
    
    # Start uvicorn
    python -m uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
}

# =============================================================================
# Full run
# =============================================================================

do_all() {
    do_setup
    do_test
    
    print_header "KLART! 🎉"
    echo ""
    print_success "Framework är uppsatt och testat!"
    echo ""
    print_info "Nästa steg:"
    echo "  1. Kör './bootstrap.sh start' för att starta servern"
    echo "  2. Öppna http://localhost:8000"
    echo "  3. Testa verktygen i UI:t"
    echo ""
    print_info "För att länka dina riktiga verktyg:"
    echo "  ln -s /path/to/ml-service/app/features v2/tools/ml_features"
    echo "  python v2/scripts/generate_manifests.py --analysis COMBINED_ANALYSIS.json --output v2/manifests/"
    echo ""
}

# =============================================================================
# Link real tools function
# =============================================================================

do_link() {
    print_header "Länka Riktiga Verktyg"
    
    if [ -z "$1" ]; then
        print_error "Usage: ./bootstrap.sh link /path/to/seo-platform"
        exit 1
    fi
    
    PLATFORM_PATH="$1"
    
    if [ ! -d "$PLATFORM_PATH" ]; then
        print_error "Sökväg finns inte: $PLATFORM_PATH"
        exit 1
    fi
    
    print_info "Skapar symlinks..."
    
    # Link ml_features if it exists
    if [ -d "$PLATFORM_PATH/ml-service/app/features" ]; then
        ln -sf "$PLATFORM_PATH/ml-service/app/features" v2/tools/ml_features
        print_success "Länkade: ml_features"
    fi
    
    # Link tier1 if it exists
    if [ -d "$PLATFORM_PATH/services/tier1-priority" ]; then
        ln -sf "$PLATFORM_PATH/services/tier1-priority" v2/tools/tier1
        print_success "Länkade: tier1"
    fi
    
    # Link tier2 if it exists
    if [ -d "$PLATFORM_PATH/services/tier2-core" ]; then
        ln -sf "$PLATFORM_PATH/services/tier2-core" v2/tools/tier2
        print_success "Länkade: tier2"
    fi
    
    # Link advanced if it exists
    if [ -d "$PLATFORM_PATH/ml-service/app/features_advanced" ]; then
        ln -sf "$PLATFORM_PATH/ml-service/app/features_advanced" v2/tools/advanced
        print_success "Länkade: advanced"
    fi
    
    print_success "Symlinks skapade!"
    print_info "Kör nu: python v2/scripts/generate_manifests.py för att generera manifests"
}

# =============================================================================
# Main
# =============================================================================

case "${1:-all}" in
    setup)
        do_setup
        ;;
    test)
        do_test
        ;;
    start)
        do_start
        ;;
    link)
        do_link "$2"
        ;;
    all)
        do_all
        ;;
    *)
        echo "Usage: $0 {setup|test|start|link|all}"
        echo ""
        echo "  setup  - Installera dependencies och skapa struktur"
        echo "  test   - Testa framework med mock-verktyg"
        echo "  start  - Starta FastAPI-servern"
        echo "  link   - Länka riktiga verktyg: ./bootstrap.sh link /path/to/platform"
        echo "  all    - Kör setup + test"
        exit 1
        ;;
esac