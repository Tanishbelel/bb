# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal
import json
from datetime import datetime, timedelta
from django.db import transaction, IntegrityError

from main.models import (
    User, UserProfile, LearningModule, UserProgress, VirtualPortfolio,
    Stock, VirtualTransaction, Holding, Budget, BudgetCategory, Expense,
    FraudScenario, UserFraudProgress, FinancialGoal, Quiz, QuizQuestion
)
from main.forms import (
    UserRegistrationForm, UserProfileForm, BudgetForm, ExpenseForm,
    FinancialGoalForm, QuizResponseForm
)

def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    context = {
        'total_users': User.objects.count(),
        'total_modules': LearningModule.objects.filter(is_active=True).count(),
        'total_scenarios': FraudScenario.objects.filter(is_active=True).count(),
    }
    return render(request, 'home.html', context)

def register(request):
    """User registration view with debugging"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        print("Registration POST request received")  # Debug
        print("POST data:", request.POST)  # Debug
        
        form = UserRegistrationForm(request.POST)
        print("Form created")  # Debug
        
        if form.is_valid():
            print("Form is valid")  # Debug
            try:
                with transaction.atomic():  # Ensure atomic transaction
                    # Save the user
                    user = form.save(commit=False)
                    print(f"User object created: {user.username}")  # Debug
                    
                    # Set additional fields if they exist
                    if hasattr(form, 'cleaned_data'):
                        user.email = form.cleaned_data.get('email', '')
                        user.phone_number = form.cleaned_data.get('phone_number', '')
                        user.age = form.cleaned_data.get('age')
                        user.occupation = form.cleaned_data.get('occupation', '')
                        user.monthly_income = form.cleaned_data.get('monthly_income') or Decimal('0.00')
                        user.financial_experience = form.cleaned_data.get('financial_experience', 'beginner')
                    
                    user.save()
                    print(f"User saved successfully: {user.id}")  # Debug
                    
                    # Create user profile
                    profile, created = UserProfile.objects.get_or_create(user=user)
                    print(f"Profile created: {created}")  # Debug
                    
                    # Create virtual portfolio
                    portfolio, created = VirtualPortfolio.objects.get_or_create(
                        user=user,
                        defaults={'virtual_cash': Decimal('100000.00')}
                    )
                    print(f"Portfolio created: {created}")  # Debug
                    
                    messages.success(request, f'Account created for {user.username}! You can now log in.')
                    return redirect('login')
                    
            except IntegrityError as e:
                print(f"IntegrityError during registration: {e}")  # Debug
                if 'UNIQUE constraint failed' in str(e):
                    if 'username' in str(e):
                        messages.error(request, 'Username already exists. Please choose a different one.')
                    elif 'email' in str(e):
                        messages.error(request, 'Email already registered. Please use a different email.')
                    elif 'phone_number' in str(e):
                        messages.error(request, 'Phone number already registered.')
                    else:
                        messages.error(request, 'Registration failed due to duplicate data.')
                else:
                    messages.error(request, f'Database error: {str(e)}')
                    
            except Exception as e:
                print(f"Unexpected error during registration: {e}")  # Debug
                print(f"Traceback: {traceback.format_exc()}")  # Debug
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            print("Form is not valid")  # Debug
            print("Form errors:", form.errors)  # Debug
            # Display form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def dashboard(request):
    """User dashboard view"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    portfolio = get_object_or_404(VirtualPortfolio, user=user)
    
    # Get user progress
    completed_modules = UserProgress.objects.filter(user=user, is_completed=True).count()
    total_modules = LearningModule.objects.filter(is_active=True).count()
    
    # Get recent transactions
    recent_transactions = VirtualTransaction.objects.filter(portfolio=portfolio)[:5]
    
    # Get active goals
    active_goals = FinancialGoal.objects.filter(user=user, is_achieved=False)[:3]
    
    # Get monthly expenses
    current_month = timezone.now().month
    monthly_expenses = Expense.objects.filter(
        user=user,
        date__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'profile': profile,
        'portfolio': portfolio,
        'completed_modules': completed_modules,
        'total_modules': total_modules,
        'progress_percentage': (completed_modules / total_modules * 100) if total_modules > 0 else 0,
        'recent_transactions': recent_transactions,
        'active_goals': active_goals,
        'monthly_expenses': monthly_expenses,
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def learning_modules(request):
    """Learning modules list view"""
    modules = LearningModule.objects.filter(is_active=True)
    user_progress = UserProgress.objects.filter(user=request.user).values_list('module_id', 'is_completed')
    progress_dict = {module_id: completed for module_id, completed in user_progress}
    
    context = {
        'modules': modules,
        'progress_dict': progress_dict,
    }
    return render(request, 'modules.html', context)

@login_required
def module_detail(request, module_id):
    """Individual module detail view"""
    module = get_object_or_404(LearningModule, id=module_id, is_active=True)
    
    # Get or create user progress
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        module=module
    )
    
    context = {
        'module': module,
        'progress': progress,
    }
    
    return render(request, 'module_detail.html', context)

