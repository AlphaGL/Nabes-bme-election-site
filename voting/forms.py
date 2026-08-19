from django import forms
from .models import Position, Contestant, Student, Vote


from .models import Student
from django.core.exceptions import ValidationError

class PasswordResetForm(forms.Form):
    reg_number = forms.CharField(max_length=100)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_reg_number(self):
        reg_number = self.cleaned_data.get('reg_number')
        if not Student.objects.filter(reg_number=reg_number).exists():
            raise ValidationError("User with this registration number does not exist.")
        return reg_number

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise ValidationError("Passwords do not match.")
        return cleaned_data
    




class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'importance']  # Adjust fields as necessary


class ContestantForm(forms.ModelForm):
    class Meta:
        model = Contestant
        fields = ['position', 'name', 'image']  # Include the image field

class AccessCodeForm(forms.Form):
    access_code = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter Access Code'}),
        label='Access Code'
    )


class ResetAllForm(forms.Form):
    access_code = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter access code'}),
        label="Access Code"
    )
    confirm_reset = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'style': 'width: 18px; height: 18px;'}),
        label="Confirm Reset",
        required=True
    )

class VoteForm(forms.Form):
    position = forms.ModelChoiceField(queryset=Position.objects.all(), required=True)
    contestant = forms.ModelChoiceField(queryset=Contestant.objects.none(), required=True)

    def __init__(self, *args, **kwargs):
        position_id = kwargs.pop('position_id', None)
        super().__init__(*args, **kwargs)
        if position_id:
            # Filter contestants based on the provided position ID
            self.fields['contestant'].queryset = Contestant.objects.filter(position_id=position_id)

    def clean(self):
        cleaned_data = super().clean()
        position = cleaned_data.get("position")
        contestant = cleaned_data.get("contestant")

        if position and contestant:
            # Check if the user has already voted for the selected position and contestant
            if Vote.objects.filter(position=position, contestant=contestant).exists():
                raise forms.ValidationError("You have already voted for this contestant in this position.")
        
        return cleaned_data
    

    
class RegisterForm(forms.Form):
    reg_number = forms.CharField(
        max_length=100,
        label='Registration Number',
        widget=forms.TextInput(attrs={'placeholder': 'Enter your registration number', 'autocomplete': 'username'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Choose a password', 'autocomplete': 'new-password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password', 'autocomplete': 'new-password'})
    )

    student = None

    def clean_reg_number(self):
        reg_number = self.cleaned_data.get('reg_number', '').strip()
        student = Student.objects.filter(reg_number=reg_number).first()
        if not student:
            raise ValidationError(
                "This registration number isn't on our approved voters list. "
                "Contact the department if you believe this is a mistake."
            )
        if student.has_usable_password():
            raise ValidationError(
                "This registration number is already registered. Please log in, "
                "or use 'Reset it here' if you forgot your password."
            )
        self.student = student
        return reg_number

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")
        if password1 and len(password1) < 4:
            raise ValidationError("Password must be at least 4 characters long.")
        return cleaned_data
