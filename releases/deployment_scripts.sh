#!/bin/bash
# AI Home CoPilot - Automated Deployment Scripts
# Erstellt: 2026-02-10 13:49 CET
# Verwendung: Nach Git-Auth-Resolution für komplettes Release-Deployment

set -e  # Exit on any error

# Farbige Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI Home CoPilot - Production Deployment${NC}"
echo -e "${BLUE}==============================================${NC}"

# Repository-Pfade
HA_REPO="/config/.openclaw/workspace/ai_home_copilot_hacs_repo"
CORE_REPO="/config/.openclaw/workspace/ha-copilot-repo"

# Deployment-Funktionen
deploy_ha_integration() {
    echo -e "\n${YELLOW}📦 Deploying HA Integration Releases...${NC}"
    
    cd "$HA_REPO"
    
    # Prüfe Git-Status
    if ! git status &>/dev/null; then
        echo -e "${RED}❌ Git nicht verfügbar in HA Integration Repo${NC}"
        exit 1
    fi
    
    # HA Integration Releases (v0.4.3, v0.4.4, v0.4.5, v0.4.6)
    local versions=("v0.4.3" "v0.4.4" "v0.4.5" "v0.4.6")
    
    for version in "${versions[@]}"; do
        echo -e "${BLUE}🏷️  Deploying HA Integration $version...${NC}"
        
        # Tag existiert lokal?
        if git tag -l | grep -q "^$version$"; then
            # Push Tag zu GitHub
            if git push origin "$version"; then
                echo -e "${GREEN}✅ $version erfolgreich deployed${NC}"
                
                # GitHub Release erstellen (optional)
                # gh release create $version --title "HA Integration $version" --notes-from-tag
                
            else
                echo -e "${RED}❌ Fehler beim Push von $version${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}⚠️  Tag $version nicht gefunden, überspringe...${NC}"
        fi
        
        sleep 2  # Rate limiting
    done
}

deploy_core_addon() {
    echo -e "\n${YELLOW}🧠 Deploying Core Add-on Releases...${NC}"
    
    cd "$CORE_REPO"
    
    # Prüfe Git-Status
    if ! git status &>/dev/null; then
        echo -e "${RED}❌ Git nicht verfügbar in Core Add-on Repo${NC}"
        exit 1
    fi
    
    # Core Add-on Releases (v0.4.6, v0.4.7, v0.4.8, v0.4.9)
    local versions=("v0.4.6" "v0.4.7" "v0.4.8" "v0.4.9")
    
    for version in "${versions[@]}"; do
        echo -e "${BLUE}🏷️  Deploying Core Add-on $version...${NC}"
        
        # Tag existiert lokal?
        if git tag -l | grep -q "^$version$"; then
            # Push Tag zu GitHub
            if git push origin "$version"; then
                echo -e "${GREEN}✅ $version erfolgreich deployed${NC}"
                
                # GitHub Release erstellen (optional)
                # gh release create $version --title "Core Add-on $version" --notes-from-tag
                
            else
                echo -e "${RED}❌ Fehler beim Push von $version${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}⚠️  Tag $version nicht gefunden, überspringe...${NC}"
        fi
        
        sleep 2  # Rate limiting
    done
}

verify_deployment() {
    echo -e "\n${YELLOW}🔍 Post-Deployment Verification...${NC}"
    
    # HA Integration Tags prüfen
    cd "$HA_REPO"
    echo -e "${BLUE}HA Integration Tags:${NC}"
    git ls-remote --tags origin | grep -E "v0\.4\.[3-6]" | tail -4
    
    # Core Add-on Tags prüfen  
    cd "$CORE_REPO"
    echo -e "${BLUE}Core Add-on Tags:${NC}"
    git ls-remote --tags origin | grep -E "v0\.4\.[6-9]" | tail -4
    
    echo -e "\n${GREEN}🎉 Deployment Verification Complete!${NC}"
    echo -e "${GREEN}📚 Nächste Schritte:${NC}"
    echo -e "  1. GitHub Releases erstellen (optional)"
    echo -e "  2. Community Communication (Discord, GitHub Discussions)"
    echo -e "  3. User Support & Feedback Monitoring"
}

# Pre-flight Checks
check_prerequisites() {
    echo -e "${YELLOW}🔧 Pre-flight Checks...${NC}"
    
    # Git Auth Test
    cd "$HA_REPO"
    if ! git ls-remote origin &>/dev/null; then
        echo -e "${RED}❌ Git Authentication fehlgeschlagen für HA Integration${NC}"
        echo -e "${YELLOW}💡 Setup erforderlich: SSH Key oder Personal Access Token${NC}"
        echo -e "${YELLOW}📖 Siehe: docs/RELEASE_DEPLOYMENT_GUIDE.md${NC}"
        exit 1
    fi
    
    cd "$CORE_REPO"
    if ! git ls-remote origin &>/dev/null; then
        echo -e "${RED}❌ Git Authentication fehlgeschlagen für Core Add-on${NC}"
        echo -e "${YELLOW}💡 Setup erforderlich: SSH Key oder Personal Access Token${NC}"
        echo -e "${YELLOW}📖 Siehe: docs/RELEASE_DEPLOYMENT_GUIDE.md${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Git Authentication erfolgreich${NC}"
}

# Main Deployment
main() {
    echo -e "${BLUE}⏱️  Start: $(date)${NC}"
    
    # Pre-flight Checks
    check_prerequisites
    
    # Deploy HA Integration
    deploy_ha_integration
    
    # Deploy Core Add-on
    deploy_core_addon
    
    # Verification
    verify_deployment
    
    echo -e "\n${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}⏱️  Ende: $(date)${NC}"
    echo -e "${GREEN}🚀 AI Home CoPilot ist jetzt live!${NC}"
}

# Script-Ausführung
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi