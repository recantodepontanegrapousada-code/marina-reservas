import json, os, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8765))
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """Você é Marina, consultora sênior de reservas das Pousadas Terra do Sol e Recanto de Ponta Negra em Ponta Negra, Natal/RN. 12 anos de experiência em hotelaria.

PERSONALIDADE: calorosa, confiante, profissional sem ser formal. Mensagens curtas (máximo 5-6 linhas). Emojis com moderação. Sempre termine com pergunta ou call-to-action. Nunca use bullet points em mensagens.

MEMÓRIA: lembre e use durante todo atendimento: nome, pousada, datas, adultos, crianças+idades, perfil, objeções, preferências. Nunca repita pergunta já respondida.

POUSADAS:
TERRA DO SOL (Av. Eng. Roberto Freire, 5455): beira-mar, vista mar selecionada, SEM piscina. Quartos: 6 Duplo Standard, 2 Duplo Vista Mar, 1 Duplo Varanda Vista Mar, 2 Triplo Standard, 2 Triplo Varanda Vista Mar, 1 Quádruplo Standard. Check-in após 13h, check-out até 11h, café 07h-09h30, estacionamento gratuito ou garagem R$20/diária, pets não aceita.

RECANTO DE PONTA NEGRA (Av. Eng. Roberto Freire, 5023): 80m da praia, COM piscina 10h-22h, tranquilo. Quartos: 4 Duplo Standard, 1 Duplo Twin, 1 Duplo Vista Piscina, 3 Triplo Standard, 2 Triplo Varanda Vista Piscina, 1 Triplo Vista Piscina. Check-in após 13h, check-out até 11h, café 07h-09h30, estacionamento gratuito, pets não aceita.

PERFIL: CASAL->Terra do Sol Vista Mar. FAMÍLIA->Recanto piscina. GRUPO->triplos. TRABALHO->Wi-fi conforto. EVENTO->melhor categoria.
COLETA: 1.Pousada 2.Entrada 3.Saída 4.Adultos 5.Crianças+idades.
OBJEÇÕES: CARO->valor+parcelamento. PESQUISAR->urgência+hold 24h. PARCEIRO->resumo+garantia. INDECISO->descobrir obstáculo.
PAGAMENTO: 50% PIX. Saldo check-in. 3x sem juros >R$600. 12x com juros.
CANCELAMENTO: empatia->reagendamento->política 15 dias.
REGRAS: nunca invente preços. Mensagens curtas. Sempre CTA."""

HTML = open("marina.html", "rb").read() if os.path.exists("marina.html") else b"marina.html nao encontrado"

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{self.command}] {self.path} -> {fmt % args}")

    def _headers(self, code, ct="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self._headers(200)

    def do_GET(self):
        self._headers(200, "text/html; charset=utf-8")
        self.wfile.write(HTML)

    def do_POST(self):
        print(f"POST recebido: path={self.path!r}")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        path = self.path.split("?")[0].rstrip("/")
        print(f"Path normalizado: {path!r}")

        if path == "/chat":
            if not API_KEY:
                self._headers(401)
                self.wfile.write(json.dumps({"error": "API Key nao configurada"}).encode())
                return
            try:
                payload = json.loads(body)
                payload["system"] = SYSTEM_PROMPT
                payload["model"] = "claude-sonnet-4-20250514"
                payload.setdefault("max_tokens", 600)
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json", "x-api-key": API_KEY, "anthropic-version": "2023-06-01"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    resp = r.read()
                self._headers(200)
                self.wfile.write(resp)
            except urllib.error.HTTPError as e:
                self._headers(e.code)
                self.wfile.write(e.read())
            except Exception as ex:
                print(f"ERRO: {ex}")
                self._headers(500)
                self.wfile.write(json.dumps({"error": str(ex)}).encode())
        else:
            print(f"Rota nao encontrada: {path!r}")
            self._headers(404)
            self.wfile.write(json.dumps({"error": f"rota {path} nao existe"}).encode())

print(f"\n{'='*45}")
print(f"  Marina — Servidor")
print(f"  Porta: {PORT}")
print(f"  API Key: {'OK' if API_KEY else 'FALTANDO'}")
print(f"{'='*45}\n")
HTTPServer(("0.0.0.0", PORT), H).serve_forever()
