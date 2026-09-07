def html_to_pdf(html_string: str) -> bytes:
    # Imported lazily: WeasyPrint needs native GTK/Pango/Cairo libraries that
    # aren't available on every dev machine (e.g. plain Windows without them).
    # Importing it at module load time would break the whole app (migrations,
    # admin, etc.) wherever those libs are missing — see CLAUDE.md/README.
    import weasyprint

    return weasyprint.HTML(string=html_string).write_pdf()
