#!/usr/bin/env python
"""Utilidad de línea de comandos para tareas administrativas de Django."""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "biocell_ai.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y disponible "
            "en tu entorno virtual? ¿Olvidaste activarlo?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
