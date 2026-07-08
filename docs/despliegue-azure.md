# Despliegue de Cordada en Azure (crédito de estudiante)

Guía paso a paso para desplegar con **Azure App Service** (web) y
**Azure Database for PostgreSQL Flexible Server** (base de datos),
pensada para el crédito de 100 € de Azure for Students.

## Coste estimado

| Recurso | SKU | Coste aprox. |
|---|---|---|
| App Service (Linux) | B1 (Basic) | ~12 €/mes |
| PostgreSQL Flexible Server | B1ms (Burstable) + 32 GB | ~15 €/mes |

≈ 27 €/mes → los 100 € cubren unos 3-4 meses, de sobra hasta la defensa.
Consejo: crea una **alerta de presupuesto** en el portal (Cost Management →
Budgets) al 50 % y 90 % del crédito.

## Requisitos previos

1. Activa [Azure for Students](https://azure.microsoft.com/free/students/) con el correo de la universidad.
2. Instala la CLI de Azure: `winget install Microsoft.AzureCLI` (reabre la terminal después).
3. Inicia sesión: `az login`.

## 1. Variables (elige tus nombres)

```powershell
$RG = "cordada-rg"
$LOC = "spaincentral"          # o "francecentral" si Spain Central no está disponible
$PLAN = "cordada-plan"
$APP = "cordada-tfg"           # el dominio será cordada-tfg.azurewebsites.net (debe ser único)
$DB_SERVER = "cordada-db-tfg"  # único a nivel global
$DB_PASS = "ELIGE-UNA-CONTRASENA-FUERTE"
```

## 2. Grupo de recursos y base de datos

```powershell
az group create --name $RG --location $LOC

az postgres flexible-server create `
    --resource-group $RG --name $DB_SERVER --location $LOC `
    --tier Burstable --sku-name Standard_B1ms --storage-size 32 `
    --version 16 --admin-user cordada_admin --admin-password $DB_PASS `
    --public-access 0.0.0.0   # permite el acceso desde servicios de Azure

az postgres flexible-server db create `
    --resource-group $RG --server-name $DB_SERVER --database-name cordada
```

## 3. Plan y aplicación web

```powershell
az appservice plan create --resource-group $RG --name $PLAN --location $LOC `
    --is-linux --sku B1

az webapp create --resource-group $RG --plan $PLAN --name $APP `
    --runtime "PYTHON:3.12"
```

## 4. Configuración de la aplicación

```powershell
$SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 50 | ForEach-Object {[char]$_})

az webapp config appsettings set --resource-group $RG --name $APP --settings `
    SECRET_KEY=$SECRET `
    DEBUG=False `
    DATABASE_URL="postgres://cordada_admin:$DB_PASS@$DB_SERVER.postgres.database.azure.com:5432/cordada?sslmode=require" `
    MEDIA_ROOT="/home/media" `
    SCM_DO_BUILD_DURING_DEPLOYMENT=true

az webapp config set --resource-group $RG --name $APP --startup-file "startup.sh"
```

`MEDIA_ROOT=/home/media` guarda las fotos y GPX en el disco **persistente**
de App Service: a diferencia de Render gratuito, no se pierden al redesplegar.

## 5. Despliegue continuo desde GitHub

La forma más sencilla es desde el portal: **App Service → Deployment Center →
GitHub**, autoriza tu cuenta y elige el repositorio `Cordada` y la rama `main`.
Azure crea un workflow de GitHub Actions que despliega en cada push.

Alternativa por CLI:

```powershell
az webapp deployment github-actions add --resource-group $RG --name $APP `
    --repo "antonio-gallego-ortiz/Cordada" --branch main --login-with-github
```

## 6. Primeros pasos tras el despliegue

Abre una consola SSH en el contenedor (App Service → SSH, o
`az webapp ssh --resource-group $RG --name $APP`) y ejecuta:

```bash
python manage.py createsuperuser
python manage.py seed_demo   # opcional: datos de ejemplo
```

La aplicación quedará en `https://<APP>.azurewebsites.net`. El endpoint de
salud es `/salud/` (configúralo en App Service → Health check).

## 7. Correo de recuperación de contraseña (opcional)

Configura un SMTP con las variables `EMAIL_*` (por ejemplo, un Gmail con
contraseña de aplicación) en App Service → Environment variables.

## Solución de problemas

- **Logs en vivo:** `az webapp log tail --resource-group $RG --name $APP`.
- **La app no arranca:** comprueba que el *startup command* es `startup.sh`
  y revisa los logs del contenedor.
- **Error de conexión a la base de datos:** verifica la regla de firewall del
  Flexible Server (paso 2, `--public-access 0.0.0.0`) y la `DATABASE_URL`.
- **Estáticos sin estilos:** confirma que `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
  y que el despliegue ejecutó `collectstatic` (lo hace `startup.sh`).
