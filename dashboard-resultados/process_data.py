import pandas as pd
import json
import os
import shutil
from datetime import datetime

BASE_INPUT = '/Users/juanmanuelarias/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/outputs/clasificaciones_conteo'
BASE_OUTPUT = '/Users/juanmanuelarias/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/dashboard-resultados/src/data'
IMAGES_SRC = BASE_INPUT
IMAGES_DST = '/Users/juanmanuelarias/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/dashboard-resultados/public/images'

os.makedirs(BASE_OUTPUT, exist_ok=True)
os.makedirs(IMAGES_DST, exist_ok=True)

def save_json(data, filename):
    path = os.path.join(BASE_OUTPUT, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'Guardado: {path}')

# Metadata
metadata = {
    'fecha_generacion': datetime.now().isoformat(),
    'archivos_procesados': []
}

# 1. analisis_resultados.xlsx
print('Procesando analisis_resultados.xlsx...')
xl = pd.ExcelFile(os.path.join(BASE_INPUT, 'analisis_resultados.xlsx'))
metadata['archivos_procesados'].append('analisis_resultados.xlsx')

# Sustancias
sustancias = pd.read_excel(xl, sheet_name='Sustancias')
# ordenar de mayor a menor
sustancias = sustancias.sort_values('numero_registros', ascending=False)
save_json(sustancias.to_dict(orient='records'), 'sustancias.json')

# Intencionalidad
intencionalidad = pd.read_excel(xl, sheet_name='Intencionalidad')
save_json(intencionalidad.to_dict(orient='records'), 'intencionalidad.json')

# Sexo
sexo = pd.read_excel(xl, sheet_name='Sexo')
save_json(sexo.to_dict(orient='records'), 'sexo.json')

# Sustancias por Intencionalidad
sust_int = pd.read_excel(xl, sheet_name='Sustancias_por_Intencionalidad')
sust_int = sust_int.sort_values('intencional', ascending=False)
# Calcular totales y porcentajes
sust_int['total'] = sust_int['intencional'] + sust_int['no_intencional']
sust_int['porcentaje_intencional'] = (sust_int['intencional'] / sust_int['total'] * 100).round(2)
sust_int['porcentaje_no_intencional'] = (sust_int['no_intencional'] / sust_int['total'] * 100).round(2)
save_json(sust_int.to_dict(orient='records'), 'sustancias_por_intencionalidad.json')

