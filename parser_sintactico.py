import re

TIPOS_VALIDOS = {"int", "float", "double", "char", "bool", "string", "void"}
TOKEN_EXPR_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+\.\d+|\d+|[()+\-*/]")
OPERADORES = {"or", "and", "==", "!=", "<=", ">=", "<", ">", "+", "-", "*", "/"}
PRECEDENCIA = {
    "or": 1,
    "and": 2,
    "==": 3,
    "!=": 3,
    "<=": 3,
    ">=": 3,
    "<": 3,
    ">": 3,
    "+": 4,
    "-": 4,
    "*": 5,
    "/": 5,
}
IDENT_RE = r"[A-Za-z_][A-Za-z0-9_]*"
PALABRAS_RESERVADAS = {
    "def", "return", "if", "else", "for", "while", "in", "range",
    "and", "or", "not", "True", "False", "None", "class", "import",
    "int", "float", "double", "char", "bool", "string", "void",
}


def _nodo(etiqueta, hijos=None):
    return {"label": etiqueta, "children": hijos or []}


def _nodo_visual(valor, rol):
    return {"value": valor, "role": rol}


def _normalizar_linea(linea):
    parte = linea.split("#", 1)[0]
    return parte.strip()


def _tokenizar_expresion(expresion):
    tokens = TOKEN_EXPR_RE.findall(expresion)
    reconstruido = "".join(tokens)
    sin_espacios = re.sub(r"\s+", "", expresion)
    if reconstruido != sin_espacios:
        raise ValueError("Expresion contiene simbolos no soportados")
    return tokens


def _es_literal_token(tok):
    return (
        re.fullmatch(r"\d+\.\d+|\d+", tok)
        or tok in {"True", "False", "None"}
        or (len(tok) >= 2 and ((tok[0] == '"' and tok[-1] == '"') or (tok[0] == "'" and tok[-1] == "'")))
    )


def _a_postfijo(tokens):
    salida = []
    pila = []

    for tok in tokens:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tok):
            salida.append(tok)
        elif _es_literal_token(tok):
            salida.append(tok)
        elif tok in OPERADORES:
            while pila and pila[-1] in OPERADORES and PRECEDENCIA[pila[-1]] >= PRECEDENCIA[tok]:
                salida.append(pila.pop())
            pila.append(tok)
        elif tok == "(":
            pila.append(tok)
        elif tok == ")":
            while pila and pila[-1] != "(":
                salida.append(pila.pop())
            if not pila:
                raise ValueError("Parentesis no balanceados")
            pila.pop()

    while pila:
        if pila[-1] in {"(", ")"}:
            raise ValueError("Parentesis no balanceados")
        salida.append(pila.pop())

    return salida


def _arbol_desde_postfijo(postfijo):
    pila = []

    for tok in postfijo:
        if tok in OPERADORES:
            if len(pila) < 2:
                raise ValueError("Expresion incompleta")
            der = pila.pop()
            izq = pila.pop()
            pila.append(_nodo(f"Op {tok}", [izq, der]))
        elif re.fullmatch(r"\d+\.\d+|\d+", tok):
            pila.append(_nodo(f"Numero {tok}"))
        else:
            pila.append(_nodo(f"Id {tok}"))

    if len(pila) != 1:
        raise ValueError("Expresion invalida")

    return pila[0]


def _ast_expresion_desde_postfijo(postfijo):
    pila = []

    for tok in postfijo:
        if tok in OPERADORES:
            if len(pila) < 2:
                raise ValueError("Expresion incompleta")
            der = pila.pop()
            izq = pila.pop()
            pila.append({
                "kind": "op",
                "value": tok,
                "role": "operador",
                "left": izq,
                "right": der,
            })
        elif _es_literal_token(tok):
            pila.append({"kind": "num", "value": tok, "role": "literal"})
        else:
            pila.append({"kind": "id", "value": tok, "role": "identificador"})

    if len(pila) != 1:
        raise ValueError("Expresion invalida")

    return pila[0]


def _parsear_expresion(expresion):
    tokens = _tokenizar_expresion(expresion)
    if not tokens:
        raise ValueError("Expresion vacia")
    postfijo = _a_postfijo(tokens)
    return _arbol_desde_postfijo(postfijo)


