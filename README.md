# FindYourSupplier - Aplicación de Mapeo de Proveedores Cercanos
Link: (https://github.com/JuanSposada/SuppliesProvider)

Author(s): Juan Sebastian Moreno Posada

Status: [Publish]

Ultima actualización: 2025-12-10

## Contenido
- Goals
- Non-Goals
- Background
- Overview
- Detailed Design
  - Solucion 1
    - Frontend
    - Backend
- Consideraciones
- Métricas


## Objetivo
El objetivo principal de este proyecto es construir un Producto Mínimo Viable (MVP) 
que demuestre la funcionalidad central de encontrar proveedores cercanos a unnegocio de referencia. 
Esto con el porposito de identificar posibles proveedores y poder evaluar la distancia.

## Goals
- Implementar un mapa interactivo capaz de renderizar todos los puntos de negocio (establecimientos) utilizando coordenadas.
- Permitir al usuario seleccionar o buscar un "Negocio Objetivo"
- Permitir al usuario seleccionar el nombre del rubro que desea buscar en los proveedores potenciales.
- Desarrollar una función que calcule eficientemente la distancia entre el Negocio Objetivo y el subconjunto de proveedores filtrados por rubro.
- Mostrar una lista y los puntos en el mapa de los "Proveedores Potenciales" que cumplan con el rubro seleccionado y se encuentren dentro de un radio configurable del Negocio Objetivo
## Non-Goals
- No se implementará gestión de usuarios, roles o permisos. La aplicación será de uso público.
- No se intentará inferir la naturaleza de la relación "proveedor-cliente" más allá de la proximidad geográfica y el rubro seleccionado.
- No se asegura la generacion indicaciones de cómo llegar. Solo se calculará la distancia en línea recta.



## Background

El proyecto se basa en un conjunto de datos del Directorio Estadístico Nacional de Unidades Económicas (DENUE) del INEGI, el cual fue sometido a un proceso de limpieza y normalización.

Recurso Principal (Predecesor):
El recurso clave para este desarrollo es el Esquema de Datos Normalizado que se finalizó en la etapa anterior del proyecto. Este esquema descompuso la tabla fuente original (denue_inegi_02_) en un modelo optimizado, asegurando que:

La información esté limpia y libre de redundancias.

Estructura Normalizada:

Tabla Central: establecimientos_final (solo contiene IDs para enlaces).

Tablas de Diccionario: ubicaciones_norm, acta, contacto, direcciones.

La aplicación asume que esta estructura de datos está estable y lista para ser consumida por el frontend.

## Overview
La aplicación será una interfaz web simple y ligera, enfocada en la funcionalidad de mapeo y cálculo de proximidad.
Esta aplicación es una herramienta de inteligencia de mercado geográfica diseñada para ayudar a cualquier negocio a identificar rápidamente a sus proveedores potenciales más cercanos en un área determinada. 
La meta es transformar la base de datos estática del DENUE en un activo visual y dinámico.

La aplicación funcionará como un filtro doble:

- El usuario define el rubro o tipo de proveedor que necesita (por ejemplo, 'Fabricantes de Plástico').
- El sistema utiliza la ubicación del negocio del usuario como centro y calcula las distancias en línea recta para mostrar solo a los proveedores que cumplen con el rubro y están dentro de un radio establecido.


### Flujo de Datos y Lógica 
- Carga Inicial: Al cargar la aplicación para dibujar todos los puntos en el mapa.
- Selección del Objetivo y Rubro
- Filtrado por Rubro
- Cálculo de Proximidad

Resultados Finales:

- Los resultados se filtran una última vez para incluir solo aquellos cuya distancia sea menor o igual al radio configurable (e.g., 5 km).
- Los Proveedores Potenciales se muestran con un marcador diferente en el mapa.
- Se genera una lista lateral que muestra la información detallada del proveedor y la distancia calculada.

## **📝 Diseño Detallado: API de Proveedores (Datos Públicos)**

Este diseño describe la estructura actual de la aplicación Flask, la cual gestiona datos del DENUE/proveedores, priorizando el rendimiento (Pandas/Memoria) y garantizando la disponibilidad (*fallback* a SQLite).

### **Solution 1: Arquitectura de Resiliencia y Control**

### **Frontend**

| Elemento | Descripción |
| :---- | :---- |
| **Integración de Mapas** | El frontend (ej. index.html con Leaflet/Mapbox) se mantiene sin cambios en su lógica principal. |
| **Manejo de Respuestas** | Debe ser capaz de manejar los tres tipos de respuesta del *backend*: **200 OK** (Datos de Pandas), **429 Too Many Requests** (Límite de tasa excedido) y **500 Internal Server Error** (Fallo crítico del *backend* o del *fallback*). |
| **Componentes de Búsqueda** | Un formulario para seleccionar el **Rubro/Actividad** y un componente de mapa para definir la **Ubicación** y el **Radio (km)** para la función de filtrado. |

### **Backend**

El *backend* está escrito en **Python/Flask** y utiliza dos mecanismos principales para gestionar las peticiones: **Caché en Memoria (Pandas)** y **Persistencia (SQLite)**.

#### **🆕 Nuevas Funciones / Componentes**

Dado que la implementación actual se centra en **decoradores** y el uso de librerías, las "nuevas funciones" son principalmente los decoradores y las funciones de *fallback*.

* **`@rate_limit(f)`:** (Decorador de Reutilización)  
  * **Propósito:** Limita el número de peticiones por **dirección IP** en una ventana de tiempo definida (`RATE_LIMIT_WINDOW`).  
  * **Necesidad:** Proteger recursos (memoria, CPU) y asegurar la disponibilidad del servicio ante *bots* o usos excesivos.  
* **`@fallback_to_sqlite(sqlite_view_func_name)`:** (Decorador de Reutilización)  
  * **Propósito:** Envuelve las funciones de vista basadas en Pandas/Excel. Si la función falla (ej. error de memoria, datos corruptos), recurre automáticamente a la función de vista de SQLite especificada.  
  * **Necesidad:** Garantizar la **tolerancia a fallos** y la **continuidad del servicio (Resiliencia)**.  
* **`haversine_distance(lat1, lon1, lat2, lon2)`:** (Función Reutilizable)  
  * **Propósito:** Calcula la distancia real en kilómetros entre dos coordenadas geográficas.  
  * **Necesidad:** Implementar la lógica de **filtro geográfico** en el *endpoint* `/api/excel/proveedor/filtrar`.  
* **Funciones de *Fallback* (Ej. `get_sqlite_negocios`):**  
  * **Propósito:** Son las funciones de vista dedicadas a consultar la base de datos **SQLite**. Sirven como alternativa a las funciones de Pandas.  
  * **Necesidad:** Son el destino del decorador `@fallback_to_sqlite`.

#### **♻️ Código Reutilizable**

* **Decoradores (`@rate_limit`, `@fallback_to_sqlite`):** Son altamente reutilizables y se aplican a múltiples *endpoints* para añadir seguridad y resiliencia sin modificar la lógica interna de la función.  
* **`haversine_distance`:** Es una función matemática pura que puede ser reutilizada en cualquier parte del código que requiera cálculo de distancia geográfica.

## **Consideraciones**

### **Preocupaciones / Trade-offs**

| Tema | Preocupación / Trade-off | Deuda Técnica (Tech Debt) |
| :---- | :---- | :---- |
| **Rate Limiting** | El control de tasa se realiza **en memoria** (USERS\_REQUESTS). Esto no escala si la aplicación se ejecuta en múltiples instancias (ej. varios procesos de Gunicorn/uWSGI o varios contenedores). | Alto: En un entorno de producción con múltiples instancias, las IP serán rastreadas de forma inconsistente, permitiendo a los usuarios exceder el límite real. Se requiere migrar a Redis. |
| **Almacenamiento de Datos** | El *fallback* a SQLite usa **Pandas** (pd.read\_sql\_query) para el filtrado geográfico, cargando los resultados de SQL en memoria. Si la consulta SQL es muy grande, esto podría causar fallos de memoria (**OOM**) incluso en el *fallback*. | Medio: El *fallback* a SQLite no es 100% robusto contra errores de memoria si los resultados son masivos. Lo ideal sería realizar el cálculo Haversine directamente en SQL (si fuera PostgreSQL, por ejemplo). |
| **JWT (Omitido)** | Al omitir JWT, la API es más simple, pero es completamente anónima. No hay forma de identificar clientes malintencionados o de revocar acceso a un usuario específico si abusa del sistema de *rate limit* con múltiples IPs (ej. una *botnet*). | Bajo, pero es una **decisión de diseño** de la API: Pura Publicidad vs. Claves de API Firmadas. |

## **Métricas**

Para validar el rendimiento y la estabilidad de esta arquitectura antes y después del lanzamiento, son esenciales las siguientes métricas:

### 

### **Métricas de Seguridad y Abuso (Rate Limiting)**

| Métrica | Propósito | Umbral de Éxito |
| :---- | :---- | :---- |
| **Respuestas 429** | Frecuencia de "Too Many Requests" (Límite excedido). | Una tasa alta indica que el límite es demasiado bajo, o que hay un alto nivel de abuso que está siendo bloqueado. |
| **Uso de Memoria (Proceso Flask)** | Memoria consumida por el proceso principal. | Debe ser estable y no tener fugas de memoria al cargar/filtrar los DataFrames. |

# **🌍 FindYourSupplier: Mapeo de Proveedores Cercanos**

Una herramienta de inteligencia de mercado geográfico diseñada para transformar datos estáticos del DENUE (INEGI) en un activo visual y dinámico, permitiendo a los negocios identificar rápidamente proveedores potenciales cercanos.

## **🌟 Características Principales**

* **Mapeo Interactivo:** Renderiza todos los puntos de negocio en un mapa (utilizando **Leaflet/Mapbox**).  
* **Doble Filtrado:** Permite seleccionar un **Rubro** (tipo de proveedor) y un **Radio de Búsqueda** (en km) alrededor de un Negocio Objetivo.  
* **Cálculo de Distancia:** Utiliza la fórmula de **Haversine** para calcular la distancia en línea recta.  
* **Arquitectura de Resiliencia:** El *Backend* utiliza **Pandas/Memoria** para un rendimiento rápido, con un **mecanismo de *fallback*** automático a **SQLite** para garantizar la continuidad del servicio ante fallos.  
* **Despliegue con Docker y Proxy:** La aplicación se despliega utilizando **Docker Compose** y un **Nginx Reverse Proxy** para manejar el enrutamiento y el *fallback* externo.
## **🚀 Acceso Rápido**
**Demo Pública**
https://juansposada.pythonanywhere.com/

Acceso a la versión desplegada en PythonAnywhere (usada como fallback externo).

## **🛠️ Instalación y Despliegue con Docker**

El proyecto está diseñado para ser desplegado fácilmente utilizando contenedores Docker. Esto asegura que todas las dependencias y la configuración del entorno sean consistentes.

### **1\. Clonar el Repositorio**

```bash
git clone https://github.com/JuanSposada/SuppliesProvider.git
```
```bash
cd SuppliesProvider
```

### **2\. Configuración del Reverse Proxy (Nginx)**

El archivo `nginx.conf` ya debe estar configurado dentro de la carpeta `docker_proxy/` para manejar dos *backends*:

1. **Backend Principal (Interno):** El servicio Flask (`app.py`) que utiliza Pandas/SQLite.  
2. **Backend de *Fallback* (Externo):** Tu API de reserva alojada en **PythonAnywhere** (o cualquier otro *endpoint* de reserva).

**Nota:** Revisa el archivo `docker_proxy/nginx.conf` y asegúrate de que la variable `proxy_pass` para el *fallback* apunte a tu URL específica de PythonAnywhere.

### **3\. Construir y Levantar los Contenedores**

Utiliza Docker Compose para construir la imagen de tu aplicación Flask y levantar el servicio de Proxy simultáneamente.
```bash
docker compose up -d
```
* `-d`: Ejecuta los contenedores en modo *detached* (en segundo plano).

### **4\. Acceder a la Aplicación**

La aplicación estará accesible a través del puerto configurado en el `docker-compose.yaml` (generalmente el puerto `80` o `8080` mapeado).
```
http://localhost:\[PUERTO\_CONFIGURADO\]
```
## **🔄 Arquitectura de Servicio con Proxy y Fallback**

La arquitectura de despliegue utiliza un **Reverse Proxy (Nginx)** para proporcionar una capa adicional de resiliencia y enrutamiento, permitiendo el *fallback* a un servicio externo (PythonAnywhere) si el servicio principal de Docker falla.

### **Flujo de Datos**

1. **Petición del Cliente:** La solicitud entra al **Nginx Proxy** (`docker_proxy`).  
2. **Ruta Principal:** Nginx intenta enrutar la petición a la API principal (`app.py` en el contenedor Python/Flask).  
3. **Fallo de la Aplicación (Internal):** Si la API principal dentro del contenedor Flask devuelve un error HTTP (ej. 500, 502, 503\) debido a un fallo en el servidor o la lógica de Pandas/SQLite...  
4. **Fallback Externo:** **Nginx** intercepta el error y, gracias a su configuración, redirige la solicitud (o intenta la misma solicitud) al *endpoint* de **PythonAnywhere**.  
5. **Respuesta Final:** La respuesta exitosa (ya sea del contenedor principal o de PythonAnywhere) se envía de vuelta al cliente.

---

## **📂 Estructura del Proyecto**

Esta estructura se basa en el sistema de directorios para manejar datos, código Python, y configuración de despliegue.
```
SuppliesProvider/
├── bk_excel_db/            # Contiene los archivos .csv normalizados (datos fuente)
│   ├── bk_establecimientos.csv
│   ├── bk_ubicaciones_norm.csv
│   └── ... (otros CSVs)
├── docker_proxy/           # Archivos de configuración de Docker y Nginx
│   ├── code/               # Código de la aplicación Python/Flask
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── docker-compose.yaml # Define los servicios (Flask App + Nginx Proxy)
│   ├── Dockerfile          # Instrucciones para construir la imagen del Backend
│   └── nginx.conf          # Configuración del Reverse Proxy con lógica de Fallback
├── sqlite_db/              # Script de utilidad para la DB
│   └── csv_to_sqlite.py    # Script para construir la DB de Fallback
├── static/                 # Archivos Frontend: JS, CSS, assets
│   ├── js/mapa.js
│   └── styles.css
├── templates/              # Vistas HTML
│   └── index.html
├── venv/                   # Entorno virtual local (uso en desarrollo)
├── .gitignore
├── app.py                  # (Versión en la raíz, puede ser removida si se usa 'docker_proxy/code/app.py')
├── notas.txt
└── README.md
```
---

## **📷 Capturas de Pantalla**
**Mapa Principal**
<img width="1880" height="938" alt="image" src="https://github.com/user-attachments/assets/8e471058-c81f-4d87-980a-517a8b966b45" />

<img width="1825" height="914" alt="image" src="https://github.com/user-attachments/assets/9574ba0e-39ad-4cd8-af1a-6a1cd4d1e16e" />

**Búsqueda y Filtrado**
<img width="1879" height="935" alt="image" src="https://github.com/user-attachments/assets/066b5873-e162-48bd-ac58-9100cb33af43" />


**Lista de Proveedores Potenciales**
<img width="1525" height="861" alt="image" src="https://github.com/user-attachments/assets/f9568a98-5d2e-463d-af3a-be7df755b8e1" />


---

## **⚙️ Arquitectura del Backend (Resiliencia)**

### **Flujo de la Petición**

La API está diseñada para priorizar la velocidad usando datos en memoria, pero garantizando la disponibilidad.

1. **Petición:** El *frontend* realiza una solicitud al *endpoint* de filtrado (ej. /api/excel/proveedor/filtrar).  
2. **Rate Limit:** El decorador @rate\_limit verifica la IP. Si excede el límite, se devuelve un **429 Too Many Requests**.  
3. **Lógica Principal (Pandas):** Si no hay límite, la función principal intenta cargar los datos en **Pandas** y realizar el filtrado geográfico (haversine\_distance).  
   * **Éxito:** Devuelve **200 OK** con los resultados de Pandas.  
4. **Fallo de Pandas (*Fallback*):** Si la lógica principal falla (ej. error de memoria, datos corruptos), el decorador @fallback\_to\_sqlite se activa.  
5. **Lógica de Reserva (SQLite):** La función de reserva consulta la base de datos **SQLite** para obtener los datos y realiza el cálculo de distancia.  
   * **Éxito:** Devuelve **200 OK** con los resultados de SQLite.  
   * **Fallo Crítico:** Si el *fallback* también falla, devuelve **500 Internal Server Error**.

### **Componentes Clave**

| Componente | Rol | Tecnología |
| :---- | :---- | :---- |
| **@rate\_limit** | Previene el abuso de recursos. | Decorador Python (Diccionario en Memoria) |
| **@fallback\_to\_sqlite** | Garantiza la continuidad del servicio (Resiliencia). | Decorador Python |
| **Carga de Datos** | Lógica de manejo de datos de alto rendimiento. | Pandas (en memoria) |
| **Persistencia** | Fuente de datos de reserva y tolerante a fallos. | SQLite |

---

## **📝 Contribuciones**

Si deseas contribuir, considera mejorar las **Deudas Técnicas** identificadas, específicamente:

* Migrar el Rate Limiting en memoria a un sistema distribuido como **Redis** para entornos de múltiples instancias.  
* Explorar el cálculo de la distancia Haversine directamente en la consulta SQL (ej. usando extensiones de SQLite o migrando a PostgreSQL/PostGIS) para mitigar el riesgo de *OOM* en el *fallback*.


