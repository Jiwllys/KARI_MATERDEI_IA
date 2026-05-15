import datetime
import re
import random
import string
# Nota: Mantive o import do seu serviço de banco de dados
from app.services.db_service import get_saude_usuario

# --- CONFIGURAÇÕES E DADOS MOCKADOS PARA O MVP ---

RESPONSAVEL_NOME = "Vinicius"
MAX_PESSOAS = 4

DEPENDENTES_MOCK = ["Kátia Yamamoto", "Vanessa Yamamoto", "Bruno Yamamoto", "Saulo Yamamoto"]
ESPECIALIDADES_MOCK = ["Cardiologia", "Dermatologia", "Ginecologia", "Neurologia", "Ortopedia", "Pediatria", "Reumatologia"]
UNIDADES_MOCK = {
    "Mater Dei Santo Agostinho": "BH - Próximo",
    "Mater Dei Contorno": "BH - Próximo",
    "Mater Dei Betim-Contagem": "Betim - Distante",
    "Mater Dei Salvador": "Salvador - Muito Distante"
}

# --- HELPERS DE HUMANIZAÇÃO ---

def _get_frase_selecao(item, acao="selecionar"):
    frases_sel = [
        f"Com certeza, adicionei {item} aqui!",
        f"Ok, {item} selecionado com sucesso.",
        f"Perfeito! {item} já está na lista.",
        f"Feito! Acabei de marcar {item} para você.",
        f"Ótima escolha! {item} foi adicionado."
    ]
    frases_rem = [
        f"Tudo bem, removi {item} da seleção.",
        f"Entendido! {item} foi retirado.",
        f"Certo, acabei de desmarcar {item}.",
        f"Sem problemas, {item} não está mais selecionado."
    ]
    return random.choice(frases_sel) if acao == "selecionar" else random.choice(frases_rem)

# --- HELPERS DE TEXTO/INTENÇÃO ---

def _gerar_lote_codigo(tamanho: int = 8) -> str:
    alfabeto = string.ascii_uppercase + string.digits
    return "".join(random.choice(alfabeto) for _ in range(tamanho))

def _get_command_part(text: str, prefix: str):
    # Otimizado para capturar o valor após os dois pontos na frase humanizada
    if (text or "").startswith(prefix):
        return (text or "").replace(prefix, "", 1).strip()
    return None

def _is_cumprimento(lower: str) -> bool:
    return any(w in lower for w in ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "eai", "e aí"])

def _is_listar_agendamentos(lower: str) -> bool:
    return any(g in lower for g in ["meus agendamentos", "minhas consultas", "ver agendamentos", "listar agendamentos"])

# --- FUNÇÕES DE CARDS ---

def _adicionar_botao_voltar(cards):
    """
    Modificado: Agora tenta agrupar o botão Voltar no mesmo card de ação (Confirmar/OK)
    se ele existir, para evitar a criação de um card extra.
    """
    btn_voltar = {"label": "⬅️ Voltar", "command": "voltar", "css_class": "btn-voltar"}
    
    if not cards:
        return [{"title": "Navegação", "actions": [btn_voltar]}]
    
    ultimo_card = cards[-1]
    
    # Lista de labels que indicam que o card é de "Avançar"
    labels_avancar = ["CONFIRMAR SELEÇÃO ✅", "CONFIRMAR ESPECIALIDADES ✅", "CONFIRMAR UNIDADE ✅", "CONFIRMAR DATA ✅", "VER RESUMO FINAL ✅", "CONFIRMAR E FINALIZAR ✅", "ok"]
    
    tem_avancar = any(act.get("label") in labels_avancar or act.get("command") == "ok" for act in ultimo_card.get("actions", []))

    if tem_avancar:
        # Insere o Voltar no início da lista de ações do mesmo card
        ultimo_card["actions"].insert(0, btn_voltar)
    else:
        # Se não houver card de confirmação, mantém o comportamento de segurança de adicionar um card de navegação
        cards.append({
            "title": "Deseja corrigir algo?",
            "actions": [{"label": "⬅️ Voltar para etapa anterior", "command": "voltar", "css_class": "btn-voltar"}]
        })
    
    return cards

