import pandas as pd
import os
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier # O novo motor da Kari
from imblearn.over_sampling import SMOTE
from dotenv import load_dotenv
import joblib

def treinar_modelo():
    load_dotenv()
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    print("🚀 Iniciando Treinamento de Alta Performance (XGBoost)...")
    
    # Adicionamos o dia da semana para captar padrões temporais
    query = """
    SELECT 
        EXTRACT(YEAR FROM AGE(p.data_nasc)) as idade,
        p.comorbidades,
        a.risco_paciente, 
        a.lead_time_dias, 
        a.priority_score,
        EXTRACT(DOW FROM a.data_consulta) as dia_semana,
        a.no_show
    FROM agendamentos a
    JOIN pacientes p ON a.paciente_id = p.id
    """
    df = pd.read_sql(query, engine)

    df = df.fillna(0)
    df['no_show'] = df['no_show'].astype(int)

    X = df.drop('no_show', axis=1)
    y = df['no_show']

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Normalização
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Balanceamento
    print("⚖️ Equilibrando dados...")
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)

    print("🧠 Treinando XGBoost...")
    # Versão limpa sem o parâmetro obsoleto
    modelo = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss' # Mantenha este para evitar outro warning de métrica
    )
    
    modelo.fit(X_train_res, y_train_res)

    # Salva os arquivos (o nome continua o mesmo para não quebrar seu script de dashboard)
    joblib.dump(modelo, 'modelo_no_show.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    
    acuracia = modelo.score(X_test_scaled, y_test)
    print("✅ Kari subiu de nível!")
    print(f"📈 Nova Acurácia com XGBoost: {acuracia:.2%}")

if __name__ == "__main__":
    treinar_modelo()