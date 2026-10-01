import pymupdf
import re


def extrair_pdf(arquivo_pdf):

    pdf = pymupdf.open(
        stream=arquivo_pdf.read(),
        filetype="pdf"
    )
    
    texto_completo = ""

    for pagina in pdf:
        texto_completo += pagina.get_text() + "\n"


        # ============================================================
    # LOCALIZAR AS SEÇÕES PELO TÍTULO
    # SEM DEPENDER DO NÚMERO DA SEÇÃO
    # ============================================================

    padrao_funcoes = re.search(
        r"(?mi)^\s*\d+\s*[-–—.]\s*"
        r"DESCRIÇÃO\s+DAS\s+FUNÇÕES\s*/\s*ATIVIDADES\s*$",
        texto_completo
    )

    if not padrao_funcoes:

        print(
            "Não foi possível encontrar "
            "a seção de descrição das funções."
        )

        pdf.close()

        return None


    inicio_funcoes = padrao_funcoes.start()


    # ============================================================
    # LOCALIZAR EPI / EPC
    # ============================================================

    padrao_epi = re.search(
        r"(?mi)^\s*\d+\s*[-–—.]\s*"
        r"EPI\s*/\s*EPC\s*$",
        texto_completo[
            inicio_funcoes:
        ]
    )

    if not padrao_epi:

        print(
            "Não foi possível encontrar "
            "a seção EPI / EPC."
        )

        pdf.close()

        return None


    inicio_epi = (
        inicio_funcoes
        + padrao_epi.start()
    )


    # ============================================================
    # LOCALIZAR INVENTÁRIO DE RISCOS
    # ============================================================

    padrao_riscos = re.search(
        r"(?mi)^\s*\d+\s*[-–—.]\s*"
        r"INVENTÁRIO\s+DE\s+RISCOS"
        r"(?:\s*-\s*ANEXO\s*I)?\s*$",
        texto_completo[
            inicio_epi:
        ]
    )

    if not padrao_riscos:

        print(
            "Não foi possível encontrar "
            "a seção de inventário de riscos."
        )

        pdf.close()

        return None


    inicio_riscos = (
        inicio_epi
        + padrao_riscos.start()
    )


    # ============================================================
    # SEPARAR AS SEÇÕES
    # ============================================================

    texto_funcoes = texto_completo[
        inicio_funcoes:
        inicio_epi
    ]

    texto_epi = texto_completo[
        inicio_epi:
        inicio_riscos
    ]

    texto_riscos = texto_completo[
        inicio_riscos:
    ]

    if inicio_riscos == -1:
        print("Não foi possível encontrar a seção 12.")
        exit()


    # Por enquanto pega tudo da seção 12 até o final do PDF
    texto_riscos = texto_completo[
        inicio_riscos:
    ]



    # ============================================================
    # MOSTRAR RESULTADO
    # ============================================================

    print()
    print("=" * 70)
    print("SEÇÃO 10 - FUNÇÕES / ATIVIDADES")
    print("=" * 70)

    print(texto_funcoes[:6000])


    print()
    print("=" * 70)
    print("SEÇÃO 11 - EPI / EPC")
    print("=" * 70)

    print(texto_epi[:6000])


    # ============================================================
    # SALVAR EM ARQUIVO
    # ============================================================

   


    # ============================================================
    # FINAL
    # ============================================================

    print()
    print("=" * 70)
    print("EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    print()
    resultado = {
        "texto_funcoes": texto_funcoes,
        "texto_epi": texto_epi,
        "texto_riscos": texto_riscos
    }
    pdf.close()
    return resultado