import re


def format_to_html(text):
    html_output = ""

    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()

        # Detectar texto en negrita y formatearlo
        if "**" in line:
            html_output += f"<p>{format_bold_text(line)}</p>"
        else:
            # Cualquier otro texto (párrafos)
            html_output += f"<p>{line}</p>"

    return html_output


def format_bold_text(line):
    # Reemplazar '**texto**' con '<strong>texto</strong>'
    return re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
