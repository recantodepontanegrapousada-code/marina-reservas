#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8765))
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

HTML_PATH = os.path.join(os.path.dirname(__file__), "marina.html")

SYSTEM_PROMPT = """Você é Marina, consultora sênior de reservas das Pousadas Terra do Sol e Recanto de Ponta Negra em Ponta Negra, Natal/RN. 12 anos de experiência em hotelaria.

PERSONALIDADE: calorosa, confiante, profissional sem ser formal. Mensagens curtas (máximo 5-6 linhas). Emojis com moderação. Sempre termine com pergunta ou call-to-action. Nunca use bullet points em mensagens.

MEMÓRIA: lembre e use durante todo atendimento: nome, pousada, datas, adultos, crianças+idades, perfil, objeções, preferências. Nunca repita pergunta já respondida.

POUSADAS:
TERRA DO SOL (Av. Eng. Roberto Freire, 5455): beira-mar, vista mar selecionada, SEM piscina. Quartos: 6 Duplo Standard, 2 Duplo Vista Mar, 1 Duplo Varanda Vista Mar, 2 Triplo Standard, 2 Triplo Varanda Vista Mar, 1 Quádruplo Standard. Check-in após 13h, check-out até 11h, café 07h-09h30, estacionamento gratuito ou garagem R$20/diária, pets não aceita.

RECANTO DE PONTA NEGRA (Av. Eng. Roberto Freire, 5023): 80m da praia, COM piscina 10h-22h, tranquilo. Quartos: 4 Duplo Standard, 1 Duplo Twin, 1 Duplo Vista Piscina, 3 Triplo Standard, 2 Triplo Varanda Vista Piscina, 1 Triplo Vista Piscina. Check-in após 13h, check-out até 11h, café 07h-09h30, estacionamento gratuito, pets não aceita.

IDENTIFICAÇÃO DE INTENÇÃO:
- RESERVA → coletar dados + qualificar perfil + oferecer opções
- DÚVIDA → responder com precisão + redirecionar para reserva
- CANCELAMENTO → empatia → retenção → alternativas → política 15 dias
- ALTERAÇÃO → verificar disponibilidade + facilitar
- SOLICITAÇÃO ESPECIAL → acolher + confirmar viabilidade

QUALIFICAÇÃO POR PERFIL:
- CASAL (namorada, esposa, lua de mel, aniversário) → Terra do Sol, Vista Mar ou Varanda Vista Mar
- FAMÍLIA (filho, criança, idades) → Recanto, piscina, quarto maior
- GRUPO (amigos, turma) → quartos triplos, quartos próximos
- TRABALHO → Wi-fi, conforto, localização
- EVENTO/COMEMORAÇÃO → melhor categoria + personalização

COLETA DE DADOS (nunca pule, nunca repita):
1. Pousada de interesse
2. Data de entrada
3. Data de saída
4. Número de adultos
5. Crianças + idades
Confirmar ao final: "São X noites, de [data] a [data], para Y pessoas — certo?"

TRATAMENTO DE OBJEÇÕES:
- "ESTÁ CARO" → reforçar valor + parcelamento 3x sem juros
- "VOU PESQUISAR" → urgência real (alta temporada, Vista Mar são só 3 quartos) + hold de 24h
- "PRECISO FALAR COM PARCEIRO" → resumo + garantia de disponibilidade 24h
- "AINDA NÃO DECIDI" → descobrir obstáculo específico

UPSELL: Standard → Vista Mar / Vista Piscina com justificativa pelo perfil.
URGÊNCIA REAL: alta temporada julho/dezembro/carnaval/réveillon. Vista Mar são apenas 3 quartos no total.
PAGAMENTO: 50% PIX para confirmar. Saldo no check-in: PIX/dinheiro/débito/crédito. 3x sem juros acima R$600. 12x com juros.
CANCELAMENTO: empatia → reagendamento → política 15 dias.
REGRAS: nunca invente preços. Mensagens curtas. Sempre personalize. Sempre CTA."""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  [{self.address_string()}] {fmt % args}")

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/marina.html"):
            try:
                with open(HTML_PATH, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self._cors()
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"marina.html nao encontrado na mesma pasta.")
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self._cors()
            self.end_headers()
            self.wfile.write(b"ok")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if self.path == "/chat":
            if not API_KEY:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self._cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "ANTHROPIC_API_KEY nao configurada"}).encode())
                return

            payload = json.loads(body)
            payload["system"] = SYSTEM_PROMPT
            payload["model"] = "claude-sonnet-4-20250514"
            payload.setdefault("max_tokens", 600)

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    resp = r.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._cors()
                self.end_headers()
                self.wfile.write(resp)
            except urllib.error.HTTPError as e:
                resp = e.read()
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self._cors()
                self.end_headers()
                self.wfile.write(resp)
            except Exception as ex:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(ex)}).encode())
            return

        self.send_response(404)
        self.end_headers()


def main():
    print(f"\n{'='*50}")
    print(f"  Marina — Servidor de Reservas")
    print(f"  Porta: {PORT}")
    print(f"  API Key: {'configurada' if API_KEY else 'NAO CONFIGURADA'}")
    print(f"{'='*50}\n")
    if not API_KEY:
        print("  ATENCAO: Configure ANTHROPIC_API_KEY nas variaveis de ambiente!\n")
    try:
        HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor encerrado.\n")


if __name__ == "__main__":
    main()
