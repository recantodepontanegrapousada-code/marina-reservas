import os, json, urllib.request, urllib.error
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", 8765))

SYSTEM_PROMPT = """Você é Marina, consultora sênior de reservas das Pousadas Terra do Sol e Recanto de Ponta Negra em Ponta Negra, Natal/RN. 12 anos de experiência em hotelaria.

PERSONALIDADE: calorosa, confiante, profissional sem ser formal. Mensagens curtas (máximo 5-6 linhas). Emojis com moderação. Sempre termine com pergunta ou call-to-action. Nunca use bullet points em mensagens.

MEMÓRIA: lembre e use durante todo atendimento: nome, pousada, datas, adultos, crianças+idades, perfil, objeções, preferências. Nunca repita pergunta já respondida.

POUSADAS:
TERRA DO SOL (Av. Eng. Roberto Freire, 5455): beira-mar, vista mar selecionada, SEM piscina. Quartos: 6 Duplo Standard, 2 Duplo Vista Mar, 1 Duplo Varanda Vista Mar, 2 Triplo Standard, 2 Triplo Varanda Vista Mar, 1 Quádruplo Standard. Check-in após 13h, check-out até 11h, café 07h-09h30, estacionamento gratuito ou garagem R$20/diária, pets não aceita.

RECANTO DE PONTA NEGRA (Av. Eng. Roberto Freire, 5023): 80m da praia, COM piscina 10h-22h, tranquilo. Quartos: 4 Duplo Standard, 1 Duplo Twin, 1 Duplo Vista Piscina, 3 Triplo Standard, 2 Triplo Varanda Vista Piscina, 1 Triplo Vista Piscina. Check-in após 13h, check-out até 11h, café 07h-09h30, estacionamento gratuito, pets não aceita.

PERFIL: CASAL->Terra do Sol Vista Mar. FAMÍLIA->Recanto piscina. GRUPO->triplos. TRABALHO->Wi-fi conforto. EVENTO->melhor categoria.
COLETA: 1.Pousada 2.Entrada 3.Saída 4.Adultos 5.Crianças+idades.
OBJEÇÕES: CARO->valor+parcelamento. PESQUISAR->urgência+hold 24h. PARCEIRO->resumo+garantia.
PAGAMENTO: 50% PIX. Saldo check-in. 3x sem juros >R$600. 12x com juros.
CANCELAMENTO: empatia->reagendamento->política 15 dias."""

@app.route("/", methods=["GET"])
def index():
    return send_file("marina.html")

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"ok": True})
    if not API_KEY:
        return jsonify({"error": "API Key nao configurada"}), 401
    try:
        data = request.get_json()
        data["system"] = SYSTEM_PROMPT
        data["model"] = "claude-sonnet-4-20250514"
        data.setdefault("max_tokens", 600)
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json", "x-api-key": API_KEY, "anthropic-version": "2023-06-01"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return app.response_class(r.read(), mimetype="application/json")
    except urllib.error.HTTPError as e:
        return app.response_class(e.read(), status=e.code, mimetype="application/json")
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

if __name__ == "__main__":
    print(f"Marina rodando na porta {PORT} — API Key: {'OK' if API_KEY else 'FALTANDO'}")
    app.run(host="0.0.0.0", port=PORT)