def _parsear_expresion_visual(expresion):
    tokens = _tokenizar_expresion(expresion)
    if not tokens:
        raise ValueError("Expresion vacia")
    postfijo = _a_postfijo(tokens)
    return _ast_expresion_desde_postfijo(postfijo)


def _parsear_sentencia(linea):
    if not linea.endswith(";"):
        return _nodo("Error: falta ';'", [_nodo(f"Entrada: {linea}")])

    sin_punto_coma = linea[:-1].strip()
    if not sin_punto_coma:
        return _nodo("Error: sentencia vacia")

    declaracion = re.match(r"^(int|float|double|char|bool|string)\s+(.+)$", sin_punto_coma)
    if declaracion:
        tipo = declaracion.group(1)
        resto = declaracion.group(2).strip()

        if "=" in resto:
            izquierda, derecha = resto.split("=", 1)
            identificador = izquierda.strip()
            expresion = derecha.strip()

            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identificador):
                return _nodo("Error en declaracion", [_nodo(f"Variable invalida: {identificador}")])

            try:
                arbol_expr = _parsear_expresion(expresion)
            except ValueError as err:
                return _nodo("Error en declaracion", [_nodo(str(err)), _nodo(f"Expresion: {expresion}")])

            return _nodo("Declaracion", [
                _nodo(f"Tipo {tipo}"),
                _nodo("Asignacion", [
                    _nodo(f"Id {identificador}"),
                    _nodo("="),
                    _nodo("Expresion", [arbol_expr]),
                ]),
            ])

        ids = [p.strip() for p in resto.split(",")]
        if not ids or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", ident) for ident in ids):
            return _nodo("Error en declaracion", [_nodo(f"Lista invalida: {resto}")])

        return _nodo("Declaracion", [
            _nodo(f"Tipo {tipo}"),
            _nodo("Identificadores", [_nodo(f"Id {ident}") for ident in ids]),
        ])

    asignacion = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", sin_punto_coma)
    if asignacion:
        identificador = asignacion.group(1)
        expresion = asignacion.group(2).strip()

        try:
            arbol_expr = _parsear_expresion(expresion)
        except ValueError as err:
            return _nodo("Error en asignacion", [_nodo(str(err)), _nodo(f"Expresion: {expresion}")])

        return _nodo("Asignacion", [
            _nodo(f"Id {identificador}"),
            _nodo("="),
            _nodo("Expresion", [arbol_expr]),
        ])

    return _nodo("No reconocido", [_nodo(f"Entrada: {sin_punto_coma}")])


def construir_arbol_sintactico(texto):
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    lineas = texto.split("\n")

    hijos_programa = []
    for numero, linea in enumerate(lineas, start=1):
        limpia = _normalizar_linea(linea)
        if not limpia:
            continue
        hijos_programa.append(_nodo(f"Linea {numero}", [_parsear_sentencia(limpia)]))

    if not hijos_programa:
        return _nodo("Programa", [_nodo("Sin sentencias")])

    return _nodo("Programa", hijos_programa)


