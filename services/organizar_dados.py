import re
import pymupdf
import unicodedata

# ============================================================
# CONFIGURAÇÕES
# ============================================================

def organizar_dados(pdf_bytes, dados_extraidos):

    ARQUIVO_PDF = pdf_bytes

    texto = (
        "=" * 70 + "\n"
        + "SEÇÃO 10 - FUNÇÕES / ATIVIDADES\n"
        + "=" * 70 + "\n\n"
        + dados_extraidos["texto_funcoes"]
        + "\n\n"
        + "=" * 70 + "\n"
        + "SEÇÃO 11 - EPI / EPC\n"
        + "=" * 70 + "\n\n"
        + dados_extraidos["texto_epi"]
    )


    # ============================================================
    # 2. EXTRAIR NOME FANTASIA DIRETAMENTE DO PDF
    # ============================================================

    print("\n========================================")
    print("EXTRAINDO NOME FANTASIA")
    print("========================================\n")

    nome_fantasia = ""

    try:

        documento_pdf = pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        texto_pdf = ""

        for pagina in documento_pdf:
            texto_pdf += pagina.get_text() + "\n"

        documento_pdf.close()

        padrao_nome_fantasia = re.search(
            r"Nome Fantasia:\s*(.+)",
            texto_pdf,
            re.IGNORECASE
        )

        if padrao_nome_fantasia:

            nome_fantasia = padrao_nome_fantasia.group(1).strip()

            # Remove espaços duplicados
            nome_fantasia = re.sub(
                r"\s+",
                " ",
                nome_fantasia
            )

        else:

            print("AVISO: Nome Fantasia não encontrado no PDF.")

    except Exception as erro:

        print("ERRO ao ler o PDF:")
        print(erro)


    print("Nome Fantasia encontrado:")
    print(nome_fantasia)

    print("\nNome Fantasia em maiúsculo:")
    print(nome_fantasia.upper())


    # ============================================================
    # 3. SEPARAR AS SEÇÕES
    # ============================================================

    inicio_10 = texto.find(
        "SEÇÃO 10 - FUNÇÕES / ATIVIDADES"
    )

    inicio_11 = texto.find(
        "SEÇÃO 11 - EPI / EPC"
    )

    if inicio_10 == -1 or inicio_11 == -1:

        print("ERRO: não foi possível localizar as seções.")

        exit()


    secao_10 = texto[inicio_10:inicio_11]

    secao_11 = texto[inicio_11:]


    # ============================================================
    # 4. LIMPAR LINHAS
    # ============================================================

    def limpar_linha(linha):

        linha = linha.strip()

        # Remove numeração criada pelo extrator.
        # Exemplo:
        # 69: SUPERVISOR
        linha = re.sub(
            r"^\d+:\s*",
            "",
            linha
        )

        return linha


    linhas_10 = [

        limpar_linha(linha)

        for linha in secao_10.splitlines()

        if limpar_linha(linha)

    ]


    linhas_11 = [

        limpar_linha(linha)

        for linha in secao_11.splitlines()

        if limpar_linha(linha)

    ]


    # ============================================================
    # 5. NORMALIZAR TEXTO
    # ============================================================

    def normalizar(texto):

        texto = texto.upper()

        texto = re.sub(
            r"\s+",
            " ",
            texto
        )

        return texto.strip()


    def normalizar_cargo_comparacao(texto):

        texto = normalizar(texto)

        # Remove acentos.
        texto = unicodedata.normalize(
            "NFD",
            texto
        )

        texto = "".join(
            caractere
            for caractere in texto
            if unicodedata.category(caractere) != "Mn"
        )

        return texto.strip()

    def cargo_corresponde(cargo, funcao_pdf):

        cargo = normalizar_cargo_comparacao(cargo)
        funcao_pdf = normalizar_cargo_comparacao(funcao_pdf)

        # Correspondência exata
        if cargo == funcao_pdf:
            return True

        # O nome do PDF pode ser uma versão mais curta do cargo.
        #
        # Exemplo:
        # GERENTE DE SAUDE E SEGURANCA
        # GERENTE DE SAUDE E SEGURANCA DO TRABALHO

        palavras_cargo = cargo.split()
        palavras_pdf = funcao_pdf.split()

        if len(palavras_pdf) >= 3:

            if cargo.startswith(
                funcao_pdf
            ):
                return True

        if len(palavras_cargo) >= 3:

            if funcao_pdf.startswith(
                cargo
            ):
                return True

        return False


    # ============================================================
    # 6. CARGOS
    # ============================================================


    print("\n=== TEXTO DAS FUNÇÕES RECEBIDO ===")
    print(dados_extraidos["texto_funcoes"])
    print("=== FIM DO TEXTO DAS FUNÇÕES ===\n")


    cargos_detectados = []

    linhas_funcoes = [
        linha.strip()
        for linha in dados_extraidos["texto_funcoes"].splitlines()
        if linha.strip()
    ]

    print("\n=== LINHAS DA SEÇÃO 10 ===")

    for indice, linha in enumerate(linhas_funcoes):
        print(indice, ":", linha)

    print("=== FIM DAS LINHAS ===\n")


    print("\n=== TEXTO EPI RECEBIDO ===")
    print(dados_extraidos["texto_epi"])
    print("=== FIM TEXTO EPI ===\n")


        # ============================================================
    # DETECTAR CARGOS DIRETAMENTE DAS TABELAS DA SEÇÃO 10
    # ============================================================

    cargos_detectados = []

    pdf_cargos = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    pagina_inicio_secao10 = None
    pagina_fim_secao10 = None


    # ------------------------------------------------------------
    # LOCALIZAR A PRIMEIRA PÁGINA REAL DA SEÇÃO 10
    # ------------------------------------------------------------

    for numero_pagina, pagina in enumerate(
        pdf_cargos
    ):

        encontrou_secao10 = False

        tabelas_pagina = pagina.find_tables()

        for tabela in tabelas_pagina.tables:

            dados_tabela = tabela.extract()

            cabecalho = " ".join(
                str(celula or "")
                for linha in dados_tabela[:4]
                for celula in linha
            )

            cabecalho_comparacao = (
                normalizar_cargo_comparacao(
                    cabecalho
                )
            )

            if (
                "DESCRICAO DAS ATIVIDADES"
                in cabecalho_comparacao
                and
                "GHE"
                in cabecalho_comparacao
            ):

                pagina_inicio_secao10 = (
                    numero_pagina
                )

                encontrou_secao10 = True

                break

        if encontrou_secao10:
            break


    # ------------------------------------------------------------
    # LOCALIZAR O INÍCIO DA SEÇÃO 11
    # ------------------------------------------------------------

    if pagina_inicio_secao10 is not None:

        for numero_pagina in range(
            pagina_inicio_secao10,
            len(pdf_cargos)
        ):

            texto_pagina = (
                normalizar_cargo_comparacao(
                    pdf_cargos[
                        numero_pagina
                    ].get_text()
                )
            )

            if re.search(
                r"\b\d+\s*[-–—.]\s*EPI\s*/\s*EPC\b",
                texto_pagina
            ):

                pagina_fim_secao10 = (
                    numero_pagina + 1
                )

                break


    if pagina_fim_secao10 is None:
        pagina_fim_secao10 = len(
            pdf_cargos
        )


    # ------------------------------------------------------------
    # EXTRAIR O CARGO DA PRIMEIRA COLUNA DAS TABELAS
    # ------------------------------------------------------------

    if pagina_inicio_secao10 is not None:

        for numero_pagina in range(
            pagina_inicio_secao10,
            pagina_fim_secao10
        ):

            pagina = pdf_cargos[
                numero_pagina
            ]

            tabelas_pagina = (
                pagina.find_tables()
            )

            for tabela in tabelas_pagina.tables:

                dados_tabela = tabela.extract()

                for linha in dados_tabela:

                    if not linha:
                        continue

                    celulas = [
                        str(celula or "").strip()
                        for celula in linha
                    ]

                    # A última coluna numérica normalmente
                    # contém a quantidade de empregados.
                    indices_quantidade = [
                        indice
                        for indice, celula
                        in enumerate(celulas)
                        if re.fullmatch(
                            r"\d+",
                            celula
                        )
                    ]

                    if not indices_quantidade:
                        continue

                    indice_quantidade = (
                        indices_quantidade[-1]
                    )

                    cargo_candidato = None

                    # O cargo é a primeira célula preenchida
                    # antes da quantidade de empregados.
                    for celula in celulas[
                        :indice_quantidade
                    ]:

                        celula = re.sub(
                            r"\s+",
                            " ",
                            celula
                        ).strip()

                        if celula:

                            cargo_candidato = (
                                celula
                            )

                            break

                    if not cargo_candidato:
                        continue

                    cargo_candidato = re.sub(
                        r"\s+",
                        " ",
                        cargo_candidato
                    ).strip(" -")


                    cargo_comparacao = (
                        normalizar_cargo_comparacao(
                            cargo_candidato
                        )
                    )


                    # Evita cabeçalhos do documento.
                    textos_invalidos = [
                        "PROGRAMA DE GERENCIAMENTO DE RISCOS OCUPACIONAIS",
                        "NUMERO DE PAGINA",
                        "ELABORADO EM",
                        "VENCIMENTO EM",
                        "NUMERO DA REVISAO",
                        "FUNCOES / CARGOS",
                        "EMPREGADOS",
                        "PREVISTOS"
                    ]

                    if any(
                        texto_invalido
                        in cargo_comparacao
                        for texto_invalido
                        in textos_invalidos
                    ):
                        continue


                    # Evita duplicar o mesmo cargo.
                    ja_existe = any(
                        normalizar_cargo_comparacao(
                            cargo
                        )
                        ==
                        cargo_comparacao
                        for cargo
                        in cargos_detectados
                    )

                    if not ja_existe:

                        cargos_detectados.append(
                            cargo_candidato
                        )


    pdf_cargos.close()

    print("\n=== CARGOS DETECTADOS AUTOMATICAMENTE ===")

    for cargo in cargos_detectados:
        print(cargo)

    print("=== FIM DOS CARGOS DETECTADOS ===\n")


    cargos = cargos_detectados
    

    print("\n=== CARGOS FIXOS ATUAIS ===")

    for cargo in cargos:
        print(cargo)

    print("=== FIM DOS CARGOS FIXOS ===\n")


    # ============================================================
    # 7. EXTRAIR EPIs DIRETAMENTE DAS TABELAS DA SEÇÃO 11
    # ============================================================

    def chave_cargo_epi(texto):

        texto = normalizar_cargo_comparacao(
            texto
        )

        # Pequenas diferenças encontradas entre
        # a Seção 10 e a tabela de EPI.
        substituicoes = {
            "ASISSTENTE": "ASSISTENTE",
            "PDREIRO": "PEDREIRO",
            "ADMINISTRATIVA": "ADMINISTRATIVO",
            "MECANICA": "MECANICO",
            "JR": "JUNIOR"
        }

        palavras = re.findall(
            r"[A-Z0-9]+",
            texto
        )

        palavras_corrigidas = []

        for palavra in palavras:

            palavra = substituicoes.get(
                palavra,
                palavra
            )

            # Palavras que não alteram a identidade
            # do cargo.
            if palavra in (
                "DE",
                "DA",
                "DO",
                "DAS",
                "DOS",
                "E"
            ):
                continue

            palavras_corrigidas.append(
                palavra
            )

        # Ordenar permite reconhecer, por exemplo:
        #
        # Supervisor de Manutenção e Elétrica
        # Supervisor de Elétrica e Manutenção
        palavras_corrigidas.sort()

        return " ".join(
            palavras_corrigidas
        )


    # ------------------------------------------------------------
    # Criar mapa dos cargos oficiais da Seção 10
    # ------------------------------------------------------------

    cargos_por_chave_epi = {}

    for cargo in cargos:

        chave = chave_cargo_epi(
            cargo
        )

        if chave:

            cargos_por_chave_epi[
                chave
            ] = cargo


    # ------------------------------------------------------------
    # Separar os EPIs existentes dentro de uma célula da tabela
    # ------------------------------------------------------------

    def separar_epis_celula(texto_celula):

        if not texto_celula:
            return []

        linhas = [
            re.sub(
                r"\s+",
                " ",
                linha
            ).strip()

            for linha in str(
                texto_celula
            ).splitlines()

            if linha.strip()
        ]

        epis = []

        epi_atual = ""

        for linha in linhas:

            # Novo EPI iniciado por "-"
            if linha.startswith("-"):

                if epi_atual:

                    epi_atual = (
                        epi_atual
                        .rstrip(" ;")
                        .strip()
                    )

                    if epi_atual:
                        epis.append(
                            epi_atual
                        )

                epi_atual = (
                    linha[1:]
                    .strip()
                )

                continue


            # Exemplo:
            #
            # Sapato de Segurança ... para
            # agentes elétricos;
            #
            # As duas linhas pertencem ao mesmo EPI.
            if epi_atual:

                if not epi_atual.rstrip().endswith(
                    (";", ".")
                ):

                    epi_atual += (
                        " " + linha
                    )

                else:

                    epi_atual = (
                        epi_atual
                        .rstrip(" ;")
                        .strip()
                    )

                    if epi_atual:
                        epis.append(
                            epi_atual
                        )

                    epi_atual = linha

            else:

                epi_atual = linha


        if epi_atual:

            epi_atual = (
                epi_atual
                .rstrip(" ;")
                .strip()
            )

            if epi_atual:
                epis.append(
                    epi_atual
                )


        return epis


    # ------------------------------------------------------------
    # Ler as tabelas reais da Seção 11
    # ------------------------------------------------------------

    dados_epi = {}

    pdf_epis = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    secao_epi_iniciada = False


    for pagina in pdf_epis:

        texto_pagina = pagina.get_text()

        limite_inicio_epi = None


        # --------------------------------------------------------
        # Encontrar o início REAL da Seção 11.
        #
        # O "$" evita confundir com a linha do Sumário.
        # --------------------------------------------------------

        if not secao_epi_iniciada:

            encontrou_inicio_epi = re.search(
                r"(?mi)^\s*\d+\s*[-–—.]\s*EPI\s*/\s*EPC\s*$",
                texto_pagina
            )

            if not encontrou_inicio_epi:
                continue

            secao_epi_iniciada = True

                        # A seção de EPI pode começar no meio da página.
            # Guardamos a posição vertical do título para ignorar
            # tabelas de atividades que estejam acima dele.
            posicoes_epi = pagina.search_for(
                "EPI / EPC"
            )

            if posicoes_epi:

                limite_inicio_epi = min(
                    area.y1
                    for area in posicoes_epi
                )


        # --------------------------------------------------------
        # Ler as tabelas da página
        # --------------------------------------------------------

        tabelas_pagina = (
            pagina.find_tables()
        )


        for tabela in tabelas_pagina.tables:

            # Na primeira página da seção de EPI,
            # ignora tabelas que estão acima do título EPI / EPC.
            if (
                limite_inicio_epi is not None
                and
                tabela.bbox[1] < limite_inicio_epi
            ):
                continue

            dados_tabela = tabela.extract()


            for linha in dados_tabela:

                if not linha:
                    continue


                celulas = [
                    str(celula or "").strip()
                    for celula in linha
                ]


                cargo_encontrado = None
                indice_cargo = None


                # ------------------------------------------------
                # Procurar em qual célula está o cargo.
                # ------------------------------------------------

                for indice, celula in enumerate(
                    celulas
                ):

                    if not celula:
                        continue


                    chave = chave_cargo_epi(
                        celula
                    )


                    if chave in cargos_por_chave_epi:

                        cargo_encontrado = (
                            cargos_por_chave_epi[
                                chave
                            ]
                        )

                        indice_cargo = indice

                        break


                if not cargo_encontrado:
                    continue


                # ------------------------------------------------
                # Procurar a primeira célula preenchida
                # depois do cargo.
                #
                # Essa será a célula dos EPIs.
                # ------------------------------------------------

                texto_epis = ""


                for celula in celulas[
                    indice_cargo + 1:
                ]:

                    if celula:

                        texto_epis = celula

                        break


                if not texto_epis:
                    continue


                epis_encontrados = (
                    separar_epis_celula(
                        texto_epis
                    )
                )


                if not epis_encontrados:
                    continue


                if cargo_encontrado not in dados_epi:

                    dados_epi[
                        cargo_encontrado
                    ] = []


                for epi in epis_encontrados:

                    if (
                        epi
                        not in dados_epi[
                            cargo_encontrado
                        ]
                    ):

                        dados_epi[
                            cargo_encontrado
                        ].append(
                            epi
                        )


        # --------------------------------------------------------
        # Depois de processar a página, verificar se chegou
        # ao início da parte de EPC.
        # --------------------------------------------------------

        encontrou_epc = re.search(
            r"(?mi)^\s*EPC\s*-\s*Equipamento de proteção coletiva\s*$",
            texto_pagina
        )

        if encontrou_epc:
            break


    pdf_epis.close()


    # ============================================================
    # 8. MOSTRAR EPIs ENCONTRADOS
    # ============================================================

    print(
        "\n================ EPIs ================\n"
    )


    for cargo in cargos:

        epis = dados_epi.get(
            cargo,
            []
        )

        if epis:

            print(cargo)

            for epi in epis:

                print(
                    "  -",
                    epi
                )

            print()


    # ============================================================
    # 9. MOSTRAR CARGOS SEM EPI
    # ============================================================

    print(
        "\n=== CARGOS SEM EPI ENCONTRADO ==="
    )


    for cargo in cargos:

        if not dados_epi.get(
            cargo
        ):

            print(cargo)


    print(
        "=== FIM DOS CARGOS SEM EPI ===\n"
    )


    # ============================================================
    # EXTRAIR ATIVIDADES DIRETAMENTE DAS TABELAS DA SEÇÃO 10
    # ============================================================

    atividades_por_cargo = {}

    pdf_atividades = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )


    if pagina_inicio_secao10 is not None:

        for numero_pagina in range(
            pagina_inicio_secao10,
            pagina_fim_secao10
        ):

            pagina = pdf_atividades[
                numero_pagina
            ]

            tabelas_pagina = (
                pagina.find_tables()
            )


            for tabela in tabelas_pagina.tables:

                dados_tabela = tabela.extract()


                for linha in dados_tabela:

                    if not linha:
                        continue


                    celulas = [
                        re.sub(
                            r"\s+",
                            " ",
                            str(celula or "")
                        ).strip()

                        for celula in linha
                    ]


                    # Só considera linhas de atividade que
                    # possuam a quantidade de empregados.
                    tem_quantidade_empregados = any(
                        re.fullmatch(
                            r"\d+",
                            celula
                        )
                        for celula in celulas
                    )

                    if not tem_quantidade_empregados:
                        continue



                    cargo_encontrado = None
                    indice_cargo = None


                    # --------------------------------------------
                    # LOCALIZAR O CARGO NA LINHA
                    # --------------------------------------------

                    for indice_celula, celula in enumerate(
                        celulas
                    ):

                        if not celula:
                            continue


                        celula_comparacao = (
                            normalizar_cargo_comparacao(
                                celula
                            )
                        )


                        for cargo in cargos:

                            if (
                                celula_comparacao
                                ==
                                normalizar_cargo_comparacao(
                                    cargo
                                )
                            ):

                                cargo_encontrado = cargo
                                indice_cargo = indice_celula

                                break


                        if cargo_encontrado:
                            break


                    if not cargo_encontrado:
                        continue


                    # --------------------------------------------
                    # PEGAR A DESCRIÇÃO DA ATIVIDADE
                    #
                    # Na linha do cargo, a descrição normalmente
                    # é a maior célula de texto.
                    # --------------------------------------------

                    candidatos_atividade = []


                    for indice_celula, celula in enumerate(
                        celulas
                    ):

                        if indice_celula == indice_cargo:
                            continue

                        if not celula:
                            continue

                        # Ignora quantidade de funcionários
                        if re.fullmatch(
                            r"\d+",
                            celula
                        ):
                            continue

                        candidatos_atividade.append(
                            celula
                        )


                    if not candidatos_atividade:
                        continue


                    atividade = max(
                        candidatos_atividade,
                        key=len
                    )


                    atividade = re.sub(
                        r"\s+",
                        " ",
                        atividade
                    ).strip()


                    if not atividade:
                        continue


                    # Se o cargo aparecer mais de uma vez,
                    # conserva a descrição mais completa.
                    atividade_existente = (
                        atividades_por_cargo.get(
                            cargo_encontrado,
                            ""
                        )
                    )


                    if (
                        len(atividade)
                        >
                        len(atividade_existente)
                    ):

                        atividades_por_cargo[
                            cargo_encontrado
                        ] = atividade


    pdf_atividades.close()


    print(
        "\n=== ATIVIDADES EXTRAÍDAS DAS TABELAS ==="
    )

    for cargo in cargos:

        print(
            cargo,
            "->",
            atividades_por_cargo.get(
                cargo,
                "NÃO ENCONTRADA"
            )
        )

    print(
        "=== FIM DAS ATIVIDADES ===\n"
    )

    
    # ============================================================
    # 11. PREPARAR SEÇÃO 10
    # ============================================================

    # Parar antes do rodapé do documento.

    linhas_10_limpo = []


    for linha in linhas_10:

        if "Docusign Envelope ID" in linha:

            break


        linhas_10_limpo.append(
            linha
        )


    # Junta tudo em uma única linha.

    texto_10 = " ".join(
        linhas_10_limpo
    )

    texto_10 = normalizar(
        texto_10
    )


    # ============================================================
    # 12. REMOVER CABEÇALHOS DA SEÇÃO 10
    # ============================================================

    cabecalhos = [

        "10- DESCRIÇÃO DAS FUNÇÕES / ATIVIDADES",

        "FUNÇÕES / CARGOS",

        "DESCRIÇÃO DAS ATIVIDADES GHE - 01",

        "DESCRIÇÃO DAS ATIVIDADES GHE - 02",

        "DESCRIÇÃO DAS ATIVIDADES – GHE - 02",

        "Nº DE EMPREGADOS PREVISTOS"

    ]


    for cabecalho in cabecalhos:

        texto_10 = texto_10.replace(

            normalizar(cabecalho),

            " "

        )


    # ============================================================
    # 13. LOCALIZAR TODOS OS CARGOS
    # ============================================================

    posicoes = []


    for cargo in cargos:

        cargo_normalizado = normalizar(
            cargo
        )

        posicao = texto_10.find(
            cargo_normalizado
        )


        if posicao != -1:

            posicoes.append({

                "cargo": cargo,

                "posicao": posicao

            })


    # Ordenar pela posição no documento

    posicoes.sort(

        key=lambda item: item["posicao"]

    )




    # ============================================================
    # 14. EXTRAIR ATIVIDADES
    # ============================================================

    dados_finais = {

        "_contrato": nome_fantasia

    }


    for indice, item in enumerate(posicoes):

        cargo = item["cargo"]

        inicio = item["posicao"]


        # --------------------------------------------------------
        # O final da atividade é o começo do próximo cargo
        # --------------------------------------------------------

        if indice + 1 < len(posicoes):

            fim = posicoes[
                indice + 1
            ]["posicao"]

        else:

            # Último cargo:
            # vai somente até o final da seção 10,
            # que já foi cortada antes do Docusign.

            fim = len(texto_10)


        # --------------------------------------------------------
        # Pegar somente o texto depois do nome do cargo
        # --------------------------------------------------------

        trecho = texto_10[

            inicio + len(
                normalizar(cargo)
            ):

            fim

        ]


        # --------------------------------------------------------
        # Remover cabeçalhos que possam ter ficado no meio
        # --------------------------------------------------------

        for cabecalho in cabecalhos:

            trecho = trecho.replace(

                normalizar(cabecalho),

                " "

            )


        # --------------------------------------------------------
        # Remover quantidade de funcionários
        #
        # Exemplo:
        #
        # atividade da função... 1
        #
        # vira:
        #
        # atividade da função...
        # --------------------------------------------------------

        trecho = re.sub(

            r"\s+\d+\s*$",

            "",

            trecho

        )


        # --------------------------------------------------------
        # Limpeza final
        # --------------------------------------------------------

        trecho = re.sub(

            r"\s+",

            " ",

            trecho

        ).strip()


        # --------------------------------------------------------
        # Salvar
        # --------------------------------------------------------

        dados_finais[cargo] = {

            "atividade": atividades_por_cargo.get(
                cargo,
                trecho
            ),

            "epis": dados_epi.get(
                cargo,
                []
            )

        }


    # ============================================================
    # DETECTAR GHE DOS CARGOS PELA SEÇÃO 10
    # ============================================================

        ghe_por_cargo = {}

    ghe_atual_secao10 = None

    for indice, linha in enumerate(linhas_funcoes):

        linha_normalizada = normalizar(
            linha
        )

        # -------------------------------------------------
        # DETECTAR O GHE ATUAL
        # -------------------------------------------------

        resultado_ghe = re.search(
            r"GHE\s*[-–]?\s*(\d+)",
            linha_normalizada
        )

        if resultado_ghe:

            numero_ghe = resultado_ghe.group(1)

            ghe_atual_secao10 = (
                f"GHE {numero_ghe.zfill(2)}"
            )

            continue

        if not ghe_atual_secao10:
            continue

        # -------------------------------------------------
        # PROCURAR CARGOS QUE PODEM ESTAR QUEBRADOS
        # EM ATÉ 4 LINHAS
        # -------------------------------------------------

        for cargo in cargos:


            if cargo in ghe_por_cargo:
                continue


            cargo_normalizado = (
                normalizar_cargo_comparacao(
                    cargo
                )
            )

            # Testa 1, 2, 3 e 4 linhas juntas
            for quantidade in range(1, 5):

                if (
                    indice + quantidade
                    > len(linhas_funcoes)
                ):
                    break

                trecho = " ".join(
                    linhas_funcoes[
                        indice:
                        indice + quantidade
                    ]
                )

                trecho_comparacao = (
                    normalizar_cargo_comparacao(
                        trecho
                    )
                )

                if (
                    trecho_comparacao
                    == cargo_normalizado
                    or
                    trecho_comparacao.startswith(
                        cargo_normalizado + " "
                    )
                ):

                    ghe_por_cargo[cargo] = (
                        ghe_atual_secao10
                    )

                    break

           

    print(
        "\n=== GHE DETECTADO PELA SEÇÃO 10 ==="
    )

    for cargo, ghe in ghe_por_cargo.items():

        print(
            cargo,
            "->",
            ghe
        )

    print(
        "=== FIM GHE SEÇÃO 10 ===\n"
    )
    

    # ============================================================
    # 15. EXTRAIR RISCOS PELAS TABELAS DO PDF
    # ============================================================

    print("\n========================================")
    print("EXTRAINDO RISCOS DAS TABELAS")
    print("========================================\n")


    def criar_riscos_vazios():

        return {
            "fisico": [],
            "quimico": [],
            "biologico": [],
            "mecanico_acidente": [],
            "ergonomico": [],
            "ergonomico_fp": []
        }


    def criar_controles_vazios():

        return {
            "fisico": [],
            "quimico": [],
            "biologico": [],
            "mecanico_acidente": [],
            "ergonomico": [],
            "ergonomico_fp": []
        }


    def limpar_celula(valor):

        if valor is None:
            return ""

        valor = str(valor)

        valor = valor.replace("\n", " ")

        valor = re.sub(
            r"\s+",
            " ",
            valor
        )

        return valor.strip()


    def descobrir_categoria(texto):

        texto = normalizar(texto)

        if texto == "FÍSICO":
            return "fisico"

        if texto == "QUÍMICO":
            return "quimico"

        if texto == "BIOLÓGICO":
            return "biologico"

        if texto in (
            "FATOR ERGONÔMICO",
            "FATOR ERGONOMICO"
        ):
            return "ergonomico"

        if texto in (
            "ERGONÔMICOS/ FP",
            "ERGONÔMICOS/FP",
            "ERGONOMICOS/ FP",
            "ERGONOMICOS/FP",
            "FATOR ERGONÔMICO FP",
            "FATOR ERGONOMICO FP"
        ):
            return "ergonomico_fp"

        if texto in (
            "RISCO DE ACIDENTE",
            "RISCO DE ACIDENTES"
        ):
            return "mecanico_acidente"

        return None


    def adicionar_risco(riscos, categoria, descricao):

        if not categoria:
            return

        descricao = limpar_celula(descricao)

        if not descricao:
            return

        if descricao not in riscos[categoria]:

            riscos[categoria].append(
                descricao
            )


    def adicionar_controle(controles, categoria, controle):

        if not categoria:
            return

        controle = limpar_celula(controle)

        if not controle:
            return

        controle_comparacao = (
            controle
            .rstrip(" .;,:")
            .lower()
        )

        for controle_existente in controles[categoria]:

            existente_comparacao = (
                controle_existente
                .rstrip(" .;,:")
                .lower()
            )

            if controle_comparacao == existente_comparacao:
                return

        # No máximo 2 controles diferentes
        if len(controles[categoria]) >= 2:
            return

        controles[categoria].append(
            controle
        )


    # ============================================================
    # TESTE - DESCRIÇÃO + CONTROLES EXISTENTES
    # ============================================================

    print("\n========================================")
    print("TESTE - RISCOS E CONTROLES")
    print("========================================")

    documento_teste = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    for numero_pagina in [34, 35, 36]:

        pagina = documento_teste[numero_pagina]

        tabelas = pagina.find_tables()

        for tabela_teste in tabelas.tables:

            dados_teste = tabela_teste.extract()

            for linha in dados_teste:

                if len(linha) <= 6:
                    continue

                descricao = limpar_celula(
                    linha[2]
                )

                controle = limpar_celula(
                    linha[6]
                )

                if not descricao:
                    continue

                if not controle:
                    continue

                if descricao.upper() == "DESCRIÇÃO DO RISCO":
                    continue

                print("\nRISCO:")
                print(descricao)

                print("CONTROLE:")
                print(controle)

    documento_teste.close()

    print("\n========================================")
    print("FIM DO TESTE")
    print("========================================\n")


    # ============================================================
    # LER AS TABELAS DO PDF
    # ============================================================

    documento_riscos = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    riscos_por_ghe = {}

    controles_por_ghe = {}

    funcoes_por_ghe = {}

    ghe_atual = None

    # Guarda uma descrição que apareceu
    # antes da categoria.
    descricao_pendente = None
    controle_pendente = None


    for pagina in documento_riscos:

        tabelas = pagina.find_tables()


        for tabela in tabelas.tables:

            dados = tabela.extract()

            if not dados:
                continue

            # -------------------------------------------------
            # LOCALIZAR AS COLUNAS PELO NOME DO CABEÇALHO
            # -------------------------------------------------

            indice_descricao = 2
            indice_controle = 6

            for linha_cabecalho in dados:

                for indice_coluna, celula in enumerate(
                    linha_cabecalho
                ):

                    texto_cabecalho = normalizar(
                        limpar_celula(celula)
                    )

                    if texto_cabecalho == "DESCRIÇÃO DO RISCO":
                        indice_descricao = indice_coluna

                    if texto_cabecalho == "CONTROLES EXISTENTES":
                        indice_controle = indice_coluna


            i = 0


            while i < len(dados):

                linha = dados[i]


                if len(linha) < 3:

                    i += 1
                    continue


                perigo = limpar_celula(
                    linha[0]
                )

                descricao = ""

                if indice_descricao < len(linha):

                    descricao = limpar_celula(
                        linha[indice_descricao]
                    )


                controle = ""

                if indice_controle < len(linha):

                    controle = limpar_celula(
                        linha[indice_controle]
                    )


                perigo_normalizado = normalizar(
                    perigo
                )


                # =================================================
                # NOVO GHE
                # =================================================

                if "INVENTARIO DE RISCO GHE" in perigo_normalizado:

                    resultado = re.search(
                        r"GHE\s*(\d+)",
                        perigo_normalizado
                    )

                    if resultado:

                        numero_ghe = resultado.group(1)

                        ghe_atual = (
                            f"GHE {numero_ghe.zfill(2)}"
                        )

                        riscos_por_ghe[ghe_atual] = (
                            criar_riscos_vazios()
                        )

                        controles_por_ghe[ghe_atual] = (
                            criar_controles_vazios()
                        )

                        funcoes_por_ghe[ghe_atual] = ""

                        descricao_pendente = None
                        controle_pendente = None


                    i += 1
                    continue


                # =================================================
                # FORA DO INVENTÁRIO
                # =================================================

                if ghe_atual is None:

                    i += 1
                    continue



                    if ghe_atual:
                        print(
                            "DEBUG TABELA",
                            ghe_atual,
                            "LINHA",
                            i,
                            ":",
                            [
                                limpar_celula(celula)
                                for celula in linha
                            ]
                        )


                    print(
                    "DEBUG LINHA DA TABELA:",
                    ghe_atual,
                    [
                        limpar_celula(celula)
                        for celula in linha
                    ]
                )


                # =================================================
                # CAPTURAR FUNÇÕES DO GHE
                # =================================================

                if perigo_normalizado == "FUNÇÕES":

                    # Normalmente os cargos estão na próxima linha
                    if i + 1 < len(dados):

                        proxima_linha = dados[i + 1]

                        if len(proxima_linha) > 0:

                            texto_funcoes = limpar_celula(
                                proxima_linha[0]
                            )

                            if texto_funcoes:

                                funcoes_por_ghe[ghe_atual] = (
                                    texto_funcoes
                                )

                    i += 1
                    continue


                # =================================================
                # IGNORAR CABEÇALHO
                # =================================================

                if normalizar(descricao) == "DESCRIÇÃO DO RISCO":

                    i += 1
                    continue


                            # =================================================
                # TENTAR IDENTIFICAR CATEGORIA
                # =================================================

                categoria = descobrir_categoria(
                    perigo
                )

                linhas_categoria = 1


                # -------------------------------------------------
                # TRATAR "FATOR ERGONÔMICO" + "FP"
                # QUE O PDF SEPARA EM DUAS LINHAS
                # -------------------------------------------------

                if normalizar(perigo) in (
                    "FATOR ERGONÔMICO",
                    "FATOR ERGONOMICO"
                ):

                    for distancia in range(1, 4):

                        if i + distancia >= len(dados):
                            break

                        proxima_linha = dados[
                            i + distancia
                        ]

                        proximo_perigo = ""

                        if len(proxima_linha) > 0:

                            proximo_perigo = limpar_celula(
                                proxima_linha[0]
                            )

                        # Ignora linhas realmente vazias
                        if not proximo_perigo:
                            continue

                        # Se a próxima parte for FP,
                        # então a categoria correta é
                        # ergonomico_fp.
                        if normalizar(
                            proximo_perigo
                        ) == "FP":

                            categoria = (
                                "ergonomico_fp"
                            )

                            linhas_categoria = (
                                distancia + 1
                            )

                        break


                # -------------------------------------------------
                # Algumas categorias estão quebradas em mais
                # de uma linha.
                #
                # Exemplos:
                #
                # Fator
                # Ergonômico
                #
                # Ergonômicos/
                # [linha vazia]
                # FP
                #
                # Risco de
                # Acidente
                # -------------------------------------------------

                if (
                    categoria is None
                    and perigo
                ):

                    for distancia in range(1, 4):

                        if i + distancia >= len(dados):
                            break


                        proxima_linha = dados[
                            i + distancia
                        ]

                        proximo_perigo = ""

                        if len(proxima_linha) > 0:

                            proximo_perigo = limpar_celula(
                                proxima_linha[0]
                            )


                        # Se a linha estiver vazia,
                        # procura mais abaixo.
                        if not proximo_perigo:
                            continue


                        categoria_junta = (
                            perigo
                            + " "
                            + proximo_perigo
                        ).strip()


                        categoria = descobrir_categoria(
                            categoria_junta
                        )


                        if categoria:

                            linhas_categoria = (
                                distancia + 1
                            )

                            break


                        # Encontrou outro texto, mas ele não
                        # completa uma categoria.
                        break


                # =================================================
                # CASO 1
                #
                # A categoria está na mesma linha da descrição.
                #
                # Exemplo:
                #
                # Físico | ... | Ruido
                # =================================================

                if categoria and descricao:

                    adicionar_risco(
                        riscos_por_ghe[ghe_atual],
                        categoria,
                        descricao
                    )

                    adicionar_controle(
                        controles_por_ghe[ghe_atual],
                        categoria,
                        controle
                    )

                    descricao_pendente = None
                    controle_pendente = None

                    i += linhas_categoria
                    continue


                # =================================================
                # CASO 2
                #
                # A categoria apareceu DEPOIS da descrição.
                #
                # Exemplo:
                #
                # ""       | ... | Postaura inadequada
                # Fator
                # Ergonômico
                # =================================================

                if categoria and descricao_pendente is not None:

                    adicionar_risco(
                        riscos_por_ghe[ghe_atual],
                        categoria,
                        descricao_pendente
                    )

                    adicionar_controle(
                        controles_por_ghe[ghe_atual],
                        categoria,
                        controle_pendente
                    )

                    descricao_pendente = None
                    controle_pendente = None

                    i += linhas_categoria
                    continue


                # =================================================
                # CASO 3
                #
                # Encontrou categoria sem descrição e sem
                # descrição pendente.
                #
                # Não salva nada ainda.
                # =================================================

                if categoria:

                    i += linhas_categoria
                    continue


                # =================================================
                # DESCRIÇÃO SEM CATEGORIA
                #
                # Guardamos temporariamente.
                #
                # A próxima categoria válida dirá a qual grupo
                # ela pertence.
                # =================================================

                if descricao:

                    descricao_pendente = descricao
                    controle_pendente = controle


                i += 1


    documento_riscos.close()


    print("\n========================================")
    print("FUNÇÕES ENCONTRADAS POR GHE")
    print("========================================\n")

    for ghe, funcoes in funcoes_por_ghe.items():

        print(ghe)
        print(funcoes)
        print()


    # ============================================================
    # MOSTRAR RESULTADO
    # ============================================================

    for ghe, riscos in riscos_por_ghe.items():

        print(ghe)

        for categoria, lista in riscos.items():

            print(
                " ",
                categoria,
                ":",
                lista
            )

        print()


    print("\n========================================")
    print("CONTROLES ENCONTRADOS POR GHE")
    print("========================================\n")

    for ghe, controles in controles_por_ghe.items():

        print(ghe)

        for categoria, lista in controles.items():

            print(
                " ",
                categoria,
                ":",
                lista
            )

        print()


    # ============================================================
    # ASSOCIAR OS RISCOS DOS GHEs AOS CARGOS
    # ============================================================

    print("\n========================================")
    print("ASSOCIANDO RISCOS AOS CARGOS")
    print("========================================\n")


    for cargo in dados_finais:

        # Ignora o campo especial do contrato
        if cargo == "_contrato":
            continue


        cargo_normalizado = normalizar(
            cargo
        )

        ghe_encontrado = ghe_por_cargo.get(
            cargo
        )


        # --------------------------------------------------------
        # Encontrou o GHE
        # --------------------------------------------------------

        if ghe_encontrado:

            riscos_cargo = {}

            for categoria, lista in riscos_por_ghe[
                ghe_encontrado
            ].items():

                # Se a categoria estiver vazia,
                # grava N/A.
                if lista:

                    riscos_cargo[categoria] = lista.copy()

                else:

                    riscos_cargo[categoria] = ["N/A"]


            dados_finais[cargo]["riscos"] = (
                riscos_cargo
            )


            controles_cargo = {}

            for categoria, lista in controles_por_ghe[
                ghe_encontrado
            ].items():

                if lista:

                    controles_cargo[categoria] = (
                        lista.copy()
                    )

                else:

                    controles_cargo[categoria] = [
                        "N/A"
                    ]

            dados_finais[cargo]["controles"] = (
                controles_cargo
    )


            print(
                cargo,
                "->",
                ghe_encontrado
            )


        # --------------------------------------------------------
        # Cargo não localizado em nenhum GHE
        # --------------------------------------------------------

        else:

            dados_finais[cargo]["riscos"] = {
                "fisico": ["N/A"],
                "quimico": ["N/A"],
                "biologico": ["N/A"],
                "mecanico_acidente": ["N/A"],
                "ergonomico": ["N/A"],
                "ergonomico_fp": ["N/A"]
            }


            print(
                cargo,
                "-> GHE NÃO ENCONTRADO"
            )


    return dados_finais


    # ============================================================
    # 16. MOSTRAR RESULTADO FINAL
    # ============================================================

    print("\n========================================")

    print("RESULTADO FINAL")

    print("========================================\n")


    for cargo, dados in dados_finais.items():

        # O contrato é uma informação especial,
        # não é um cargo.

        if cargo == "_contrato":

            print("CONTRATO:")

            print(
                dados.upper()
            )

            print(
                "\n----------------------------------------\n"
            )

            continue


        print("CARGO:", cargo)


        print("\nATIVIDADE:")

        print(
            dados["atividade"]
        )


        print("\nEPIs:")


        for epi in dados["epis"]:

            print(
                " -",
                epi
            )


        print(
            "\n----------------------------------------\n"
        )


    print(
        "Arquivo criado: dados_organizados.json"
    )