@login_required
def complete_module(request, module_id):
    """Mark module as completed"""
    if request.method == 'POST':
        module = get_object_or_404(LearningModule, id=module_id)
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            module=module
        )
        
        if not progress.is_completed:
            progress.is_completed = True
            progress.completion_date = timezone.now()
            progress.save()
            
            # Update user profile points
            profile = request.user.profile
            profile.total_points += module.points_reward
            profile.save()
            
            messages.success(request, f'Module completed! You earned {module.points_reward} points.')
        
        return redirect('module_detail', module_id=module_id)
    
    return redirect('learning_modules')

@login_required
def take_quiz(request, module_id):
    """Quiz taking view"""
    module = get_object_or_404(LearningModule, id=module_id)
    quiz = get_object_or_404(Quiz, module=module)
    questions = quiz.questions.all()
    
    if request.method == 'POST':
        score = 0
        total_questions = questions.count()
        
        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}')
            if user_answer == question.correct_answer:
                score += 1
        
        percentage_score = (score / total_questions * 100) if total_questions > 0 else 0
        
        # Update progress
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            module=module
        )
        progress.quiz_score = percentage_score
        progress.save()
        
        if percentage_score >= quiz.passing_score:
            messages.success(request, f'Congratulations! You passed with {percentage_score:.1f}%')
            return redirect('complete_module', module_id=module_id)
        else:
            messages.error(request, f'You scored {percentage_score:.1f}%. You need {quiz.passing_score}% to pass.')
    
    context = {
        'module': module,
        'quiz': quiz,
        'questions': questions,
    }
    
    return render(request, 'quiz.html', context)

@login_required
def portfolio_view(request):
    """Virtual portfolio view"""
    portfolio = get_object_or_404(VirtualPortfolio, user=request.user)
    holdings = portfolio.holdings.all()
    recent_transactions = portfolio.transactions.all()[:10]
    
    # Update current values for holdings
    for holding in holdings:
        holding.current_value = holding.quantity * holding.stock.current_price
        holding.save()
    
    # Update portfolio current value
    total_current_value = holdings.aggregate(
        total=Sum('current_value')
    )['total'] or 0
    
    portfolio.current_value = total_current_value
    portfolio.profit_loss = total_current_value - portfolio.total_invested
    portfolio.save()
    
    context = {
        'portfolio': portfolio,
        'holdings': holdings,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'portfolio.html', context)

@login_required
def stock_list(request):
    """Stock list for trading"""
    stocks = Stock.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        stocks = stocks.filter(
            Q(symbol__icontains=search_query) |
            Q(company_name__icontains=search_query)
        )
    
    paginator = Paginator(stocks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'stocks.html', context)

