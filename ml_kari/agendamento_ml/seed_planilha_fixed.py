import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:32693515@localhost/agendamento_ml_dev')

def seed_planilha(caminho='C:/dev/ml_kari/kari_historico.xlsx'):
    with engine.begin() as conn:
        # TRUNCATE seguro (só tabelas existentes)
        conn.execute(text('TRUNCATE TABLE pacientes RESTART IDENTITY CASCADE'))
        conn.execute(text('TRUNCATE TABLE agendamentos RESTART IDENTITY CASCADE'))

        # Aba 0: pacientes (500 rows)
        df_pac = pd.read_excel(caminho, sheet_name=0)
        print('Pacientes columns:', df_pac.columns.tolist())
        # Converte score_risco_saude TEXT -> FLOAT
        if 'score_risco_saude' in df_pac.columns:
            df_pac['score_risco_saude'] = pd.to_numeric(df_pac['score_risco_saude'], errors='coerce')
        df_pac.to_sql('pacientes', conn, if_exists='append', index=False)
        print(f'Pacientes inseridos: {len(df_pac)}')

        # Aba 1: agendamentos (2000 rows)
        df_ag = pd.read_excel(caminho, sheet_name=1)
        print('Agendamentos columns:', df_ag.columns.tolist())
        # no_show INT 0/1 (já compatível com INTEGER)
        if 'no_show' in df_ag.columns:
            df_ag['no_show'] = df_ag['no_show'].astype(int)
        # Datas STR -> DATE
        for col in ['data_criada', 'data_agendada', 'data_realizada']:
            if col in df_ag.columns:
                df_ag[col] = pd.to_datetime(df_ag[col], format='%d/%m/%Y', errors='coerce').dt.date
        df_ag.to_sql('agendamentos', conn, if_exists='append', index=False)
        print(f'Agendamentos inseridos: {len(df_ag)}')

if __name__ == '__main__':
    seed_planilha()