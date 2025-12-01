// static/mapa.js

// ====================================================================
// CONFIGURACIÓN INICIAL Y GLOBALES DEL MVP
// ====================================================================

const API_BASE = 'http://127.0.0.1:5000/api/excel'; 

let mapa;
// Capa para manejar el clustering de todos los marcadores (eficiencia)
let markerClusterGroup = L.markerClusterGroup(); 
// ¡CAMBIO CLAVE! Usamos L.featureGroup() para que el método getBounds() funcione
let capaObjetivo = L.featureGroup(); 

// Almacena las coordenadas del negocio objetivo seleccionado
let negocioObjetivo = null; 

// Inicializar el Mapa de Leaflet
function inicializarMapa() {
    // Coordenadas de ejemplo: Baja California (cerca de la zona de tus datos de prueba)
    mapa = L.map('mapa').setView([32.5, -116.6], 9); 

    // Agregar la capa base (Tiles de OpenStreetMap)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(mapa);

    // Agregar las capas al mapa
    markerClusterGroup.addTo(mapa);
    capaObjetivo.addTo(mapa); 
}

// 4. Iniciar el mapa
inicializarMapa();


// ====================================================================
// FUNCIONES DE INTERACCIÓN CON LA API (ENDPOINTS /api/excel/...)
// ====================================================================

/**
 * Función que obtiene el detalle completo de un negocio por su ID y actualiza su popup.
 */
function obtenerDetalle(idNegocio) {
    fetch(`${API_BASE}/negocio/${idNegocio}`)
        .then(response => {
            if (!response.ok) {
                return response.json()
                    .then(err => { throw new Error(err.mensaje || JSON.stringify(err) || "Error al obtener detalle."); })
                    .catch(() => { throw new Error(`Error HTTP ${response.status} (${response.statusText})`); });
            }
            return response.json();
        })
        .then(data => {
            // Estructura el HTML para el Popup (Ventana emergente)
            const detalleHTML = `
                <h4>${data.nombre_establecimiento} (ID: ${data.id})</h4>
                <hr>
                <b>Actividad:</b> ${data.actividad.nombre || 'N/A'}<br>
                <b>Ubicación:</b> ${data.ubicacion_keys.municipio || 'N/A'} (${data.ubicacion_keys.entidad || 'N/A'})<br>
                <b>Teléfono:</b> ${data.contacto.telefono || 'Sin datos'}<br>
                <b>Correo:</b> ${data.contacto.correo || 'Sin datos'}<br>
                <br>
                <i>Haga clic para ver más detalles en la consola.</i>
            `;
            
            // Busca el marcador y actualiza el popup (funciona con cluster)
            markerClusterGroup.eachLayer(function(marcador) {
                if (marcador.options.id === data.id) {
                    marcador.setPopupContent(detalleHTML).openPopup();
                }
            });

            console.log(`Detalle completo del Negocio ID ${data.id}:`, data);
        })
        .catch(error => {
            console.error('Error al obtener el detalle:', error);
            alert(`Error al cargar el detalle: ${error.message}`);
        });
}


/**
 * Carga y dibuja todos los negocios del CSV en el mapa (usando clustering).
 */
function cargarTodosLosNegocios() {
    console.log("Cargando todos los negocios para el mapa...");
    
    // Limpiar: Ambos grupos
    markerClusterGroup.clearLayers(); 
    capaObjetivo.clearLayers();
    document.getElementById('btnBuscar').disabled = true; 
    document.getElementById('resultadosLista').innerHTML = '<h4>Proveedores Potenciales (0 resultados)</h4>';

    fetch(`${API_BASE}/negocios`)
        .then(response => {
             if (!response.ok) {
                if (response.status === 204) {
                    return { negocios: [] };
                }
                return response.json()
                    .then(err => { throw new Error(err.mensaje || JSON.stringify(err) || `Error HTTP ${response.status}`); })
                    .catch(() => { throw new Error(`Error HTTP: ${response.status} (${response.statusText}) - Verifique el log de Flask/NaN.`); });
            }
            return response.json();
        })
        .then(negocios => {
            if (negocios.length === 0) {
                alert("La API no devolvió negocios válidos.");
                return;
            }

            let bounds = [];
            negocios.forEach(n => {
                if (n.latitud && n.longitud) {
                    const lat = parseFloat(n.latitud);
                    const long = parseFloat(n.longitud);

                    const marcador = L.marker([lat, long], { id: n.id }) 
                        .bindPopup(`<b>ID: ${n.id}</b><br>Haga clic para ver detalle.`);

                    // Agregar al grupo de clústeres
                    markerClusterGroup.addLayer(marcador); 

                    // Añadir listener para la carga dinámica de detalles
                    marcador.on('click', () => {
                        obtenerDetalle(n.id);
                    });

                    bounds.push([lat, long]);
                }
            });
            
            // Ajustar el mapa al clúster si hay datos
            if (bounds.length > 0) {
                 mapa.fitBounds(markerClusterGroup.getBounds());
            }

            console.log(`Carga exitosa: ${negocios.length} negocios dibujados (en clústeres).`);
            alert(`Se cargaron ${negocios.length} negocios en el mapa.`);
        })
        .catch(error => {
            console.error('Error al cargar todos los negocios:', error);
            alert(`Error de red o API: ${error.message}`);
        });
}