def construir_arbol_descendente(texto):
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    sentencias = []

    for numero, linea in enumerate(texto.split("\n"), start=1):
        limpia = _normalizar_linea(linea)
        if not limpia:
            continue

        # ── declaración de función Python: def nombre(params):
        m_def = re.match(
            rf"^def\s+({IDENT_RE})\s*\(([^)]*)\)\s*:$",
            limpia,
        )
        if m_def:
            nombre_func = m_def.group(1)
            raw_params = m_def.group(2).strip()
            params_nodes = []
            if raw_params:
                for p in raw_params.split(","):
                    p = p.strip()
                    if p:
                        # param puede ser "tipo nombre" o solo "nombre"
                        partes = p.split()
                        if len(partes) == 2 and partes[0] in TIPOS_VALIDOS:
                            params_nodes.append(_nodo_visual(partes[0], "reservada"))
                            params_nodes.append(_nodo_visual(partes[1], "identificador"))
                        else:
                            params_nodes.append(_nodo_visual(partes[-1], "identificador"))
            sentencias.append({
                "linea": numero,
                "tipo": "decl_funcion",
                "def_node": _nodo_visual("def", "reservada"),
                "nombre_node": _nodo_visual(nombre_func, "identificador"),
                "paren_izq": _nodo_visual("(", "delimitador"),
                "params": params_nodes,
                "paren_der": _nodo_visual(")", "delimitador"),
                "dos_puntos": _nodo_visual(":", "delimitador"),
            })
            continue

        # ── declaración de función C: tipo nombre(params) { o tipo nombre(params);
        m_cfunc = re.match(
            rf"^(int|float|double|char|bool|string|void)\s+({IDENT_RE})\s*\(([^)]*)\)\s*([;{{])$",
            limpia,
        )
        if m_cfunc:
            tipo_ret = m_cfunc.group(1)
            nombre_func = m_cfunc.group(2)
            raw_params = m_cfunc.group(3).strip()
            terminador = m_cfunc.group(4)
            params_nodes = []
            if raw_params:
                for p in raw_params.split(","):
                    p = p.strip()
                    if p:
                        partes = p.split()
                        if len(partes) == 2 and partes[0] in TIPOS_VALIDOS:
                            params_nodes.append(_nodo_visual(partes[0], "reservada"))
                            params_nodes.append(_nodo_visual(partes[1], "identificador"))
                        else:
                            params_nodes.append(_nodo_visual(partes[-1], "identificador"))
            sentencias.append({
                "linea": numero,
                "tipo": "decl_funcion",
                "def_node": _nodo_visual(tipo_ret, "reservada"),
                "nombre_node": _nodo_visual(nombre_func, "identificador"),
                "paren_izq": _nodo_visual("(", "delimitador"),
                "params": params_nodes,
                "paren_der": _nodo_visual(")", "delimitador"),
                "dos_puntos": _nodo_visual(terminador, "delimitador"),
            })
            continue

        if not limpia.endswith(";"):
            sentencias.append({
                "linea": numero,
                "tipo": "error",
                "mensaje": "Falta ';' al final",
                "entrada": limpia,
            })
            continue

        base = limpia[:-1].strip()
        if not base:
            continue

        declaracion = re.match(r"^(int|float|double|char|bool|string)\s+(.+)$", base)
        if declaracion:
            tipo_dato = declaracion.group(1)
            resto = declaracion.group(2).strip()

            if "=" in resto:
                izquierda, derecha = resto.split("=", 1)
                identificador = izquierda.strip()
                expresion = derecha.strip()

                if not re.fullmatch(IDENT_RE, identificador):
                    sentencias.append({
                        "linea": numero,
                        "tipo": "error",
                        "mensaje": "Identificador invalido en declaracion",
                        "entrada": limpia,
                    })
                    continue

                try:
                    expr_ast = _parsear_expresion_visual(expresion)
                except ValueError as err:
                    sentencias.append({
                        "linea": numero,
                        "tipo": "error",
                        "mensaje": str(err),
                        "entrada": limpia,
                    })
                    continue

                sentencias.append({
                    "linea": numero,
                    "tipo": "decl_asig",
                    "tipo_node": _nodo_visual(tipo_dato, "reservada"),
                    "asignacion_node": _nodo_visual("=", "operador"),
                    "identificador_node": _nodo_visual(identificador, "identificador"),
                    "expr": expr_ast,
                    "fin_node": _nodo_visual(";", "delimitador"),
                })
                continue

            identificadores = [p.strip() for p in resto.split(",") if p.strip()]
            if not identificadores or any(not re.fullmatch(IDENT_RE, ident) for ident in identificadores):
                sentencias.append({
                    "linea": numero,
                    "tipo": "error",
                    "mensaje": "Lista de identificadores invalida",
                    "entrada": limpia,
                })
                continue

            sentencias.append({
                "linea": numero,
                "tipo": "decl_lista",
                "tipo_node": _nodo_visual(tipo_dato, "reservada"),
                "identificadores": [_nodo_visual(ident, "identificador") for ident in identificadores],
                "fin_node": _nodo_visual(";", "delimitador"),
            })
            continue

        asignacion = re.match(rf"^({IDENT_RE})\s*=\s*(.+)$", base)
        if asignacion:
            identificador = asignacion.group(1)
            expresion = asignacion.group(2).strip()

            try:
                expr_ast = _parsear_expresion_visual(expresion)
            except ValueError as err:
                sentencias.append({
                    "linea": numero,
                    "tipo": "error",
                    "mensaje": str(err),
                    "entrada": limpia,
                })
                continue

            sentencias.append({
                "linea": numero,
                "tipo": "asignacion",
                "asignacion_node": _nodo_visual("=", "operador"),
                "identificador_node": _nodo_visual(identificador, "identificador"),
                "expr": expr_ast,
                "fin_node": _nodo_visual(";", "delimitador"),
            })
            continue

        sentencias.append({
            "linea": numero,
            "tipo": "error",
            "mensaje": "Sentencia no reconocida",
            "entrada": limpia,
        })

    return sentencias


