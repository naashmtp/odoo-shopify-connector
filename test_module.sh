#!/bin/bash

# Script de test automatique du module Shopify Integration
# Pour Odoo 17

set -e

COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

DB_NAME="odoo17_shopify"
CONTAINER_NAME="shopify_odoo17"

echo -e "${COLOR_BLUE}╔═══════════════════════════════════════════════════════════════╗${COLOR_RESET}"
echo -e "${COLOR_BLUE}║     TEST AUTOMATIQUE - SHOPIFY INTEGRATION ODOO 17           ║${COLOR_RESET}"
echo -e "${COLOR_BLUE}╚═══════════════════════════════════════════════════════════════╝${COLOR_RESET}"
echo ""

# Fonction pour afficher les étapes
step() {
    echo -e "\n${COLOR_YELLOW}▶ $1${COLOR_RESET}"
}

# Fonction pour afficher le succès
success() {
    echo -e "${COLOR_GREEN}✓ $1${COLOR_RESET}"
}

# Fonction pour afficher les erreurs
error() {
    echo -e "${COLOR_RED}✗ $1${COLOR_RESET}"
}

# Test 1: Vérifier que les conteneurs sont en cours d'exécution
step "Test 1: Vérification des conteneurs Docker"
if docker ps | grep -q "$CONTAINER_NAME"; then
    success "Conteneur Odoo en cours d'exécution"
else
    error "Conteneur Odoo non trouvé"
    exit 1
fi

if docker ps | grep -q "shopify_postgres"; then
    success "Conteneur PostgreSQL en cours d'exécution"
else
    error "Conteneur PostgreSQL non trouvé"
    exit 1
fi

# Test 2: Vérifier que Odoo répond
step "Test 2: Test de connectivité Odoo"
if curl -s http://localhost:8069/web/database/selector > /dev/null; then
    success "Odoo répond sur le port 8069"
else
    error "Odoo ne répond pas"
    exit 1
fi

# Test 3: Vérifier que le module est présent
step "Test 3: Vérification de la présence du module"
if docker exec $CONTAINER_NAME ls /mnt/extra-addons/shopify_integration/__manifest__.py > /dev/null 2>&1; then
    success "Module shopify_integration trouvé"

    # Afficher la version
    VERSION=$(docker exec $CONTAINER_NAME grep "version" /mnt/extra-addons/shopify_integration/__manifest__.py | head -1 | cut -d"'" -f2)
    echo -e "   Version: ${COLOR_GREEN}$VERSION${COLOR_RESET}"
else
    error "Module shopify_integration non trouvé"
    exit 1
fi

# Test 4: Vérifier la structure du module
step "Test 4: Vérification de la structure du module"

check_file() {
    if docker exec $CONTAINER_NAME ls "/mnt/extra-addons/shopify_integration/$1" > /dev/null 2>&1; then
        success "$1"
    else
        error "$1 manquant"
        return 1
    fi
}

check_file "models/shopify_instance.py"
check_file "models/shopify_product.py"
check_file "models/shopify_order.py"
check_file "controllers/webhooks.py"
check_file "views/shopify_instance_views.xml"
check_file "security/ir.model.access.csv"
check_file "static/src/js/shopify_dashboard.js"

# Test 5: Mettre à jour la liste des modules
step "Test 5: Mise à jour de la liste des modules Odoo"
docker exec $CONTAINER_NAME odoo -d $DB_NAME --stop-after-init > /tmp/odoo_update.log 2>&1
if [ $? -eq 0 ]; then
    success "Liste des modules mise à jour"
else
    error "Erreur lors de la mise à jour"
    cat /tmp/odoo_update.log
    exit 1
fi

# Test 6: Installer le module
step "Test 6: Installation du module shopify_integration"
echo "   (Cela peut prendre 30-60 secondes...)"

docker exec $CONTAINER_NAME odoo -d $DB_NAME -i shopify_integration --stop-after-init > /tmp/odoo_install.log 2>&1

if grep -q "Module shopify_integration loaded" /tmp/odoo_install.log; then
    success "Module installé avec succès"
else
    if grep -q "error" /tmp/odoo_install.log; then
        error "Erreur lors de l'installation"
        echo "Dernières lignes du log:"
        tail -20 /tmp/odoo_install.log
        exit 1
    else
        success "Module installé (vérification partielle)"
    fi
