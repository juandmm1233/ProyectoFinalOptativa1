from __future__ import annotations
from django import forms

class CelulaForm(forms.Form):

    # Morfología principal
    cell_diameter_um = forms.FloatField(label="Diámetro celular (μm)", min_value=0.0, max_value=100.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.01","placeholder":"Ej: 12.5"}))
    nucleus_area_pct = forms.FloatField(label="Área núcleo (%)", min_value=0.0, max_value=100.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.01","placeholder":"Ej: 35.2"}))
    chromatin_density = forms.FloatField(label="Densidad cromatina", min_value=0.0, max_value=10.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.001","placeholder":"Ej: 2.45"}))
    cytoplasm_ratio = forms.FloatField(label="Ratio citoplasma", min_value=0.0, max_value=5.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.001","placeholder":"Ej: 1.2"}))
    circularity = forms.FloatField(label="Circularidad", min_value=0.0, max_value=1.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.001","placeholder":"Ej: 0.85"}))
    eccentricity = forms.FloatField(label="Excentricidad", min_value=0.0, max_value=1.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.001","placeholder":"Ej: 0.32"}))
    granularity_score = forms.FloatField(label="Granularidad", min_value=0.0, max_value=10.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.001","placeholder":"Ej: 1.8"}))
    lobularity_score = forms.FloatField(label="Lobularidad", min_value=0.0, max_value=10.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.001","placeholder":"Ej: 2.1"}))
    membrane_smoothness = forms.FloatField(label="Suavidad membrana", min_value=0.0, max_value=1.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.001","placeholder":"Ej: 0.75"}))
    cell_area_px = forms.FloatField(label="Área celular (px)", min_value=0.0, max_value=100000.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"1","placeholder":"Ej: 1250"}))
    perimeter_px = forms.FloatField(label="Perímetro (px)", min_value=0.0, max_value=5000.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"1","placeholder":"Ej: 145"}))

    # Color
    mean_r = forms.FloatField(label="Color medio R", min_value=0.0, max_value=255.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"1","placeholder":"Ej: 180"}))
    mean_g = forms.FloatField(label="Color medio G", min_value=0.0, max_value=255.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"1","placeholder":"Ej: 120"}))
    mean_b = forms.FloatField(label="Color medio B", min_value=0.0, max_value=255.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"1","placeholder":"Ej: 95"}))
    stain_intensity = forms.FloatField(label="Intensidad tinción", min_value=0.0, max_value=10.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.001","placeholder":"Ej: 3.2"}))

    # Datos clínicos
    wbc_count_per_ul = forms.FloatField(label="Leucocitos (WBC/μL)", min_value=0.0, max_value=100000.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"1","placeholder":"Ej: 7500"}))
    rbc_count_millions_per_ul = forms.FloatField(label="Eritrocitos (RBC millones/μL)", min_value=0.0, max_value=10.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.01","placeholder":"Ej: 4.8"}))
    hemoglobin_g_dl = forms.FloatField(label="Hemoglobina (g/dL)", min_value=0.0, max_value=25.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.1","placeholder":"Ej: 14.0"}))
    hematocrit_pct = forms.FloatField(label="Hematocrito (%)", min_value=0.0, max_value=100.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.1","placeholder":"Ej: 42.0"}))
    platelet_count_per_ul = forms.FloatField(label="Plaquetas (/μL)", min_value=0.0, max_value=1000000.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"1","placeholder":"Ej: 250000"}))
    mcv_fl = forms.FloatField(label="VCM - MCV (fL)", min_value=0.0, max_value=200.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.1","placeholder":"Ej: 90.0"}))
    mchc_g_dl = forms.FloatField(label="CHCM - MCHC (g/dL)", min_value=0.0, max_value=50.0,
        widget=forms.NumberInput(attrs={"class":"form-input","step":"0.1","placeholder":"Ej: 33.0"}))

    # Demografía
    patient_age_group = forms.ChoiceField(label="Grupo de edad", choices=[
        (0, "Pediátrico (0-17)"),
        (1, "Adulto joven (18-35)"),
        (2, "Adulto (36-60)"),
        (3, "Adulto mayor (60+)"),
    ], widget=forms.Select(attrs={"class":"form-input"}))

    patient_sex = forms.ChoiceField(label="Sexo", choices=[
        (0, "Femenino"),
        (1, "Masculino"),
    ], widget=forms.Select(attrs={"class":"form-input"}))