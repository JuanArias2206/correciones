#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
from openpyxl.drawing.image import Image
import seaborn as sns
import numpy as np

# Configuración de matplotlib y seaborn
plt.style.use('ggplot')
sns.set_theme(style="whitegrid")

# Define las rutas de los archivos usando rutas relativas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
base_out = os.path.join(BASE_DIR, 'outputs', 'clasificaciones_conteo')
output_dir = base_out  # Directorio para las imágenes
file_path = os.path.join(base_out, 'resultados_clasificacion_llm_avanzada.xlsx')
output_path = os.path.join(base_out, 'analisis_resultados.xlsx')

# Cargar el archivo de Excel
df = pd.read_excel(file_path, engine='openpyxl')

# ==============================
# PREPROCESAMIENTO
# ==============================

# Limpiar y preparar los datos de grupos_sustancia_final
df['grupos_sustancia_final'] = (
    df['grupos_sustancia_final']
    .astype(str)
    .str.strip("[]")
    .str.replace("'", "", regex=False)
    .str.replace(" ", "", regex=False)
    .str.split(',')
)
df = df.explode('grupos_sustancia_final')

# Clasificar la intencionalidad
df['intencionalidad'] = np.where(
    df['origen_hoja'].astype(str).str.contains('356'),
    'intencional',
    'no_intencional'
)

# ==============================
# TABLAS BÁSICAS
# ==============================

# Contar registros por tipo de sustancia
sustancia_counts = df['grupos_sustancia_final'].value_counts().reset_index()
sustancia_counts.columns = ['sustancia', 'numero_registros']

# Contar frecuencia por intencionalidad
intencionalidad_counts = df['intencionalidad'].value_counts().reset_index()
intencionalidad_counts.columns = ['intencionalidad', 'numero_registros']

# Contar frecuencia por sexo
sexo_counts = df['sexo'].value_counts().reset_index()
sexo_counts.columns = ['sexo', 'numero_registros']

# Contar por sustancia e intencionalidad
sustancia_intencionalidad = (
    df.groupby(['grupos_sustancia_final', 'intencionalidad'])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)
sustancia_intencionalidad.columns = ['sustancia', 'intencional', 'no_intencional']

# ==============================
# ANÁLISIS DETALLADO
# ==============================

# Tabla cruzada Sustancia × Sexo
tabla_sustancia_sexo = df.pivot_table(
    index='grupos_sustancia_final',
    columns='sexo',
    aggfunc='size',
    fill_value=0
).reset_index()

# Tabla cruzada Sustancia × Sexo × Intencionalidad
tabla_detallada = df.pivot_table(
    index='grupos_sustancia_final',
    columns=['sexo', 'intencionalidad'],
    aggfunc='size',
    fill_value=0
)

# Top 10 sustancias
top10_sustancias = (
    df['grupos_sustancia_final']
    .value_counts()
    .head(10)
    .reset_index()
)
top10_sustancias.columns = ['sustancia', 'numero_registros']

# Sustancia × rango de edad (si existe columna 'edad')
if 'edad' in df.columns:
    bins = [0, 11, 17, 29, 44, 59, 200]
    labels = ['0-11', '12-17', '18-29', '30-44', '45-59', '60+']
    df['rango_edad'] = pd.cut(df['edad'], bins=bins, labels=labels, right=True)

    tabla_sustancia_edad = df.pivot_table(
        index='grupos_sustancia_final',
        columns='rango_edad',
        aggfunc='size',
        fill_value=0
    ).reset_index()
else:
    tabla_sustancia_edad = pd.DataFrame({"info": ["No existe columna edad en la base"]})

# ==============================
# RESUMEN TOP 100 POR SUSTANCIA
# ==============================

# Total por sustancia
resumen_sustancia = (
    df.groupby('grupos_sustancia_final')
    .size()
    .reset_index(name='total_registros')
    .rename(columns={'grupos_sustancia_final': 'sustancia'})
)

# Desglose por intencionalidad
tabla_int = df.pivot_table(
    index='grupos_sustancia_final',
    columns='intencionalidad',
    aggfunc='size',
    fill_value=0
)
tabla_int.columns = [f"n_{c}" for c in tabla_int.columns]
tabla_int = tabla_int.reset_index().rename(columns={'grupos_sustancia_final': 'sustancia'})

