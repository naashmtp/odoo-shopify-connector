# Shopify Integration pour Odoo 17

Module complet d'intégration Shopify pour **Odoo 17** développé pour offrir une synchronisation bidirectionnelle complète entre Shopify et Odoo.

> ℹ️ **Version Odoo 17** - Pour Odoo 16, voir la branche `main`

## 🆕 Nouveautés Odoo 17

Cette version est optimisée pour Odoo 17 avec :
- ✅ Assets OWL mis à jour pour Odoo 17
- ✅ Dashboard avec lifecycle hooks modernes
- ✅ Bundles JS/CSS optimisés
- ✅ Compatibilité totale avec l'API Odoo 17

## 🚀 Fonctionnalités

*(Identiques à la version Odoo 16)*

### 1. Configuration & Authentification
- ✅ Gestion multi-instances Shopify
- ✅ Authentification OAuth et API
- ✅ Assistant de configuration en 4 étapes
- ✅ Test de connexion et validation des credentials
- ✅ Configuration automatique des webhooks

### 2. Gestion des Produits
- ✅ Import/Export de produits avec variantes et images
- ✅ Synchronisation des stocks multi-entrepôts
- ✅ Gestion des prix et listes de prix
- ✅ Mapping par SKU et gestion des attributs
- ✅ Support des images produits

### 3. Gestion des Commandes
- ✅ Import automatique des commandes
- ✅ Workflow de traitement automatisé
- ✅ Gestion des statuts et suivi
- ✅ Support des commandes partielles
- ✅ Création automatique des bons de commande Odoo

### 4. Gestion des Clients
- ✅ Synchronisation des clients et adresses
- ✅ Gestion des tags et types de clients
- ✅ Support des adresses multiples
- ✅ Création automatique des partenaires Odoo

### 5. Gestion Financière
- ✅ Import des virements Shopify
- ✅ Réconciliation automatique des paiements
- ✅ Gestion des remboursements et avoirs
- ✅ Création automatique des factures

### 6. Webhooks
- ✅ Configuration automatique des webhooks
- ✅ Traitement en temps réel des événements
- ✅ Validation des signatures
- ✅ Logs détaillés des appels

### 7. Planificateurs et Files d'attente
- ✅ Jobs automatisés pour la synchronisation
- ✅ Gestion des erreurs et reprises
- ✅ Monitoring des performances
- ✅ Système de queue avec priorités

### 8. Rapports et Analytique
- ✅ Tableaux de bord KPI
- ✅ Rapports de ventes et profits
- ✅ Analytics des canaux de vente
- ✅ Dashboard temps réel

## 📦 Installation

### Prérequis

- **Odoo 17.0**
- Python 3.10+
- PostgreSQL 14+
- Bibliothèques Python requises :
  - `requests`

```bash
pip install requests
```

### Installation du module

1. Copiez le module dans le dossier addons d'Odoo :
```bash
# Cloner depuis la branche odoo-17
git clone -b odoo-17 https://github.com/naashmtp/odoo-shopify-connector.git shopify_integration

# Ou copier le dossier
cp -r shopify_integration /path/to/odoo/addons/
```

2. Redémarrez le serveur Odoo :
```bash
sudo systemctl restart odoo
```

3. Activez le mode développeur dans Odoo

4. Allez dans Apps > Mettre à jour la liste des applications

5. Recherchez "Shopify Integration" et cliquez sur Installer

## 🔄 Migration depuis Odoo 16

Si vous avez déjà le module installé en Odoo 16, consultez le fichier `MIGRATION_17.md` pour les instructions de migration.

### Différences principales avec Odoo 16

| Aspect | Odoo 16 | Odoo 17 |
|--------|---------|---------|
| Version module | 16.0.1.0.0 | 17.0.1.0.0 |
| Assets | Glob patterns | Fichiers explicites |
| OWL Dashboard | Lifecycle dans classe | Lifecycle dans setup() |
| Python | 3.8+ | 3.10+ |
| PostgreSQL | 12+ | 14+ |

## ⚙️ Configuration

*(Identique à la version Odoo 16 - voir README.md ou INSTALLATION.md)*

### Étape 1 : Créer une application privée dans Shopify

*[Voir INSTALLATION.md pour les détails complets]*

### Étape 2 : Configurer l'instance dans Odoo

1. Allez dans **Shopify > Configuration > Instances**
2. Cliquez sur **Setup Wizard**
3. Suivez les 4 étapes de configuration

## 🔧 Configuration avancée

### Cron Jobs

*(Identiques à la version Odoo 16)*

Les tâches planifiées sont les mêmes :

| Tâche | Fréquence | Description |
|-------|-----------|-------------|
| Process Queue Jobs | 5 minutes | Traite les jobs en file d'attente |
| Sync Orders | 1 heure | Synchronise les commandes |
| Sync Products | Quotidien (2h) | Synchronise les produits |
| Sync Customers | Quotidien (3h) | Synchronise les clients |
| Sync Stock | 30 minutes | Synchronise les stocks |

