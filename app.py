from flask import Flask, jsonify, request
import pandas as pd
import numpy as np

app = Flask(__name__)

try:
    DF_ESTABLECIMIENTOS = pd.read_csv("bk_excel_db/bk_establecimientos.csv")
    DF_ACTA = pd.read_csv("bk_excel_db/bk_acta.csv")
    DF_UBICACIONES = pd.read_csv("bk_excel_db/bk_ubicaciones.csv")
    DF_CONTACTO = pd.read_csv("bk_excel_db/bk_contacto.csv")
    DF_TABLA_PRINCIPAL = pd.read_csv("bk_excel_db/bk_TABLA_FINAL_NORMALIZADA.csv")
except FileNotFoundError:
    print("Error: Asegúrate de que los archivos CSV existan en 'bk_excel_db/'")
    exit()

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


@app.route("/")
def hello_world():
    return "<h1>Whasaaaaa!!!! 🤪! Esta es la API de FindYourSupplier</h1>"

@app.route("/api/excel/negocios", methods=['GET'])
def get_negocios():
    df_mapa = DF_ESTABLECIMIENTOS[['id','latitud', 'longitud']]
    if df_mapa.empty:
        return jsonify({"mensaje": "No se encontraron negocios"}), 204

    data_json = df_mapa.to_dict(orient='records')
    return jsonify(data_json), 200

@app.route("/api/excel/negocio/<int:idNegocio>", methods=["GET"])
def get_negocio_by_id(idNegocio):
    df_claves = DF_TABLA_PRINCIPAL[DF_TABLA_PRINCIPAL["id_establecimiento"] == idNegocio]
    if df_claves.empty:
        return jsonify({"mensaje": f"Negocio con ID {idNegocio} no encontrado en la tabla principal."}), 404
    claves_data = df_claves.iloc[0].to_dict()
    # 2. Obtener la información básica (Lat/Long y Nombre) de la tabla de establecimientos
    df_establec = DF_ESTABLECIMIENTOS[DF_ESTABLECIMIENTOS["id"] == idNegocio]
    if df_establec.empty:
        # Esto podría pasar si el ID está en la tabla principal pero no en establecimientos
        return jsonify({"mensaje": f"No se encontró información geográfica/nombre para el ID {idNegocio}."}), 404
     
    establec_data = df_establec.iloc[0].to_dict()
    # a) Unir Actividad (usando codigo_acta)
    act_code = claves_data.get('codigo_acta')
    # Usamos DF_ACTA (tu nombre de variable)
    act_info = DF_ACTA[DF_ACTA['codigo_act'] == act_code].iloc[0].to_dict() if act_code and not DF_ACTA[DF_ACTA['codigo_act'] == act_code].empty else {}
    
    # b) Unir Ubicación (usando id_ubicacion)
    ubic_id = claves_data.get('id_ubicacion')
    ubic_info = DF_UBICACIONES[DF_UBICACIONES['id_ubicacion'] == ubic_id].iloc[0].to_dict() if ubic_id and not DF_UBICACIONES[DF_UBICACIONES['id_ubicacion'] == ubic_id].empty else {}
    
    # c) Unir Contacto (usando id_contacto)
    cont_id = claves_data.get('id_contancto')
    cont_info = DF_CONTACTO[DF_CONTACTO['id_contancto'] == cont_id].iloc[0].to_dict() if cont_id and not DF_CONTACTO[DF_CONTACTO['id_contancto'] == cont_id].empty else {}
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


@app.route("/api/excel/proveedor/filtrar", methods=["GET"])
def filtrar_proveedores():
    """Filtra proveedores por rubro (idActa) y proximidad geográfica."""
    
    # 1. Obtener parámetros y validarlos
    try:
        # idActa se convierte a float para asegurar la coincidencia con el tipo de dato en Pandas
        id_acta_float = float(request.args.get('idActa')) 
        lat_obj = float(request.args.get('lat'))
        long_obj = float(request.args.get('long'))
        # Radio es opcional, 5 km por defecto
        radio_km = float(request.args.get('radio', 5)) 
    except (ValueError, TypeError):
        # 400 Bad Request si faltan o son inválidos
        return jsonify({"error": "Parámetros idActa, lat y long son requeridos y deben ser números válidos."}), 400
    
    df_filtrado_claves = DF_TABLA_PRINCIPAL[DF_TABLA_PRINCIPAL['codigo_acta'] == id_acta_float]

    if df_filtrado_claves.empty:
        return jsonify({"mensaje": f"No se encontraron proveedores para la actividad {id_acta_float}."}), 204 # 204 No Content

    # 3. Realizar el JOIN (Merge) para obtener las coordenadas y nombres
    df_proveedores = pd.merge(
        # Tabla de la que obtuvimos las claves filtradas
        df_filtrado_claves,
        # Tabla de la que necesitamos los datos geográficos y el nombre
        DF_ESTABLECIMIENTOS[['id', 'nom_estab', 'latitud', 'longitud']], 
        # Unir por id_establecimiento (en la tabla de claves) y id (en la tabla de establecimientos)
        left_on='id_establecimiento', 
        right_on='id',                
        how='inner' # Solo incluir coincidencias
    )
    if df_proveedores.empty:
        return jsonify({"mensaje": "Los proveedores filtrados no tienen información geográfica válida."}), 204
        
    # 4. Calcular la distancia Haversine y añadirla como columna
    df_proveedores['distancia_km'] = haversine_distance(
        lat_obj, long_obj, 
        df_proveedores['latitud'], df_proveedores['longitud']
    )

    # 5. Filtrar por el radio geográfico
    df_proveedores_final = df_proveedores[df_proveedores['distancia_km'] <= radio_km]

    if df_proveedores_final.empty:
        return jsonify({"mensaje": f"No se encontraron proveedores dentro de {radio_km} km para la actividad {id_acta_float}."}), 204
        
    # 6. Preparar la respuesta JSON (solo con las columnas necesarias para el mapa)
    respuesta = df_proveedores_final[['id', 'nom_estab', 'latitud', 'longitud', 'distancia_km']].to_dict(orient='records')
    return jsonify(respuesta), 200 # 200 OK}


@app.route("/api/excel/ubicacion/simular", methods=["POST"])
def simular_ubicacion():
    """
    Recibe coordenadas (lat, long) en el cuerpo JSON para simular el Negocio Objetivo 
    y confirma la recepción de los datos.
    """
    data = request.get_json()
    
    # 1. Validación de datos de entrada desde el cuerpo JSON
    try:
        # Intentamos obtener y convertir las coordenadas a float
        lat = float(data['lat'])
        long = float(data['long'])
    except (TypeError, KeyError, ValueError):
        # 400 Bad Request si faltan datos ('lat'/'long') o no son números válidos
        return jsonify({"error": "El cuerpo de la solicitud JSON debe contener 'lat' y 'long' válidos."}), 400

    # 2. Confirmación
    # Se retorna el estado 201 Created para indicar que se recibió y "creó" el recurso temporalmente.
    return jsonify({
        "mensaje": "Ubicación temporal del Negocio Objetivo creada exitosamente para búsquedas.",
        "latitud_objetivo": lat,
        "longitud_objetivo": long
    }), 201


if __name__ == "__main__":
    app.run(debug=True)