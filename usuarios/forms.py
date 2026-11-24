from django import forms
from django.core.validators import RegexValidator

from .models import Flor


class FlorInventarioForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields.pop('cantidad')

    class Meta:
        model = Flor
        fields = ('nombre', 'categoria', 'descripcion', 'precio', 'cantidad', 'imagen_url')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'precio': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'cantidad': forms.NumberInput(attrs={'min': '0', 'step': '1'}),
            'imagen_url': forms.URLInput(attrs={'placeholder': 'https://…'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        duplicados = Flor.objects.filter(nombre__iexact=nombre, activo=True)
        if self.instance.pk:
            duplicados = duplicados.exclude(pk=self.instance.pk)
        if duplicados.exists():
            raise forms.ValidationError('Ya existe una flor activa con ese nombre.')
        return nombre

    def clean_categoria(self):
        return self.cleaned_data['categoria'].strip()

    def clean_descripcion(self):
        return self.cleaned_data['descripcion'].strip()


class CantidadFlorForm(forms.Form):
    cantidad = forms.IntegerField(
        label='Unidades disponibles',
        min_value=0,
        max_value=2_147_483_647,
        widget=forms.NumberInput(attrs={'min': '0', 'step': '1'}),
    )


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
