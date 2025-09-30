# Shopify Integration pour Odoo 16

Module complet d'intégration Shopify pour Odoo 16 développé pour offrir une synchronisation bidirectionnelle complète entre Shopify et Odoo.

## 🚀 Fonctionnalités

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

- Odoo 16.0
- Python 3.8+
- Bibliothèques Python requises :
  - `requests`

```bash
pip install requests
```

### Installation du module

1. Copiez le module dans le dossier addons d'Odoo :
```bash
cp -r shopify_integration /path/to/odoo/addons/
```

2. Redémarrez le serveur Odoo :
```bash
sudo systemctl restart odoo
```

3. Activez le mode développeur dans Odoo

4. Allez dans Apps > Mettre à jour la liste des applications

5. Recherchez "Shopify Integration" et cliquez sur Installer

## ⚙️ Configuration

### Étape 1 : Créer une application privée dans Shopify

1. Connectez-vous à votre boutique Shopify
2. Allez dans Settings > Apps and sales channels > Develop apps
3. Cliquez sur "Create an app"
4. Donnez un nom à votre application (ex: "Odoo Integration")
5. Configurez les permissions API (Admin API access scopes) :
   - `read_products`, `write_products`
   - `read_orders`, `write_orders`
   - `read_customers`, `write_customers`
   - `read_inventory`, `write_inventory`
   - `read_fulfillments`, `write_fulfillments`
6. Installez l'application et récupérez :
   - API Key
   - API Secret
   - Access Token

### Étape 2 : Configurer l'instance dans Odoo

1. Dans Odoo, allez dans **Shopify > Configuration > Instances**
2. Cliquez sur **Créer**
3. Cliquez sur **Setup Wizard** pour lancer l'assistant de configuration :

#### **Étape 1 - Credentials**
- Nom de l'instance : `Ma Boutique Shopify`
- Shop URL : `monmagasin.myshopify.com`
- API Key : `votre_api_key`
- API Secret : `votre_api_secret`
- Access Token : `votre_access_token`
- Cliquez sur **Test Connection** pour vérifier
- Cliquez sur **Suivant**

#### **Étape 2 - Configuration**
- Cochez les options souhaitées :
  - ✅ Auto Import Orders
  - ✅ Auto Import Customers
  - ✅ Auto Sync Stock
  - ✅ Auto Create Invoices
- Cliquez sur **Suivant**

#### **Étape 3 - Mapping**
- Sélectionnez l'entrepôt par défaut
- Sélectionnez la liste de prix par défaut
- Sélectionnez les conditions de paiement
- Sélectionnez l'équipe commerciale
- Cliquez sur **Suivant**

#### **Étape 4 - Webhooks**
- Cochez **Setup Webhooks**
- Cliquez sur **Terminer**

### Étape 3 : Première synchronisation

1. Allez dans **Shopify > Tools > Synchronize**
2. Sélectionnez votre instance
3. Cochez les éléments à synchroniser :
   - ✅ Sync Products
   - ✅ Sync Orders
   - ✅ Sync Customers
4. Cliquez sur **Sync All**

## 🔄 Utilisation

### Import/Export de produits

#### Import depuis Shopify
```
Shopify > Tools > Import/Export
- Opération : Import Products
- Instance : [Sélectionner votre instance]
- Create Queue Job : Oui (recommandé)
- Exécuter
```

#### Export vers Shopify
```
Shopify > Tools > Import/Export
- Opération : Export Products
- Sélectionner les produits à exporter
- Exécuter
```

### Gestion des commandes

Les commandes sont importées automatiquement via webhooks ou cron jobs.

Pour forcer une synchronisation :
```
Shopify > Tools > Synchronize
- Sync Orders uniquement
```

### Monitoring

#### Dashboard
```
Shopify > Dashboard
- Vue d'ensemble en temps réel
- Statistiques de synchronisation
- Erreurs récentes
```

#### Logs
```
Shopify > Operations > Logs
- Filtres par type d'opération
- Filtres par statut
- Recherche avancée
```

#### Queue
```
Shopify > Operations > Queue
- Jobs en attente
- Jobs en cours
- Jobs échoués avec retry
```

## 🔧 Configuration avancée

### Cron Jobs

Les tâches planifiées suivantes sont configurées par défaut :

| Tâche | Fréquence | Description |
|-------|-----------|-------------|
| Process Queue Jobs | 5 minutes | Traite les jobs en file d'attente |
| Sync Orders | 1 heure | Synchronise les commandes |
| Sync Products | Quotidien (2h) | Synchronise les produits |
| Sync Customers | Quotidien (3h) | Synchronise les clients |
| Sync Stock | 30 minutes | Synchronise les stocks |
| Cleanup Logs | Hebdomadaire | Nettoie les logs > 90 jours |
| Error Notifications | Quotidien (9h) | Envoie les notifications d'erreurs |

