"""Formulier voor de herroepingsfunctie (voorwaarden, artikel 10)."""
from django import forms


class WithdrawalForm(forms.Form):
    name = forms.CharField(label="Je naam", max_length=120)
    email = forms.EmailField(label="Je e-mailadres", help_text="Hier sturen we de ontvangstbevestiging naartoe.")
    order_number = forms.CharField(label="Bestelnummer", max_length=40, required=False, help_text="Bijvoorbeeld VL26-00021. Staat in je bestelbevestiging.")
    product = forms.CharField(label="Product of dienst (optioneel)", max_length=200, required=False)
    order_date = forms.CharField(label="Besteldatum (optioneel)", max_length=40, required=False)
    note = forms.CharField(label="Toelichting (optioneel)", required=False, widget=forms.Textarea(attrs={"rows": 3}), max_length=2000)

    def clean(self):
        data = super().clean()
        if not (data.get("order_number") or data.get("product")):
            raise forms.ValidationError("Vul je bestelnummer in, of omschrijf welk product of welke dienst je herroept.")
        return data
