import pandas as pd

print('=== resultados_clasificacion_llm_avanzada.xlsx ===')
df1 = pd.read_excel('resultados_v5/resultados_clasificacion_llm_avanzada.xlsx', sheet_name=0)
print(f'Total registros: {len(df1)}')
print(f'Columnas: {list(df1.columns)}')
print('Primeras 3 filas:')
print(df1.head(3))

print('\n=== resumen_clasificacion_avanzada.xlsx ===')
df2 = pd.read_excel('resultados_v5/resumen_clasificacion_avanzada.xlsx', sheet_name=0)
print(f'Total: {len(df2)}')
print(f'Columnas: {list(df2.columns)}')
print(df2.head(15))

print('\n=== resumen_conteo_clasificacion_final.xlsx ===')
xls = pd.ExcelFile('resultados_v5/resumen_conteo_clasificacion_final.xlsx')
print(f'Sheets: {xls.sheet_names}')
for sheet in xls.sheet_names:
    df = pd.read_excel('resultados_v5/resumen_conteo_clasificacion_final.xlsx', sheet_name=sheet)
    print(f'\n  {sheet}: {len(df)} registros')
    print(df.head(8))
