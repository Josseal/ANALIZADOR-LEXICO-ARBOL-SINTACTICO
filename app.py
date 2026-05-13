from flask import Flask, render_template, request
from analizador_lexico import analizar_lexico
from parser_sintactico import construir_arbol_programa, renderizar_arbol_grafico

app = Flask(__name__)


def formatear_token(lexema, tipo):
    return f"<'{lexema}', {tipo}>"


@app.route("/", methods=["GET", "POST"])
def index():
    texto = ""
    salida = []
    arbol_texto = ""

    if request.method == "POST":
        texto = request.form.get("texto", "")
        tokens = analizar_lexico(texto)
        salida = [
            {
                "lexema": lexema,
                "tipo": tipo,
                "texto": formatear_token(lexema, tipo),
            }
            for lexema, tipo in tokens
        ]
        arbol_desc = construir_arbol_programa(tokens)
        if arbol_desc:
            arbol_texto = renderizar_arbol_grafico(arbol_desc)
        else:
            arbol_texto = ""

    return render_template("index.html", texto=texto, salida=salida, arbol_texto=arbol_texto)


if __name__ == "__main__":
    app.run(debug=True)