## 📊 Dashboard Odoo 17

Le dashboard a été optimisé pour Odoo 17 avec :
- Composants OWL modernes
- Lifecycle hooks dans `setup()`
- Meilleure gestion de la mémoire
- Performance améliorée

Accès : **Shopify > Dashboard**

## 🆕 Spécificités Odoo 17

### Assets

Les assets sont maintenant listés de manière plus explicite :

```python
'assets': {
    'web.assets_backend': [
        'shopify_integration/static/src/js/shopify_dashboard.js',
        'shopify_integration/static/src/css/**/*.css',
        'shopify_integration/static/src/xml/**/*.xml',
    ],
}
```

### Composant OWL

Le dashboard utilise la nouvelle syntaxe OWL d'Odoo 17 :

```javascript
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";

export class ShopifyDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        onWillStart(async () => {
            await this.loadDashboardData();
        });

        onMounted(() => {
            this.startAutoRefresh();
        });

        onWillUnmount(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
    }
}
```

## 🐛 Dépannage

### Erreur : "Module not found" après upgrade

```bash
# Vérifier la version d'Odoo
odoo --version  # Doit afficher 17.0

# Mettre à jour le module
odoo -u shopify_integration -d your_database

# Redémarrer Odoo
sudo systemctl restart odoo
```

### Erreur : "Invalid asset bundle"

Si vous voyez cette erreur, vérifiez que vous êtes bien sur Odoo 17 :

```python
# Dans __manifest__.py, la version doit être :
'version': '17.0.1.0.0'
```

### Dashboard ne s'affiche pas

1. Vérifiez les assets :
```bash
# En mode développeur, allez dans :
Settings > Technical > User Interface > Assets
# Recherchez "shopify_dashboard"
```

2. Videz le cache navigateur (Ctrl+F5)

3. Vérifiez les logs :
```bash
tail -f /var/log/odoo/odoo-server.log | grep shopify
```

## 🔄 Retour vers Odoo 16

Si vous devez revenir à Odoo 16 :

```bash
# Basculer vers la branche main
git checkout main

# Désinstaller la version 17
# Dans Odoo : Apps > Shopify Integration > Uninstall

# Redémarrer Odoo 16
# Réinstaller le module

# Restaurer la sauvegarde de base de données si nécessaire
```

## 📁 Structure du module

*(Identique à la version Odoo 16)*

```
shopify_integration/
├── __init__.py
├── __manifest__.py (version 17.0.1.0.0)
├── CLAUDE.md
├── README.md (Odoo 16)
├── README_ODOO17.md (ce fichier)
├── MIGRATION_17.md
├── INSTALLATION.md
├── models/              # 100% compatible
├── controllers/         # 100% compatible
├── wizards/             # 100% compatible
├── views/               # 100% compatible
├── security/            # 100% compatible
├── data/                # 100% compatible
└── static/
    └── src/
        ├── js/          # Adapté pour Odoo 17
        ├── css/         # Compatible
        └── xml/         # Compatible
```

## 🆚 Compatibilité des versions

| Composant | Odoo 16 | Odoo 17 | Modifications |
|-----------|---------|---------|---------------|
| Modèles Python | ✅ | ✅ | Aucune |
| Vues XML | ✅ | ✅ | Aucune |
| Contrôleurs | ✅ | ✅ | Aucune |
| Wizards | ✅ | ✅ | Aucune |
| Sécurité | ✅ | ✅ | Aucune |
| Data | ✅ | ✅ | Aucune |
| Dashboard JS | ✅ | ✅✨ | Lifecycle hooks |
| Assets | ✅ | ✅✨ | Syntaxe bundles |

✨ = Optimisé pour la version

## 📞 Support

Pour toute question spécifique à Odoo 17 :
1. Consultez `MIGRATION_17.md`
2. Vérifiez les logs Odoo
3. Ouvrez une issue GitHub avec le tag `odoo-17`

## 📜 License

LGPL-3

## 🗺️ Roadmap Odoo 17

- [ ] Utiliser les nouveaux widgets Odoo 17
- [ ] Support du nouveau système de tours
- [ ] Intégration avec Odoo 17 Studio
- [ ] Nouveaux rapports avec Query Builder
- [ ] Support des nouvelles fonctionnalités multi-sociétés

## 📚 Ressources

- [Documentation Odoo 17](https://www.odoo.com/documentation/17.0/)
- [Shopify API Documentation](https://shopify.dev/docs/api)
- [OWL Framework](https://github.com/odoo/owl)
- [Repository GitHub](https://github.com/naashmtp/odoo-shopify-connector)

---

**Version Odoo 17 - Optimisé pour les performances et la modernité** 🚀