def _tn(value, role, children=None, final=None):
    return {"value": value, "role": role, "children": children or [], "final": final}


def _ast_a_tn(nodo):
    if nodo["kind"] == "op":
        return _tn(nodo["value"], "operador", [
            _ast_a_tn(nodo["left"]),
            _ast_a_tn(nodo["right"]),
        ])
    return _tn(nodo["value"], nodo["role"], [])


def _rol_desde_tipo_lexico(tipo):
    if tipo == "Palabra reservada":
        return "reservada"
    if tipo in {"Entero", "Flotante", "Cadena de texto"}:
        return "literal"
    if tipo == "Operador":
        return "operador"
    if tipo in {"Caracter especial", "Comilla doble", "Comilla simple"}:
        return "delimitador"
    return "identificador"


def _normalizar_tokens_linea(tokens_linea):
    salida = []
    i = 0

    while i < len(tokens_linea):
        lexema, tipo = tokens_linea[i]
        if tipo in {"Espacio", "Tabulador", "Salto de linea"}:
            i += 1
            continue

        # Une comillas + contenido + comillas en un único literal.
        if (
            tipo in {"Comilla doble", "Comilla simple"}
            and i + 2 < len(tokens_linea)
            and tokens_linea[i + 1][1] == "Cadena de texto"
            and tokens_linea[i + 2][1] == tipo
        ):
            comp = lexema + tokens_linea[i + 1][0] + tokens_linea[i + 2][0]
            salida.append({"lexema": comp, "tipo": "Cadena de texto", "role": "literal"})
            i += 3
            continue

        salida.append({"lexema": lexema, "tipo": tipo, "role": _rol_desde_tipo_lexico(tipo)})
        i += 1

    return salida


def _tokens_a_ast_expresion(tokens_n):
    expr_toks = []
    for t in tokens_n:
        lx = t["lexema"]
        if (
            re.fullmatch(IDENT_RE, lx)
            or re.fullmatch(r"\d+\.\d+|\d+", lx)
            or t["tipo"] == "Cadena de texto"
            or lx in OPERADORES
            or lx in {"(", ")"}
        ):
            expr_toks.append(lx)
        else:
            return None

    if not expr_toks:
        return None

    try:
        postfijo = _a_postfijo(expr_toks)
        ast = _ast_expresion_desde_postfijo(postfijo)
        return _ast_a_tn(ast)
    except ValueError:
        return None


def _agrupar_brackets(tokens_n):
    """Agrupa pares de brackets en un único token con los tokens internos como hijos."""
    ABRE = {"(": ")", "[": "]", "{": "}"}
    result = []
    i = 0
    while i < len(tokens_n):
        t = tokens_n[i]
        lx = t["lexema"]
        if lx in ABRE:
            cierre = ABRE[lx]
            profundidad = 1
            j = i + 1
            while j < len(tokens_n) and profundidad > 0:
                jlx = tokens_n[j]["lexema"]
                if jlx == lx:
                    profundidad += 1
                elif jlx == cierre:
                    profundidad -= 1
                j += 1
            internos = tokens_n[i + 1 : j - 1]
            result.append({
                "lexema": "{}",
                "tipo": "grupo_bracket",
                "role": "delimitador",
                "grupo_hijos": _agrupar_brackets(internos),
            })
            i = j
        elif lx in {")", "]", "}"}:
            result.append({"lexema": "{}", "tipo": t["tipo"], "role": "delimitador"})
            i += 1
        else:
            result.append(t)
            i += 1
    return result


