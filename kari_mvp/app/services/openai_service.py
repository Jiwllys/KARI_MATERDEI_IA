import os
from openai import OpenAI

_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY não encontrado no ambiente (.env).")
        _client = OpenAI(api_key=api_key)
    return _client

def humanizar_resposta(resposta_base, etapa, intent):
    """
    Deixa a resposta mais humana sem alterar os fatos.
    Se falhar, retorna a resposta original.
    """
    if not resposta_base:
        return resposta_base

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = _get_client()

    system = (
    "Você é Alencarina, concierge amigável de agendamento familiar. "
    "Reescreva a mensagem base para soar natural, casual e empática, como uma conversa real. "
    "Exemplos bons: 'Beleza, Vinicius! Qual unidade fica melhor pra vocês?' em vez de 'Escolha a unidade.' "
    "'Legal que escolheu Cardiologia pra Kátia 😊 Agora, data?' em vez de 'Escolha a data.' "
    "NÃO invente dados (nomes, horários, unidades). Mantenha listas/horários com quebras. "
    "Adicione entusiasmo leve (1 emoji max), confirme o que o user disse e pergunte 1 coisa só. "
    "Mantenha curto (1-2 frases)."
    )

    user = (
    f"Etapa: {etapa}\nIntent: {intent}\n\n"
    f"Mensagem base (torne natural):\n{resposta_base}\n\n"
    "Resposta em pt-br:"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.7,
            max_tokens=180,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return resposta_base