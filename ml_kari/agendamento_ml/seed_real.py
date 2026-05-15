import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime

# Carrega as variáveis de ambiente
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

def importar_dados_reais():
    caminho = 'C:/dev/ml_kari/kari_historico.xlsx'
    
    print("📖 Lendo Planilha Mater Dei...")
    try:
        df_pacientes = pd.read_excel(caminho, sheet_name=0)
        df_agendamentos = pd.read_excel(caminho, sheet_name=1)
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo Excel: {e}")
        return

    # --- TRATAMENTO DE PACIENTES ---
    print("🧹 Ajustando dados de pacientes...")
    
    df_pacientes = df_pacientes.rename(columns={
        'paciente_id': 'id',
        'score_risco_saude': 'risco_score'
    })

    # Regra de Idade -> Data de Nascimento (Cálculo para popular o banco)
    if 'idade' in df_pacientes.columns:
        print("🎂 Convertendo idades em datas de nascimento...")
        ano_atual = 2024 # Base fixa para bater com o histórico da planilha
        df_pacientes['data_nasc'] = df_pacientes['idade'].apply(
            lambda x: datetime(ano_atual - int(x), 1, 1).date()
        )
    elif 'data_nasc' in df_pacientes.columns:
        df_pacientes['data_nasc'] = pd.to_datetime(df_pacientes['data_nasc']).dt.date
    else:
        df_pacientes['data_nasc'] = pd.to_datetime('1980-01-01').date()

    # Regra de CPF Único
    if 'cpf' in df_pacientes.columns:
        df_pacientes['cpf'] = df_pacientes['cpf'].fillna(df_pacientes.index.to_series().map(lambda x: str(x+1).zfill(11)))
        df_pacientes['cpf'] = df_pacientes['cpf'].astype(str).str.replace(r'\D', '', regex=True)
    else:
        df_pacientes['cpf'] = [str(i).zfill(11) for i in range(1, len(df_pacientes) + 1)]

    # Colunas que o banco POSSUI e que vamos enviar
    col_pac = ['id', 'nome', 'cpf', 'data_nasc', 'risco_score', 'familia_id', 'sexo', 'comorbidades', 'telefone']
    df_pacientes = df_pacientes[[c for c in col_pac if c in df_pacientes.columns]]

    # --- TRATAMENTO DE AGENDAMENTOS ---
    print("🧹 Ajustando dados de agendamentos...")
    df_agendamentos = df_agendamentos.rename(columns={
        'agendamento_id': 'id',
        'data_agendada': 'data_consulta'
    })

    # Regra de Hora (Obrigatória no Banco)
    if 'hora' not in df_agendamentos.columns:
        df_agendamentos['hora'] = '08:00'
    else:
        df_agendamentos['hora'] = df_agendamentos['hora'].fillna('08:00')

    if 'no_show' in df_agendamentos.columns:
        df_agendamentos['no_show'] = df_agendamentos['no_show'].fillna(0).astype(int)

    # Colunas que o banco POSSUI e que vamos enviar
    col_ag = ['id', 'paciente_id', 'data_consulta', 'hora', 'status', 'lead_time_dias', 'priority_score', 'risco_paciente', 'especialidade', 'no_show']
    df_agendamentos = df_agendamentos[[c for c in col_ag if c in df_agendamentos.columns]]

    with engine.begin() as conn:
        print(f"🚀 Enviando {len(df_pacientes)} Pacientes...")
        df_pacientes.to_sql('pacientes', conn, if_exists='append', index=False)
        
        print(f"🚀 Enviando {len(df_agendamentos)} Agendamentos...")
        df_agendamentos.to_sql('agendamentos', conn, if_exists='append', index=False)

    print("✅ Sincronização concluída com sucesso!")

if __name__ == "__main__":
    importar_dados_reais()