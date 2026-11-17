# streaming.py
# AcolheTech - Comparador de streamings
#
# Este arquivo NÃO usa internet nem APIs: lê os dados do streaming.json
# (que você atualiza manualmente, conferindo os sites oficiais) e faz:
#   1) formatação de preços e planos
#   2) recomendação personalizada
#   3) comparação entre plataformas

import re
import json
import unicodedata
from datetime import date
from pathlib import Path

PASTA = Path(__file__).parent
ARQUIVO = PASTA / "streaming.json"

# Depois de quantos dias avisamos que os dados podem estar velhos
IDADE_MAXIMA_DIAS = 30

# Opções dos botões: "código": "texto"
GENEROS = {
    "filmes": "🎬 Filmes",
    "series": "📺 Séries",
    "animes": "🎌 Animes",
    "documentarios": "🔎 Documentários",
    "esportes": "⚽ Esportes",
    "infantil": "🧸 Infantil",
}
NOMES_GENERO = {
    "filmes": "filmes", "series": "séries", "animes": "animes",
    "documentarios": "documentários", "esportes": "esportes",
    "infantil": "conteúdo infantil",
}
ORCAMENTOS = {"20": 20.0, "30": 30.0, "40": 40.0, "60": 60.0, "100": 100.0}
PERFIS = {
    "variedade": "📚 Grande variedade",
    "especializada": "🎯 Especializada",
}

# Palavras que a pessoa pode digitar para citar uma plataforma
APELIDOS = {
    "netflix": "netflix",
    "prime": "prime", "amazon": "prime",
    "disney": "disney",
    "hbo": "hbomax", "max": "hbomax",
    "globoplay": "globoplay", "globo": "globoplay",
    "apple": "appletv",
    "paramount": "paramount",
}