def _card_pergunta_ver_agendamentos():
    return [{
        "title": "Agendamentos",
        "lines": ["Quer ver seus agendamentos agora?"],
        "actions": [
            {"label": "Sim", "command": "sim", "css_class": "btn-avancar"},
            {"label": "Não", "command": "não", "css_class": "btn-voltar"}
        ]
    }]

def _card_cta_agendamentos():
    return [{
        "title": "O que você quer fazer agora?",
        "lines": ["Você pode cancelar por paciente ou encerrar."],
        "actions": [
            {"label": "Cancelar agendamento", "command": "meus agendamentos", "css_class": "btn-remover"},
            {"label": "Fechar consulta", "command": "fechar consulta", "css_class": "btn-voltar"}
        ]
    }]

def _montar_cards_dependentes(dependentes_disponiveis: list, dependentes_selecionados: list):
    cards = []
    
    # Adicionando o próprio usuário como primeira opção (Fluxo Familiar)
    todos_disponiveis = [RESPONSAVEL_NOME] + dependentes_disponiveis
    
    for nome in todos_disponiveis:
        selecionado = nome in dependentes_selecionados
        label_nome = f"{nome} (Você)" if nome == RESPONSAVEL_NOME else nome
        # Humanização da mensagem que sobe no chat
        label_acao = "Remover Dependente" if selecionado else "Selecionar Dependente"
        
        cards.append({
            "title": label_nome + (" (Selecionado)" if selecionado else ""),
            "lines": [],
            "actions": [{
                "label": "Remover" if selecionado else "Selecionar",
                "command": f"{label_acao}: {nome}",
                "css_class": "btn-remover" if selecionado else "btn-selecionar"
            }]
        })
    
    if dependentes_selecionados:
        cards.append({
            "title": "Finalizar seleção",
            "lines": [f"Selecionados: {', '.join(dependentes_selecionados)}"],
            "actions": [{"label": "CONFIRMAR SELEÇÃO ✅", "command": "ok", "css_class": "btn-avancar"}]
        })
    return _adicionar_botao_voltar(cards)

def _montar_cards_especialidades(dependentes_selecionados: list, especialidades_por_dep: dict):
    cards = []
    total_preenchido = 0
    especialidades_destaque = ["Ortopedia", "Reumatologia", "Neurologia"]
    
    for nome in (dependentes_selecionados or []):
        esp_selecionada = (especialidades_por_dep or {}).get(nome) or ""
        if esp_selecionada:
            total_preenchido += 1
            
        opcoes_formatadas = []
        for esp in ESPECIALIDADES_MOCK:
            if RESPONSAVEL_NOME in nome and esp in especialidades_destaque:
                opcoes_formatadas.append(f"🟢 {esp}")
            else:
                opcoes_formatadas.append(esp)

        cards.append({
            "title": f"Especialidade para {nome}",
            "lines": [f"Selecionada: {esp_selecionada or '-'}"],
            "select": {
                "placeholder": "Clique para escolher a especialidade",
                "options": opcoes_formatadas,
                "selected": esp_selecionada,
                # Humanização do prefixo da especialidade
                "commandPrefix": f"Especialidade para {nome}: "
            },
            "actions": []
        })
    
    if dependentes_selecionados and total_preenchido == len(dependentes_selecionados):
        cards.append({
            "title": "Tudo pronto?",
            "actions": [{"label": "CONFIRMAR ESPECIALIDADES ✅", "command": "ok", "css_class": "btn-avancar"}]
        })
    return _adicionar_botao_voltar(cards)