// ====================================================================
// FUNCIONES DE FLUJO DEL MVP (Negocio Objetivo y Filtrado)
// ====================================================================

/**
 * Paso 1: Obtiene los detalles de un negocio por ID, lo centra y lo guarda como objetivo.
 */
function seleccionarNegocioObjetivo() {
    const idObjetivo = document.getElementById('idObjetivo').value;
    if (!idObjetivo) {
        alert("Por favor, ingresa un ID para el Negocio Objetivo.");
        return;
    }

    // 1. Limpiar el mapa y el estado
    markerClusterGroup.clearLayers(); // Limpiamos todos los demás puntos
    capaObjetivo.clearLayers();
    document.getElementById('btnBuscar').disabled = true;
    document.getElementById('resultadosLista').innerHTML = '<h4>Proveedores Potenciales (0 resultados)</h4>';

    fetch(`${API_BASE}/negocio/${idObjetivo}`)
        .then(response => {
            if (!response.ok) {
                return response.json()
                    .then(err => { throw new Error(err.mensaje || "Error al obtener detalle."); });
            }
            return response.json();
        })
        .then(data => {
            if (!data.latitud || !data.longitud) {
                throw new Error("El negocio objetivo no tiene coordenadas válidas.");
            }

            // 2. Guardar el objetivo globalmente
            negocioObjetivo = {
                id: data.id,
                lat: parseFloat(data.latitud),
                long: parseFloat(data.longitud),
                nombre: data.nombre_establecimiento
            };

            // 3. Resaltar el punto en el mapa con un icono especial
            const objetivoIcono = L.divIcon({
                className: 'objetivo-icon', 
                html: '🎯', 
                iconSize: [30, 30]
            });

            L.marker([negocioObjetivo.lat, negocioObjetivo.long], { icon: objetivoIcono })
                .bindPopup(`<b>Negocio Objetivo:</b><br>${negocioObjetivo.nombre}<br>ID: ${negocioObjetivo.id}`)
                .addTo(capaObjetivo)
                .openPopup();
            
            mapa.setView([negocioObjetivo.lat, negocioObjetivo.long], 13);
            
            // 4. Habilitar la búsqueda de proveedores
            document.getElementById('btnBuscar').disabled = false;
            console.log(`Negocio Objetivo: ${negocioObjetivo.nombre} (Lat: ${negocioObjetivo.lat}, Long: ${negocioObjetivo.long})`);
            alert(`Negocio Objetivo seleccionado: ${negocioObjetivo.nombre}. ¡Listo para buscar proveedores!`);
        })
        .catch(error => {
            negocioObjetivo = null;
            console.error('Error al seleccionar el Negocio Objetivo:', error);
            alert(`Error: ${error.message}`);
        });
}

/**
 * Paso 2: Ejecuta la búsqueda de proveedores filtrados por rubro y radio.
 */
