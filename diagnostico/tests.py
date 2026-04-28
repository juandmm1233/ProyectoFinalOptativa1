"""Pruebas básicas para la app `diagnostico`."""

from django.test import TestCase
from django.urls import reverse


class DiagnosticoViewsTests(TestCase):
    def test_index_renderiza_formulario(self) -> None:
        response = self.client.get(reverse("diagnostico:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BioCell AI")

    def test_predecir_requiere_post(self) -> None:
        response = self.client.get(reverse("diagnostico:predecir"))
        # La vista solo acepta POST.
        self.assertEqual(response.status_code, 405)
