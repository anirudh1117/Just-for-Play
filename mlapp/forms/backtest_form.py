from django import forms

class BacktestRunForm(forms.Form):
    symbols = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "TATAMOTORS,TATASTEEL,…"}),
        label="Symbols (comma-separated)"
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    strict_mode = forms.BooleanField(
        required=False,
        initial=True,
        label="Strict TP/SL Mode?"
    )