function ejecutarBusquedaProveedor() {
    if (!negocioObjetivo) {
        alert("Primero debes seleccionar un Negocio Objetivo.");
        return;
    }

    const idActa = document.getElementById('rubroBusqueda').value;
    const radioKm = document.getElementById('radioBusqueda').value;

    if (!idActa) {
        alert("Por favor, ingresa el Código de Rubro (Acta) para buscar.");
        return;
    }

    // 1. Limpiar resultados anteriores y dibujar el círculo de búsqueda
    markerClusterGroup.clearLayers();
    capaObjetivo.clearLayers(); 
    
    // Dibujar el punto objetivo y el círculo de radio
    const radioMeters = parseFloat(radioKm) * 1000;
    
    // Círculo de radio
    L.circle([negocioObjetivo.lat, negocioObjetivo.long], {
        color: 'blue',
        fillColor: '#007bff',
        fillOpacity: 0.1,
        radius: radioMeters
    }).addTo(capaObjetivo).bindPopup(`Radio de Búsqueda: ${radioKm} km`).openPopup();
    
    // Marcador objetivo (redibujado)
    L.marker([negocioObjetivo.lat, negocioObjetivo.long], { 
        icon: L.divIcon({className: 'objetivo-icon', html: '🎯', iconSize: [30, 30]})
    }).addTo(capaObjetivo);


    // 2. Llamar al endpoint de filtrado
    const url = `${API_BASE}/proveedor/filtrar?idActa=${idActa}&lat=${negocioObjetivo.lat}&long=${negocioObjetivo.long}&radio=${radioKm}`;
    console.log(`Ejecutando búsqueda: ${url}`);
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                // Manejo explícito de 204 No Content (No hay resultados)
                if (response.status === 204) {
                    return { proveedores: [] };
                }
                
                // Manejo de otros errores (4xx, 5xx)
                return response.json()
                    .then(err => { 
                        throw new Error(err.mensaje || `Error HTTP ${response.status}`); 
                    })
                    .catch(() => {
                        // Captura errores de JSON (como Unexpected end of JSON input) o cuerpos vacíos
                        throw new Error(`Error HTTP: ${response.status} (${response.statusText || 'Cuerpo de respuesta vacío'})`);
                    });
            }
            
            // Si la respuesta es OK (200), leemos el JSON
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                return response.json();
            } else {
                 console.warn("Respuesta 200 OK pero sin contenido JSON esperado. Tratando como 0 resultados.");
                 return { proveedores: [] };
            }
        })
        .then(data => {
            // Unificamos el manejo de datos (si viene como lista directa o dentro de un objeto)
            const proveedores = data.proveedores || data;
            
            // 3. Procesar resultados y actualizar la UI
            if (proveedores.length === 0) {
                alert(`No se encontraron Proveedores Potenciales.`);
                actualizarListaResultados([]);
                return;
            }

            proveedores.forEach(p => {
                // Dibujar el proveedor con un ícono diferente (estrella)
                const proveedorIcono = L.divIcon({
                    className: 'proveedor-icon', 
                    html: '⭐', 
                    iconSize: [25, 25]
                });

                const marcador = L.marker([p.latitud, p.longitud], { 
                    id: p.id,
                    icon: proveedorIcono
                })
                    .bindPopup(`<b>${p.nom_estab}</b><br>Distancia: ${p.distancia_km.toFixed(2)} km<br>Clic para detalle.`)
                    .addTo(markerClusterGroup); 

                marcador.on('click', () => {
                    obtenerDetalle(p.id); 
                });
            });

            // 4. Ajustar el mapa para incluir ambos grupos de puntos
            try {
                // EXTEND ahora funciona porque capaObjetivo es un L.FeatureGroup
                mapa.fitBounds(markerClusterGroup.getBounds().extend(capaObjetivo.getBounds()));
            } catch (e) {
                console.warn("No se pudo ajustar a los límites, probablemente no hay suficientes marcadores.", e);
                mapa.setView([negocioObjetivo.lat, negocioObjetivo.long], 11);
            }

            actualizarListaResultados(proveedores);
            alert(`Búsqueda exitosa: ${proveedores.length} Proveedores Potenciales encontrados.`);
        })
        .catch(error => {
            console.error('Error al ejecutar el filtro de proveedores:', error);
            actualizarListaResultados([]);
            alert(`Error al buscar proveedores: ${error.message}`);
        });
}

/**
 * Función auxiliar para renderizar la lista de resultados en el panel de control.
 */
function actualizarListaResultados(proveedores) {
    const listaDiv = document.getElementById('resultadosLista');
    let html = `<h4>Proveedores Potenciales (${proveedores.length} resultados)</h4>`;

    if (proveedores.length > 0) {
        html += '<ol style="padding-left: 20px; margin-top: 5px;">';
        // Ordenar por distancia (menor a mayor)
        proveedores.sort((a, b) => a.distancia_km - b.distancia_km); 
        
        proveedores.forEach(p => {
            // Se usa el evento 'setView' de Leaflet para centrar el mapa en el punto
            html += `
                <li style="margin-bottom: 5px;">
                    <b>${p.nom_estab || `ID: ${p.id}`}</b>
                    <br>Distancia: <b>${p.distancia_km.toFixed(2)} km</b>
                    (<a href="#" onclick="mapa.setView([${p.latitud}, ${p.longitud}], 15); return false;">Ver en mapa</a>)
                </li>
            `;
        });
        html += '</ol>';
    } else if (negocioObjetivo) {
         html += '<p>No se encontraron proveedores dentro del radio especificado.</p>';
    }

    listaDiv.innerHTML = html;
}