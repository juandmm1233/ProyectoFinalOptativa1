"""
Formulario para ingresar las características morfológicas de la célula.

Las cuatro features son las que espera el modelo Random Forest entrenado:
Area, Perímetro, Concavidad y Textura.
"""

from __future__ import annotations

from django import forms


class CelulaForm(forms.Form):
    """Formulario con validación para los datos morfológicos de una célula."""

    area = forms.FloatField(
        label="Área (μm²)",
        min_value=0.0,
        max_value=10000.0,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "step": "0.01",
                "placeholder": "Ej: 654.89",
                "autocomplete": "off",
            }
        ),
        help_text="Área total de la célula en micrómetros cuadrados.",
    )

    perimetro = forms.FloatField(
        label="Perímetro (μm)",
        min_value=0.0,
        max_value=1000.0,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "step": "0.01",
                "placeholder": "Ej: 98.45",
                "autocomplete": "off",
            }
        ),
        help_text="Perímetro del contorno celular.",
    )

    concavidad = forms.FloatField(
        label="Concavidad",
        min_value=0.0,
        max_value=1.0,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "step": "0.0001",
                "placeholder": "Ej: 0.1245",
                "autocomplete": "off",
            }
        ),
        help_text="Severidad de las porciones cóncavas del contorno (0 a 1).",
    )

    textura = forms.FloatField(
        label="Textura",
        min_value=0.0,
        max_value=100.0,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "step": "0.01",
                "placeholder": "Ej: 17.33",
                "autocomplete": "off",
            }
        ),
        help_text="Desviación estándar de los valores de gris en la imagen.",
    )

    def clean(self) -> dict:
        """Validación adicional: ningún valor puede ser negativo."""
        cleaned = super().clean()
        for field, value in cleaned.items():
            if value is not None and value < 0:
                self.add_error(field, "El valor no puede ser negativo.")
        return cleaned
