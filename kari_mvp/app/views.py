from flask import Blueprint, render_template, request, jsonify, session
from app.services.nlu_service import nlu_kari

views = Blueprint("views", __name__)

@views.route("/")
def home():
    # NÃO resetar automaticamente: senão o usuário perde meus_agendamentos a cada refresh
    if "kari_state" not in session:
        session["kari_state"] = {"etapa": "inicio", "slots": {}, "meus_agendamentos": [], "owner_nome": "Vinicius"}
    return render_template("index.html")

@views.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()

    state = session.get("kari_state") or {"etapa": "inicio", "slots": {}, "meus_agendamentos": [], "owner_nome": "Vinicius"}

    result = nlu_kari(msg, state)

    if "_state" in result:
        session["kari_state"] = result["_state"]
        result.pop("_state", None)
    else:
        session["kari_state"] = state

    session.modified = True
    return jsonify(result)