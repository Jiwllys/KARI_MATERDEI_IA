import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from dotenv import load_dotenv

def sugerir_agenda_familiar(familia_id, hora_inicio_str="08:00"):
    load_dotenv()
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    # 1. Busca os membros da família e seus scores
    query = f"""
    SELECT id, nome, risco_score 
    FROM pacientes 
    WHERE familia_id = {familia_id}
    """
    membros = pd.read_sql(query, engine)
    
    if membros.empty:
        print(f"Nenhum membro encontrado para a família {familia_id}")
        return

    # 2. Calcula a prioridade interna (usando a mesma lógica da Kari)
    membros['prioridade'] = membros['risco_score'].fillna(0)
    membros = membros.sort_values(by='prioridade', ascending=False)

    # 3. Organiza o Bloco de 20 minutos
    hora_atual = datetime.strptime(hora_inicio_str, "%H:%M")
    
    print(f"\n📅 SUGESTÃO DE BLOCO FAMILIAR - ID: {familia_id}")
    print("-" * 50)
    
    for _, paciente in membros.iterrows():
        print(f"🕒 {hora_atual.strftime('%H:%M')} | Paciente: {paciente['nome']} (Risco: {paciente['risco_score']})")
        hora_atual += timedelta(minutes=20)
    
    print("-" * 50)
    print("Kari: Intervalos de 20 min aplicados para otimização logística.")

if __name__ == "__main__":
    # Teste com uma familia_id que você tenha no banco
    # Se você ainda não populou o familia_id no SQL, o resultado será vazio.
    f_id = input("Digite o ID da família para teste: ")
    sugerir_agenda_familiar(f_id)