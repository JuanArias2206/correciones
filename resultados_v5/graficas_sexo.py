import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Configuración de matplotlib y seaborn
plt.style.use('ggplot')
sns.set_theme(style="whitegrid")

# Define las rutas de los archivos
# Reemplaza 'ruta/resultados_clasificacion_llm_avanzada.xlsx' con la ruta completa a tu archivo
file_path = '/Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/outputs/salidas_llm/resultados_v5/resultados_clasificacion_llm_avanzada.xlsx'
output_dir = os.path.dirname(file_path)
output_path = os.path.join(output_dir, 'analisis_resultados.xlsx')

# Asegurarse de que el directorio de salida existe
os.makedirs(output_dir, exist_ok=True)

# Cargar el archivo de Excel
try:
    df = pd.read_excel(file_path, engine='openpyxl')
except FileNotFoundError:
    print(f"Error: El archivo de Excel no se encontró en la ruta especificada: {file_path}")
    exit()
except Exception as e:
    print(f"Ocurrió un error al leer el archivo: {e}")
    exit()

# Limpiar y preparar los datos
df['grupos_sustancia_final'] = df['grupos_sustancia_final'].astype(str).str.strip("[]").str.replace("'", "").str.replace(" ", "").str.split(',')
df = df.explode('grupos_sustancia_final')

# Clasificar la intencionalidad
df['intencionalidad'] = np.where(df['origen_hoja'].astype(str).str.contains('356'), 'intencional', 'no_intencional')

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
sustancia_intencionalidad = df.groupby(['grupos_sustancia_final', 'intencionalidad']).size().unstack(fill_value=0).reset_index()
sustancia_intencionalidad.columns = ['sustancia', 'intencional', 'no_intencional']

# Guardar los resultados en un archivo de Excel con gráficos
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    # Escribir los DataFrames en hojas separadas
    sustancia_counts.to_excel(writer, sheet_name='Sustancias', index=False)
    intencionalidad_counts.to_excel(writer, sheet_name='Intencionalidad', index=False)
    sexo_counts.to_excel(writer, sheet_name='Sexo', index=False)
    sustancia_intencionalidad.to_excel(writer, sheet_name='Sustancias_por_Intencionalidad', index=False)

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
    intencionalidad_counts.set_index('intencionalidad').plot(kind='bar', ax=ax2, color=['skyblue', 'salmon'])
    ax2.set_title('Frecuencia por Intencionalidad', fontsize=16)
    ax2.set_xlabel('Intencionalidad', fontsize=12)
    ax2.set_ylabel('Número de Registros', fontsize=12)
    plt.xticks(rotation=0)
    plt.tight_layout()
    fig2.savefig(os.path.join(output_dir, 'intencionalidad.png'))

    # Gráfico de distribución por sexo
    fig3, ax3 = plt.subplots(figsize=(8, 6))
    sns.countplot(x='sexo', data=df, ax=ax3, palette='viridis')
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
    sustancia_intencionalidad.set_index('sustancia').plot(kind='bar', stacked=True, ax=ax5, colormap='viridis')
    ax5.set_title('Distribución de Sustancias por Intencionalidad', fontsize=16)
    ax5.set_xlabel('Tipo de Sustancia', fontsize=12)
    ax5.set_ylabel('Número de Registros', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Intencionalidad')
    plt.tight_layout()
    fig5.savefig(os.path.join(output_dir, 'sustancias_por_intencionalidad.png'))

    # Guardar las imágenes en el archivo de Excel
    workbook = writer.book
    worksheet_sustancias = writer.sheets['Sustancias']
    worksheet_intencionalidad = writer.sheets['Intencionalidad']
    worksheet_sexo = writer.sheets['Sexo']

    worksheet_sustancias.insert_image('D2', os.path.join(output_dir, 'sustancias.png'))
    worksheet_intencionalidad.insert_image('D2', os.path.join(output_dir, 'intencionalidad.png'))
    worksheet_sexo.insert_image('D2', os.path.join(output_dir, 'sexo.png'))

    print(f"\nAnálisis completado. Los resultados y gráficos se han guardado en: {output_path}")