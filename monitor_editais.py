import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Arquivo JSON que guarda o histórico de editais já notificados
HISTORICO_FILE = 'editais_vistos.json'
BASE_URL = 'https://portal.imd.ufrn.br'
URL_PORTAL = f'{BASE_URL}/portal/editais'

def carregar_historico():
    """Carrega a lista de editais já vistos do arquivo JSON."""
    if os.path.exists(HISTORICO_FILE):
        try:
            with open(HISTORICO_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
            return set()
    return set()

def salvar_historico(historico):
    """Salva a lista atualizada de editais vistos no JSON."""
    try:
        with open(HISTORICO_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(historico), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")

def enviar_telegram(mensagem):
    """Envia uma mensagem individual para o bot do Telegram."""
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("Erro: TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID não configurados.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': mensagem,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': True
    }

    try:
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code != 200:
            print(f"Erro ao enviar para o Telegram: {res.text}")
    except Exception as e:
        print(f"Falha na conexão com o Telegram: {e}")

def monitorar():
    editais_vistos = carregar_historico()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(URL_PORTAL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Erro ao acessar o portal do IMD: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Busca as linhas/blocos de editais na página
    blocos_editais = soup.find_all(['tr', 'div', 'li'], class_=lambda c: c and any(x in c.lower() for x in ['edital', 'linha', 'item', 'card']))

    if not blocos_editais:
        blocos_editais = soup.find_all('tr')

    novos_editais_count = 0

    for bloco in blocos_editais:
        texto_limpo = " ".join(bloco.get_text().split())

        # Ignora blocos vazios ou cabeçalhos
        if len(texto_limpo) < 20 or ("Inscrições" not in texto_limpo and "Processo" not in texto_limpo):
            continue

        # Tenta encontrar um link específico (`<a>`) dentro do bloco do edital
        link_tag = bloco.find('a', href=True)
        if link_tag and link_tag['href']:
            link_edital = urljoin(BASE_URL, link_tag['href'])
        else:
            link_edital = URL_PORTAL  # Fallback para o portal geral se não achar link interno

        id_edital = texto_limpo

        # Se for um edital novo
        if id_edital not in editais_vistos:
            novos_editais_count += 1
            editais_vistos.add(id_edital)

            # Formata a mensagem com o link específico apontando direto para o edital
            mensagem = (
                f"🚨 *NOVO EDITAL OU ATUALIZAÇÃO DETECTADA!*\n\n"
                f"{texto_limpo}\n\n"
                f"🔗 [Acessar Página do Edital]({link_edital})"
            )
            
            enviar_telegram(mensagem)
            print(f"Novo edital enviado com link direto: {texto_limpo[:50]}...")

    if novos_editais_count > 0:
        salvar_historico(editais_vistos)
        print(f"Sucesso: {novos_editais_count} novo(s) edital(is) notificado(s).")
    else:
        print("Nenhum edital novo detectado nesta verificação.")

if __name__ == '__main__':
    monitorar()