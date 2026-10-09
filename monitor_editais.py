import os
import json
import logging
import requests
from bs4 import BeautifulSoup

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# URLs e Ficheiros
URL_EDITAIS = "https://www.metropoledigital.ufrn.br/portal/editais"
HISTORICO_FILE = "editais_vistos.json"

# Credenciais lidas de Variáveis de Ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def carregar_historico() -> set:
    """Carregamento do histórico de editais vistos."""
    if os.path.exists(HISTORICO_FILE):
        try:
            with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            logging.error(f"Erro ao carregar histórico: {e}")
            return set()
    return set()


def salvar_historico(historico: set):
    """Guarda a lista atualizada de editais no ficheiro JSON."""
    try:
        with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
            json.dump(list(historico), f, ensure_ascii=False, indent=2)
        logging.info("Histórico atualizado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao salvar histórico: {e}")


def enviar_notificacao_telegram(mensagem: str):
    """Envia a mensagem de alerta para o Telegram via Bot API."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID não definidos nas variáveis de ambiente.")
        return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info("Notificação enviada com sucesso para o Telegram!")
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem no Telegram: {e}")


def raspar_editais() -> list:
    """Acessa a página do IMD e extrai o texto das chamadas/editais."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(URL_EDITAIS, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Erro ao aceder {URL_EDITAIS}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    editais_encontrados = []

    for item in soup.find_all(class_=lambda x: x and any(c in x.lower() for c in ['edital', 'card', 'item', 'box'])):
        texto = " ".join(item.get_text(separator=" ", strip=True).split())
        if texto and len(texto) > 15:
            editais_encontrados.append(texto)

    if not editais_encontrados:
        for tag in soup.find_all(['div', 'a']):
            txt = " ".join(tag.get_text(strip=True).split())
            if any(termo in txt for termo in ["Processo Seletivo", "PROCESSO SELETI", "Bolsista", "SELEÇÃO SIMPLIFICADA"]):
                if len(txt) > 20 and txt not in editais_encontrados:
                    editais_encontrados.append(txt)

    return editais_encontrados


def executar_verificacao():
    """Fluxo principal do monitoramento."""
    logging.info("Iniciando verificação do portal de editais...")
    editais_atuais = raspar_editais()

    if not editais_atuais:
        logging.warning("Nenhum edital localizado.")
        return

    historico = carregar_historico()
    novos_editais = []

    for edital in editais_atuais:
        if edital not in historico:
            historico.add(edital)
            novos_editais.append(edital)

    if not os.path.exists(HISTORICO_FILE):
        salvar_historico(historico)
        logging.info("Primeira execução: estado atual registado em JSON sem disparar notificações.")
        return

    if novos_editais:
        logging.info(f"{len(novos_editais)} novo(s) edital(is) detectado(s)!")
        salvar_historico(historico)
        for edital in novos_editais[:5]:
            msg = (
                f"🚨 *NOVO EDITAL OU ATUALIZAÇÃO DETECTADA!*\n\n"
                f"{edital}\n\n"
                f"🔗 [Acessar Portal de Editais IMD]({URL_EDITAIS})"
            )
            enviar_notificacao_telegram(msg)
    else:
        logging.info("Nenhuma alteração detectada nos editais.")


if __name__ == "__main__":
    executar_verificacao()