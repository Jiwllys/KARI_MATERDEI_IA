from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Paciente(Base):
    __tablename__ = 'pacientes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False)
    sexo = Column(String(1)) 
    telefone = Column(String(20))
    data_nasc = Column(Date) # Para o cálculo de idade dinâmica
    comorbidades = Column(Integer, default=0) # Base para o modelo XGBoost
    risco_score = Column(Float, default=0.0)
    familia_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    agendamentos = relationship("Agendamento", back_populates="paciente")

class Agendamento(Base):
    __tablename__ = 'agendamentos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'), nullable=False)
    data_consulta = Column(DateTime, nullable=False)
    hora = Column(String(5), default='08:00')
    status = Column(String(20), default='agendado')
    lead_time_dias = Column(Float)
    priority_score = Column(Float) 
    no_show = Column(Integer, default=0) 
    especialidade = Column(String(50))
    
    paciente = relationship("Paciente", back_populates="agendamentos")