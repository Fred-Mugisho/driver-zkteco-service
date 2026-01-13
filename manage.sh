#!/bin/bash
# Script de gestion simplifié du service ZKTeco

set -e

SERVICE_NAME="zkteco_attendance"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Détection de l'OS
OS_TYPE="$(uname -s)"
HAS_SYSTEMD=false
if [ -d "/etc/systemd/system" ]; then
    HAS_SYSTEMD=true
fi

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${YELLOW}ℹ${NC} $1"; }

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Cette commande nécessite sudo"
        exit 1
    fi
}

check_systemd() {
    if [ "$HAS_SYSTEMD" = false ]; then
        print_error "systemd non disponible sur ce système ($OS_TYPE)"
        print_info "Utilisez 'run' pour lancer le service manuellement"
        exit 1
    fi
}

# Installation
install() {
    print_info "Installation des dépendances..."

    # Créer venv si nécessaire
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
    fi

    # Installer dépendances
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r "$SCRIPT_DIR/requirements.txt"
    print_success "Dépendances installées"

    # Copier .env si nécessaire
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        if [ -f "$SCRIPT_DIR/.env.example" ]; then
            cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
            print_info "Fichier .env créé - À CONFIGURER !"
        fi
    fi

    # Installer service systemd si disponible
    if [ "$HAS_SYSTEMD" = true ]; then
        check_root
        cp "$SCRIPT_DIR/zkteco_attendance.service" "/etc/systemd/system/"
        systemctl daemon-reload
        print_success "Service systemd installé"
    else
        print_info "systemd non disponible - Service installé pour exécution manuelle"
        print_info "Utilisez './manage.sh run' pour lancer le service"
    fi
}

# Lancer le service manuellement
run() {
    print_info "Lancement du service..."
    cd "$SCRIPT_DIR"
    source "$VENV_DIR/bin/activate"
    python3 zkteco_service.py
}

# Démarrer (systemd)
start() {
    check_systemd
    check_root
    systemctl start "$SERVICE_NAME"
    print_success "Service démarré"
    sleep 1
    systemctl status "$SERVICE_NAME" --no-pager
}

# Arrêter (systemd)
stop() {
    check_systemd
    check_root
    systemctl stop "$SERVICE_NAME"
    print_success "Service arrêté"
}

# Redémarrer (systemd)
restart() {
    check_systemd
    check_root
    systemctl restart "$SERVICE_NAME"
    print_success "Service redémarré"
    sleep 1
    systemctl status "$SERVICE_NAME" --no-pager
}

# Statut (systemd)
status() {
    check_systemd
    systemctl status "$SERVICE_NAME" --no-pager
}

# Activer au démarrage (systemd)
enable() {
    check_systemd
    check_root
    systemctl enable "$SERVICE_NAME"
    print_success "Service activé au démarrage"
}

# Désactiver au démarrage (systemd)
disable() {
    check_systemd
    check_root
    systemctl disable "$SERVICE_NAME"
    print_success "Service désactivé au démarrage"
}

# Logs (systemd)
logs() {
    check_systemd
    if [ "$1" = "-f" ]; then
        journalctl -u "$SERVICE_NAME" -f
    else
        journalctl -u "$SERVICE_NAME" -n 50 --no-pager
    fi
}

# Logs applicatifs
app_logs() {
    if [ -f "$SCRIPT_DIR/zkteco_sync.log" ]; then
        tail -f "$SCRIPT_DIR/zkteco_sync.log"
    else
        print_error "Fichier log non trouvé"
    fi
}

# Test
test() {
    print_info "Test de la configuration..."

    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        print_error "Fichier .env manquant"
        return 1
    fi

    cd "$SCRIPT_DIR"
    source "$VENV_DIR/bin/activate"
    export SYNC_INTERVAL=0
    python3 zkteco_service.py
}

# Désinstaller
uninstall() {
    if [ "$HAS_SYSTEMD" = true ]; then
        check_root
        systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        systemctl disable "$SERVICE_NAME" 2>/dev/null || true
        rm -f "/etc/systemd/system/zkteco_attendance.service"
        systemctl daemon-reload
        print_success "Service systemd désinstallé"
    else
        print_info "Rien à désinstaller (systemd non utilisé)"
    fi
}

# Main
case "$1" in
    install) install ;;
    run) run ;;
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    status) status ;;
    enable) enable ;;
    disable) disable ;;
    logs) logs "$2" ;;
    app-logs) app_logs ;;
    test) test ;;
    uninstall) uninstall ;;
    *)
        echo "Usage: $0 {install|run|start|stop|restart|status|enable|disable|logs|app-logs|test|uninstall}"
        echo ""
        echo "Commandes:"
        echo "  install   - Installer les dépendances (+ systemd si disponible)"
        echo "  run       - Lancer le service manuellement (macOS/dev)"
        echo "  start     - Démarrer le service (systemd)"
        echo "  stop      - Arrêter le service (systemd)"
        echo "  restart   - Redémarrer le service (systemd)"
        echo "  status    - Voir le statut (systemd)"
        echo "  enable    - Activer au démarrage (systemd)"
        echo "  disable   - Désactiver au démarrage (systemd)"
        echo "  logs      - Voir les logs (systemd, -f pour suivre)"
        echo "  app-logs  - Logs applicatifs"
        echo "  test      - Tester la config"
        echo "  uninstall - Désinstaller le service (systemd)"
        echo ""
        if [ "$HAS_SYSTEMD" = false ]; then
            echo "Note: systemd non disponible sur ce système ($OS_TYPE)"
            echo "Utilisez './manage.sh run' pour lancer le service"
        fi
        exit 1
        ;;
esac
