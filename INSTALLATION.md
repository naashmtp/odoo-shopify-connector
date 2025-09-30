# Guide d'Installation - Shopify Integration pour Odoo 16

## Prérequis système

### Serveur Odoo
- Odoo 16.0
- Python 3.8 ou supérieur
- PostgreSQL 12 ou supérieur
- Accès SSH au serveur (pour installation)
- Accès root ou sudo (pour installation des dépendances)

### Dépendances Python
```bash
pip install requests
```

### Accès Shopify
- Compte Shopify (Plan Basic ou supérieur recommandé)
- Accès administrateur à la boutique
- Possibilité de créer une application privée

## Installation pas à pas

### 1. Installation des dépendances Python

```bash
# Se connecter au serveur Odoo
ssh user@your-odoo-server

# Activer l'environnement virtuel Odoo (si utilisé)
source /path/to/odoo-venv/bin/activate

# Installer requests
pip install requests

# Vérifier l'installation
python -c "import requests; print(requests.__version__)"
```

### 2. Installation du module dans Odoo

#### Option A : Installation via Git (Recommandé)

```bash
# Aller dans le dossier des modules Odoo
cd /path/to/odoo/addons

# Cloner le repository
git clone https://github.com/naashmtp/odoo-shopify-connector.git shopify_integration

# Vérifier les permissions
chown -R odoo:odoo shopify_integration
chmod -R 755 shopify_integration
```

#### Option B : Installation manuelle

```bash
# Copier le dossier du module
cp -r /chemin/source/shopify_integration /path/to/odoo/addons/

# Vérifier les permissions
chown -R odoo:odoo /path/to/odoo/addons/shopify_integration
chmod -R 755 /path/to/odoo/addons/shopify_integration
```

### 3. Redémarrage d'Odoo

```bash
# Avec systemd
sudo systemctl restart odoo

# Ou manuellement
sudo /etc/init.d/odoo restart

# Vérifier que le service est actif
sudo systemctl status odoo
```

### 4. Mise à jour de la liste des applications

1. Connectez-vous à Odoo en tant qu'administrateur
2. Activez le mode développeur :
   - Allez dans **Paramètres**
   - En bas de page, cliquez sur **Activer le mode développeur**
3. Allez dans **Apps** (Applications)
4. Cliquez sur **Mettre à jour la liste des applications**
5. Attendez la fin du processus (environ 30 secondes)

### 5. Installation du module

1. Dans **Apps**, recherchez "Shopify Integration"
2. Cliquez sur **Installer**
3. Patientez pendant l'installation (1-2 minutes)
4. Vérifiez qu'il n'y a pas d'erreurs dans les logs

### 6. Vérification de l'installation

```bash
# Vérifier les logs Odoo
sudo tail -f /var/log/odoo/odoo-server.log

# Vous devriez voir :
# INFO shopify_integration: Shopify Integration: Running pre-installation checks...
# INFO shopify_integration: ✓ requests library found
# INFO shopify_integration: Module installed successfully!
```

## Configuration Shopify

### 1. Créer une application privée dans Shopify

1. Connectez-vous à votre admin Shopify
2. Allez dans **Settings** > **Apps and sales channels**
3. Cliquez sur **Develop apps**
4. Cliquez sur **Create an app**
5. Nom de l'application : "Odoo Integration"
6. Cliquez sur **Create app**

### 2. Configurer les permissions API

1. Dans l'onglet **Configuration**, cliquez sur **Configure Admin API scopes**
2. Sélectionnez les permissions suivantes :

#### Products (Produits)
- ✅ `read_products`
- ✅ `write_products`

#### Orders (Commandes)
- ✅ `read_orders`
- ✅ `write_orders`

#### Customers (Clients)
- ✅ `read_customers`
- ✅ `write_customers`

#### Inventory (Inventaire)
- ✅ `read_inventory`
- ✅ `write_inventory`

#### Fulfillments (Livraisons)
- ✅ `read_fulfillments`
- ✅ `write_fulfillments`

#### Locations (Emplacements)
- ✅ `read_locations`

3. Cliquez sur **Save**

### 3. Installer l'application et récupérer les credentials

1. Cliquez sur l'onglet **API credentials**
2. Cliquez sur **Install app**
3. Confirmez l'installation
4. Notez les informations suivantes :
   - **API key** (commence généralement par `shppa_`)
   - **API secret key**
   - **Admin API access token** (commence par `shpat_`)

⚠️ **IMPORTANT** : Conservez ces informations en sécurité !

## Configuration dans Odoo

### 1. Première connexion au module

1. Dans Odoo, allez dans **Shopify**
2. Vous verrez le menu principal vide
3. Allez dans **Configuration** > **Instances**
4. Cliquez sur **Créer**

### 2. Utilisation de l'assistant de configuration

1. Dans la fiche instance, cliquez sur le bouton **Setup Wizard**
2. L'assistant s'ouvre en 4 étapes

#### Étape 1 : Credentials

- **Instance Name** : Donnez un nom (ex: "Ma Boutique")
- **Shop URL** : Votre URL Shopify (ex: `monmagasin.myshopify.com`)
  - ⚠️ Ne pas mettre `https://`
  - ⚠️ Doit se terminer par `.myshopify.com`
- **API Key** : Collez votre API key
- **API Secret** : Collez votre API secret
- **Access Token** : Collez votre Admin API access token

Cliquez sur **Test Connection** pour vérifier.

Si le test est réussi ✅, cliquez sur **Suivant**

