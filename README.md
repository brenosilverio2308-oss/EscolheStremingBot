# AcolheTech

Bot de Telegram em Python com um comparador de serviços de streaming, desenvolvido
como projeto acadêmico de Engenharia da Computação.

## Funcionalidades
- 🎬 Streamings: preços, recomendação personalizada e comparação direta (sem APIs)
- Menu do Telegram com botões, `/start`, `/ajuda` e `/cancelar`

As funções de ONGs e restaurantes estão planejadas, mas seus módulos ainda não estão
nesta pasta. O bot atual concentra-se no comparador de streaming.

## Arquivos
| Arquivo | Função |
|---|---|
| `bot.py` | Conversa, menus e botões do Telegram |
| `streaming.py` | Preços, recomendação e comparação de streamings |
| `streaming.json` | Dados das plataformas de streaming (atualização manual) |
| `verificar_streaming.py` | Mostra a idade dos dados e campos a confirmar |
| `requirements.txt` | Bibliotecas necessárias para executar o bot |

## Instalação
```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
Crie o arquivo `.env` na mesma pasta de `bot.py` (nunca publique esse arquivo):
```
TELEGRAM_TOKEN=token_do_botfather
```
O token é criado pelo `@BotFather` no Telegram. Execute: `python bot.py`.

No menu, o usuário pode consultar preços e planos, receber recomendações por
orçamento, gêneros, número de pessoas e perfil de catálogo, ou comparar duas
plataformas. Use `/cancelar` durante uma pergunta para encerrar o fluxo.

## Como os dados do streaming são atualizados
1. Confira os preços nas páginas oficiais de cada plataforma.
2. Edite `streaming.json` (valores, planos) e troque `verificado_em` e `fonte`.
3. Use `null` para o que não foi confirmado: o bot mostra "a confirmar".
4. Rode `python verificar_streaming.py` para validar o arquivo.

O bot avisa quando os dados de uma plataforma têm mais de 30 dias
(`IDADE_MAXIMA_DIAS` em `streaming.py`). Preços não são lidos automaticamente
dos sites: as páginas mudam com frequência e podem proibir esse uso.

## Segurança
- O token fica no `.env`, fora do código e excluído pelo `.gitignore`.
- O bot não pede dados pessoais e nunca recebe dinheiro.
- Não inclua ONGs, telefones ou preços sem conferir a fonte oficial.

