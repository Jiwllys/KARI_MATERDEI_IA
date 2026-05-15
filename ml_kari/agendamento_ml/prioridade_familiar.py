import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def ranking_geral_familias():
    load_dotenv()
    engine = create_engine(os.getenv('DATABASE_URL'))

    # 1. Busca os dados unificados (Individual -> Familiar)
    query = """
    SELECT 
        p.familia_id,
        p.risco_score,
        COALESCE(AVG(CASE WHEN a.status IN ('faltou', 'cancelado') THEN 0 ELSE 1 END), 1.0) as taxa_presenca
    FROM pacientes p
    LEFT JOIN agendamentos a ON p.id = a.paciente_id
    WHERE p.familia_id IS NOT NULL
    GROUP BY p.id, p.familia_id, p.risco_score
    """
    df = pd.read_sql(query, engine)

    # 2. Agrupa por Família para criar o Score do Grupo
    # Calculamos a média de risco e presença da família inteira
    familias_ranking = df.groupby('familia_id').agg({
        'risco_score': 'mean',
        'taxa_presenca': 'mean'
    }).reset_index()

    # 3. Algoritmo Kari para Famílias (60% saúde média / 40% presença média)
    familias_ranking['score_prioridade_grupo'] = (
        (familias_ranking['risco_score'] / 100 * 0.6) + 
        (familias_ranking['taxa_presenca'] * 0.4)
    ) * 100

    return familias_ranking.sort_values(by='score_prioridade_grupo', ascending=False)

if __name__ == "__main__":
    ranking = ranking_geral_familias()
    print("\n🏆 RANKING DE PRIORIDADE POR FAMÍLIA (Kari AI)")
    print("-" * 60)
    print(ranking[['familia_id', 'score_prioridade_grupo', 'risco_score', 'taxa_presenca']].to_string(index=False))
    print("-" * 60)
    print("A Kari sugere agendar os blocos na ordem acima.")