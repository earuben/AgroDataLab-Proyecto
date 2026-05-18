# Guia de entrega y despliegue - AgroDataLab EnviroPro

Esta guia resume los pasos para subir el proyecto a GitHub y desplegarlo en PythonAnywhere sin incluir archivos locales de trabajo, configuracion privada, entorno virtual ni archivos internos de Codex/IA.

## 1. Archivos que NO deben subirse

Comprobar que estos archivos o carpetas no aparecen en GitHub:

```text
.codex/
AGENTS.md
PROMPT_INICIAL_CODEX.txt
.env
.venv/
venv/
env/
db.sqlite3
db.sqlite3-journal
__pycache__/
*.pyc
staticfiles/
media/
pdf_pages/
*.log
```

Motivo:

- `.codex/`, `AGENTS.md` y `PROMPT_INICIAL_CODEX.txt` son archivos locales de trabajo.
- `.env` puede contener claves privadas.
- `.venv/` no se sube nunca; se reconstruye con `requirements.txt`.
- `db.sqlite3` no se sube; se crea en el servidor con migraciones e importacion.
- `staticfiles/` se genera con `collectstatic`.
- `__pycache__/`, `*.pyc` y `*.log` son archivos temporales.

## 2. Comprobar `.gitignore`

El archivo `.gitignore` debe contener al menos:

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.venv/
venv/
env/

# Django
*.log
db.sqlite3
db.sqlite3-journal
media/
staticfiles/
pdf_pages/

# Environment
.env

# IDE
.vscode/
.idea/
.codex/

# Codex / IA local
AGENTS.md
PROMPT_INICIAL_CODEX.txt

# OS
.DS_Store
Thumbs.db
```

## 3. Comprobar que Git no incluye archivos internos

Desde la raiz del proyecto:

```powershell
git status --short
git ls-files .codex AGENTS.md PROMPT_INICIAL_CODEX.txt .env db.sqlite3 .venv
```

El segundo comando no debe mostrar nada.

Si aparece algun archivo interno, sacarlo del indice sin borrarlo del ordenador:

```powershell
git rm --cached -r .codex
git rm --cached AGENTS.md PROMPT_INICIAL_CODEX.txt
git rm --cached .env
git rm --cached src\db.sqlite3
```

Despues:

```powershell
git add .gitignore
git commit --amend --no-edit
```

Si ya se habia hecho `push`, usar un commit nuevo:

```powershell
git add .gitignore
git commit -m "Limpiar archivos locales de trabajo"
git push
```

## 4. Archivos que SI deben subirse

Estos archivos son necesarios para la entrega:

```text
README.md
requirements.txt
.env.example
data/processed/enviropro_completo_2024_2026.csv
docs/EnunciadoProyecto.pdf
docs/GUIA_MINIMA_CODEX.md
docs/GUIA_ENTREGA_DESPLIEGUE.md
notebooks/analisis_enviropro.ipynb
notebooks/analisis_enviropro.py
reports/analisis_enviropro.md
reports/figures/
src/
static/.gitkeep
```

Tambien se suben los resultados generados del proyecto:

```text
src/exports/alertas.csv
src/exports/recomendaciones.csv
src/exports/resumen_indicadores.csv
src/ml/artifacts/dryness_classifier.joblib
src/ml/artifacts/dryness_metrics.json
```

## 5. Validar antes de subir

Desde `src/`:

```powershell
cd src
..\.venv\Scripts\python.exe manage.py check
```

Opcional, comprobar que la web arranca:

```powershell
..\.venv\Scripts\python.exe manage.py runserver
```

Abrir:

```text
http://127.0.0.1:8000/
```

## 6. Crear o actualizar el repositorio GitHub

Si todavia no existe remoto:

```powershell
git branch -M main
git remote add origin URL_DEL_REPOSITORIO
git push -u origin main
```

Si ya existe remoto:

```powershell
git push
```

Comprobar en GitHub que no aparecen:

```text
.codex/
AGENTS.md
PROMPT_INICIAL_CODEX.txt
.env
db.sqlite3
.venv/
```

## 7. Despliegue en PythonAnywhere

Abrir una consola Bash en PythonAnywhere:

```bash
git clone URL_DEL_REPOSITORIO
cd agrodatalab_minimo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crear `.env` en PythonAnywhere:

```bash
nano .env
```

Contenido:

```text
DJANGO_SECRET_KEY=poner-una-clave-larga-y-segura
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tuusuario.pythonanywhere.com
```

Preparar Django:

```bash
cd src
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
python manage.py import_enviropro
python manage.py generate_alerts
python manage.py suggest_recommendations --limit 25
python manage.py train_dryness_model
python manage.py export_results
```

## 8. Configuracion Web en PythonAnywhere

En la pestana **Web**:

- Crear nueva web app.
- Elegir **Manual configuration**.
- Elegir version de Python compatible.

Configurar:

```text
Source code: /home/tuusuario/agrodatalab_minimo
Working directory: /home/tuusuario/agrodatalab_minimo/src
Virtualenv: /home/tuusuario/agrodatalab_minimo/.venv
```

Editar el archivo WSGI:

```python
import os
import sys

project_home = "/home/tuusuario/agrodatalab_minimo/src"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Configurar static files:

```text
URL: /static/
Directory: /home/tuusuario/agrodatalab_minimo/src/staticfiles
```

Pulsar **Reload**.

## 9. Comprobaciones finales en la web desplegada

Abrir:

```text
https://tuusuario.pythonanywhere.com
```

Comprobar:

- Login y logout.
- Registro de usuario.
- Dashboard privado.
- Importacion.
- Alertas.
- Revision manual de alertas.
- CRUD de recomendaciones.
- Pagina Acerca.
- Graficos e indicadores del dashboard.

## 10. README antes de entregar

Rellenar en `README.md`:

```text
Integrantes
URL publica
Usuario de prueba
Video explicativo
```

No poner contrasenas personales. Si se entrega un usuario de prueba, usar una contrasena creada solo para la entrega.

## 11. Nota academica

Esta guia se limita a limpiar archivos locales, secretos y configuraciones internas que no pertenecen al despliegue. Si las normas del centro exigen declarar herramientas utilizadas durante el desarrollo, debe hacerse segun esas normas.
