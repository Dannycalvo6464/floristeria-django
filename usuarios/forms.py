import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import Flor


class PrecioPesosColombianosField(forms.IntegerField):
    default_error_messages = {
        'invalid': 'Ingresa un precio en pesos enteros, por ejemplo 12.000.',
        'min_value': 'El precio debe ser de al menos $1 COP.',
    }

    def __init__(self, **kwargs):
        super().__init__(
            min_value=1,
            widget=forms.TextInput(
                attrs={
                    'inputmode': 'numeric',
                    'autocomplete': 'off',
                    'placeholder': 'Ej. 12.000',
                }
            ),
            **kwargs,
        )

    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith('$'):
                value = value[1:].strip()
            if not re.fullmatch(r'(?:\d+|\d{1,3}(?:\.\d{3})+)', value):
                raise forms.ValidationError(
                    self.error_messages['invalid'],
                    code='invalid',
                )
            value = value.replace('.', '')
        return super().to_python(value)

    def prepare_value(self, value):
        if value in self.empty_values:
            return value
        try:
            decimal_amount = Decimal(str(value))
        except InvalidOperation:
            return value
        if decimal_amount != decimal_amount.to_integral_value():
            return value
        amount = int(decimal_amount)
        return f'{amount:,}'.replace(',', '.')


class PerfilUsuarioForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre',
        max_length=100,
        widget=forms.TextInput(attrs={'autocomplete': 'name'}),
    )
    direccion = forms.CharField(
        label='Dirección',
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'street-address',
                'placeholder': 'Calle, carrera, número y barrio',
            }
        ),
    )
    contrasena_actual = forms.CharField(
        label='Contraseña actual',
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'current-password'}
        ),
    )
    nueva_contrasena = forms.CharField(
        label='Nueva contraseña',
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'new-password'}
        ),
    )
    confirmar_contrasena = forms.CharField(
        label='Confirmar nueva contraseña',
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'new-password'}
        ),
    )

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].initial = usuario.nombre
        self.fields['direccion'].initial = usuario.direccion
        self.usuario = usuario

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('contrasena_actual')
        new_password = cleaned_data.get('nueva_contrasena')
        confirmation = cleaned_data.get('confirmar_contrasena')

        if not any((current_password, new_password, confirmation)):
            return cleaned_data

        if not current_password:
            self.add_error('contrasena_actual', 'Ingresa tu contraseña actual.')
        if not new_password:
            self.add_error('nueva_contrasena', 'Ingresa una nueva contraseña.')
        if not confirmation:
            self.add_error(
                'confirmar_contrasena',
                'Confirma tu nueva contraseña.',
            )
        if new_password and confirmation and new_password != confirmation:
            self.add_error(
                'confirmar_contrasena',
                'Las contraseñas no coinciden.',
            )
        if new_password:
            try:
                validate_password(new_password, user=self.usuario)
            except ValidationError as error:
                self.add_error('nueva_contrasena', error)

        return cleaned_data


class FlorInventarioForm(forms.ModelForm):
    precio = PrecioPesosColombianosField(
        label='Precio (COP)',
        help_text='Ingresa pesos enteros. Ejemplo: 12.000 pesos.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields.pop('cantidad')

    class Meta:
        model = Flor
        fields = (
            'nombre',
            'categoria',
            'descripcion',
            'precio',
            'cantidad',
            'imagen_url',
            'imagen_credito',
            'imagen_fuente',
        )
        labels = {
            'imagen_credito': 'Crédito de la imagen',
            'imagen_fuente': 'Fuente y licencia de la imagen',
        }
        help_texts = {
            'imagen_credito': 'Indica el autor y la licencia mostrados en la fuente.',
            'imagen_fuente': 'Enlace a la página de origen de la imagen.',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'cantidad': forms.NumberInput(attrs={'min': '0', 'step': '1'}),
            'imagen_url': forms.URLInput(attrs={'placeholder': 'https://…'}),
            'imagen_credito': forms.TextInput(attrs={'placeholder': 'Autor y licencia'}),
            'imagen_fuente': forms.URLInput(attrs={'placeholder': 'https://commons.wikimedia.org/…'}),
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
