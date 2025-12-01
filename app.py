from flask import Flask, jsonify, request, render_template
import pandas as pd
import numpy as np
import sqlite3
import time
from functools import wraps

app = Flask(__name__)
DATABASE = './supplier.db'

# --- Carga Inicial de DataFrames (CSV) ---
# Intenta cargar los archivos CSV al inicio de la aplicación
try:
    DF_ESTABLECIMIENTOS = pd.read_csv("bk_excel_db/bk_establecimientos.csv")
    DF_ACTA = pd.read_csv("bk_excel_db/bk_acta.csv")
    DF_UBICACIONES = pd.read_csv("bk_excel_db/bk_ubicaciones.csv")
    DF_CONTACTO = pd.read_csv("bk_excel_db/bk_contacto.csv")
    DF_TABLA_PRINCIPAL = pd.read_csv("bk_excel_db/bk_TABLA_FINAL_NORMALIZADA.csv")
except FileNotFoundError:
    print("Error: Asegúrate de que los archivos CSV existan en 'bk_excel_db/'")
    exit()

# --- Función para Conectar a SQLite ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return conn

# Funcion para calcular la distancia entre dos puntors por medio de la formula de Haversine
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcula la distancia Haversine entre dos puntos en km."""
    R = 6371  # Radio de la Tierra en km

    # Conversión de grados a radianes
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Fórmula de Haversine
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = R * c
    return distance


## Manejo de tasa de solicitudes por usuario (simple, en memoria)

USERS_REQUESTS = {}
RATE_LIMIT_WINDOW = 60  # segundos (1 minuto)
RATE_LIMIT_MAX_REQUESTS = 100 # 10 solicitudes por minuto

def rate_limit(f):
    """
    Decorador para limitar el número de solicitudes por dirección IP.
    Permite RATE_LIMIT_MAX_REQUESTS por RATE_LIMIT_WINDOW segundos.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtener la dirección IP del usuario (maneja proxy/load balancer)
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        current_time = time.time()
        
        if ip_address not in USERS_REQUESTS:
            USERS_REQUESTS[ip_address] = []
        
        # Limpiar el historial
        USERS_REQUESTS[ip_address] = [
            t for t in USERS_REQUESTS[ip_address] 
            if t > current_time - RATE_LIMIT_WINDOW
        ]
        
        # Verificar si el límite ha sido excedido
        if len(USERS_REQUESTS[ip_address]) >= RATE_LIMIT_MAX_REQUESTS:
            # Respuesta 429 Too Many Requests
            return jsonify({
                "error": "Límite de solicitudes excedido.", 
                "detalles": f"Solo se permiten {RATE_LIMIT_MAX_REQUESTS} solicitudes por minuto."
            }), 429
            
        # Si no se excede, registrar la solicitud actual
        USERS_REQUESTS[ip_address].append(current_time)
        
        # Continuar con la función original del endpoint
        return f(*args, **kwargs)
    return decorated_function

#### Endpoints para Excel (Pandas) ######

@app.route("/")
@rate_limit
def hello_world():
    # Renderiza el mapa principal (index.html)
    return render_template('index.html')


@app.route("/api/excel/negocios", methods=['GET'])
@rate_limit
def get_negocios():
    """Endpoint para cargar todos los puntos del DENUE para el mapa inicial."""
    try:
        # Creamos una copia para trabajar y evitar SettingWithCopyWarning
        df_mapa = DF_ESTABLECIMIENTOS[['id', 'latitud', 'longitud', 'nom_estab']].copy()
        
        # 1. Limpieza de NaN y Conversión de Tipo
        df_mapa['id'] = pd.to_numeric(df_mapa['id'], errors='coerce')
        df_mapa['latitud'] = pd.to_numeric(df_mapa['latitud'], errors='coerce')
        df_mapa['longitud'] = pd.to_numeric(df_mapa['longitud'], errors='coerce')
        
        # 2. Eliminamos cualquier fila donde ID, latitud o longitud sea NaN
        df_mapa = df_mapa.dropna(subset=['id', 'latitud', 'longitud'])

        if df_mapa.empty:
            return jsonify({"mensaje": "No se encontraron negocios válidos con coordenadas."}), 204

        # 3. Serialización
        data_json = df_mapa.to_dict(orient='records')
        
        return jsonify(data_json), 200
        
    except Exception as e:
        app.logger.error(f"Error en get_negocios: {e}")
        return jsonify({"error": "Error interno del servidor al procesar los datos de establecimientos."}), 500