@login_required
def trade_stock(request, stock_id):
    """Stock trading view"""
    stock = get_object_or_404(Stock, id=stock_id, is_active=True)
    portfolio = get_object_or_404(VirtualPortfolio, user=request.user)
    
    # Get current holding
    holding = portfolio.holdings.filter(stock=stock).first()
    
    if request.method == 'POST':
        transaction_type = request.POST.get('transaction_type')
        quantity = int(request.POST.get('quantity', 0))
        
        if quantity <= 0:
            messages.error(request, 'Please enter a valid quantity.')
            return redirect('trade_stock', stock_id=stock_id)
        
        total_amount = quantity * stock.current_price
        
        if transaction_type == 'buy':
            if portfolio.virtual_cash >= total_amount:
                # Create transaction
                VirtualTransaction.objects.create(
                    portfolio=portfolio,
                    stock=stock,
                    transaction_type='buy',
                    quantity=quantity,
                    price_per_share=stock.current_price,
                    total_amount=total_amount
                )
                
                # Update portfolio cash
                portfolio.virtual_cash -= total_amount
                portfolio.total_invested += total_amount
                portfolio.save()
                
                # Update or create holding
                if holding:
                    new_quantity = holding.quantity + quantity
                    new_invested = holding.invested_amount + total_amount
                    holding.quantity = new_quantity
                    holding.average_price = new_invested / new_quantity
                    holding.invested_amount = new_invested
                    holding.save()
                else:
                    Holding.objects.create(
                        portfolio=portfolio,
                        stock=stock,
                        quantity=quantity,
                        average_price=stock.current_price,
                        invested_amount=total_amount
                    )
                
                messages.success(request, f'Successfully bought {quantity} shares of {stock.symbol}')
            else:
                messages.error(request, 'Insufficient funds!')
        
        elif transaction_type == 'sell':
            if holding and holding.quantity >= quantity:
                # Create transaction
                VirtualTransaction.objects.create(
                    portfolio=portfolio,
                    stock=stock,
                    transaction_type='sell',
                    quantity=quantity,
                    price_per_share=stock.current_price,
                    total_amount=total_amount
                )
                
                # Update portfolio cash
                portfolio.virtual_cash += total_amount
                portfolio.save()
                
                # Update holding
                holding.quantity -= quantity
                if holding.quantity == 0:
                    holding.delete()
                else:
                    holding.invested_amount -= (holding.average_price * quantity)
                    holding.save()
                
                messages.success(request, f'Successfully sold {quantity} shares of {stock.symbol}')
            else:
                messages.error(request, 'Insufficient shares to sell!')
        
        return redirect('portfolio_view')
    
    context = {
        'stock': stock,
        'portfolio': portfolio,
        'holding': holding,
    }
    
    return render(request, 'trade.html', context)

@login_required
def budget_management(request):
    """Budget management view"""
    budgets = Budget.objects.filter(user=request.user, is_active=True)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, 'Budget created successfully!')
            return redirect('budget_management')
    else:
        form = BudgetForm()
    
    context = {
        'budgets': budgets,
        'form': form,
    }
    
    return render(request, 'budget.html', context)

