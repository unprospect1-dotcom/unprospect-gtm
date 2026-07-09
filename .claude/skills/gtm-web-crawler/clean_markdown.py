"""Limpieza de markdown crawleado -> texto útil para el LLM (sin ruido).

Quita lo que confunde y llena de tokens inútiles:
  - imágenes `![alt](url)` (puro ruido),
  - convierte links `[texto](url)` -> `texto` (tira la URL, deja el ancla),
  - dedup de líneas repetidas (menús/footers que se repiten en cada página),
  - basura de UI/formularios (Saltar al contenido, Enviando formulario, cookies…),
  - colapsa espacios/blancos.
Conserva encabezados de sección `# /ruta` para que se vea de qué página salió cada bloque.
"""
import re

UI_NOISE = re.compile(r"""^\s*(
    saltar\ al\ contenido | ir\ al\ contenido | skip\ to\ content |
    enviando\ formulario.* | formulario\ recibido.* | el\ servidor\ ha\ detectado.* |
    introducir\ (nombre|correo|mensaje).* | escriba\ su\ mensaje.* | enviar |
    men[uú] | toggle\ navigation | cargando.* | loading.* |
    aceptar\ cookies.* | usamos\ cookies.* | this\ site\ uses\ cookies.* |
    \d+ | x | ← | → | »  | «
)\s*$""", re.IGNORECASE | re.VERBOSE)

def clean_markdown(md: str) -> str:
    if not md:
        return ""
    # 1. fuera imágenes
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    # 2. links -> solo el texto ancla
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    # 3. URLs sueltas
    md = re.sub(r"https?://\S+", "", md)

    out, seen = [], set()
    for raw in md.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw).strip(" \t*>-|")
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        if UI_NOISE.match(line):
            continue
        # líneas triviales (solo símbolos o < 3 letras) fuera
        if len(re.sub(r"[^0-9A-Za-zÁÉÍÓÚÑáéíóúñ ]", "", line)) < 3:
            continue
        # dedup global exacto (menús/footers repetidos), salvo encabezados de sección
        keyable = not line.startswith("# /")
        if keyable and line in seen:
            continue
        if keyable:
            seen.add(line)
        out.append(line)

    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

if __name__ == "__main__":
    import sys, json
    d = json.load(open(sys.argv[1]))
    print(clean_markdown(d.get("combined_markdown", "")))