def _montar_cards_unidades(unidades_disponiveis: dict, unidade_selecionada: str):
    cards = [{
        "title": nome,
        "lines": [f"Proximidade: {status}"],
        "actions": [{
            "label": "Selecionada ✅" if nome == unidade_selecionada else "Selecionar",
            # Humanização da unidade
            "command": f"Unidade Selecionada: {nome}",
            "css_class": "btn-avancar" if nome == unidade_selecionada else "btn-selecionar"
        }]
    } for nome, status in unidades_disponiveis.items()]
    
    if unidade_selecionada:
        cards.append({
            "title": "Prosseguir com esta unidade?",
            "actions": [{"label": "CONFIRMAR UNIDADE ✅", "command": "ok", "css_class": "btn-avancar"}]
        })
    return _adicionar_botao_voltar(cards)

def _montar_cards_calendario(ano: int, mes: int, data_selecionada: str):
    cards = []
    for dia in [10, 11, 14, 15, 16, 17, 18]:
        data_str = f"{ano}-{mes:02d}-{dia:02d}"
        data_humanizada = f"{dia:02d}/{mes:02d}/{ano}"
        selecionada = data_str == data_selecionada
        cards.append({
            "title": data_humanizada,
            "actions": [{
                "label": "Data Selecionada ✅" if selecionada else "Selecionar Data",
                # Humanização da data enviada ao chat
                "command": f"Data Selecionada: {data_humanizada} (ID:{data_str})",
                "css_class": "btn-avancar" if selecionada else "btn-selecionar"
            }]
        })
    if data_selecionada:
        cards.append({
            "title": "Prosseguir com esta data?",
            "actions": [{"label": "CONFIRMAR DATA ✅", "command": "ok", "css_class": "btn-avancar"}]
        })
    return _adicionar_botao_voltar(cards)

def _montar_cards_horarios(num_dependentes: int, data_selecionada: str, horario_selecionado: list):
    if not data_selecionada: return []
    cards = []
    hora_inicio = 8
    for i in range(3):
        bloco = []
        hora_atual = datetime.datetime(2026, 1, 1, hour=hora_inicio + i, minute=0)
        for _ in range(num_dependentes):
            bloco.append(hora_atual.strftime("%H:%M"))
            hora_atual += datetime.timedelta(minutes=20)
        bloco_str = ",".join(bloco)
        selecionado = (bloco == (horario_selecionado or []))
        cards.append({
            "title": f"Opção {i+1}",
            "lines": [f"Horários: {', '.join(bloco)}"],
            "actions": [{
                "label": "Bloco Selecionado ✅" if selecionado else "Selecionar Bloco",
                # Humanização do horário
                "command": f"Horário Selecionado: {', '.join(bloco)}",
                "css_class": "btn-avancar" if selecionado else "btn-selecionar"
            }]
        })
    if horario_selecionado:
        cards.append({
            "title": "Prosseguir com este horários?",
            "actions": [{"label": "VER RESUMO FINAL ✅", "command": "ok", "css_class": "btn-avancar"}]
        })
    return _adicionar_botao_voltar(cards)

def _montar_cards_confirmacao_final(slots: dict):
    cards = []
    dependentes = slots.get("dependentes_selecionados", [])
    horarios = slots.get("horarios_selecionados", [])
    especialidades = slots.get("especialidades_selecionadas", {})
    
    for i, nome in enumerate(dependentes):
        cards.append({
            "title": f"Consulta {i+1}",
            "lines": [
                f"Paciente: {nome}",
                f"Especialidade: {especialidades.get(nome, 'N/A')}",
                f"Data/Hora: {slots.get('data_selecionada', 'N/A')}, {horarios[i] if i < len(horarios) else 'N/A'}",
                f"Local: {slots.get('unidade_selecionada', 'N/A')}"
            ],
            "actions": []
        })
    cards.append({
        "title": "Confirmar Agendamento?",
        "actions": [{"label": "CONFIRMAR E FINALIZAR ✅", "command": "ok", "css_class": "btn-avancar"}]
    })
    return _adicionar_botao_voltar(cards)

# --- NLU PRINCIPAL ---