@login_required
def expense_tracking(request):
    """Expense tracking view"""
    expenses = Expense.objects.filter(user=request.user).order_by('-date')[:20]
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            
            # Update budget category if applicable
            if expense.category:
                expense.category.spent_amount += expense.amount
                expense.category.save()
            
            messages.success(request, 'Expense added successfully!')
            return redirect('expense_tracking')
    else:
        form = ExpenseForm()
        # Filter categories for current user's budgets
        form.fields['category'].queryset = BudgetCategory.objects.filter(
            budget__user=request.user,
            budget__is_active=True
        )
    
    # Monthly expense summary
    monthly_expenses = {}
    for i in range(6):
        date = timezone.now() - timedelta(days=30*i)
        month_expenses = Expense.objects.filter(
            user=request.user,
            date__year=date.year,
            date__month=date.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_expenses[date.strftime('%b %Y')] = float(monthly_expenses)
    
    context = {
        'expenses': expenses,
        'form': form,
        'monthly_expenses': monthly_expenses,
    }
    
    return render(request, 'expenses.html', context)

@login_required
def financial_goals(request):
    """Financial goals view"""
    goals = FinancialGoal.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        form = FinancialGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Financial goal created successfully!')
            return redirect('financial_goals')
    else:
        form = FinancialGoalForm()
    
    context = {
        'goals': goals,
        'form': form,
    }
    
    return render(request, 'goals.html', context)

@login_required
def fraud_scenarios(request):
    """Fraud scenario challenges"""
    scenarios = FraudScenario.objects.filter(is_active=True)
    user_progress = UserFraudProgress.objects.filter(user=request.user).values_list(
        'scenario_id', 'is_completed', 'is_correct'
    )
    progress_dict = {scenario_id: (completed, correct) for scenario_id, completed, correct in user_progress}
    
    context = {
        'scenarios': scenarios,
        'progress_dict': progress_dict,
    }
    
    return render(request, 'scenarios.html', context)

@login_required
def fraud_scenario_detail(request, scenario_id):
    """Individual fraud scenario view"""
    scenario = get_object_or_404(FraudScenario, id=scenario_id, is_active=True)
    
    # Check if user has already completed this scenario
    progress = UserFraudProgress.objects.filter(
        user=request.user,
        scenario=scenario
    ).first()
    
    if request.method == 'POST' and not progress:
        user_response = request.POST.get('user_response', '')
        
        # Simple check - in a real app, you'd have more sophisticated evaluation
        red_flags_mentioned = 0
        for flag in scenario.red_flags:
            if flag.lower() in user_response.lower():
                red_flags_mentioned += 1
        
        # Consider correct if user mentioned at least 60% of red flags
        is_correct = red_flags_mentioned >= len(scenario.red_flags) * 0.6
        
        # Create progress record
        UserFraudProgress.objects.create(
            user=request.user,
            scenario=scenario,
            user_response=user_response,
            is_correct=is_correct,
            is_completed=True,
            completion_date=timezone.now()
        )
        
        # Award points if correct
        if is_correct:
            profile = request.user.profile
            profile.total_points += scenario.points_reward
            profile.save()
            messages.success(request, f'Correct! You earned {scenario.points_reward} points.')
        else:
            messages.warning(request, 'Good try! Review the explanation and try similar scenarios.')
        
        progress = UserFraudProgress.objects.get(user=request.user, scenario=scenario)
    
    context = {
        'scenario': scenario,
        'progress': progress,
    }
    
    return render(request, 'scenario_detail.html', context)

@login_required
def profile_settings(request):
    """User profile settings view"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_settings')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
        'profile': profile,
    }
    
    return render(request, 'settings.html', context)

@login_required
def leaderboard(request):
    """Leaderboard view"""
    top_users = UserProfile.objects.select_related('user').order_by('-total_points')[:20]
    
    # Get current user's rank
    user_rank = UserProfile.objects.filter(
        total_points__gt=request.user.profile.total_points
    ).count() + 1
    
    context = {
        'top_users': top_users,
        'user_rank': user_rank,
        'user_profile': request.user.profile,
    }
    
    return render(request, 'leaderboard.html', context)

# API Views for AJAX requests
@login_required
def api_stock_price(request, stock_id):
    """API endpoint to get current stock price"""
    try:
        stock = Stock.objects.get(id=stock_id, is_active=True)
        return JsonResponse({
            'symbol': stock.symbol,
            'current_price': float(stock.current_price),
            'previous_close': float(stock.previous_close),
            'change': float(stock.current_price - stock.previous_close),
            'change_percent': float((stock.current_price - stock.previous_close) / stock.previous_close * 100),
        })
    except Stock.DoesNotExist:
        return JsonResponse({'error': 'Stock not found'}, status=404)

@login_required
def api_portfolio_summary(request):
    """API endpoint for portfolio summary"""
    portfolio = get_object_or_404(VirtualPortfolio, user=request.user)
    
    return JsonResponse({
        'virtual_cash': float(portfolio.virtual_cash),
        'total_invested': float(portfolio.total_invested),
        'current_value': float(portfolio.current_value),
        'profit_loss': float(portfolio.profit_loss),
        'profit_loss_percent': float(portfolio.profit_loss / portfolio.total_invested * 100) if portfolio.total_invested > 0 else 0,
    })

@login_required
def api_user_stats(request):
    """API endpoint for user statistics"""
    profile = request.user.profile
    
    # Calculate completion rates
    total_modules = LearningModule.objects.filter(is_active=True).count()
    completed_modules = UserProgress.objects.filter(user=request.user, is_completed=True).count()
    
    total_scenarios = FraudScenario.objects.filter(is_active=True).count()
    completed_scenarios = UserFraudProgress.objects.filter(user=request.user, is_completed=True).count()
    
    return JsonResponse({
        'total_points': profile.total_points,
        'level': profile.level,
        'streak_days': profile.streak_days,
        'modules_completed': completed_modules,
        'total_modules': total_modules,
        'scenarios_completed': completed_scenarios,
        'total_scenarios': total_scenarios,
        'completion_rate': (completed_modules / total_modules * 100) if total_modules > 0 else 0,
    })
