from django import forms
from django.core.validators import RegexValidator


class DireccionEntregaForm(forms.Form):
    direccion = forms.CharField(
        label='Dirección de entrega',
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'street-address',
                'placeholder': 'Calle, carrera, número y barrio',
            }
        ),
        error_messages={'required': 'Ingresa la dirección de entrega.'},
    )
    codigo_postal = forms.CharField(
        label='Código postal',
        max_length=6,
        validators=[
            RegexValidator(
                regex=r'^\d{6}$',
                message='Ingresa un código postal colombiano de 6 dígitos.',
            )
        ],
        widget=forms.TextInput(
            attrs={
                'inputmode': 'numeric',
                'pattern': r'\d{6}',
                'autocomplete': 'postal-code',
                'placeholder': '000000',
            }
        ),
        error_messages={'required': 'Ingresa el código postal.'},
    )
    ciudad = forms.CharField(
        label='Ciudad',
        max_length=100,
        widget=forms.TextInput(attrs={'autocomplete': 'address-level2'}),
        error_messages={'required': 'Ingresa la ciudad.'},
    )
    comuna = forms.CharField(
        label='Comuna',
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'address-level3',
                'placeholder': 'Número o nombre de la comuna',
            }
        ),
        error_messages={'required': 'Ingresa la comuna.'},
    )
    detalles_domicilio = forms.CharField(
        label='Detalles adicionales (opcional)',
        max_length=250,
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'placeholder': 'Unidad, torre, casa, conjunto, indicaciones para llegar…',
            }
        ),
    )
    acepta_uso_datos = forms.BooleanField(
        label='Autorizo guardar estos datos para gestionar esta solicitud de pedido.',
        required=True,
        error_messages={
            'required': 'Debes autorizar el uso de los datos para enviar la solicitud.'
        },
    )
