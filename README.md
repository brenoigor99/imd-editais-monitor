# 📢 Monitor de Editais - IMD / UFRN

Bot em Python desenvolvido para monitorar automaticamente o portal de editais do Instituto Metrópole Digital (IMD/UFRN) e enviar notificações em tempo real via Telegram sempre que um novo edital for publicado.

## 🚀 Funcionalidades

- **Web Scraping:** Raspa periodicamente o portal de editais utilizando `requests` e `BeautifulSoup`.
- **Persistência de Estado:** Mantém um histórico local (`editais_vistos.json`) para evitar alertas duplicados.
- **Notificação Via Telegram:** Dispara mensagens instantâneas utilizando a API oficial de Bots do Telegram.
- **Execução Automatizada:** Agendado via **GitHub Actions** para rodar periodicamente sem necessidade de servidor dedicado.

## 🛠️ Tecnologias Utilizadas

- **Python 3**
- **BeautifulSoup4** & **Requests** (Scraping HTTP)
- **Telegram Bot API** (Notificações)
- **GitHub Actions** (CI/CD & Cron Job)

## 🔧 Configuração e Execução Local

### 1. Clonar o repositório
```bash
git clone https://github.com/brenoigor99/imd-editais-monitor.git
cd imd-editais-monitor