@app.route("/api/excel/negocio/<int:idNegocio>", methods=["GET"])
@rate_limit
def get_negocio_by_id(idNegocio):
    """Consulta la información detallada de un solo negocio por su ID."""
    try:
        # 1. Obtener claves de la tabla principal
        df_claves = DF_TABLA_PRINCIPAL[DF_TABLA_PRINCIPAL["id_establecimiento"] == idNegocio]
        if df_claves.empty:
            return jsonify({"mensaje": f"Negocio con ID {idNegocio} no encontrado en la tabla principal."}), 404
        claves_data = df_claves.iloc[0].to_dict()
        
        # 2. Obtener la información básica (Lat/Long y Nombre) de la tabla de establecimientos
        df_establec = DF_ESTABLECIMIENTOS[DF_ESTABLECIMIENTOS["id"] == idNegocio]
        if df_establec.empty:
            return jsonify({"mensaje": f"No se encontró información geográfica/nombre para el ID {idNegocio}."}), 404
          
        establec_data = df_establec.iloc[0].to_dict()
        
        # 3. Realizar LOOKUPS (Busquedas) en tablas auxiliares
        
        # a) Unir Actividad (usando codigo_acta)
        act_code = claves_data.get('codigo_acta')
        df_act = DF_ACTA[DF_ACTA['codigo_act'] == act_code]
        act_info = df_act.iloc[0].to_dict() if act_code and not df_act.empty else {}
        
        # b) Unir Ubicación (usando id_ubicacion)
        ubic_id = claves_data.get('id_ubicacion')
        df_ubic = DF_UBICACIONES[DF_UBICACIONES['id_ubicacion'] == ubic_id]
        ubic_info = df_ubic.iloc[0].to_dict() if ubic_id and not df_ubic.empty else {}
        
        # c) Unir Contacto (usando id_contacto)
        cont_id = claves_data.get('id_contancto')
        df_cont = DF_CONTACTO[DF_CONTACTO['id_contancto'] == cont_id]
        cont_info = df_cont.iloc[0].to_dict() if cont_id and not df_cont.empty else {}
        
        # 4. Estructurar la respuesta
        respuesta = {
            "id": establec_data.get('id'),
            "nombre_establecimiento": establec_data.get('nom_estab'),
            "latitud": establec_data.get('latitud'),
            "longitud": establec_data.get('longitud'),
            
            "actividad": {
                "codigo": act_info.get('codigo_act'),
                "nombre": act_info.get('nombre_act')
            },
            
            "ubicacion_keys": {
                "id_ubicacion": ubic_info.get('id_ubicacion'),
                "entidad": ubic_info.get('entidad'),
                "municipio": ubic_info.get('municipio'),
                "localidad": ubic_info.get('localidad')
            },
            
            "contacto": {
                "id_contacto": cont_info.get('id_contancto'),
                "telefono": cont_info.get('telefono'),
                "correo": cont_info.get('correoelec'),
                "web": cont_info.get('www')
            }
        }
        
        return jsonify(respuesta), 200
        
    except Exception as e:
        app.logger.error(f"Error en get_negocio_by_id (ID: {idNegocio}): {e}")
        return jsonify({"error": "Error interno del servidor al buscar el detalle del negocio."}), 500


