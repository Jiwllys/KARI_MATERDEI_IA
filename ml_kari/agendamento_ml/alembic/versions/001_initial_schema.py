from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('paciente',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('risco_score', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('agendamento_consulta',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('profissional_id', sa.Integer(), nullable=False),
        sa.Column('especialidade_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('data_consulta', sa.TIMESTAMP(), nullable=False),
        sa.Column('hora', sa.Time(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
        sa.Column('no_show', sa.Boolean(), server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['paciente_id'], ['paciente.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_data_consulta', 'agendamento_consulta', ['data_consulta'])
    op.create_index('idx_paciente_data', 'agendamento_consulta', ['paciente_id', 'data_consulta'])

def downgrade():
    op.drop_index('idx_paciente_data', table_name='agendamento_consulta')
    op.drop_index('idx_data_consulta', table_name='agendamento_consulta')
    op.drop_table('agendamento_consulta')
    op.drop_table('paciente')