# Base completa (muestra de 5000 registros para tabla exploratoria)
base_completa = pd.read_excel(xl, sheet_name='Base_Completa')
# convertir fechas a string
for col in base_completa.columns:
    if base_completa[col].dtype == 'datetime64[ns]':
        base_completa[col] = base_completa[col].dt.strftime('%Y-%m-%d')
    # convertir listas a strings
    if base_completa[col].dtype == 'object':
        base_completa[col] = base_completa[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
# Usamos toda la base para permitir análisis completo, pero guardamos como JSON
base_completa = base_completa.fillna('')
save_json(base_completa.to_dict(orient='records'), 'base_completa.json')

# Sustancia Sexo
sust_sexo = pd.read_excel(xl, sheet_name='Sustancia_Sexo')
# Renombrar columnas si es necesario
if 'grupos_sustancia_final' in sust_sexo.columns:
    sust_sexo = sust_sexo.rename(columns={'grupos_sustancia_final': 'sustancia'})
save_json(sust_sexo.to_dict(orient='records'), 'sustancia_sexo.json')

# Top10 Sustancias
top10 = pd.read_excel(xl, sheet_name='Top10_Sustancias')
save_json(top10.to_dict(orient='records'), 'top10_sustancias.json')

# Conteo Sustancias Tipo (igual a sustancias)
conteo_tipo = pd.read_excel(xl, sheet_name='Conteo_Sustancias_Tipo')
save_json(conteo_tipo.to_dict(orient='records'), 'conteo_sustancias_tipo.json')

# Resumen Top100 Sust
resumen_top100 = pd.read_excel(xl, sheet_name='Resumen_Top100_Sust')
save_json(resumen_top100.to_dict(orient='records'), 'resumen_top100_sust.json')

# 2. productos_filtrados_blacklist.xlsx
print('Procesando productos_filtrados_blacklist.xlsx...')
df_blacklist = pd.read_excel(os.path.join(BASE_INPUT, 'productos_filtrados_blacklist.xlsx'))
df_blacklist['blacklist'] = True
df_blacklist = df_blacklist.fillna('')
save_json(df_blacklist.to_dict(orient='records'), 'productos_blacklist.json')
metadata['archivos_procesados'].append('productos_filtrados_blacklist.xlsx')

# 3. productos_por_categoria.xlsx
print('Procesando productos_por_categoria.xlsx...')
df_prod_cat = pd.read_excel(os.path.join(BASE_INPUT, 'productos_por_categoria.xlsx'))
# Convertir listas a strings
for col in df_prod_cat.columns:
    if df_prod_cat[col].dtype == 'object':
        df_prod_cat[col] = df_prod_cat[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
df_prod_cat = df_prod_cat.fillna('')
save_json(df_prod_cat.to_dict(orient='records'), 'productos_por_categoria.json')
metadata['archivos_procesados'].append('productos_por_categoria.xlsx')

# 4. productos_por_categoria_conteo.xlsx
print('Procesando productos_por_categoria_conteo.xlsx...')
xl_prod = pd.ExcelFile(os.path.join(BASE_INPUT, 'productos_por_categoria_conteo.xlsx'))
# Hoja Todos
df_prod_todos = pd.read_excel(xl_prod, sheet_name='Todos')
for col in df_prod_todos.columns:
    if df_prod_todos[col].dtype == 'object':
        df_prod_todos[col] = df_prod_todos[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
df_prod_todos = df_prod_todos.fillna('')
save_json(df_prod_todos.to_dict(orient='records'), 'productos_todos.json')
# Conteo por categoria
conteo_categorias = df_prod_todos.groupby('categoria')['conteo'].sum().reset_index().sort_values('conteo', ascending=False)
save_json(conteo_categorias.to_dict(orient='records'), 'conteo_categorias.json')
metadata['archivos_procesados'].append('productos_por_categoria_conteo.xlsx')

# 5. resultados_clasificacion_llm_avanzada.xlsx
print('Procesando resultados_clasificacion_llm_avanzada.xlsx...')
df_llm = pd.read_excel(os.path.join(BASE_INPUT, 'resultados_clasificacion_llm_avanzada.xlsx'))
for col in df_llm.columns:
    if df_llm[col].dtype == 'datetime64[ns]':
        df_llm[col] = df_llm[col].dt.strftime('%Y-%m-%d')
    if df_llm[col].dtype == 'object':
        df_llm[col] = df_llm[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
df_llm = df_llm.fillna('')
save_json(df_llm.to_dict(orient='records'), 'resultados_llm.json')
metadata['archivos_procesados'].append('resultados_clasificacion_llm_avanzada.xlsx')

# 6. resumen_clasificacion_avanzada.xlsx
print('Procesando resumen_clasificacion_avanzada.xlsx...')
df_res_av = pd.read_excel(os.path.join(BASE_INPUT, 'resumen_clasificacion_avanzada.xlsx'))
df_res_av = df_res_av.fillna('')
save_json(df_res_av.to_dict(orient='records'), 'resumen_clasificacion_avanzada.json')
metadata['archivos_procesados'].append('resumen_clasificacion_avanzada.xlsx')

# 7. resumen_conteo_clasificacion_final.xlsx
print('Procesando resumen_conteo_clasificacion_final.xlsx...')
xl_res_final = pd.ExcelFile(os.path.join(BASE_INPUT, 'resumen_conteo_clasificacion_final.xlsx'))
resumen_cat = pd.read_excel(xl_res_final, sheet_name='Resumen por Categoría')
resumen_cat = resumen_cat.sort_values('Conteo', ascending=False)
save_json(resumen_cat.to_dict(orient='records'), 'resumen_categorias.json')
detalle_prod = pd.read_excel(xl_res_final, sheet_name='Detalle por Producto')
detalle_prod = detalle_prod.fillna('')
save_json(detalle_prod.to_dict(orient='records'), 'detalle_productos.json')
metadata['archivos_procesados'].append('resumen_conteo_clasificacion_final.xlsx')

# Copiar imagenes PNG
print('Copiando imagenes PNG...')
images = [
    'conteo_sustancias_tipo.png',
    'heatmap_sustancia_sexo.png',
    'intencionalidad.png',
    'sexo.png',
    'sustancias_por_intencionalidad.png',
    'sustancias_por_sexo.png',
    'sustancias.png',
    'top10_sustancias.png'
]
for img in images:
    src = os.path.join(IMAGES_SRC, img)
    dst = os.path.join(IMAGES_DST, img)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f'Copiado: {img}')
    else:
        print(f'ADVERTENCIA: No existe {img}')

# Calcular KPIs
print('Calculando KPIs...')
total_registros = int(base_completa.shape[0])
intencional = intencionalidad[intencionalidad['intencionalidad'] == 'intencional']['numero_registros'].values[0] if len(intencionalidad[intencionalidad['intencionalidad'] == 'intencional']) > 0 else 0
no_intencional = intencionalidad[intencionalidad['intencionalidad'] == 'no_intencional']['numero_registros'].values[0] if len(intencionalidad[intencionalidad['intencionalidad'] == 'no_intencional']) > 0 else 0
pct_intencional = round(intencional / total_registros * 100, 2) if total_registros > 0 else 0
pct_no_intencional = round(no_intencional / total_registros * 100, 2) if total_registros > 0 else 0

sustancias_sorted = sustancias.sort_values('numero_registros', ascending=False)
sustancia_mas_frecuente = str(sustancias_sorted.iloc[0]['sustancia']) if len(sustancias_sorted) > 0 else ''
segunda_sustancia = str(sustancias_sorted.iloc[1]['sustancia']) if len(sustancias_sorted) > 1 else ''
tercera_sustancia = str(sustancias_sorted.iloc[2]['sustancia']) if len(sustancias_sorted) > 2 else ''

# Sustancia mas asociada a intencionalidad (mayor porcentaje intencional, minimo 100 registros)
sust_int_filtered = sust_int[sust_int['total'] >= 100].sort_values('porcentaje_intencional', ascending=False)
sustancia_mas_intencional = str(sust_int_filtered.iloc[0]['sustancia']) if len(sust_int_filtered) > 0 else ''

sexo_f = int(sexo[sexo['sexo'] == 'F']['numero_registros'].values[0]) if len(sexo[sexo['sexo'] == 'F']) > 0 else 0
sexo_m = int(sexo[sexo['sexo'] == 'M']['numero_registros'].values[0]) if len(sexo[sexo['sexo'] == 'M']) > 0 else 0

categorias_detectadas = int(sustancias.shape[0])

kpis = {
    'total_registros': total_registros,
    'intencional': int(intencional),
    'no_intencional': int(no_intencional),
    'pct_intencional': pct_intencional,
    'pct_no_intencional': pct_no_intencional,
    'sustancia_mas_frecuente': sustancia_mas_frecuente,
    'segunda_sustancia': segunda_sustancia,
    'tercera_sustancia': tercera_sustancia,
    'sustancia_mas_intencional': sustancia_mas_intencional,
    'sexo_f': sexo_f,
    'sexo_m': sexo_m,
    'categorias_detectadas': categorias_detectadas
}

save_json(kpis, 'kpis.json')

# Guardar metadata
save_json(metadata, 'metadata.json')

print('\nProcesamiento completado exitosamente.')