@app.route("/api/excel/proveedor/filtrar", methods=["GET"])
@rate_limit
def filtrar_proveedores():
    """Filtra proveedores por rubro (idActa) y proximidad geográfica."""
    
    # 1. Obtener parámetros y validarlos
    try:
        id_acta_float = float(request.args.get('idActa')) 
        lat_obj = float(request.args.get('lat'))
        long_obj = float(request.args.get('long'))
        radio_km = float(request.args.get('radio', 5)) 
    except (ValueError, TypeError):
        return jsonify({"error": "Parámetros idActa, lat y long son requeridos y deben ser números válidos."}), 400
    
    try:
        # 2. Filtrar por ID de Acta (Rubro)
        df_filtrado_claves = DF_TABLA_PRINCIPAL[DF_TABLA_PRINCIPAL['codigo_acta'] == id_acta_float]

        if df_filtrado_claves.empty:
            return jsonify({"mensaje": f"No se encontraron proveedores para la actividad {id_acta_float}."}), 204 # 204 No Content

        # 3. Realizar el JOIN (Merge) para obtener las coordenadas y nombres
        df_proveedores = pd.merge(
            df_filtrado_claves,
            DF_ESTABLECIMIENTOS[['id', 'nom_estab', 'latitud', 'longitud']], 
            left_on='id_establecimiento', 
            right_on='id', 
            how='inner'
        )
        if df_proveedores.empty:
            return jsonify({"mensaje": "Los proveedores filtrados no tienen información geográfica válida."}), 204
            
        # 4. Limpieza post-Merge (Clave para evitar SyntaxError en el cliente)
        # Forzar la conversión a numérico y eliminar NaNs residuales en las coordenadas
        df_proveedores['latitud'] = pd.to_numeric(df_proveedores['latitud'], errors='coerce')
        df_proveedores['longitud'] = pd.to_numeric(df_proveedores['longitud'], errors='coerce')
        df_proveedores = df_proveedores.dropna(subset=['latitud', 'longitud'])

        if df_proveedores.empty:
            return jsonify({"mensaje": "Los proveedores filtrados no tienen coordenadas válidas después de la limpieza."}), 204

        # 5. Calcular la distancia Haversine y añadirla como columna
        df_proveedores['distancia_km'] = haversine_distance(
            lat_obj, long_obj, 
            df_proveedores['latitud'], df_proveedores['longitud']
        )

        # 6. Filtrar por el radio geográfico
        df_proveedores_final = df_proveedores[df_proveedores['distancia_km'] <= radio_km]

        if df_proveedores_final.empty:
            return jsonify({"mensaje": f"No se encontraron proveedores dentro de {radio_km} km para la actividad {id_acta_float}."}), 204
            
        # 7. Preparar la respuesta JSON
        respuesta = df_proveedores_final[['id', 'nom_estab', 'latitud', 'longitud', 'distancia_km']].to_dict(orient='records')
        return jsonify(respuesta), 200
        
    except Exception as e:
        app.logger.error(f"Error en filtrar_proveedores: {e}")
        return jsonify({"error": "Error interno del servidor al aplicar filtros geográficos."}), 500


@app.route("/api/excel/ubicacion/simular", methods=["POST"])
@rate_limit
def simular_ubicacion():
    """
    Recibe coordenadas (lat, long) en el cuerpo JSON para simular el Negocio Objetivo 
    y confirma la recepción de los datos. (Este endpoint no se usó en el MVP final)
    """
    data = request.get_json()
    
    try:
        lat = float(data['lat'])
        long = float(data['long'])
    except (TypeError, KeyError, ValueError):
        return jsonify({"error": "El cuerpo de la solicitud JSON debe contener 'lat' y 'long' válidos."}), 400

    return jsonify({
        "mensaje": "Ubicación temporal del Negocio Objetivo creada exitosamente para búsquedas.",
        "latitud_objetivo": lat,
        "longitud_objetivo": long
    }), 201

# En app.py

@app.route("/api/excel/rubros", methods=["GET"])
@rate_limit
def get_rubros():
    """Devuelve la lista de todos los códigos de acta y sus nombres."""
    try:
        # Seleccionar solo las columnas necesarias para el dropdown
        df_rubros = DF_ACTA[['codigo_act', 'nombre_act']].copy()
        
        # Opcional: limpiar NaNs si los hubiera y asegurar formato
        df_rubros = df_rubros.dropna().drop_duplicates()
        
        # Convertir a una lista de diccionarios
        data_json = df_rubros.to_dict(orient='records')
        
        return jsonify(data_json), 200
        
    except Exception as e:
        app.logger.error(f"Error en get_rubros: {e}")
        return jsonify({"error": "Error interno del servidor al obtener la lista de rubros."}), 500
    

####### Endpoints para Base de Datos SQLite ######
# Nota: Estos endpoints están incluidos pero no se están utilizando en el frontend
# actual (mapa.js) que se enfoca en la versión de Pandas (Excel).

