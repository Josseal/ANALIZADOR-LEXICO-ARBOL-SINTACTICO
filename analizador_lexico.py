def analizar_lexico(texto):
    # Normaliza texto pegado desde navegador/Windows para evitar ruido en tokens.
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = texto.replace("\u00A0", " ").replace("\u2007", " ").replace("\u202F", " ")
    texto = texto.replace("\u200B", "").replace("\u200C", "").replace("\u200D", "")
    texto = texto.replace("\u2060", "").replace("\uFEFF", "")

    palabras_reservadas = {
        # Python
        "def", "return", "if", "else", "elif", "for", "while", "in", "range",
        "and", "or", "not", "True", "False", "None", "class", "import", "from", "as",
        "try", "except", "finally", "with", "lambda", "pass", "break", "continue", "yield",
        # C / C++ / Java / C#-like
        "int", "float", "double", "char", "bool", "string", "void", "short", "long", "signed", "unsigned",
        "public", "private", "protected", "static", "final", "const", "new", "this", "super", "interface",
        "implements", "extends", "namespace", "using", "include", "struct", "enum", "switch", "case", "default",
        "do", "goto", "typedef", "sizeof", "null", "nullptr", "true", "false",
        # JavaScript / TypeScript / PHP / Go / Rust
        "function", "let", "var", "const", "async", "await", "export", "default", "module", "require",
        "package", "func", "fn", "mut", "pub", "crate", "impl", "trait", "match", "where", "use",
        "echo", "foreach", "endif", "endforeach", "fi", "then", "done",
        # SQL
        "select", "from", "where", "join", "inner", "left", "right", "full", "on", "group", "by",
        "order", "having", "limit", "insert", "into", "values", "update", "set", "delete", "create",
        "table", "index", "drop", "alter", "as", "distinct", "union", "all", "is", "like", "between",
        # HTML-like tokens comunes
        "html", "head", "body", "div", "span", "script", "style", "title", "meta", "link"
    }

    operadores_dobles = {
        "==", "!=", "<=", ">=", "+=", "-=", "*=", "/=", "%=", "//", "**",
        "&&", "||", "<<", ">>", "++", "--", "::", "->", "=>", "??"
    }
    operadores_simples = {"+", "-", "*", "/", "%", "=", "<", ">", "!", "&", "|", "^", "~", "?"}
    caracteres_especiales = {"(", ")", "[", "]", "{", "}", ",", ":", ";", ".", "\"", "'", "#"}

    tokens = []
    j = 0
    largo = len(texto)

    while j < largo:
        caracter = texto[j]

        if caracter == " ":
            pos_inicio = j
            while j < largo and texto[j] == " ":
                j = j + 1
            espacios = texto[pos_inicio:j]
            tokens.append((espacios, "Espacio"))
            continue

        if caracter == "\t":
            tokens.append(("\\t", "Tabulador"))
            j = j + 1
            continue

        if caracter == "\n":
            tokens.append(("\\n", "Salto de linea"))
            j = j + 1
            continue

        if caracter.isalpha() or caracter == "_":
            pos_inicio = j
            while j < largo and (texto[j].isalnum() or texto[j] == "_"):
                j = j + 1
            
            palabra = texto[pos_inicio:j]
            if palabra in palabras_reservadas:
                tokens.append((palabra, "Palabra reservada"))
            else:
                tokens.append((palabra, "Variable"))
            continue

        if caracter.isdigit():
            pos_inicio = j
            while j < largo and texto[j].isdigit():
                j = j + 1
            
            hay_punto = False
            if j < largo and texto[j] == ".":
                if j + 1 < largo and texto[j + 1].isdigit():
                    hay_punto = True
                    j = j + 1  # Me salto el punto
                    while j < largo and texto[j].isdigit():
                        j = j + 1
            
            numero = texto[pos_inicio:j]
            if hay_punto:
                tokens.append((numero, "Flotante"))
            else:
                tokens.append((numero, "Entero"))
            continue

        if caracter == '"' or caracter == "'":
            tipo_comilla = caracter

            if tipo_comilla == '"':
                tokens.append((tipo_comilla, "Comilla doble"))
            else:
                tokens.append((tipo_comilla, "Comilla simple"))

            j = j + 1
            pos_inicio = j

            while j < largo and texto[j] != tipo_comilla:
                j = j + 1

            cadena = texto[pos_inicio:j]
            if cadena != "":
                tokens.append((cadena, "Cadena de texto"))

            if j < largo and texto[j] == tipo_comilla:
                if tipo_comilla == '"':
                    tokens.append((tipo_comilla, "Comilla doble"))
                else:
                    tokens.append((tipo_comilla, "Comilla simple"))
                j = j + 1

            continue

        if j + 1 < largo:
            operador_dos = texto[j:j + 2]
            if operador_dos in operadores_dobles:
                tokens.append((operador_dos, "Operador"))
                j = j + 2
                continue

        if caracter in operadores_simples:
            tokens.append((caracter, "Operador"))
            j = j + 1
            continue

        if caracter in caracteres_especiales:
            tokens.append((caracter, "Caracter especial"))
            j = j + 1
            continue

        tokens.append((caracter, "Desconocido"))
        j = j + 1

    return tokens

if __name__ == "__main__":
    print("Ingresa la cadena o codigo a analizar.")
    print("Cuando termines, presiona Enter en una linea vacia.")

    lineas = []

    while True:
        linea = input()
        if linea == "":
            break
        lineas.append(linea)

    entrada = "\n".join(lineas)
    resultado = analizar_lexico(entrada)
    contador = 1

    for par in resultado:
        lexema = par[0]
        tipo = par[1]
        print(f"{contador:03d}  < '{lexema}' , {tipo} >")
        contador = contador + 1