def _encadenar_tokens(tokens_n):
    if not tokens_n:
        return _tn("vacio", "delimitador")

    agrupados = _agrupar_brackets(tokens_n)

    def _hacer_nodo(t):
        if "grupo_hijos" in t:
            hijos = [_hacer_nodo(h) for h in t["grupo_hijos"]]
            return _tn(t["lexema"], t["role"], hijos)
        return _tn(t["lexema"], t["role"])

    raiz = _hacer_nodo(agrupados[0])
    if len(agrupados) == 1:
        return raiz

    # Cadena: cada nodo regular pasa a ser el punto de continuación.
    # Los nodos de grupo (bracket) no se desciende en ellos para la cadena;
    # el siguiente token se añade al mismo nivel (sibling del grupo).
    chain_parent = raiz
    for t in agrupados[1:]:
        nodo = _hacer_nodo(t)
        chain_parent["children"].append(nodo)
        if "grupo_hijos" not in t:
            chain_parent = nodo

    return raiz


def _asignar_final(nodo, valor, rol="delimitador"):
    nodo["final"] = {"value": valor, "role": rol}


def _normalizar_lexema_arbol(lexema):
    if lexema in {"(", ")", "[", "]", "{", "}"}:
        return "{}"
    return lexema


def _etiqueta_arbol(nodo):
    # nodo puede ser una estructura _tn o un dict final {"value", "role"}
    if nodo is None:
        return "?"
    valor_raw = nodo.get("value") if isinstance(nodo, dict) else None
    if valor_raw is None:
        valor_raw = str(nodo.get("value", ""))
    valor = _normalizar_lexema_arbol(str(valor_raw))

    role = nodo.get("role") if isinstance(nodo, dict) else nodo.get("role")
    # Mapa de roles a nombres legibles
    ROLE_NICE = {
        "reservada": "Palabra reservada",
        "identificador": "Identificador",
        "operador": "Operador",
        "literal": "Literal",
        "delimitador": "Delimitador",
    }
    tipo_humano = ROLE_NICE.get(role, None)

    if tipo_humano:
        return f"{valor} ({tipo_humano})"
    return valor if valor else "?"


def _hijos_para_render(nodo):
    hijos = list(nodo.get("children", []))
    final = nodo.get("final")
    if final:
        hijos.append(final)
    return hijos


def _renderizar_arbol_vertical(nodo, prefijo="", es_ultimo=True, raiz=True):
    etiqueta = _etiqueta_arbol(nodo)
    if raiz:
        lineas = [etiqueta]
    else:
        conector = "└── " if es_ultimo else "├── "
        lineas = [prefijo + conector + etiqueta]

    hijos = _hijos_para_render(nodo)
    if not hijos:
        return lineas

    nuevo_prefijo = "" if raiz else prefijo + ("    " if es_ultimo else "│   ")
    for indice, hijo in enumerate(hijos):
        ultimo_hijo = indice == len(hijos) - 1
        lineas.extend(_renderizar_arbol_vertical(hijo, nuevo_prefijo, ultimo_hijo, False))
    return lineas


def renderizar_arbol_vertical(nodo):
    if nodo is None:
        return ""
    return "\n".join(_renderizar_arbol_vertical(nodo))


def _subarbol_izquierdo_asignacion(tokens_izq):
    if not tokens_izq:
        return _tn("?", "delimitador")

    if (
        len(tokens_izq) >= 2
        and tokens_izq[0]["lexema"] in TIPOS_VALIDOS
        and re.fullmatch(IDENT_RE, tokens_izq[1]["lexema"])
    ):
        tipo = _tn(tokens_izq[0]["lexema"], "reservada", [_tn(tokens_izq[1]["lexema"], "identificador")])
        if len(tokens_izq) > 2:
            tipo["children"].append(_encadenar_tokens(tokens_izq[2:]))
        return tipo

    if len(tokens_izq) == 1:
        t = tokens_izq[0]
        return _tn(t["lexema"], t["role"])

    return _encadenar_tokens(tokens_izq)


def _indice_superficie(tokens_n, objetivo):
    profundidad = 0
    for i, t in enumerate(tokens_n):
        lx = t["lexema"]
        if lx == "(":
            profundidad += 1
            continue
        if lx == ")":
            profundidad = max(0, profundidad - 1)
            continue
        if profundidad == 0 and lx == objetivo:
            return i
    return -1


