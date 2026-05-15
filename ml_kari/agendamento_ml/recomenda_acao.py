import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def conectar_banco():
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    return create_engine(db_url)

def gerar_recomendacoes_kari(paciente_id=None):
    engine = conectar_banco()
    
    # Busca dados dos pacientes e calcula idade baseada na data_nasc (que está no seu SQL)
    # Usamos o AGE do PostgreSQL para calcular a idade exata
    query = """
        SELECT 
            id, 
            nome, 
            risco_score, 
            data_nasc,
            EXTRACT(YEAR FROM AGE(data_nasc)) as idade
        FROM pacientes
    """
    
    if paciente_id:
        query += f" WHERE id = {paciente_id}"
        
    df = pd.read_sql(query, engine)
    
    recomendacoes = []

    for _, row in df.iterrows():
        acoes = []
        score = row['risco_score'] or 0
        idade = row['idade'] or 0

        # Lógica 1: Risco Cardiovascular
        if score > 80: # Na sua escala 0.8 é 80
            acoes.append("🚨 Check-up Cardiovascular urgente")
        elif 50 <= score <= 80:
            acoes.append("📅 Exames de rotina semestrais")

        # Lógica 2: Idosos (Avaliação Geriátrica)
        if idade > 65:
            acoes.append("👴 Avaliação geriátrica anual")

        # Lógica 3: Prevenção básica (Exemplo adicional)
        if score < 50 and len(acoes) == 0:
            acoes.append("✅ Manter acompanhamento anual")

        recomendacoes.append({
            "Paciente": row['nome'],
            "Idade": int(idade),
            "Risco": score,
            "Recomendações da Kari": " | ".join(acoes)
        })

    return pd.DataFrame(recomendacoes)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🏥 KARI AI - MÓDULO DE PRESCRIÇÃO PREVENTIVA")
    print("="*60)
    
    df_recomenda = gerar_recomendacoes_kari()
    
    # Exibe apenas pacientes que possuem recomendações críticas primeiro
    print(df_recomenda.sort_values(by="Risco", ascending=False).to_string(index=False))
    print("="*60)