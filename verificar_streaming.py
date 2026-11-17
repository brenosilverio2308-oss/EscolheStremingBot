# verificar_streaming.py
# Ferramenta de manutenção: confere o streaming.json e mostra a idade dos dados.
# Uso:  python verificar_streaming.py

import streaming

dados = streaming.carregar()
obrigatorios = ["id", "nome", "tipo", "verificado_em", "fonte", "planos",
                "conteudo", "esportes", "exclusivos", "perfil",
                "vantagens", "desvantagens"]
problemas = 0

for plat in dados["plataformas"]:
    faltando = [c for c in obrigatorios if c not in plat]
    if faltando:
        print(f"❌ {plat.get('nome', '?')}: faltam os campos {faltando}")
        problemas += 1
        continue
    idade = streaming.idade_dias(plat)
    situacao = "OK" if idade is not None and idade <= streaming.IDADE_MAXIMA_DIAS \
        else "ATUALIZAR"
    print(f"{'✅' if situacao == 'OK' else '⚠️'} {plat['nome']}: verificado em "
          f"{streaming.data_br(plat)} ({idade} dias) - {situacao}")
    for plano in plat["planos"]:
        for campo in ("preco", "telas", "qualidade", "anuncios"):
            if plano.get(campo) is None:
                print(f"     (a confirmar) {plano['nome']}: {campo}")

print("\nProblemas de estrutura:", problemas)