# Desglose por sexo
tabla_sexo_res = df.pivot_table(
    index='grupos_sustancia_final',
    columns='sexo',
    aggfunc='size',
    fill_value=0
)
tabla_sexo_res.columns = [f"n_sexo_{c}" for c in tabla_sexo_res.columns]
tabla_sexo_res = tabla_sexo_res.reset_index().rename(columns={'grupos_sustancia_final': 'sustancia'})

# Unir todo en un solo resumen
resumen = (
    resumen_sustancia
    .merge(tabla_int, on='sustancia', how='left')
    .merge(tabla_sexo_res, on='sustancia', how='left')
)

# Ordenar por total y tomar top 100
resumen_top100 = resumen.sort_values('total_registros', ascending=False).head(100)

# ==============================
# CONTEO DE SUSTANCIAS POR TIPO
# usando grupos_sustancia_filtrado
# ==============================

df_tipos = df.copy()
df_tipos['grupos_sustancia_filtrado'] = (
    df_tipos['grupos_sustancia_filtrado']
    .astype(str)
    .str.strip("[]")
    .str.replace("'", "", regex=False)
    .str.replace(" ", "", regex=False)
    .str.split(',')
)
df_tipos = df_tipos.explode('grupos_sustancia_filtrado')

tipo_counts = df_tipos['grupos_sustancia_filtrado'].value_counts().reset_index()
tipo_counts.columns = ['tipo_sustancia', 'numero_registros']

