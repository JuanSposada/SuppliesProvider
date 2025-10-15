# FindYourSupplier - Aplicación de Mapeo de Proveedores Cercanos
Link: [[Link a este design doc](#)](https://github.com/JuanSposada/SuppliesProvider)

Author(s): Juan Sebastian Moreno Posada

Status: [Draft]

Ultima actualización: 2025-10-14

## Contenido
- Goals
- Non-Goals
- Background
- Overview
- Detailed Design
  - Solucion 1
    - Frontend
    - Backend
  - Solucion 2
    - Frontend
    - Backend
- Consideraciones
- Métricas

## Links
- [Un link](#)
- [Otro link](#)

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

Esto proporciona una visión estratégica e inmediata para la logística y la planificación de compras, todo a través de una sencilla interfaz web con un mapa interactivo.
_Esta sección debería ser entendible por nuevos miembros de tu equipo que no están relacionados al proyecto_

_Pon detalles en la siguiente sección_

## Detailed Design
_Usa diagramas donde veas necesario_

_Herramientas como [Excalidraw](https://excalidraw.com) son buenos recursos para esto_

_Cubre los cambios principales:_

 _- Cuales son las nuevas funciones que vas a escribir?_
 _- Porque necesitas nuevos componentes?_
 _- Hay código que puede ser reusable?_

_No elabores minuciosamente la implementación._

## Solution 1
### Frontend
_Frontend…_
### Backend
_Backend…_

## Solution 2
### Frontend
_Frontend…_
### Backend
_Backend…_

## Consideraciones
_Preocupaciones / trade-offs / tech debt_

## Métricas
_Que información necesitas para validar antes de lanzar este feature?_
