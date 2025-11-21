import pandas as pd
import json
import os

# Exemplo de padrão interno (lista de nomes de colunas)
PADRAO_INTERNO = ['nome', 'email', 'telefone', 'data_nascimento']

def sugerir_mapeamento(colunas_entrada, colunas_padrao):
    """
    Sugere automaticamente o mapeamento entre as colunas do arquivo de entrada
    e o padrão, com correspondência simples por similaridade de nome.
    """
    mapeamento = {}
    for col in colunas_padrao:
        match = next((c for c in colunas_entrada if col in c.lower()), None)
        mapeamento[col] = match if match else ''
    return mapeamento

# Solicita o arquivo CSV de entrada ao usuário
entrada_csv = input('Digite o caminho do arquivo CSV de entrada: ').strip()
while not os.path.isfile(entrada_csv):
    entrada_csv = input('Arquivo não encontrado. Digite novamente o caminho do CSV de entrada: ').strip()

# --- Leitura do arquivo CSV de entrada ---
df = pd.read_csv(entrada_csv)
colunas_entrada = df.columns.str.lower().tolist()
mapeamento_sugerido = sugerir_mapeamento(colunas_entrada, PADRAO_INTERNO)

print('\n--- Revisão do Mapeamento de Colunas ---')
mapeamento_final = {}
for campo_padrao, sugestao in mapeamento_sugerido.items():
    print(f"\nCampo do padrão interno: '{campo_padrao}'")
    if sugestao:
        print(f"Sugestão de coluna original: '{sugestao}'")
    else:
        print("Nenhuma sugestão automática encontrada.")
    print(f"Colunas disponíveis: {df.columns.tolist()}")
    entrada = input(f"Digite o nome da coluna para '{campo_padrao}' (pressione Enter para aceitar '{sugestao}', ou deixe em branco para ignorar): ").strip()
    if not entrada:
        entrada = sugestao
    mapeamento_final[campo_padrao] = entrada if entrada in df.columns else None

# Confirmação final
print("\nMapeamento final selecionado:")
for k, v in mapeamento_final.items():
    print(f"{k} <- {v if v else '(não mapeado)'}")

confirmar = input("\nDeseja aplicar este mapeamento? (s/n): ").strip().lower()
if confirmar != 's':
    print("Processo cancelado.")
    exit(0)

saida_csv = input('\nNome do arquivo CSV padronizado (padrão: padronizado.csv): ').strip()
if not saida_csv:
    saida_csv = 'padronizado.csv'

df_transformado = pd.DataFrame()
for campo_padrao, coluna_origem in mapeamento_final.items():
    if coluna_origem and coluna_origem in df.columns:
        df_transformado[campo_padrao] = df[coluna_origem]
    else:
        df_transformado[campo_padrao] = None

df_transformado.to_csv(saida_csv, index=False)
print(f'\nCSV padronizado gerado em {saida_csv}')