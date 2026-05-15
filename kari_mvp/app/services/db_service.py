import psycopg2
from dotenv import load_dotenv
import os
import random
import string

load_dotenv()

def get_db_connection():
    """Conexão com o banco de dados via DATABASE_URL"""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

def get_saude_usuario(usuario_nome='Vinicius'):
    """Lê saúde do banco e gera corações degradê"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT score_saude, status, especialidades_rotina FROM usuario_saude WHERE usuario_nome = %s", (usuario_nome,))
            result = cur.fetchone()
        
        if result:
            score, status, rotina = result
            coracoes = gerar_coracoes(score)
            return f"{status} ({coracoes})", list(rotina)
        
        # Fallback caso não encontre o usuário, agora apenas com corações
        return "estável (❤️🧡🧡💛💛💚💚💚🤍🤍)", ['ortopedista', 'reumatologista', 'neurologista']
    finally:
        conn.close()

def gerar_coracoes(score):
    """Degradê de saúde: apenas corações (vermelho → laranja → amarelo → verde)"""
    # Lista de 10 corações representando o score máximo
    paleta_coracoes = ['❤️', '🧡', '🧡', '💛', '💛', '💚', '💚', '💚', '💚', '💚']
    
    # Seleciona os corações baseados no score (0 a 10)
    cheios = ''.join(paleta_coracoes[:score])
    
    # Coração branco/cinza para os espaços vazios
    vazios = '🤍' * (10 - score)
    
    return f"{cheios}{vazios}"

def gerar_lote_codigo():
    """Gera ID único de 8 caracteres para agendamentos"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=8))

def listar_agendamentos_owner(owner_nome):
    """Lista agendamentos de um proprietário"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT l.lote_codigo, l.owner_nome, c.paciente_ordem, c.paciente_nome, c.especialidade, c.data_preferida, c.horario, c.status
                FROM agendamento_lote l
                LEFT JOIN agendamento_consulta c ON l.id = c.lote_id
                WHERE l.owner_nome = %s;
            """, (owner_nome,))
            return cur.fetchall()
    finally:
        conn.close()