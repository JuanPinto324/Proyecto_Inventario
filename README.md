# 🛒 PyCommerceX

Sistema de Gestión de Inventario y Punto de Venta  
**Universidad de La Guajira — Ingeniería de Software II**

---

## 🚀 Instalación Local (Paso a Paso)

### 1. Requisitos
- Python 3.10 o superior
- Git

### 2. Clonar y configurar
```bash
git clone https://github.com/TU_USUARIO/pycommercex.git
cd pycommercex

# Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Instalar dependencias
pip install -r requirements.txt

# Copiar archivo de entorno
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux
```

### 3. Ejecutar
```bash
python run.py
```

Abre `http://localhost:5000` en tu navegador.

### 🔑 Credenciales por defecto
| Campo | Valor |
|-------|-------|
| Identificación | `0000000000` |
| Contraseña | `admin123` |
| Rol | Jefe |

---

## ☁️ Despliegue en Render (Gratis)

### Paso 1 — Subir a GitHub
```bash
git init
git add .
git commit -m "Initial commit PyCommerceX"
git remote add origin https://github.com/TU_USUARIO/pycommercex.git
git push -u origin main
```

### Paso 2 — Crear cuenta en Render
1. Ir a [render.com](https://render.com) → Sign up con GitHub
2. Dashboard → **New** → **Web Service**
3. Conectar el repositorio `pycommercex`

### Paso 3 — Configurar el servicio
| Campo | Valor |
|-------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn run:app` |

### Paso 4 — Base de datos PostgreSQL
1. En Render → **New** → **PostgreSQL** → plan **Free**
2. Nombre: `pycommercex-db`
3. En tu Web Service → **Environment** → agregar variable:
   - `DATABASE_URL` = (copiar desde la BD de Render)
   - `SECRET_KEY` = (cualquier texto largo aleatorio)

### Paso 5 — Deploy
- Click **Deploy** → esperar ~2 minutos
- Tu app estará en: `https://pycommercex.onrender.com`

---

## 📁 Estructura del Proyecto

```
pycommercex/
├── run.py                    # Punto de entrada
├── requirements.txt          # Dependencias
├── render.yaml               # Config Render
├── Procfile                  # Comando de inicio
└── app/
    ├── __init__.py           # App factory + config
    ├── models.py             # Modelos BD
    ├── routes/
    │   ├── auth.py           # Login / Logout
    │   ├── dashboard.py      # Panel principal
    │   ├── inventory.py      # Inventario
    │   ├── pos.py            # Punto de venta
    │   ├── sales.py          # Historial ventas
    │   └── users.py          # Gestión usuarios
    ├── templates/            # HTML (Jinja2)
    └── static/css/main.css   # Estilos globales
```

---

## 👥 Roles del Sistema

| Rol | Color | Acceso |
|-----|-------|--------|
| Jefe | 🟡 Amarillo | Control total |
| Administrador | 🔴 Rojo | Todo excepto gestionar Jefes/Admins |
| Cajero | ⚪ Gris | Solo Punto de Venta |
