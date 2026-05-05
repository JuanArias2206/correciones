# Dashboard de Análisis de Clasificación de Sustancias

Dashboard web interactivo para explorar los resultados de clasificación de productos/sustancias generados por el pipeline de análisis.

---

## Descripción

Este tablero resume de forma visual e interactiva los resultados de clasificación, distribución por sustancia, sexo e intencionalidad de los registros procesados. Los datos provienen de la carpeta `outputs/clasificaciones_conteo` del proyecto principal.

El dashboard incluye:

- **KPIs principales** con métricas clave del análisis.
- **Análisis por tipo de sustancia** con gráficos de barras interactivos.
- **Análisis por sexo** con distribuciones, comparaciones y heatmap.
- **Análisis por intencionalidad** con gráficos apilados, tablas ordenables y porcentajes.
- **Análisis de productos** con tablas filtrables, búsqueda y exportación a CSV.
- **Tabla exploratoria** de resultados completos con paginación y filtros.
- **Hallazgos principales** con interpretación automática en lenguaje no técnico.
- **Gráficas originales** generadas por la corrida de análisis.

---

## Requisitos

- Node.js >= 18.0.0
- npm >= 9.0.0
- Python 3.x (solo para regenerar datos desde Excel)

---

## Instalación de dependencias

```bash
cd dashboard-resultados
npm install
```

---

## Ejecución local

```bash
npm run dev
```

El dashboard estará disponible en `http://localhost:5173`.

---

## Construcción para producción

```bash
npm run build
```

Los archivos estáticos se generarán en la carpeta `dist/`. Puedes desplegar esta carpeta en cualquier servidor web estático (GitHub Pages, Netlify, Vercel, Apache, Nginx, etc.).

---

## Regenerar datos desde `outputs`

Si los archivos en `outputs/clasificaciones_conteo/` cambian, puedes regenerar los datos JSON ejecutando:

```bash
python3 process_data.py
```

Este script:

1. Lee todos los archivos `.xlsx` de `outputs/clasificaciones_conteo/`.
2. Detecta las hojas disponibles y extrae las tablas relevantes.
3. Calcula KPIs y métricas derivadas.
4. Guarda datasets limpios en `src/data/` como archivos JSON.
5. Copia las imágenes PNG a `public/images/`.

Después de regenerar los datos, vuelve a construir el proyecto:

```bash
npm run build
```

---

## Despliegue

### Opción 1: Servidor local con preview

```bash
npm run preview
```

### Opción 2: Cualquier servidor estático

Copia el contenido de la carpeta `dist/` a tu servidor web. Por ejemplo, con Python:

```bash
cd dist
python3 -m http.server 8000
```

### Opción 3: GitHub Pages / Netlify / Vercel

Sube el contenido de `dist/` o conecta el repositorio para despliegue automático.

---

## Archivos que utiliza

### Datos procesados (JSON en `src/data/`)

- `kpis.json` — métricas principales calculadas.
- `sustancias.json` — conteo por sustancia.
- `intencionalidad.json` — conteo por intencionalidad.
- `sexo.json` — conteo por sexo.
- `sustancias_por_intencionalidad.json` — desglose por sustancia e intencionalidad.
- `sustancia_sexo.json` — desglose por sustancia y sexo.
- `base_completa.json` — registros completos con intencionalidad.
- `resultados_llm.json` — resultados de clasificación avanzada.
- `productos_todos.json` — productos por categoría con conteo.
- `conteo_categorias.json` — conteo agregado por categoría.
- `productos_blacklist.json` — productos filtrados por blacklist.
- `resumen_categorias.json` — resumen por categoría final.
- `detalle_productos.json` — detalle por producto.
- `metadata.json` — información de generación.

### Imágenes originales (PNG en `public/images/`)

- `conteo_sustancias_tipo.png`
- `heatmap_sustancia_sexo.png`
- `intencionalidad.png`
- `sexo.png`
- `sustancias_por_intencionalidad.png`
- `sustancias_por_sexo.png`
- `sustancias.png`
- `top10_sustancias.png`

---

## Análisis incluidos

1. **Distribución general**: total de registros, intencionales vs no intencionales, distribución por sexo.
2. **Ranking de sustancias**: conteo ordenado por frecuencia con opción de Top 5 / Top 10 / Todas.
3. **Análisis cruzado Sustancia × Sexo**: barras agrupadas y heatmap con interpretación textual.
4. **Análisis cruzado Sustancia × Intencionalidad**: barras apiladas, porcentajes y tabla ordenable.
5. **Exploración de productos**: buscador, filtros por categoría y método, exportación CSV.
6. **Tabla exploratoria de registros**: búsqueda global, filtros, ordenamiento, paginación y exportación.
7. **Hallazgos automáticos**: resumen en lenguaje natural con patrones, alertas y limitaciones.
8. **Gráficas originales**: visualizaciones generadas por el pipeline de análisis.

---

## Tecnologías

- **React 18** + **Vite** — framework y bundler.
- **Recharts** — gráficos interactivos.
- **CSS puro** — estilos responsivos sin dependencias pesadas.

---

## Notas

- Los datos se empaquetan estáticamente en el build. No es necesario un backend.
- Si algún archivo Excel no tiene las columnas esperadas, el script `process_data.py` imprime una advertencia y continúa con los demás archivos.
- La categoría "otros" concentra un volumen significativo; considérese al interpretar los rankings.

---

## Autor

Generado automáticamente a partir de los resultados del pipeline de clasificación de sustancias.