def _construir_nucleo(core):
    if not core:
        return _tn("vacio", "delimitador")

    # def nombre(...)
    if core[0]["lexema"] == "def" and len(core) >= 2:
        nombre = core[1]["lexema"]
        params = []
        ini = next((i for i, t in enumerate(core) if t["lexema"] == "("), -1)
        fin = -1
        if ini != -1:
            # busca ')' cerrando el grupo de parámetros
            profundidad = 0
            for j in range(ini, len(core)):
                if core[j]["lexema"] == "(":
                    profundidad += 1
                elif core[j]["lexema"] == ")":
                    profundidad -= 1
                    if profundidad == 0:
                        fin = j
                        break
        if ini != -1 and fin != -1 and fin > ini:
            for t in core[ini + 1 : fin]:
                if t["lexema"] in {",", "*", "**"}:
                    continue
                params.append(_tn(t["lexema"], t["role"]))

        nodo_nombre = _tn(nombre, "identificador", params)
        return _tn("def", "reservada", [nodo_nombre])

    # if condicion
    if core[0]["lexema"] == "if" and len(core) > 1:
        condicion = _tokens_a_ast_expresion(core[1:])
        if condicion is None:
            condicion = _encadenar_tokens(core[1:])
        return _tn("if", "reservada", [condicion])

    # return expresion
    if core[0]["lexema"] == "return":
        if len(core) == 1:
            return _tn("return", "reservada")
        expr = _tokens_a_ast_expresion(core[1:])
        if expr is None:
            expr = _encadenar_tokens(core[1:])
        return _tn("return", "reservada", [expr])

    # Caso prioritario: asignación solo si '=' está fuera de paréntesis.
    idx_eq = _indice_superficie(core, "=")
    if idx_eq != -1:
        izq = core[:idx_eq]
        der = core[idx_eq + 1 :]
        nodo_izq = _subarbol_izquierdo_asignacion(izq)
        nodo_der = _tokens_a_ast_expresion(der)
        if nodo_der is None:
            nodo_der = _encadenar_tokens(der) if der else _tn("?", "delimitador")
        return _tn("=", "operador", [nodo_izq, nodo_der])

    # Declaracion de lista: tipo a, b, c
    if core[0]["lexema"] in TIPOS_VALIDOS and len(core) > 1:
        hijos = []
        for t in core[1:]:
            if t["lexema"] == ",":
                continue
            hijos.append(_tn(t["lexema"], t["role"]))
        if hijos:
            return _tn(core[0]["lexema"], "reservada", hijos)

    # Expresion pura
    expr = _tokens_a_ast_expresion(core)
    if expr is not None:
        return expr

    # Fallback universal
    return _encadenar_tokens(core)


def _construir_sentencia_desde_tokens(tokens_linea):
    tokens_n = _normalizar_tokens_linea(tokens_linea)
    if not tokens_n:
        return None

    terminadores = {";", ":", "}"}
    terminador = None
    core = tokens_n

    # Soporta cabecera y cuerpo en una misma línea: "def f(...): return ..."
    idx_colon = _indice_superficie(tokens_n, ":")
    if idx_colon != -1 and idx_colon < len(tokens_n) - 1:
        izquierda = tokens_n[:idx_colon]
        derecha = tokens_n[idx_colon + 1 :]
        nodo = _construir_nucleo(izquierda)
        _asignar_final(nodo, ":", "delimitador")
        nodo["_abre_bloque"] = True

        cuerpo = _construir_nucleo(derecha)
        nodo["children"].append(cuerpo)
        return nodo

    if tokens_n[-1]["lexema"] in terminadores:
        terminador = tokens_n[-1]
        core = tokens_n[:-1]

    if not core and terminador is not None:
        return _tn(terminador["lexema"], terminador["role"])

    nodo = _construir_nucleo(core)

    if terminador is not None:
        _asignar_final(nodo, terminador["lexema"], terminador["role"])
        if terminador["lexema"] == ":":
            nodo["_abre_bloque"] = True

    return nodo