# ---------------------------------------------------------------
# DADOS
# ---------------------------------------------------------------
def carregar():
    """Lê o streaming.json e devolve o conteúdo."""
    with open(ARQUIVO, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def por_id(dados):
    """Dicionário {id: plataforma}, para achar uma plataforma pelo id."""
    return {p["id"]: p for p in dados["plataformas"]}


def reais(valor):
    """25.9 -> 'R$ 25,90'"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def sem_acento(texto):
    texto = unicodedata.normalize("NFD", texto)
    return texto.encode("ascii", "ignore").decode().lower()


def achar_plataformas(texto):
    """Procura nomes de plataformas num texto digitado.
    'Netflix ou Disney+, qual vale mais?' -> ['netflix', 'disney']"""
    palavras = re.split(r"[^a-z]+", sem_acento(texto))
    achadas = []
    for palavra in palavras:
        id_plat = APELIDOS.get(palavra)
        if id_plat and id_plat not in achadas:
            achadas.append(id_plat)
    return achadas


# ---------------------------------------------------------------
# ATUALIDADE DOS DADOS (não apresentar dado antigo como atual)
# ---------------------------------------------------------------
def idade_dias(plat):
    try:
        return (date.today() - date.fromisoformat(plat["verificado_em"])).days
    except (KeyError, ValueError):
        return None


def data_br(plat):
    try:
        return date.fromisoformat(plat["verificado_em"]).strftime("%d/%m/%Y")
    except (KeyError, ValueError):
        return "data desconhecida"


def aviso_idade(plat):
    """Texto de alerta se os dados estiverem velhos; senão, None."""
    idade = idade_dias(plat)
    if idade is None:
        return f"⚠️ {plat['nome']}: data de verificação desconhecida."
    if idade > IDADE_MAXIMA_DIAS:
        return (f"⚠️ {plat['nome']}: dados verificados há {idade} dias "
                f"({data_br(plat)}); podem estar desatualizados.")
    return None


def avisos_idade(plataformas):
    return [a for a in (aviso_idade(p) for p in plataformas) if a]


RODAPE_CONFIRMAR = ("ℹ️ Valores mensais, sem promoções nem pacotes de operadoras. "
                    "Preços mudam com frequência: confirme no site oficial "
                    "antes de assinar.")


# ---------------------------------------------------------------
# TEXTOS: PREÇOS E DETALHES
# ---------------------------------------------------------------
def linha_plano(plano):
    preco = reais(plano["preco"]) + "/mês" if plano.get("preco") is not None \
        else "preço a confirmar"
    telas = plano.get("telas")
    if telas is None:
        telas_txt = "telas: a confirmar"
    else:
        telas_txt = f"{telas} tela" + ("s" if telas > 1 else "")
    qualidade = plano.get("qualidade") or "qualidade: a confirmar"
    anuncios = {True: "com anúncios", False: "sem anúncios",
                None: "anúncios: a confirmar"}[plano.get("anuncios")]
    return f"• {plano['nome']}: {preco} - {telas_txt}, {qualidade}, {anuncios}"


def texto_precos(dados):
    linhas = ["💲 Preços e planos no Brasil\n"]
    for plat in dados["plataformas"]:
        linhas.append(f"🎬 {plat['nome']} (verificado em {data_br(plat)})")
        linhas += [linha_plano(p) for p in plat["planos"]]
        linhas.append("")
    avisos = avisos_idade(dados["plataformas"])
    if avisos:
        linhas += avisos + [""]
    linhas.append(RODAPE_CONFIRMAR)
    return "\n".join(linhas)


def texto_detalhe(plat):
    linhas = [
        f"🎬 {plat['nome']}",
        f"📚 Tipo: {'grande variedade' if plat['tipo'] == 'variedade' else 'mais especializada'}",
        f"🎞️ Conteúdo: {plat['conteudo']}",
        f"⚽ Esportes: {plat['esportes']}",
        f"🏆 Destaques: {plat['exclusivos']}",
        "",
        "💲 Planos:",
    ]
    for plano in plat["planos"]:
        linhas.append(linha_plano(plano))
        if plano.get("preco_anual"):
            linhas.append(f"    (plano anual: {reais(plano['preco_anual'])})")
    linhas.append("")
    linhas.append("✅ Vantagens:")
    linhas += [f"• {v}" for v in plat["vantagens"]]
    linhas.append("")
    linhas.append("⚠️ Desvantagens:")
    linhas += [f"• {d}" for d in plat["desvantagens"]]
    linhas.append("")
    linhas.append(f"📅 Dados verificados em {data_br(plat)}.")
    linhas.append(f"🔗 Fonte: {plat['fonte']}")
    aviso = aviso_idade(plat)
    if aviso:
        linhas.append(aviso)
    linhas.append(RODAPE_CONFIRMAR)
    return "\n".join(linhas)


# ---------------------------------------------------------------
# RECOMENDAÇÃO PERSONALIZADA
# ---------------------------------------------------------------
def tem_preferencias(resp):
    return bool(resp.get("orcamento") or resp.get("generos")
                or resp.get("pessoas") or resp.get("perfil"))


def menor_preco(plat):
    precos = [p["preco"] for p in plat["planos"] if p.get("preco") is not None]
    return min(precos) if precos else None


def escolher_plano(plat, resp):
    """Escolhe o plano mais barato que cabe no orçamento e nas telas.
    Devolve (plano, situacao) onde situacao é 'ok', 'incerta' ou 'menos'.
    Devolve (None, None) se nenhum plano cabe no orçamento."""
    orcamento = resp.get("orcamento")
    pessoas = resp.get("pessoas")
    planos = sorted((p for p in plat["planos"] if p.get("preco") is not None),
                    key=lambda p: p["preco"])
    cabem = [p for p in planos if orcamento is None or p["preco"] <= orcamento]
    if not cabem:
        return None, None

    primeiro_incerto = None
    for plano in cabem:
        if pessoas is None:
            return plano, "ok"
        telas = plano.get("telas")
        if telas is None:
            if primeiro_incerto is None:
                primeiro_incerto = plano
        elif telas >= pessoas:
            return plano, "ok"
    if primeiro_incerto:
        return primeiro_incerto, "incerta"
    return cabem[0], "menos"


def pontuar(plat, resp, plano, situacao):
    """Devolve (pontos, motivos, ressalvas)."""
    pontos, motivos, ressalvas = 0.0, [], []
    generos = resp.get("generos") or []
    perfil = plat["perfil"]

    # 1) Combina com os gostos? (0 a 10 pontos)
    if generos:
        soma = sum(perfil.get(g, 0) for g in generos)
        pontos += 10 * soma / (3 * len(generos))
        for g in generos:
            nivel = perfil.get(g, 0)
            if g == "esportes" and nivel >= 1:
                motivos.append(f"esportes: {plat['esportes'].rstrip('.')}")
            elif nivel >= 3:
                motivos.append(f"muito forte em {NOMES_GENERO[g]}")
            elif nivel == 2:
                motivos.append(f"bom catálogo de {NOMES_GENERO[g]}")
            elif nivel == 0:
                ressalvas.append(f"quase não tem {NOMES_GENERO[g]}")
    else:
        pontos += 5   # sem preferência de gênero: pontuação neutra

    # 2) Custo-benefício dentro do orçamento (0 a 2 pontos)
    orcamento = resp.get("orcamento")
    if orcamento:
        pontos += 2 * (1 - plano["preco"] / orcamento)
        motivos.insert(0, f"cabe no orçamento: {reais(plano['preco'])}/mês no plano {plano['nome']}")
    else:
        motivos.insert(0, f"plano {plano['nome']} por {reais(plano['preco'])}/mês")

    # 3) Variedade x especializada
    if resp.get("perfil") and plat["tipo"] == resp["perfil"]:
        pontos += 1.5
        motivos.append("é uma plataforma de grande variedade" if plat["tipo"] == "variedade"
                       else "é mais especializada, como você preferiu")

    # 4) Telas simultâneas
    pessoas = resp.get("pessoas")
    if pessoas:
        if situacao == "ok":
            pontos += 0.5
            if plano.get("telas"):
                motivos.append(f"permite {plano['telas']} telas ao mesmo tempo")
        elif situacao == "menos":
            pontos -= 1.5
            ressalvas.append(f"este plano permite só {plano['telas']} tela(s) "
                             f"para {pessoas} pessoa(s)")
        else:
            ressalvas.append("número de telas a confirmar")

    return pontos, motivos, ressalvas


def recomendar(dados, resp, ids=None):
    """Devolve (ranking, fora). ranking = lista ordenada de dicionários;
    fora = lista de (plataforma, motivo) das que não entraram."""
    ranking, fora = [], []
    for plat in dados["plataformas"]:
        if ids and plat["id"] not in ids:
            continue
        plano, situacao = escolher_plano(plat, resp)
        if plano is None:
            fora.append((plat, f"acima do orçamento (a partir de {reais(menor_preco(plat))})"))
            continue
        generos = resp.get("generos") or []
        if generos and sum(plat["perfil"].get(g, 0) for g in generos) == 0:
            nomes = ", ".join(NOMES_GENERO[g] for g in generos)
            fora.append((plat, f"quase não tem {nomes}"))
            continue
        pontos, motivos, ressalvas = pontuar(plat, resp, plano, situacao)
        ranking.append({"plat": plat, "plano": plano, "pontos": pontos,
                        "motivos": motivos, "ressalvas": ressalvas})
    ranking.sort(key=lambda r: (-r["pontos"], r["plano"]["preco"]))
    return ranking, fora


def resumo_respostas(resp):
    partes = []
    if resp.get("orcamento"):
        partes.append(f"até {reais(resp['orcamento'])}")
    if resp.get("generos"):
        partes.append(", ".join(NOMES_GENERO[g] for g in GENEROS if g in resp["generos"]))
    if resp.get("pessoas"):
        n = resp["pessoas"]
        partes.append("4 ou mais pessoas" if n >= 4 else f"{n} pessoa" + ("s" if n > 1 else ""))
    if resp.get("perfil"):
        partes.append("grande variedade" if resp["perfil"] == "variedade" else "especializada")
    return " • ".join(partes) if partes else "sem filtros"


def texto_recomendacao(dados, resp, maximo=3):
    ranking, fora = recomendar(dados, resp)
    linhas = ["🎯 Minhas recomendações", f"Suas respostas: {resumo_respostas(resp)}", ""]

    if not ranking:
        linhas.append("😕 Nenhuma plataforma atende a essas condições.")
        precos = [(menor_preco(p), p["nome"]) for p in dados["plataformas"] if menor_preco(p)]
        if precos:
            barato = min(precos)
            linhas.append(f"A mais barata é {barato[1]}, a partir de {reais(barato[0])}/mês.")
    numeros = ["1️⃣", "2️⃣", "3️⃣"]
    for i, item in enumerate(ranking[:maximo]):
        linhas.append(f"{numeros[i]} {item['plat']['nome']} - {item['plano']['nome']}: "
                      f"{reais(item['plano']['preco'])}/mês")
        linhas.append("   Por quê: " + "; ".join(item["motivos"]) + ".")
        if item["ressalvas"]:
            linhas.append("   ⚠️ Atenção: " + "; ".join(item["ressalvas"]) + ".")
        linhas.append("")

    if fora:
        linhas.append("Não entraram na lista:")
        linhas += [f"• {p['nome']}: {motivo}" for p, motivo in fora]
        linhas.append("")

    mostradas = [i["plat"] for i in ranking[:maximo]]
    avisos = avisos_idade(mostradas)
    if avisos:
        linhas += avisos + [""]
    linhas.append("ℹ️ A força de cada plataforma em cada gênero é uma avaliação "
                  "do projeto, não um dado oficial.")
    linhas.append(RODAPE_CONFIRMAR)
    return "\n".join(linhas)


# ---------------------------------------------------------------
# COMPARAÇÃO DIRETA
# ---------------------------------------------------------------
def nota_conteudo(plat, resp):
    """Nota 0 a 10 do conteúdo, conforme os gêneros pedidos."""
    generos = resp.get("generos") or list(NOMES_GENERO)
    soma = sum(plat["perfil"].get(g, 0) for g in generos)
    return 10 * soma / (3 * len(generos))


def texto_comparacao(dados, ids, resp):
    plataformas = [por_id(dados)[i] for i in ids]
    linhas = ["⚖️ Comparação: " + " x ".join(p["nome"] for p in plataformas), ""]

    for plat in plataformas:
        linhas.append(f"🎬 {plat['nome']}")
        linhas += [linha_plano(p) for p in plat["planos"]]
        linhas.append(f"🎞️ Conteúdo: {plat['conteudo']}")
        linhas.append(f"⚽ Esportes: {plat['esportes']}")
        linhas.append(f"🏆 Destaques: {plat['exclusivos']}")
        linhas.append(f"✅ {plat['vantagens'][0]}")
        linhas.append(f"⚠️ {plat['desvantagens'][0]}")
        linhas.append("")

    # Custo-benefício: nota do conteúdo dividida pelo preço de entrada
    indices = []
    for plat in plataformas:
        preco = menor_preco(plat)
        if preco:
            indices.append((nota_conteudo(plat, resp) / preco, plat["nome"], preco))
    if indices:
        melhor = max(indices)
        pedido = "para o que você pediu" if resp.get("generos") else "no geral"
        linhas.append(f"💡 Custo-benefício {pedido}: {melhor[1]} "
                      f"(a partir de {reais(melhor[2])}/mês).")

    # Indicação final, usando as preferências guardadas
    if tem_preferencias(resp):
        ranking, fora = recomendar(dados, resp, ids)
        if ranking:
            linhas.append(f"🎯 Combina mais com você: {ranking[0]['plat']['nome']} "
                          f"({'; '.join(ranking[0]['motivos'][:2])}).")
        else:
            linhas.append("🎯 Nenhuma delas atende bem às suas respostas "
                          "(veja orçamento e gêneros).")
    else:
        linhas.append("🎯 Para eu indicar qual combina mais com você, use "
                      "\"Descobrir qual combina comigo\".")

    linhas.append("")
    avisos = avisos_idade(plataformas)
    if avisos:
        linhas += avisos + [""]
    linhas.append(RODAPE_CONFIRMAR)
    return "\n".join(linhas)