fi

# Test 7: Vérifier que le module est installé
step "Test 7: Vérification de l'installation"
docker exec -i $CONTAINER_NAME psql -U odoo -d $DB_NAME -t -c "SELECT state FROM ir_module_module WHERE name='shopify_integration';" > /tmp/module_state.txt 2>&1

if grep -q "installed" /tmp/module_state.txt; then
    success "Module marqué comme installé dans la base de données"
else
    error "Module non installé correctement"
    cat /tmp/module_state.txt
    exit 1
fi

# Test 8: Vérifier les tables créées
step "Test 8: Vérification des tables de la base de données"

check_table() {
    if docker exec -i $CONTAINER_NAME psql -U odoo -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='$1';" | grep -q "1"; then
        success "Table $1"
    else
        error "Table $1 manquante"
        return 1
    fi
}

check_table "shopify_instance"
check_table "shopify_product"
check_table "shopify_order"
check_table "shopify_customer"
check_table "shopify_webhook"
check_table "shopify_queue"
check_table "shopify_log"

# Test 9: Vérifier les menus
step "Test 9: Vérification des menus"
MENU_COUNT=$(docker exec -i $CONTAINER_NAME psql -U odoo -d $DB_NAME -t -c "SELECT COUNT(*) FROM ir_ui_menu WHERE name LIKE '%Shopify%';" | tr -d ' ')

if [ "$MENU_COUNT" -gt "0" ]; then
    success "$MENU_COUNT menus Shopify créés"
else
    error "Aucun menu Shopify trouvé"
    exit 1
fi

# Test 10: Redémarrer Odoo
step "Test 10: Redémarrage d'Odoo"
docker-compose restart odoo > /dev/null 2>&1
sleep 10

if docker ps | grep -q "$CONTAINER_NAME"; then
    success "Odoo redémarré avec succès"
else
    error "Erreur lors du redémarrage"
    exit 1
fi

# Test 11: Test final - Accès à l'interface
step "Test 11: Test d'accès à l'interface web"
if curl -s http://localhost:8069/web > /dev/null; then
    success "Interface web accessible"
else
    error "Interface web non accessible"
    exit 1
fi

# Résumé
echo ""
echo -e "${COLOR_GREEN}╔═══════════════════════════════════════════════════════════════╗${COLOR_RESET}"
echo -e "${COLOR_GREEN}║              TOUS LES TESTS SONT PASSÉS ✓                    ║${COLOR_RESET}"
echo -e "${COLOR_GREEN}╚═══════════════════════════════════════════════════════════════╝${COLOR_RESET}"
echo ""
echo -e "${COLOR_BLUE}📊 RÉSUMÉ DE L'INSTALLATION${COLOR_RESET}"
echo -e "   Base de données: ${COLOR_GREEN}$DB_NAME${COLOR_RESET}"
echo -e "   Module version:  ${COLOR_GREEN}$VERSION${COLOR_RESET}"
echo -e "   Menus créés:     ${COLOR_GREEN}$MENU_COUNT${COLOR_RESET}"
echo ""
echo -e "${COLOR_BLUE}🌐 ACCÈS${COLOR_RESET}"
echo -e "   URL:      ${COLOR_GREEN}http://localhost:8069${COLOR_RESET}"
echo -e "   Email:    ${COLOR_GREEN}admin${COLOR_RESET}"
echo -e "   Password: ${COLOR_GREEN}admin${COLOR_RESET}"
echo -e "   Database: ${COLOR_GREEN}$DB_NAME${COLOR_RESET}"
echo ""
echo -e "${COLOR_BLUE}📍 PROCHAINES ÉTAPES${COLOR_RESET}"
echo "   1. Ouvrir http://localhost:8069 dans votre navigateur"
echo "   2. Se connecter avec admin/admin"
echo "   3. Aller dans Shopify > Configuration > Instances"
echo "   4. Cliquer sur 'Setup Wizard' pour configurer"
echo ""
echo -e "${COLOR_YELLOW}💡 LOGS EN TEMPS RÉEL${COLOR_RESET}"
echo "   docker-compose logs -f odoo"
echo ""