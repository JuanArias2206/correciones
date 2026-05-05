// Importación de todos los datasets procesados
import kpisRaw from './kpis.json'
import sustanciasRaw from './sustancias.json'
import intencionalidadRaw from './intencionalidad.json'
import sexoRaw from './sexo.json'
import sustanciasPorIntencionalidadRaw from './sustancias_por_intencionalidad.json'
import sustanciaSexoRaw from './sustancia_sexo.json'
import top10SustanciasRaw from './top10_sustancias.json'
import conteoSustanciasTipoRaw from './conteo_sustancias_tipo.json'
import resumenTop100Raw from './resumen_top100_sust.json'
import productosBlacklistRaw from './productos_blacklist.json'
import productosPorCategoriaRaw from './productos_por_categoria.json'
import productosTodosRaw from './productos_todos.json'
import conteoCategoriasRaw from './conteo_categorias.json'
import resultadosLlmRaw from './resultados_llm.json'
import resumenClasificacionAvanzadaRaw from './resumen_clasificacion_avanzada.json'
import resumenCategoriasRaw from './resumen_categorias.json'
import detalleProductosRaw from './detalle_productos.json'
import baseCompletaRaw from './base_completa.json'
import metadataRaw from './metadata.json'

// Asegurar que sean arrays
const ensureArray = (d) => Array.isArray(d) ? d : []

export const kpis = kpisRaw || {}
export const sustancias = ensureArray(sustanciasRaw)
export const intencionalidad = ensureArray(intencionalidadRaw)
export const sexo = ensureArray(sexoRaw)
export const sustanciasPorIntencionalidad = ensureArray(sustanciasPorIntencionalidadRaw)
export const sustanciaSexo = ensureArray(sustanciaSexoRaw)
export const top10Sustancias = ensureArray(top10SustanciasRaw)
export const conteoSustanciasTipo = ensureArray(conteoSustanciasTipoRaw)
export const resumenTop100 = ensureArray(resumenTop100Raw)
export const productosBlacklist = ensureArray(productosBlacklistRaw)
export const productosPorCategoria = ensureArray(productosPorCategoriaRaw)
export const productosTodos = ensureArray(productosTodosRaw)
export const conteoCategorias = ensureArray(conteoCategoriasRaw)
export const resultadosLlm = ensureArray(resultadosLlmRaw)
export const resumenClasificacionAvanzada = ensureArray(resumenClasificacionAvanzadaRaw)
export const resumenCategorias = ensureArray(resumenCategoriasRaw)
export const detalleProductos = ensureArray(detalleProductosRaw)
export const baseCompleta = ensureArray(baseCompletaRaw)
export const metadata = metadataRaw || {}
