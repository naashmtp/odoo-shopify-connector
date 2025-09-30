# Test Odoo 17 avec Docker

## Démarrage rapide

### 1. Démarrer les conteneurs

```bash
# Dans le dossier du module
docker-compose up -d

# Vérifier les logs
docker-compose logs -f odoo
```

### 2. Accéder à Odoo

Ouvrez votre navigateur : http://localhost:8069

**Credentials par défaut:**
- Email: admin
- Password: admin
- Base de données: odoo17_shopify

### 3. Installer le module

1. Activez le mode développeur : Settings > Activate Developer Mode
2. Allez dans Apps
3. Cliquez sur "Update Apps List"
4. Recherchez "Shopify Integration"
5. Cliquez sur "Install"

### 4. Tester le module

#### Test 1: Configuration Wizard
```
Shopify > Configuration > Instances > Create > Setup Wizard
```

#### Test 2: Dashboard
```
Shopify > Dashboard
```

#### Test 3: Vues principales
```
Shopify > Operations > Products
Shopify > Operations > Orders
Shopify > Operations > Customers
```

## Commandes utiles

### Arrêter les conteneurs
```bash
docker-compose down
```

### Arrêter et supprimer les données
```bash
docker-compose down -v
```

### Redémarrer Odoo uniquement
```bash
docker-compose restart odoo
```

### Voir les logs
```bash
# Tous les logs
docker-compose logs -f

# Logs Odoo uniquement
docker-compose logs -f odoo

# Logs PostgreSQL
docker-compose logs -f db
```

### Accéder au shell Odoo
```bash
docker exec -it shopify_odoo17 bash
```

### Accéder au shell PostgreSQL
```bash
docker exec -it shopify_postgres psql -U odoo -d odoo17_shopify
```

### Réinstaller le module
```bash
docker exec -it shopify_odoo17 odoo -d odoo17_shopify -u shopify_integration --stop-after-init
docker-compose restart odoo
```

## Résolution de problèmes

### Le port 8069 est déjà utilisé

Modifiez le port dans docker-compose.yml :
```yaml
ports:
  - "8070:8069"  # Utilisez 8070 au lieu de 8069
```

### PostgreSQL ne démarre pas

```bash
# Supprimer le volume
docker-compose down -v

# Redémarrer
docker-compose up -d
```

### Le module n'apparaît pas

```bash
# Vérifier que le module est bien monté
docker exec -it shopify_odoo17 ls -la /mnt/extra-addons/shopify_integration

# Mettre à jour la liste
docker exec -it shopify_odoo17 odoo -d odoo17_shopify --stop-after-init
docker-compose restart odoo
```

## URLs utiles

- **Interface Odoo:** http://localhost:8069
- **API Webhook test:** http://localhost:8069/shopify/webhook/test
- **Database Manager:** http://localhost:8069/web/database/manager

## Nettoyage complet

Pour tout supprimer et repartir de zéro :

```bash
# Arrêter et supprimer tout
docker-compose down -v

# Supprimer les images (optionnel)
docker rmi odoo:17.0 postgres:15

# Redémarrer
docker-compose up -d
```