@app.route("/api/sqlite/negocios", methods=["GET"])
@rate_limit
def get_sqlite_negocios():
    """Consulta ID, Latitud y Longitud para la carga inicial del mapa."""
    conn = get_db_connection()
    query = "SELECT id, latitud, longitud FROM establecimientos"
    negocios = conn.execute(query).fetchall()
    conn.close()
    
    if not negocios:
        return jsonify({"mensaje": "No se encontraron negocios en SQLite"}), 204

    data_json = [dict(row) for row in negocios]
    return jsonify(data_json), 200


@app.route("/api/sqlite/negocio/<int:idNegocio>", methods=["GET"])
@rate_limit
def get_sqlite_negocio_detallado(idNegocio):
    """Consultar los datos detallados de un negocio específico mediante JOINs en SQL."""
    conn = get_db_connection()

    query = f"""
    SELECT 
        e.id, e.nom_estab, e.latitud, e.longitud,
        t.codigo_acta, t.id_ubicacion, t.id_contacto,
        a.nombre_act,
        u.entidad, u.municipio, u.localidad,
        c.telefono, c.correoelec, c.www
    FROM 
        establecimientos e
    INNER JOIN 
        tabla_final t ON e.id = t.id_establecimiento
    LEFT JOIN 
        acta a ON t.codigo_acta = a.codigo_act
    LEFT JOIN 
        ubicaciones u ON t.id_ubicacion = u.id_ubicacion
    LEFT JOIN 
        contacto c ON t.id_contacto = c.id_contancto
    WHERE 
        e.id = ?
    """
    
    negocio = conn.execute(query, (idNegocio,)).fetchone()
    conn.close()

    if not negocio:
        return jsonify({"mensaje": f"Negocio con ID {idNegocio} no encontrado en SQLite"}), 404
        
    row = dict(negocio)
    respuesta = {
        "id": row['id'],
        "nombre_establecimiento": row['nom_estab'],
        "latitud": row['latitud'],
        "longitud": row['longitud'],
        "actividad": {
            "codigo": row['codigo_acta'],
            "nombre": row['nombre_act']
        },
        "ubicacion": {
            "id_ubicacion": row['id_ubicacion'],
            "entidad": row['entidad'],
            "municipio": row['municipio'],
            "localidad": row['localidad']
        },
        "contacto": {
            "id_contacto": row['id_contacto'],
            "telefono": row['telefono'],
            "correo": row['correoelec'],
            "web": row['www']
        }
    }
    return jsonify(respuesta), 200


@app.route("/api/sqlite/proveedor/filtrar", methods=["GET"])
@rate_limit
def filtrar_sqlite_proveedores():
    """Filtra proveedores por rubro (idActa) y proximidad geográfica."""
    
    try:
        id_acta = request.args.get('idActa') 
        lat_obj = float(request.args.get('lat'))
        long_obj = float(request.args.get('long'))
        radio_km = float(request.args.get('radio', 5)) 
    except (ValueError, TypeError):
        return jsonify({"error": "Parámetros idActa, lat y long son requeridos y deben ser números válidos."}), 400

    conn = get_db_connection()
    
    query = f"""
    SELECT 
        e.id, e.nom_estab, e.latitud, e.longitud
    FROM 
        tabla_final t
    INNER JOIN 
        establecimientos e ON t.id_establecimiento = e.id
    WHERE 
        t.codigo_acta = ?
    """
    df_proveedores = pd.read_sql_query(query, conn, params=(id_acta,))
    conn.close()

    if df_proveedores.empty:
        return jsonify({"mensaje": f"No se encontraron proveedores para la actividad {id_acta}."}), 204

    df_proveedores['distancia_km'] = haversine_distance(
        lat_obj, long_obj, 
        df_proveedores['latitud'], df_proveedores['longitud']
    )

    df_proveedores_final = df_proveedores[df_proveedores['distancia_km'] <= radio_km]

    if df_proveedores_final.empty:
        return jsonify({"mensaje": f"No se encontraron proveedores dentro de {radio_km} km para la actividad {id_acta}."}), 204
        
    respuesta = df_proveedores_final[['id', 'nom_estab', 'latitud', 'longitud', 'distancia_km']].to_dict(orient='records')
    return jsonify(respuesta), 200

if __name__ == "__main__":
    # Importante: usar debug=False en producción o desactivar las advertencias de Flask
    app.run(debug=True)