def construir_arbol_programa(tokens):
    programa = _tn("Programa", "reservada", [])

    lineas = []
    linea_actual = []
    for lexema, tipo in tokens:
        if tipo == "Salto de linea":
            lineas.append(linea_actual)
            linea_actual = []
            continue
        linea_actual.append((lexema, tipo))
    if linea_actual:
        lineas.append(linea_actual)

    # Stack de bloques por indentación.
    pila = [(-1, programa)]

    for numero_linea, linea_tokens in enumerate(lineas, start=1):
        if not linea_tokens:
            continue

        indent = 0
        idx = 0
        while idx < len(linea_tokens) and linea_tokens[idx][1] in {"Espacio", "Tabulador"}:
            if linea_tokens[idx][1] == "Espacio":
                indent += len(linea_tokens[idx][0])
            else:
                indent += 4
            idx += 1

        nodo = _construir_sentencia_desde_tokens(linea_tokens[idx:])
        if nodo is None:
            continue

        while len(pila) > 1 and indent <= pila[-1][0]:
            pila.pop()

        nodo_linea = _tn(f"Linea {numero_linea}", "delimitador", [nodo])
        pila[-1][1]["children"].append(nodo_linea)

        if nodo.get("_abre_bloque"):
            pila.append((indent, nodo))

    return programa


def renderizar_arbol_grafico(arbol_desc):
    import base64
    from html import escape

    if not arbol_desc:
        return ""

    nodos = []
    aristas = []

    def recorrer(nodo, depth=0, padre=None):
        nodo_id = f"n{len(nodos)}"
        item = {
            "id": nodo_id,
            "label": str(nodo.get("label", "")),
            "children": nodo.get("children", []) or [],
            "depth": depth,
            "x": 0,
            "y": 0,
            "w": max(54, 14 + len(str(nodo.get("label", ""))) * 7),
            "h": 34,
        }
        nodos.append(item)
        if padre is not None:
            aristas.append((padre["id"], nodo_id))
        for hijo in item["children"]:
            recorrer(hijo, depth + 1, item)
        return item

    raiz = recorrer(arbol_desc)

    x_gap = 92
    y_gap = 92
    margen_x = 42
    margen_y = 42
    siguiente_x = [0]

    def asignar_posicion(nodo):
        if not nodo["children"]:
            nodo["x"] = siguiente_x[0] * x_gap
            siguiente_x[0] += 1
        else:
            for hijo in nodo["children"]:
                asignar_posicion(hijo)
            nodo["x"] = sum(h["x"] for h in nodo["children"]) / len(nodo["children"])
        nodo["y"] = nodo["depth"] * y_gap

    asignar_posicion(raiz)

    min_x = min(n["x"] - n["w"] / 2 for n in nodos)
    max_x = max(n["x"] + n["w"] / 2 for n in nodos)
    min_y = min(n["y"] - n["h"] / 2 for n in nodos)
    max_y = max(n["y"] + n["h"] / 2 for n in nodos)

    width = int(max_x - min_x + margen_x * 2)
    height = int(max_y - min_y + margen_y * 2)

    for nodo in nodos:
        nodo["x"] = nodo["x"] - min_x + margen_x
        nodo["y"] = nodo["y"] - min_y + margen_y

    index = {n["id"]: n for n in nodos}
    piezas = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<g fill="none" stroke="#000000" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">',
    ]

    for padre_id, hijo_id in aristas:
        padre = index[padre_id]
        hijo = index[hijo_id]
        x1 = padre["x"]
        y1 = padre["y"] + padre["h"] / 2
        x2 = hijo["x"]
        y2 = hijo["y"] - hijo["h"] / 2
        piezas.append(f'<path d="M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}"/>')

    piezas.append('</g>')

    for nodo in nodos:
        piezas.append(
            f'<ellipse cx="{nodo["x"]:.1f}" cy="{nodo["y"]:.1f}" rx="{nodo["w"] / 2:.1f}" ry="{nodo["h"] / 2:.1f}" '
            'fill="#ffffff" stroke="#000000" stroke-width="1.6"/>'
        )
        piezas.append(
            f'<text x="{nodo["x"]:.1f}" y="{nodo["y"] + 4:.1f}" text-anchor="middle" '
            'font-family="Arial, Helvetica, sans-serif" font-size="15" fill="#000000">'
            f'{escape(nodo["label"])}</text>'
        )

    piezas.append('</svg>')
    svg = ''.join(piezas)
    svg_base64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
    return f"data:image/svg+xml;base64,{svg_base64}"
