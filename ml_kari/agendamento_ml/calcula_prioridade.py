import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def conectar_banco():
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    return create_engine(db_url)

def obter_fila_prioritaria():
    engine = conectar_banco()
    
    # 1. Busca os pesos da configuração
    try:
        config = pd.read_sql("SELECT peso_saude, peso_presenca FROM config_prioridade ORDER BY id DESC LIMIT 1", engine)
        w_saude = config['peso_saude'][0]
        w_presenca = config['peso_presenca'][0]
    except:
        w_saude, w_presenca = 0.6, 0.4 # Fallback

    # 2. Busca Pacientes e calcula histórico de faltas (No-Show)
    # Note os nomes: p.id e p.risco_score (conforme seu SQL)
    query = """
    SELECT 
        p.id as paciente_id, 
        p.nome, 
        p.risco_score,
        COALESCE(AVG(CASE WHEN a.status IN ('faltou', 'cancelado') THEN 0 ELSE 1 END), 1.0) as taxa_presenca
    FROM pacientes p
    LEFT JOIN agendamentos a ON p.id = a.paciente_id
    GROUP BY p.id, p.nome, p.risco_score
    """
    df = pd.read_sql(query, engine)
    
    # 3. ALGORITMO KARI: Cálculo da Prioridade
    # Normalizamos o risco_score (0-100 para 0-1) e multiplicamos pelos pesos
    df['risco_norm'] = df['risco_score'].fillna(0) / 100
    
    df['prioridade_final'] = (
        (df['risco_norm'] * w_saude) + 
        (df['taxa_presenca'] * w_presenca)
    ) * 100
    
    return df.sort_values(by='prioridade_final', ascending=False)

if __name__ == "__main__":
    fila = obter_fila_prioritaria()
    print("\n" + "="*50)
    print("📋 FILA DE PRIORIDADE INTELIGENTE KARI")
    print("="*50)
    # Mostra os 10 primeiros da fila
    print(fila[['nome', 'prioridade_final', 'risco_score', 'taxa_presenca']].head(10))
    print("="*50)