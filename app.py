from flask import Flask, render_template, request, send_file
from services.extrair_dados import extrair_pdf
from services.organizar_dados import organizar_dados
from services.gerador_os import gerar_os

app = Flask(__name__)



@app.route("/")
def inicio():

    return render_template(
        "index.html"
    )





@app.route(
    "/upload",
    methods=["POST"]
)
def upload():

    arquivo = request.files.get(
        "arquivo_pdf"
    )

    if not arquivo:
        return "Nenhum arquivo foi enviado."

    if not arquivo.filename.lower().endswith(
        ".pdf"
    ):
        return "O arquivo precisa ser PDF."

    dados_extraidos = extrair_pdf(arquivo)

    arquivo.seek(0)
    pdf_bytes = arquivo.read()

    dados_finais = organizar_dados(
        pdf_bytes,
        dados_extraidos
    )

    zip_os = gerar_os(dados_finais)

    return send_file(
        zip_os,
        mimetype="application/zip",
        as_attachment=True,
        download_name="Ordens_de_Servico.zip"
    )


if __name__ == "__main__":
    app.run(debug=True)