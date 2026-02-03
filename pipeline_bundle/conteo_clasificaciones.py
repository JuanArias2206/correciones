#!/usr/bin/env python3
import os
import pandas as pd
import ast

# Define rutas relativas usando BASE_DIR
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
base_out = os.path.join(BASE_DIR, 'outputs', 'clasificaciones_conteo')

# Input and output paths relative to bundle
input_file_path = os.path.join(base_out, 'resultados_clasificacion_llm_avanzada.xlsx')
output_file_path = os.path.join(base_out, 'resumen_conteo_clasificacion_final.xlsx')


# 2. Cargar el DataFrame desde el archivo de Excel
try:
    df = pd.read_excel(input_file_path, sheet_name=0)
    print("Archivo de entrada cargado exitosamente.")
except FileNotFoundError:
    print(f"Error: No se encontró el archivo en la ruta especificada: {input_file_path}")
    exit()

# 3. Preparar los datos para el conteo
#    La columna 'grupos_sustancia_filtrado' contiene listas como cadenas de texto,
#    así que usamos 'ast.literal_eval' para convertirlas en listas de Python.
#    Luego, se "apilan" las categorías para contarlas fácilmente.
df['grupos_sustancia_filtrado'] = df['grupos_sustancia_filtrado'].apply(lambda x: ast.literal_eval(str(x)))

# Crear una lista de todas las categorías de sustancia únicas
all_categories = df['grupos_sustancia_filtrado'].explode()

# 4. Calcular el conteo de cada categoría
conteo_por_categoria = all_categories.value_counts().reset_index()
conteo_por_categoria.columns = ['Clasificación Final', 'Conteo']

# 5. Calcular el conteo de cada producto ('nom_pro') por su clasificación final
#    Primero, expandimos la columna de listas para tener una fila por cada categoría.
df_exploded = df.explode('grupos_sustancia_filtrado')

# Luego, agrupamos por la clasificación final y el nombre del producto para contar.
conteo_por_sustancia = df_exploded.groupby(['grupos_sustancia_filtrado', 'nom_pro']).size().reset_index(name='Conteo')
conteo_por_sustancia.columns = ['Clasificación Final', 'Nombre de Producto', 'Conteo']

# Ordenar los resultados por el conteo de forma descendente.
conteo_por_sustancia = conteo_por_sustancia.sort_values(by=['Clasificación Final', 'Conteo'], ascending=[True, False])

# 6. Guardar los resultados en un único archivo de Excel con dos hojas
with pd.ExcelWriter(output_file_path) as writer:
    conteo_por_categoria.to_excel(writer, sheet_name='Resumen por Categoría', index=False)
    conteo_por_sustancia.to_excel(writer, sheet_name='Detalle por Producto', index=False)

print(f"\nEl archivo de resumen de conteo se ha guardado correctamente en: {output_file_path}")

# Opcional: Imprimir los resultados en la consola para una vista rápida
print("\n--- Conteo por Categoría Final ---")
print(conteo_por_categoria)

print("\n--- Conteo Detallado por Producto y Categoría ---")
print(conteo_por_sustancia.head(20))