Pour modifier : **Settings > Technical > Automation > Scheduled Actions**

### Webhooks

Les webhooks suivants sont créés automatiquement :

- `orders/create` : Nouvelle commande
- `orders/updated` : Commande mise à jour
- `orders/cancelled` : Commande annulée
- `orders/fulfilled` : Commande livrée
- `products/create` : Nouveau produit
- `products/update` : Produit mis à jour
- `customers/create` : Nouveau client
- `refunds/create` : Nouveau remboursement

URL de base : `https://votre-domaine.com/shopify/webhook/`

## 🐛 Dépannage

### Erreur : "Connection failed"
- Vérifiez que l'URL Shopify se termine par `.myshopify.com`
- Vérifiez que l'Access Token est valide
- Vérifiez les permissions API dans Shopify

### Les commandes ne s'importent pas
- Vérifiez que "Auto Import Orders" est activé
- Vérifiez les webhooks dans Shopify Admin
- Consultez les logs : **Shopify > Operations > Logs**

### Les stocks ne se synchronisent pas
- Vérifiez que "Auto Sync Stock" est activé
- Vérifiez que les produits sont liés (SKU matching)
- Vérifiez les logs de synchronisation

### Les webhooks ne fonctionnent pas
- Vérifiez que votre serveur Odoo est accessible depuis Internet
- Vérifiez le Webhook Secret dans la configuration
- Testez avec : **Shopify > Operations > Webhooks > Test Webhook**

## 📝 Structure du module

```
shopify_integration/
├── __init__.py
├── __manifest__.py
├── CLAUDE.md                    # Instructions projet
├── README.md                    # Ce fichier
├── models/
│   ├── __init__.py
│   ├── shopify_instance.py      # Configuration instances
│   ├── shopify_product.py       # Gestion produits
│   ├── shopify_order.py         # Gestion commandes
│   ├── shopify_customer.py      # Gestion clients
│   ├── shopify_webhook.py       # Webhooks
│   ├── shopify_queue.py         # File d'attente
│   └── shopify_log.py           # Logs
├── controllers/
│   ├── __init__.py
│   └── webhooks.py              # Contrôleur webhooks
├── wizards/
│   ├── __init__.py
│   ├── onboarding_wizard.py     # Assistant configuration
│   ├── import_export_wizard.py  # Import/Export
│   └── sync_wizard.py           # Synchronisation
├── views/
│   ├── shopify_instance_views.xml
│   ├── shopify_product_views.xml
│   ├── shopify_order_views.xml
│   ├── shopify_customer_views.xml
│   ├── shopify_webhook_views.xml
│   ├── shopify_queue_views.xml
│   ├── shopify_log_views.xml
│   ├── onboarding_wizard_views.xml
│   ├── import_export_wizard_views.xml
│   ├── sync_wizard_views.xml
│   └── menu_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
├── data/
│   ├── ir_cron.xml              # Tâches planifiées
│   ├── queue_job.xml            # Configuration queue
│   └── demo.xml                 # Données démo
└── static/
    ├── description/
    │   ├── icon.png
    │   ├── banner.png
    │   └── index.html
    └── src/
        ├── js/
        │   └── shopify_dashboard.js
        ├── css/
        │   └── shopify.css
        └── xml/
            └── shopify_dashboard.xml
```

## 🔐 Sécurité

### Groupes de sécurité

- **Shopify User** : Lecture seule sur toutes les données
- **Shopify Manager** : Accès complet (CRUD)

### Multi-sociétés

Le module supporte le multi-sociétés :
- Chaque instance Shopify est liée à une société
- Les données sont automatiquement filtrées par société
- Les utilisateurs ne voient que les données de leurs sociétés

## 🤝 Support

Pour toute question ou problème :
1. Consultez la documentation dans le dossier `static/description/`
2. Vérifiez les logs dans **Shopify > Operations > Logs**
3. Créez une issue sur le repository

## 📜 License

LGPL-3

## 👨‍💻 Développement

### Tests

```bash
# Lancer les tests
python -m pytest tests/

# Vérifier le code
pylint models/ controllers/ wizards/
```

### Contribuer

1. Forkez le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Pushez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 🗺️ Roadmap

- [ ] Support Shopify Plus
- [ ] Gestion des promotions
- [ ] Analytics avancées
- [ ] Support multi-devises avancé
- [ ] Import des avis clients
- [ ] Gestion des abonnements
- [ ] Support des metafields personnalisés

## 📚 Ressources

- [Documentation Odoo 16](https://www.odoo.com/documentation/16.0/)
- [Shopify API Documentation](https://shopify.dev/docs/api)
- [Repository GitHub](https://github.com/naashmtp/odoo-shopify-connector)

---

**Fait avec ❤️ pour casser le prix du marché**