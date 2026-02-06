import pandas as pd

input1 = 'pipeline_bundle/data/wetransfer_sivigila_2025-07-24_1807/356_365_2022.xlsx'
input2 = 'pipeline_bundle/data/wetransfer_sivigila_2025-07-24_1807/356_365_2023.xlsx'
output = 'resultados_v5/resultados_clasificacion_llm_avanzada.xlsx'

total_in = 0
print('='*70)
print('ENTRADA (con nom_pro no nulo):')
print('='*70)

for f in [input1, input2]:
    print(f'\n{f.split("/")[-1]}:')
    xls = pd.ExcelFile(f)
    file_total = 0
    for s in xls.sheet_names:
        df = pd.read_excel(f, sheet_name=s)
        c = len(df[df['nom_pro'].notna()])
        file_total += c
        print(f'  {s}: {c:,}')
    print(f'  Subtotal: {file_total:,}')
    total_in += file_total

print(f'\n{"="*70}')
print(f'TOTAL ENTRADA: {total_in:,}')
print(f'{"="*70}')

df_out = pd.read_excel(output)
print(f'\nSALIDA:')
print(f'  resultados_clasificacion_llm_avanzada.xlsx: {len(df_out):,}')

print(f'\n{"="*70}')
print(f'COMPARACIÓN:')
print(f'{"="*70}')
print(f'  Entrada:  {total_in:,}')
print(f'  Salida:   {len(df_out):,}')
print(f'  Diferencia: {total_in - len(df_out):,}')

if total_in == len(df_out):
    print(f'\n✅ COINCIDEN')
else:
    print(f'\n⚠️  NO COINCIDEN')
    if total_in > len(df_out):
        print(f'   → Faltan {total_in - len(df_out):,} registros')