def nlu_kari(user_text: str, state: dict):
    text = (user_text or "").strip()
    lower = text.lower()

    if not state or _is_cumprimento(lower) or lower == "reiniciar":
        state = {
            "etapa": "inicio",
            "historico_etapas": [],
            "slots": {},
            "meus_agendamentos": [],
            "owner_nome": RESPONSAVEL_NOME
        }

    slots = state.get("slots", {})
    state["slots"] = slots
    etapa = state.get("etapa", "inicio")

    if lower in ["fechar consulta", "fechar", "encerrar", "sair"]:
        state.update({"etapa": "inicio", "historico_etapas": [], "slots": {}})
        return {"intent": "despedida", "slots": {}, "resposta_alencarina": "Certo! Se precisar de algo mais, estarei por aqui. Tenha um ótimo dia!", "_state": state}

    # LÓGICA DE VOLTAR
    if lower == "voltar":
        if state.get("historico_etapas"):
            nova_etapa = state["historico_etapas"].pop()
            state["etapa"] = nova_etapa
            etapa = nova_etapa 
            text = "" 
            lower = ""
        else:
            state["etapa"] = "inicio"
            etapa = "inicio"

    # ETAPA: INICIO
    if etapa == "inicio":
        saude, _ = get_saude_usuario(state["owner_nome"])
        state["etapa"] = "ramificacao_agendamento"
        return {
            "intent": "cumprimento",
            "slots": slots,
            "resposta_alencarina": f"Olá {state['owner_nome']}, tudo bom?\n\nVi aqui que sua saúde está {saude}. 😊\nO que você deseja fazer hoje?\n\nPosso organizar agendamentos para você ou para sua família. Selecione abaixo como prefere seguir!",
            "cards": [{
                "title": "Tipo de Agendamento",
                "actions": [
                    {"label": "👤 Individual (Para mim)", "command": "individual", "css_class": "btn-individual"},
                    {"label": "👨‍👩‍👧‍👦 Familiar (Dependentes)", "command": "familiar", "css_class": "btn-familiar"}
                ]
            }],
            "_state": state
        }

    # ETAPA: RAMIFICAÇÃO
    if etapa == "ramificacao_agendamento":
        if "individual" in lower:
            state["historico_etapas"].append("ramificacao_agendamento")
            state["etapa"] = "aguardando_especialidades"
            state["fluxo_individual"] = True
            slots["dependentes_selecionados"] = [f"{state['owner_nome']} (1ª)", f"{state['owner_nome']} (2ª)", f"{state['owner_nome']} (3ª)"]
            slots["especialidades_selecionadas"] = {}
            return {
                "intent": "individual",
                "resposta_alencarina": f"Combinado, {state['owner_nome']}! Vamos agendar suas 3 consultas individuais. Por favor, escolha a especialidade para cada uma:",
                "cards": _montar_cards_especialidades(slots["dependentes_selecionados"], {}),
                "_state": state
            }
        elif "familiar" in lower:
            state["historico_etapas"].append("ramificacao_agendamento")
            state["etapa"] = "aguardando_dependentes"
            state["fluxo_individual"] = False
            slots["dependentes_selecionados"] = []
            return {
                "intent": "familiar",
                "resposta_alencarina": "Com certeza! Para quais dependentes você deseja realizar o agendamento hoje?",
                "cards": _montar_cards_dependentes(DEPENDENTES_MOCK, []),
                "_state": state
            }
        return {
            "intent": "navegacao",
            "resposta_alencarina": "Sem problemas. Qual tipo de agendamento você gostaria de fazer?",
            "cards": [{"title": "Tipo de Agendamento", "actions": [{"label": "👤 Individual", "command": "individual", "css_class": "btn-individual"}, {"label": "👨‍👩‍👧‍👦 Familiar", "command": "familiar", "css_class": "btn-familiar"}]}],
            "_state": state
        }

    # ETAPA: DEPENDENTES
    if etapa == "aguardando_dependentes":
        # NLU agora busca pela frase humanizada
        dep_sel = _get_command_part(text, "Selecionar Dependente: ") or _get_command_part(text, "Remover Dependente: ")
        if dep_sel:
            sel = slots.get("dependentes_selecionados", [])
            if dep_sel in sel: 
                sel.remove(dep_sel)
                msg = _get_frase_selecao(dep_sel, "remover")
            else: 
                sel.append(dep_sel)
                msg = _get_frase_selecao(dep_sel, "selecionar")
            slots["dependentes_selecionados"] = sel
            return {"intent": "coletar", "resposta_alencarina": msg, "cards": _montar_cards_dependentes(DEPENDENTES_MOCK, sel), "_state": state}

        if lower == "ok" and slots.get("dependentes_selecionados"):
            state["historico_etapas"].append("aguardando_dependentes")
            state["etapa"] = "aguardando_especialidades"
            return {"intent": "avancar", "resposta_alencarina": "Ótima seleção! Agora, me diga quais as especialidades para cada um.", "cards": _montar_cards_especialidades(slots["dependentes_selecionados"], {}), "_state": state}
        
        return {"intent": "navegacao", "resposta_alencarina": "Pode selecionar os dependentes na lista abaixo:", "cards": _montar_cards_dependentes(DEPENDENTES_MOCK, slots.get("dependentes_selecionados", [])), "_state": state}

    # ETAPA: ESPECIALIDADES
    if etapa == "aguardando_especialidades":
        # Ajustado para reconhecer "Especialidade para [Nome]: [Especialidade]"
        match = re.search(r"Especialidade para (.*?): (.*)", text)
        if match:
            nome, esp = match.groups()
            esp = esp.replace("🟢 ", "") # Limpa o emoji se houver
            
            # REGRA: Não permitir a mesma especialidade no atendimento individual
            if state.get("fluxo_individual"):
                especialidades_ja_escolhidas = slots.get("especialidades_selecionadas", {}).values()
                if esp in especialidades_ja_escolhidas:
                    return {
                        "intent": "erro_validacao",
                        "resposta_alencarina": f"Ei, você já selecionou {esp} para uma de suas consultas. Por favor, escolha uma especialidade diferente para este agendamento individual.",
                        "cards": _montar_cards_especialidades(slots["dependentes_selecionados"], slots.get("especialidades_selecionadas", {})),
                        "_state": state
                    }

            slots.setdefault("especialidades_selecionadas", {})[nome] = esp
            msg = f"Perfeito! Já anotei {esp} para {nome}."
            return {"intent": "coletar", "resposta_alencarina": msg, "cards": _montar_cards_especialidades(slots["dependentes_selecionados"], slots["especialidades_selecionadas"]), "_state": state}

        if lower == "ok" and len(slots.get("especialidades_selecionadas", {})) == len(slots.get("dependentes_selecionados", [])):
            state["historico_etapas"].append("aguardando_especialidades")
            state["etapa"] = "aguardando_unidade"
            return {"intent": "avancar", "resposta_alencarina": "Tudo anotado. Em qual unidade você prefere o atendimento?", "cards": _montar_cards_unidades(UNIDADES_MOCK, None), "_state": state}

        return {"intent": "navegacao", "resposta_alencarina": "Por favor, defina as especialidades para continuar:", "cards": _montar_cards_especialidades(slots["dependentes_selecionados"], slots.get("especialidades_selecionadas", {})), "_state": state}

    # ETAPA: UNIDADE
    if etapa == "aguardando_unidade":
        uni = _get_command_part(text, "Unidade Selecionada: ")
        if uni:
            slots["unidade_selecionada"] = uni
            return {"intent": "coletar", "resposta_alencarina": f"Excelente! A unidade {uni} é uma ótima escolha.", "cards": _montar_cards_unidades(UNIDADES_MOCK, uni), "_state": state}
        if lower == "ok" and slots.get("unidade_selecionada"):
            state["historico_etapas"].append("aguardando_unidade")
            state["etapa"] = "aguardando_data"
            return {"intent": "avancar", "resposta_alencarina": "Agora, escolha o melhor dia para vocês.", "cards": _montar_cards_calendario(2026, 3, None), "_state": state}

        return {"intent": "navegacao", "resposta_alencarina": "Escolha uma de nossas unidades abaixo:", "cards": _montar_cards_unidades(UNIDADES_MOCK, slots.get("unidade_selecionada")), "_state": state}

    # ETAPA: DATA
    if etapa == "aguardando_data":
        # Extrai o ID técnico da data que enviamos entre parênteses
        match_dt = re.search(r"\(ID:(.*?)\)", text)
        if match_dt:
            dt = match_dt.group(1)
            slots["data_selecionada"] = dt
            data_formatada = datetime.datetime.strptime(dt, "%Y-%m-%d").strftime("%d/%m/%Y")
            return {"intent": "coletar", "resposta_alencarina": f"Data {data_formatada} selecionada! Vamos ver os horários?", "cards": _montar_cards_calendario(2026, 3, dt), "_state": state}
        if lower == "ok" and slots.get("data_selecionada"):
            state["historico_etapas"].append("aguardando_data")
            state["etapa"] = "aguardando_horarios"
            return {"intent": "avancar", "resposta_alencarina": "Quase lá! Escolha o bloco de horários que fica melhor para todos:", "cards": _montar_cards_horarios(len(slots["dependentes_selecionados"]), slots["data_selecionada"], None), "_state": state}

        return {"intent": "navegacao", "resposta_alencarina": "Qual dia fica melhor para o agendamento?", "cards": _montar_cards_calendario(2026, 3, slots.get("data_selecionada")), "_state": state}

    # ETAPA: HORÁRIOS
    if etapa == "aguardando_horarios":
        hr_text = _get_command_part(text, "Horário Selecionado: ")
        if hr_text:
            slots["horarios_selecionados"] = [h.strip() for h in hr_text.split(',')]
            return {"intent": "coletar", "resposta_alencarina": "Horários reservados! Vamos conferir o resumo?", "cards": _montar_cards_horarios(len(slots["dependentes_selecionados"]), slots["data_selecionada"], slots["horarios_selecionados"]), "_state": state}
        if lower == "ok" and slots.get("horarios_selecionados"):
            state["historico_etapas"].append("aguardando_horarios")
            state["etapa"] = "aguardando_confirmacao_final"
            return {"intent": "avancar", "resposta_alencarina": "Tudo pronto! Confira se os dados estão corretos antes de finalizarmos:", "cards": _montar_cards_confirmacao_final(slots), "_state": state}

        return {"intent": "navegacao", "resposta_alencarina": "Selecione o bloco de horários desejado:", "cards": _montar_cards_horarios(len(slots["dependentes_selecionados"]), slots["data_selecionada"], slots.get("horarios_selecionados")), "_state": state}

    # ETAPA: CONFIRMAÇÃO
    if etapa == "aguardando_confirmacao_final":
        if lower == "ok":
            lote = _gerar_lote_codigo()
            state.update({"etapa": "inicio", "slots": {}, "historico_etapas": []})
            return {"intent": "sucesso", "resposta_alencarina": f"🎉 Prontinho! Seus agendamentos foram confirmados com sucesso.\n\nO código do seu agendamento familiar é: **{lote}**.\n\nEm instantes uma mensagem chegará ao seu número de Whatsapp Cadastrado com todas as informações do seu agendamento.\n\nMuito obrigada pela confiança, estarei aqui se precisar de qualquer outra coisa!", "_state": state}
        return {"intent": "navegacao", "resposta_alencarina": "Aqui está o resumo dos seus agendamentos:", "cards": _montar_cards_confirmacao_final(slots), "_state": state}

    return {"intent": "fallback", "resposta_alencarina": "Ops, não consegui entender essa parte. 😕 Tente usar os botões abaixo ou clique em voltar para ajustar algo.", "cards": _adicionar_botao_voltar([]), "_state": state}