# ==============================
# GUARDAR RESULTADOS EN EXCEL
# ==============================

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    # ---- TABLAS BÁSICAS ORIGINALES ----
    sustancia_counts.to_excel(writer, sheet_name='Sustancias', index=False)
    intencionalidad_counts.to_excel(writer, sheet_name='Intencionalidad', index=False)
    sexo_counts.to_excel(writer, sheet_name='Sexo', index=False)
    sustancia_intencionalidad.to_excel(writer, sheet_name='Sustancias_por_Intencionalidad', index=False)

    # ---- NUEVAS TABLAS ----
    df.to_excel(writer, sheet_name='Base_Completa', index=False)
    tabla_sustancia_sexo.to_excel(writer, sheet_name='Sustancia_Sexo', index=False)
    tabla_detallada.to_excel(writer, sheet_name='Sustancia_Sexo_Int')
    top10_sustancias.to_excel(writer, sheet_name='Top10_Sustancias', index=False)
    tabla_sustancia_edad.to_excel(writer, sheet_name='Sustancia_Edad', index=False)
    resumen_top100.to_excel(writer, sheet_name='Resumen_Top100_Sust', index=False)
    tipo_counts.to_excel(writer, sheet_name='Conteo_Sustancias_Tipo', index=False)

    # ==============================
    # GRÁFICOS ORIGINALES
    # ==============================

    # Gráfico de distribución de sustancias
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    sustancia_counts.set_index('sustancia').plot(kind='bar', ax=ax1)
    ax1.set_title('Distribución de Registros por Tipo de Sustancia', fontsize=16)
    ax1.set_xlabel('Tipo de Sustancia', fontsize=12)
    ax1.set_ylabel('Número de Registros', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    fig1.savefig(os.path.join(output_dir, 'sustancias.png'))

    # Gráfico de frecuencia por intencionalidad
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    intencionalidad_counts.set_index('intencionalidad').plot(
        kind='bar', ax=ax2, color=['skyblue', 'salmon']
    )
    ax2.set_title('Frecuencia por Intencionalidad', fontsize=16)
    ax2.set_xlabel('Intencionalidad', fontsize=12)
    ax2.set_ylabel('Número de Registros', fontsize=12)
    plt.xticks(rotation=0)
    plt.tight_layout()
    fig2.savefig(os.path.join(output_dir, 'intencionalidad.png'))

    # Gráfico de distribución por sexo
    fig3, ax3 = plt.subplots(figsize=(8, 6))
    sns.countplot(x='sexo', data=df, ax=ax3)
    ax3.set_title('Distribución de Registros por Sexo', fontsize=16)
    ax3.set_xlabel('Sexo', fontsize=12)
    ax3.set_ylabel('Número de Registros', fontsize=12)
    plt.tight_layout()
    fig3.savefig(os.path.join(output_dir, 'sexo.png'))

    # Gráfico de distribución de sustancias por sexo
    fig4, ax4 = plt.subplots(figsize=(15, 10))
    sns.countplot(y='grupos_sustancia_final', hue='sexo', data=df, ax=ax4, palette='coolwarm')
    ax4.set_title('Distribución de Tipos de Sustancias por Sexo', fontsize=16)
    ax4.set_xlabel('Número de Registros', fontsize=12)
    ax4.set_ylabel('Tipo de Sustancia', fontsize=12)
    plt.tight_layout()
    fig4.savefig(os.path.join(output_dir, 'sustancias_por_sexo.png'))

    # Gráfico de barras apiladas: Sustancia vs Intencionalidad
    fig5, ax5 = plt.subplots(figsize=(15, 10))
    sustancia_intencionalidad.set_index('sustancia').plot(
        kind='bar', stacked=True, ax=ax5, colormap='viridis'
    )
    ax5.set_title('Distribución de Sustancias por Intencionalidad', fontsize=16)
    ax5.set_xlabel('Tipo de Sustancia', fontsize=12)
    ax5.set_ylabel('Número de Registros', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Intencionalidad')
    plt.tight_layout()
    fig5.savefig(os.path.join(output_dir, 'sustancias_por_intencionalidad.png'))

    # ==============================
    # NUEVOS GRÁFICOS
    # ==============================

    # Top 10 sustancias
    fig6, ax6 = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top10_sustancias, x='numero_registros', y='sustancia', ax=ax6)
    ax6.set_title("Top 10 sustancias más frecuentes")
    ax6.set_xlabel("Número de registros")
    ax6.set_ylabel("Sustancia")
    plt.tight_layout()
    fig6.savefig(os.path.join(output_dir, 'top10_sustancias.png'))

    # Heatmap Sustancia × Sexo
    fig7, ax7 = plt.subplots(figsize=(12, 10))
    hm_data = tabla_sustancia_sexo.set_index('grupos_sustancia_final')
    sns.heatmap(hm_data, cmap='viridis', annot=True, fmt='d', ax=ax7)
    ax7.set_title("Heatmap: Sustancia × Sexo")
    ax7.set_xlabel("Sexo")
    ax7.set_ylabel("Tipo de sustancia")
    plt.tight_layout()
    fig7.savefig(os.path.join(output_dir, 'heatmap_sustancia_sexo.png'))

    # Gráfico de conteo de sustancias por tipo (grupos_sustancia_filtrado)
    fig8, ax8 = plt.subplots(figsize=(12, 8))
    sns.barplot(data=tipo_counts, x='numero_registros', y='tipo_sustancia', ax=ax8)
    ax8.set_title("Conteo de sustancias por tipo (filtrado)", fontsize=16)
    ax8.set_xlabel("Número de registros", fontsize=12)
    ax8.set_ylabel("Tipo de sustancia", fontsize=12)
    plt.tight_layout()
    fig8.savefig(os.path.join(output_dir, 'conteo_sustancias_tipo.png'))

    # ==============================
    # INSERTAR IMÁGENES EN EXCEL
    # ==============================

    workbook = writer.book
    worksheet_sustancias = writer.sheets['Sustancias']
    worksheet_intencionalidad = writer.sheets['Intencionalidad']
    worksheet_sexo = writer.sheets['Sexo']
    worksheet_top10 = writer.sheets['Top10_Sustancias']
    worksheet_sustancia_sexo_ws = writer.sheets['Sustancia_Sexo']
    worksheet_conteo_tipo = writer.sheets['Conteo_Sustancias_Tipo']

    img_sustancias = Image(os.path.join(output_dir, 'sustancias.png'))
    img_intencionalidad = Image(os.path.join(output_dir, 'intencionalidad.png'))
    img_sexo = Image(os.path.join(output_dir, 'sexo.png'))
    img_top10 = Image(os.path.join(output_dir, 'top10_sustancias.png'))
    img_hm = Image(os.path.join(output_dir, 'heatmap_sustancia_sexo.png'))
    img_conteo_tipo = Image(os.path.join(output_dir, 'conteo_sustancias_tipo.png'))

    worksheet_sustancias.add_image(img_sustancias, 'D2')
    worksheet_intencionalidad.add_image(img_intencionalidad, 'D2')
    worksheet_sexo.add_image(img_sexo, 'D2')
    worksheet_top10.add_image(img_top10, 'D2')
    worksheet_sustancia_sexo_ws.add_image(img_hm, 'D2')
    worksheet_conteo_tipo.add_image(img_conteo_tipo, 'D2')

print(f"\nAnálisis completado. Los resultados y gráficos se han guardado en: {output_path}")