#### Étape 2 : Configuration

Cochez les options souhaitées :

- ✅ **Auto Import Orders** : Import automatique des nouvelles commandes
- ⬜ **Auto Import Products** : Import auto des nouveaux produits (décoché par défaut)
- ✅ **Auto Import Customers** : Import auto des nouveaux clients
- ✅ **Auto Sync Stock** : Synchronisation automatique des stocks
- ✅ **Auto Create Invoices** : Création automatique des factures

Cliquez sur **Suivant**

#### Étape 3 : Mapping

Sélectionnez les valeurs par défaut :

- **Default Warehouse** : Votre entrepôt principal
- **Default Pricelist** : Votre liste de prix (ex: "Public Pricelist")
- **Default Payment Term** : Conditions de paiement (ex: "Immédiat")
- **Sales Team** : Équipe commerciale (optionnel)

Cliquez sur **Suivant**

#### Étape 4 : Webhooks

- ✅ **Setup Webhooks** : Laissez coché pour configurer automatiquement les webhooks

Cliquez sur **Terminer**

### 3. Vérification de la configuration

1. L'instance doit maintenant avoir le statut **Connected** (vert)
2. Vérifiez dans **Shopify** > **Operations** > **Webhooks** que 8 webhooks ont été créés :
   - orders/create
   - orders/updated
   - orders/cancelled
   - orders/fulfilled
   - products/create
   - products/update
   - customers/create
   - refunds/create

## Première synchronisation

### 1. Synchronisation initiale

1. Allez dans **Shopify** > **Tools** > **Synchronize**
2. Sélectionnez votre instance
3. Cochez tout :
   - ✅ Sync Products
   - ✅ Sync Orders
   - ✅ Sync Customers
4. ✅ **Use Queue** : Recommandé pour grandes quantités
5. Cliquez sur **Sync All**

### 2. Monitoring de la synchronisation

1. Allez dans **Shopify** > **Operations** > **Queue**
2. Vous verrez 3 jobs créés :
   - Import Products
   - Import Orders
   - Import Customers
3. Les jobs passent de **Queued** → **Running** → **Done**

### 3. Vérification des données importées

#### Produits
```
Shopify > Operations > Products
```
- Vérifiez que vos produits Shopify sont listés
- Vérifiez les variantes et images

#### Commandes
```
Shopify > Operations > Orders
```
- Vérifiez vos commandes récentes
- Vérifiez les statuts financiers

#### Clients
```
Shopify > Operations > Customers
```
- Vérifiez vos clients
- Vérifiez les adresses

## Tests de fonctionnement

### Test 1 : Création de commande

1. Créez une commande de test dans Shopify
2. Attendez 1-2 minutes (webhook)
3. Vérifiez dans **Shopify > Operations > Orders**
4. La commande doit apparaître
5. Un bon de commande Odoo doit être créé automatiquement

### Test 2 : Modification de stock

1. Modifiez le stock d'un produit dans Odoo
2. Attendez le prochain cron (max 30 minutes)
3. Vérifiez dans Shopify que le stock a été mis à jour

### Test 3 : Webhooks

1. Allez dans **Shopify > Operations > Webhooks**
2. Sélectionnez un webhook
3. Cliquez sur **Test Webhook**
4. Vérifiez dans les logs qu'il n'y a pas d'erreur

## Dépannage

### Erreur : "Module not found"

```bash
# Vérifier le chemin du module
ls -la /path/to/odoo/addons/shopify_integration

# Vérifier les permissions
sudo chown -R odoo:odoo /path/to/odoo/addons/shopify_integration

# Redémarrer Odoo
sudo systemctl restart odoo
```

### Erreur : "No module named 'requests'"

```bash
# Installer requests dans le bon environnement
source /path/to/odoo-venv/bin/activate
pip install requests

# Redémarrer Odoo
sudo systemctl restart odoo
```

### Erreur : "Connection failed"

1. Vérifiez l'URL Shopify (doit finir par `.myshopify.com`)
2. Vérifiez l'Access Token
3. Vérifiez les permissions API dans Shopify
4. Testez manuellement avec curl :

```bash
curl -X GET \
  "https://VOTRE-BOUTIQUE.myshopify.com/admin/api/2023-10/shop.json" \
  -H "X-Shopify-Access-Token: VOTRE-ACCESS-TOKEN"
```

### Webhooks ne fonctionnent pas

1. Vérifiez que votre serveur Odoo est accessible depuis Internet
2. Vérifiez le pare-feu :

```bash
sudo ufw status
sudo ufw allow 8069/tcp  # Si nécessaire
```

3. Testez l'endpoint webhook :

```bash
curl -X GET https://votre-domaine.com/shopify/webhook/test
# Doit retourner : {"status": "ok", "message": "Webhook endpoint is accessible"}
```

## Support

Pour toute question :
1. Consultez les logs : `/var/log/odoo/odoo-server.log`
2. Vérifiez les logs du module : **Shopify > Operations > Logs**
3. Ouvrez une issue sur GitHub

## Checklist de mise en production

- [ ] Module installé et testé en développement
- [ ] Credentials Shopify sécurisés
- [ ] Webhooks testés
- [ ] Synchronisation initiale réussie
- [ ] Tests de création de commande OK
- [ ] Tests de mise à jour de stock OK
- [ ] Backup de la base de données effectué
- [ ] Monitoring des logs configuré
- [ ] Documentation équipe complétée
- [ ] Formation utilisateurs effectuée

Bonne installation ! 🚀
