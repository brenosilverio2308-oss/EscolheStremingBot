"""Bot do Telegram do AcolheTech, com comparador de streaming."""

import os

import streaming
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)


ORCAMENTO, GENEROS, PESSOAS, PERFIL, COMPARA_A, COMPARA_B = range(6)


def menu_teclado():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Descobrir qual combina comigo", callback_data="menu:recomendar")],
        [InlineKeyboardButton("💲 Ver preços e planos", callback_data="menu:precos")],
        [InlineKeyboardButton("⚖️ Comparar duas plataformas", callback_data="menu:comparar")],
    ])


def teclado_opcoes(opcoes, prefixo):
    linhas = [[InlineKeyboardButton(rotulo, callback_data=f"{prefixo}:{codigo}")]
              for codigo, rotulo in opcoes]
    return InlineKeyboardMarkup(linhas)


def teclado_generos(selecionados):
    linhas = []
    for codigo, rotulo in streaming.GENEROS.items():
        marca = "✅ " if codigo in selecionados else ""
        linhas.append([InlineKeyboardButton(
            marca + rotulo, callback_data=f"genero:{codigo}")])
    linhas.append([InlineKeyboardButton("Continuar", callback_data="genero:pronto")])
    return InlineKeyboardMarkup(linhas)


def teclado_plataformas(prefixo, excluir=None):
    plataformas = streaming.carregar()["plataformas"]
    botoes = [[InlineKeyboardButton(p["nome"], callback_data=f"{prefixo}:{p['id']}")]
              for p in plataformas if p["id"] != excluir]
    return InlineKeyboardMarkup(botoes)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Olá! Eu sou o AcolheTech. Posso ajudar você a comparar serviços de streaming.\n\n"
        "Escolha uma opção:", reply_markup=menu_teclado())
    return ConversationHandler.END


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Use /start para abrir o menu. Você pode descobrir qual plataforma combina "
        "com suas preferências, consultar planos ou comparar duas plataformas.\n"
        "Use /cancelar para interromper uma pergunta.")
    return ConversationHandler.END


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    acao = query.data.split(":", 1)[1]

    if acao == "precos":
        await query.edit_message_text(streaming.texto_precos(streaming.carregar()),
                                      reply_markup=menu_teclado())
        return ConversationHandler.END

    if acao == "recomendar":
        context.user_data["respostas_streaming"] = {"generos": []}
        opcoes = [(str(n), f"Até R$ {n},00") for n in (20, 30, 40, 60, 100)]
        opcoes.append(("sem_limite", "Sem limite definido"))
        await query.edit_message_text(
            "Qual é o seu orçamento mensal máximo?",
            reply_markup=teclado_opcoes(opcoes, "orcamento"))
        return ORCAMENTO

    if acao == "comparar":
        await query.edit_message_text(
            "Escolha a primeira plataforma:",
            reply_markup=teclado_plataformas("plataforma_a"))
        return COMPARA_A

    await query.edit_message_text("Escolha uma opção:", reply_markup=menu_teclado())
    return ConversationHandler.END


async def escolher_orcamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    codigo = query.data.split(":", 1)[1]
    contexto = context.user_data["respostas_streaming"]
    contexto["orcamento"] = None if codigo == "sem_limite" else float(codigo)
    await query.edit_message_text(
        "Que tipos de conteúdo você costuma assistir? Selecione todos os que quiser:",
        reply_markup=teclado_generos(contexto["generos"]))
    return GENEROS


async def escolher_genero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    codigo = query.data.split(":", 1)[1]
    contexto = context.user_data["respostas_streaming"]
    if codigo != "pronto":
        selecionados = contexto["generos"]
        if codigo in selecionados:
            selecionados.remove(codigo)
        else:
            selecionados.append(codigo)
        await query.edit_message_reply_markup(reply_markup=teclado_generos(selecionados))
        return GENEROS

    opcoes = [(str(n), "4 ou mais pessoas" if n == 4 else
               f"{n} pessoa" + ("s" if n > 1 else "")) for n in (1, 2, 3, 4)]
    opcoes.append(("pular", "Não informar"))
    await query.edit_message_text(
        "Quantas pessoas usarão a assinatura?",
        reply_markup=teclado_opcoes(opcoes, "pessoas"))
    return PESSOAS


async def escolher_pessoas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    codigo = query.data.split(":", 1)[1]
    context.user_data["respostas_streaming"]["pessoas"] = (
        None if codigo == "pular" else int(codigo))
    opcoes = [("variedade", "📚 Grande variedade"),
              ("especializada", "🎯 Especializada"),
              ("pular", "Não tenho preferência")]
    await query.edit_message_text(
        "Você prefere uma plataforma de grande variedade ou especializada?",
        reply_markup=teclado_opcoes(opcoes, "perfil"))
    return PERFIL


async def escolher_perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    codigo = query.data.split(":", 1)[1]
    respostas = context.user_data["respostas_streaming"]
    respostas["perfil"] = None if codigo == "pular" else codigo
    texto = streaming.texto_recomendacao(streaming.carregar(), respostas)
    await query.edit_message_text(texto, reply_markup=menu_teclado())
    return ConversationHandler.END


async def escolher_primeira_plataforma(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    codigo = query.data.split(":", 1)[1]
    context.user_data["plataforma_a"] = codigo
    nome = streaming.por_id(streaming.carregar())[codigo]["nome"]
    await query.edit_message_text(
        f"Agora escolha a plataforma para comparar com {nome}:",
        reply_markup=teclado_plataformas("plataforma_b", excluir=codigo))
    return COMPARA_B


async def escolher_segunda_plataforma(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    codigo = query.data.split(":", 1)[1]
    primeira = context.user_data.pop("plataforma_a")
    texto = streaming.texto_comparacao(
        streaming.carregar(), [primeira, codigo], {})
    await query.edit_message_text(texto, reply_markup=menu_teclado())
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Tudo bem, parei a comparação. Use /start para voltar ao menu.")
    return ConversationHandler.END


def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError(
            "Defina a variável de ambiente TELEGRAM_TOKEN com o token do BotFather.")

    conversa = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("ajuda", ajuda),
            CallbackQueryHandler(menu, pattern=r"^menu:"),
        ],
        states={
            ORCAMENTO: [CallbackQueryHandler(escolher_orcamento, pattern=r"^orcamento:")],
            GENEROS: [CallbackQueryHandler(escolher_genero, pattern=r"^genero:")],
            PESSOAS: [CallbackQueryHandler(escolher_pessoas, pattern=r"^pessoas:")],
            PERFIL: [CallbackQueryHandler(escolher_perfil, pattern=r"^perfil:")],
            COMPARA_A: [CallbackQueryHandler(escolher_primeira_plataforma,
                                             pattern=r"^plataforma_a:")],
            COMPARA_B: [CallbackQueryHandler(escolher_segunda_plataforma,
                                             pattern=r"^plataforma_b:")],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        allow_reentry=True,
    )

    app = Application.builder().token(token).build()
    app.add_handler(conversa)
    print("AcolheTech iniciado. Use Ctrl+C para encerrar.")
    app.run_polling()


if __name__ == "__main__":
    main()

