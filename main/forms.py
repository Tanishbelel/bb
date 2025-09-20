# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from django.contrib.auth import get_user_model
from .models import Budget, BudgetCategory, Expense, FinancialGoal, QuizQuestion, UserFraudProgress

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """Extended user registration form"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your phone number'
    }))
    age = forms.IntegerField(min_value=16, max_value=35, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your age'
    }))
    occupation = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your occupation'
    }))
    monthly_income = forms.DecimalField(max_digits=10, decimal_places=2, required=False, 
                                      widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your monthly income (optional)'
    }))
    financial_experience = forms.ChoiceField(
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'age', 'occupation', 
                 'monthly_income', 'financial_experience', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

class UserProfileForm(forms.ModelForm):
    """User profile update form"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'age', 
                 'occupation', 'monthly_income', 'financial_experience')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_income': forms.NumberInput(attrs={'class': 'form-control'}),
            'financial_experience': forms.Select(attrs={'class': 'form-control'}),
        }

class BudgetForm(forms.ModelForm):
    """Budget creation form"""
    class Meta:
        model = Budget
        fields = ('name', 'total_amount', 'start_date', 'end_date')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Monthly Budget, Travel Fund'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter budget amount',
                'step': '0.01'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError('End date must be after start date.')
            if start_date < date.today():
                raise ValidationError('Start date cannot be in the past.')
        
        return cleaned_data

class BudgetCategoryForm(forms.ModelForm):
    """Budget category form"""
    class Meta:
        model = BudgetCategory
        fields = ('name', 'allocated_amount')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Food, Transportation, Entertainment'
            }),
            'allocated_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter allocated amount',
                'step': '0.01'
            }),
        }

class ExpenseForm(forms.ModelForm):
    """Expense tracking form"""
    class Meta:
        model = Expense
        fields = ('description', 'amount', 'date', 'category', 'is_recurring')
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What did you spend on?'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'step': '0.01'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_recurring': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['category'].queryset = BudgetCategory.objects.filter(
                budget__user=user,
                budget__is_active=True
            )
        
        # Set default date to today
        self.fields['date'].initial = date.today()

class FinancialGoalForm(forms.ModelForm):
    """Financial goal form"""
    class Meta:
        model = FinancialGoal
        fields = ('title', 'goal_type', 'target_amount', 'target_date')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Emergency Fund, New Laptop, Trip to Goa'
            }),
            'goal_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'target_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter target amount',
                'step': '0.01'
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean_target_date(self):
        target_date = self.cleaned_data['target_date']
        if target_date <= date.today():
            raise ValidationError('Target date must be in the future.')
        return target_date
    
    def clean_target_amount(self):
        target_amount = self.cleaned_data['target_amount']
        if target_amount <= 0:
            raise ValidationError('Target amount must be greater than zero.')
        return target_amount

class GoalContributionForm(forms.Form):
    """Form for contributing to financial goals"""
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter contribution amount',
            'step': '0.01'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.goal = kwargs.pop('goal', None)
        super().__init__(*args, **kwargs)
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if self.goal:
            remaining_amount = self.goal.target_amount - self.goal.saved_amount
            if amount > remaining_amount:
                raise ValidationError(f'Amount exceeds remaining goal amount of ₹{remaining_amount}')
        return amount

class StockTradeForm(forms.Form):
    """Stock trading form"""
    TRANSACTION_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter quantity'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.stock = kwargs.pop('stock', None)
        self.portfolio = kwargs.pop('portfolio', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        quantity = cleaned_data.get('quantity')
        
        if self.stock and self.portfolio and quantity:
            if transaction_type == 'buy':
                required_amount = quantity * self.stock.current_price
                if required_amount > self.portfolio.virtual_cash:
                    raise ValidationError('Insufficient funds for this purchase.')
            
            elif transaction_type == 'sell':
                holding = self.portfolio.holdings.filter(stock=self.stock).first()
                if not holding or holding.quantity < quantity:
                    available = holding.quantity if holding else 0
                    raise ValidationError(f'You only have {available} shares available to sell.')
        
        return cleaned_data

class QuizResponseForm(forms.Form):
    """Dynamic quiz response form"""
    def __init__(self, *args, **kwargs):
        quiz = kwargs.pop('quiz', None)
        super().__init__(*args, **kwargs)
        
        if quiz:
            for question in quiz.questions.all():
                choices = [
                    ('A', question.option_a),
                    ('B', question.option_b),
                    ('C', question.option_c),
                    ('D', question.option_d),
                ]
                self.fields[f'question_{question.id}'] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    label=question.question_text,
                    required=True
                )

class FraudScenarioResponseForm(forms.Form):
    """Fraud scenario response form"""
    user_response = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Analyze this scenario. What are the red flags? How would you respond?'
        }),
        label='Your Analysis',
        help_text='Identify the warning signs and explain how you would handle this situation.',
        min_length=50,
        max_length=1000
    )

class ContactForm(forms.Form):
    """Contact form for support"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message'
        })
    )

class SearchForm(forms.Form):
    """Search form for stocks and content"""
    query = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search stocks, companies, or topics...',
            'autocomplete': 'off'
        }),
        required=False
    )
    
    category = forms.ChoiceField(
        choices=[
            ('', 'All Categories'),
            ('stocks', 'Stocks'),
            ('modules', 'Learning Modules'),
            ('fraud', 'Fraud Scenarios'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )