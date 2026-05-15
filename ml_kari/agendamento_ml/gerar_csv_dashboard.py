import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def exportar_dados():
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url)
    
    print("🚀 Acessando a View dashboard_kari...")
    
    try:
        # Lê a View que criamos no pgAdmin
        df = pd.read_sql("SELECT * FROM dashboard_kari", engine)
        
        # Salva o CSV com ponto e vírgula (padrão que o Excel e Looker aceitam bem)
        nome_arquivo = 'dados_dashboard_kari.csv'
        df.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')
        
        print(f"✅ Sucesso! O arquivo '{nome_arquivo}' foi criado na sua pasta.")
        print(f"📊 Total de registros exportados: {len(df)}")
        
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")
        print("Dica: Verifique se você rodou o comando CREATE VIEW no pgAdmin antes.")

if __name__ == "__main__":
    exportar_dados()