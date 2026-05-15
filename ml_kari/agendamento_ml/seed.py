import os
from datetime import datetime, timedelta
from random import choice, randint
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
fake = Faker('pt_BR')

def inserir_pacientes():
    pacientes_ids = []
    with engine.connect() as conn:
        for i in range(200):
            nome = fake.name()
            cpf = str(fake.random_number(digits=11))  # 11 dígitos limpos
            data_nasc = fake.date_of_birth(minimum_age=18, maximum_age=80)
            risco_score = round(randint(0, 100)/100, 2)
            stmt = text("INSERT INTO pacientes (nome, cpf, data_nasc, risco_score) VALUES (:nome, :cpf, :data_nasc, :risco_score) RETURNING id")
            result = conn.execute(stmt, {'nome': nome, 'cpf': cpf, 'data_nasc': data_nasc, 'risco_score': risco_score})
            paciente_id = result.fetchone()[0]
            pacientes_ids.append(paciente_id)
            if (i + 1) % 50 == 0:
                print(f'Inseridos {i + 1} pacientes')
        conn.commit()
    return pacientes_ids

def inserir_agendamentos(pacientes_ids):
    datas_consulta = [fake.date_between(start_date=datetime(2024, 1, 1), end_date=datetime(2026, 4, 21)) for _ in range(1000)]
    datas_consulta.sort()
    with engine.connect() as conn:
        batch_size = 100
        for i in range(0, 1000, batch_size):
            batch = []
            for j in range(batch_size):
                if i + j >= 1000:
                    break
                paciente_id = choice(pacientes_ids)
                data_consulta = datas_consulta[i + j]
                h = randint(8,17)
                m = randint(0,59)
                hora = f"{h:02d}:{m:02d}"
                status_options = ['agendado', 'confirmado', 'cancelado', 'realizado']
                status = choice(status_options)
                lead_time_dias = randint(1, 30)
                priority_score = round(randint(0, 100)/100, 2)
                risco_paciente = round(randint(0, 100)/100, 2)
                batch.append({
                    'paciente_id': paciente_id,
                    'data_consulta': data_consulta,
                    'hora': hora,
                    'status': status,
                    'lead_time_dias': lead_time_dias,
                    'priority_score': priority_score,
                    'risco_paciente': risco_paciente
                })
            stmt = text("""
                INSERT INTO agendamentos (paciente_id, data_consulta, hora, status, lead_time_dias, priority_score, risco_paciente)
                VALUES (:paciente_id, :data_consulta, :hora, :status, :lead_time_dias, :priority_score, :risco_paciente)
            """)
            conn.execute(stmt, batch)
            conn.commit()
            print(f'Inseridos {min(i + batch_size, 1000)} agendamentos')

def contar_registros():
    with engine.connect() as conn:
        count_p = conn.execute(text("SELECT COUNT(*) FROM pacientes")).fetchone()[0]
        count_a = conn.execute(text("SELECT COUNT(*) FROM agendamentos")).fetchone()[0]
        print(f'Total pacientes: {count_p}')
        print(f'Total agendamentos: {count_a}')

def main():
    try:
        print("Iniciando seed...")
        pacientes_ids = inserir_pacientes()
        inserir_agendamentos(pacientes_ids)
        contar_registros()
        print("Seed concluído!")
    except Exception as e:
        print(f'Erro: {e}')

if __name__ == '__main__':
    main()