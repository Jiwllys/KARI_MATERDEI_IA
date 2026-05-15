import pandas as pd
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def sincronizar():
    load_dotenv()
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    print("🔄 Sincronizando dados do Excel com o Postgres...")

    # 1. Sincronizar Pacientes (Telefone, Sexo, Comorbidades)
    df_p = pd.read_csv('kari_historico.xlsx - pacientes.csv')
    with engine.connect() as conn:
        for _, row in df_p.iterrows():
            conn.execute(text("""
                UPDATE pacientes 
                SET sexo = :sexo, comorbidades = :comorb, telefone = :tel 
                WHERE id = :id
            """), {"sexo": row['sexo'], "comorb": row['comorbidades'], "tel": row['telefone'], "id": row['paciente_id']})
        conn.commit()
    print("✅ Pacientes atualizados!")

    # 2. Sincronizar Agendamentos (Especialidade)
    df_a = pd.read_csv('kari_historico.xlsx - agendamentos.csv')
    with engine.connect() as conn:
        for _, row in df_a.iterrows():
            conn.execute(text("""
                UPDATE agendamentos 
                SET especialidade = :esp 
                WHERE id = :id
            """), {"esp": row['especialidade'], "id": row['agendamento_id']})
        conn.commit()
    print("✅ Especialidades atualizadas!")

if __name__ == "__main__":
    sincronizar()