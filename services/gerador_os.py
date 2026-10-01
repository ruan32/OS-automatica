from docx import Document
from pathlib import Path
from docx.shared import Pt
import io
import zipfile


# ============================================================
# CAMINHOS
# ============================================================

PASTA_PROJETO = Path(
    r"C:\Users\RuanPabloPereira\OneDrive - FX Serviço\Área de Trabalho\OS automatico"
)

PASTA_MODELO = PASTA_PROJETO / "Modelo OS"

ARQUIVO_MODELO = PASTA_MODELO / "Modelo OS.docx"




# ============================================================
# VERIFICAR ARQUIVOS
# ============================================================

if not ARQUIVO_MODELO.exists():
    print("ERRO: Modelo OS.docx não encontrado.")
    print(ARQUIVO_MODELO)
    exit()



# ============================================================
# CRIAR PASTA DE SAÍDA
# ============================================================


def gerar_os(dados):

    contrato = dados.get("_contrato", "")

    zip_buffer = io.BytesIO()


    # ============================================================
    # GERAR UMA OS PARA CADA FUNÇÃO
    # ============================================================

    for cargo, informacoes in dados.items():

        print("\nGerando:", cargo)

        if cargo == "_contrato":
            continue

        # --------------------------------------------------------
        # Nome seguro para o arquivo
        # --------------------------------------------------------

        nome_arquivo = cargo

        caracteres_invalidos = '<>:"/\\|?*'

        for caractere in caracteres_invalidos:

            nome_arquivo = nome_arquivo.replace(
                caractere,
                ""
            )

        nome_arquivo = f"OS - {nome_arquivo}.docx"

        


        # --------------------------------------------------------
        # Copiar o modelo original
        # --------------------------------------------------------

        documento = Document(
            ARQUIVO_MODELO
        )


        # ========================================================
        # TABELA 0
        # ========================================================

        tabela = documento.tables[0]


        


        # ============================================================
        # CONTRATO
        # ============================================================

        celula_contrato = tabela.cell(0, 1)

        # Remove o conteúdo antigo
        for paragrafo_antigo in celula_contrato.paragraphs:

            p = paragrafo_antigo._element

            p.getparent().remove(p)


        # Cria um novo parágrafo
        paragrafo = celula_contrato.add_paragraph()


        # Texto "Contrato:"
        run_contrato = paragrafo.add_run("Contrato: ")
        run_contrato.bold = True


        # Nome da empresa
        run_nome = paragrafo.add_run(contrato.upper())
        run_nome.bold = True


        # ========================================================
        # FUNÇÃO
        # ========================================================

        celula_funcao = tabela.cell(0, 3)

        # Remove os parágrafos existentes
        for paragrafo_antigo in celula_funcao.paragraphs:

            p = paragrafo_antigo._element

            p.getparent().remove(p)


        # Cria novo parágrafo
        paragrafo = celula_funcao.add_paragraph()


        # "Função:" em negrito
        run_funcao = paragrafo.add_run("Função: ")
        run_funcao.bold = True


        # Nome da função em maiúsculo e negrito
        run_cargo = paragrafo.add_run(cargo.upper())
        run_cargo.bold = True


        # ============================================================
        # DESCRIÇÃO DA ATIVIDADE
        # ============================================================

        atividade = informacoes.get("atividade", "")

        if atividade:
            # Campo grande abaixo de Contrato / Função
            celula_atividade = tabela.cell(2, 0)

            # Limpa o conteúdo atual da célula
            for paragrafo_antigo in celula_atividade.paragraphs:
                p = paragrafo_antigo._element
                p.getparent().remove(p)

            # Cria o parágrafo com a descrição
            paragrafo_atividade = celula_atividade.add_paragraph()

            # Insere a descrição
            run_atividade = paragrafo_atividade.add_run(atividade.capitalize())

            # Formatação
            run_atividade.bold = False
            run_atividade.font.size = Pt(10)


        # ========================================================
        # RISCOS
        # ========================================================

        riscos = informacoes.get(
            "riscos",
            {}
        )

        controles = informacoes.get(
            "controles",
            {}
        )   

        print("\nRISCOS DE:", cargo)

        for categoria, lista_riscos in riscos.items():

            print(
                " ",
                categoria,
                ":",
                lista_riscos
            )


        # ========================================================
        # RISCOS - PREENCHER TABELA
        # ========================================================

        linhas_riscos = {
            "fisico": 5,
            "quimico": 6,
            "biologico": 7,
            "mecanico_acidente": 8,
            "ergonomico": 9,
            "ergonomico_fp": 10
        }

        for categoria, linha in linhas_riscos.items():

            lista_riscos = riscos.get(
                categoria,
                ["N/A"]
            )

            celula_risco = tabela.cell(
                linha,
                3
            )

            celula_risco.text = ""

            for i, risco in enumerate(lista_riscos):

                if i == 0:
                    paragrafo = celula_risco.paragraphs[0]
                else:
                    paragrafo = celula_risco.add_paragraph()

                run = paragrafo.add_run(
                    "• " + risco.lower()
                )

                run.font.size = Pt(10)

        # ========================================================
        # MEDIDAS DE CONTROLE
        # ========================================================

        linhas_controles = {
            "fisico": 5,
            "quimico": 6,
            "biologico": 7,
            "mecanico_acidente": 8,
            "ergonomico": 9,
            "ergonomico_fp": 10
        }

        for categoria, linha in linhas_controles.items():

            lista_controles = controles.get(
                categoria,
                ["N/A"]
            )

            celula_controle = tabela.cell(
                linha,
                4
            )

            for i, controle in enumerate(lista_controles):

                if i == 0:
                    celula_controle.text = "• " + controle

                else:
                    paragrafo = celula_controle.add_paragraph()
                    paragrafo.add_run(
                        "• " + controle
                    )


            
        # ========================================================
        # EPIs
        # ========================================================

        epis = informacoes.get("epis", [])


        # Divide os EPIs em duas partes
        meio = (len(epis) + 1) // 2

        epis_esquerda = epis[:meio]

        epis_direita = epis[meio:]


        # ========================================================
        # CAMPO ESQUERDO DOS EPIs
        # ========================================================

        celula_esquerda = tabela.cell(12, 0)

        celula_esquerda.text = ""


        for i, epi in enumerate(epis_esquerda):

            if i == 0:

                paragrafo = celula_esquerda.paragraphs[0]

            else:

                paragrafo = celula_esquerda.add_paragraph()


            paragrafo.add_run("• " + epi)


        # ========================================================
        # CAMPO DIREITO DOS EPIs
        # ========================================================

        celula_direita = tabela.cell(12, 3)

        celula_direita.text = ""


        for i, epi in enumerate(epis_direita):

            if i == 0:

                paragrafo = celula_direita.paragraphs[0]

            else:

                paragrafo = celula_direita.add_paragraph()


            paragrafo.add_run("• " + epi)


        # ========================================================
        # SALVAR
        # ========================================================

        docx_buffer = io.BytesIO()

        documento.save(docx_buffer)

        docx_buffer.seek(0)

        with zipfile.ZipFile(
            zip_buffer,
            "a",
            zipfile.ZIP_DEFLATED
        ) as zip_arquivo:

            zip_arquivo.writestr(
                nome_arquivo,
                docx_buffer.getvalue()
            )

        print(
            "Adicionado ao ZIP:",
            nome_arquivo
        )


    # ============================================================
    # FINAL
    # ============================================================

    print("\n========================================")
    print("FINALIZADO")
    print("========================================")
    
    zip_buffer.seek(0)

    return zip_buffer