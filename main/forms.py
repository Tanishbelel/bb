from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from main.models import User, Budget, BudgetCategory, Expense, FinancialGoal

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    age = forms.IntegerField(
        required=False,
        validators=[MinValueValidator(16), MaxValueValidator(35)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your age',
            'min': '16',
            'max': '35'
        })
    )
    occupation = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your occupation'
        })
    )
    monthly_income = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your monthly income',
            'step': '0.01'
        })
    )
    financial_experience = forms.ChoiceField(
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone_number', 
                 'age', 'occupation', 'monthly_income', 'financial_experience')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'age', 'occupation', 'monthly_income', 'financial_experience']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter age',
                'min': '16',
                'max': '35'
            }),
            'occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter occupation'
            }),
            'monthly_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter monthly income',
                'step': '0.01'
            }),
            'financial_experience': forms.Select(attrs={
                'class': 'form-select'
            })
        }

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['name', 'total_amount', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Budget name (e.g., Monthly Budget)'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Total budget amount',
                'step': '0.01'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'amount', 'date', 'category', 'is_recurring']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Expense description'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Amount spent',
                'step': '0.01'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_recurring': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class FinancialGoalForm(forms.ModelForm):
    class Meta:
        model = FinancialGoal
        fields = ['title', 'goal_type', 'target_amount', 'target_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Goal title (e.g., Emergency Fund)'
            }),
            'goal_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'target_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Target amount',
                'step': '0.01'
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }

class QuizResponseForm(forms.Form):
    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for question in questions:
            choices = [
                ('A', question.option_a),
                ('B', question.option_b),
                ('C', question.option_c),
                ('D', question.option_d),
            ]
            self.fields[f'question_{question.id}'] = forms.ChoiceField(
                label=question.question_text,
                choices=choices,
                widget=forms.RadioSelect(attrs={
                    'class': 'form-check-input'
                }),
                required=True
            )