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
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse


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
    
    return render(request, 'profile.html', context)

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
@login_required
def profile_settings(request):
    """Enhanced profile settings view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get statistics for display
    total_modules = LearningModule.objects.filter(is_active=True).count()
    total_scenarios = FraudScenario.objects.filter(is_active=True).count()
    completed_modules = UserProgress.objects.filter(user=request.user, is_completed=True).count()
    completed_scenarios = UserFraudProgress.objects.filter(user=request.user, is_completed=True).count()
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                user = request.user
                
                # Update user fields
                user.username = request.POST.get('username', user.username)
                user.email = request.POST.get('email', user.email)
                user.first_name = request.POST.get('first_name', user.first_name)
                user.last_name = request.POST.get('last_name', user.last_name)
                user.phone_number = request.POST.get('phone_number', user.phone_number)
                
                # Handle age field
                age = request.POST.get('age')
                if age:
                    user.age = int(age)
                
                # Handle monthly_income field
                monthly_income = request.POST.get('monthly_income')
                if monthly_income:
                    user.monthly_income = Decimal(monthly_income)
                
                user.occupation = request.POST.get('occupation', user.occupation)
                user.financial_experience = request.POST.get('financial_experience', user.financial_experience)
                
                user.save()
                messages.success(request, 'Profile updated successfully!')
                
        except IntegrityError as e:
            if 'username' in str(e):
                messages.error(request, 'Username already exists. Please choose a different one.')
            elif 'email' in str(e):
                messages.error(request, 'Email already registered. Please use a different email.')
            else:
                messages.error(request, 'Failed to update profile due to duplicate data.')
        except Exception as e:
            messages.error(request, f'Failed to update profile: {str(e)}')
        
        return redirect('profile_settings')
    
    context = {
        'profile': profile,
        'total_modules': total_modules,
        'total_scenarios': total_scenarios,
        'completed_modules': completed_modules,
        'completed_scenarios': completed_scenarios,
    }
    
    return render(request, 'profile.html', context)

@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile_settings')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    
    return redirect('profile_settings')

@login_required
def delete_account(request):
    """Delete user account"""
    if request.method == 'POST':
        user = request.user
        try:
            with transaction.atomic():
                # Log out the user first
                logout(request)
                # Delete user will cascade delete related data
                user.delete()
                messages.success(request, 'Your account has been deleted successfully.')
                return redirect('home')
        except Exception as e:
            messages.error(request, f'Failed to delete account: {str(e)}')
    
    return redirect('profile_settings')

@login_required
def user_achievements(request):
    """View user achievements"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Calculate achievements based on user progress
    achievements = []
    
    # Module completion achievements
    completed_modules = UserProgress.objects.filter(user=request.user, is_completed=True).count()
    if completed_modules >= 1:
        achievements.append("First Steps")
    if completed_modules >= 5:
        achievements.append("Learning Enthusiast")
    if completed_modules >= 10:
        achievements.append("Knowledge Seeker")
    
    # Points achievements
    if profile.total_points >= 100:
        achievements.append("Point Collector")
    if profile.total_points >= 500:
        achievements.append("High Achiever")
    if profile.total_points >= 1000:
        achievements.append("Master Learner")
    
    # Streak achievements
    if profile.streak_days >= 7:
        achievements.append("Week Warrior")
    if profile.streak_days >= 30:
        achievements.append("Monthly Master")
    
    # Portfolio achievements
    try:
        portfolio = request.user.portfolio
        if portfolio.profit_loss > 0:
            achievements.append("Profit Maker")
        if portfolio.current_value > 110000:  # More than starting amount
            achievements.append("Investment Growth")
    except:
        pass  # Portfolio might not exist yet
    
    # Update profile achievements
    profile.achievements = achievements
    profile.save()
    
    context = {
        'achievements': achievements,
        'profile': profile,
    }
    
    return render(request, 'achievements.html', context)
from datetime import datetime, timedelta
import calendar
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Budget, Expense  # Make sure these imports match your model names

@login_required
def budget_analysis(request):
    current_year = datetime.now().year
    today = datetime.now().date()
    
    # Get month and year with proper error handling
    try:
        selected_month = int(request.GET.get('month', datetime.now().month))
        if selected_month < 1 or selected_month > 12:
            selected_month = datetime.now().month
    except (ValueError, TypeError):
        selected_month = datetime.now().month
    
    try:
        selected_year = int(request.GET.get('year', current_year))
        if selected_year < (current_year - 10) or selected_year > (current_year + 1):
            selected_year = current_year
    except (ValueError, TypeError):
        selected_year = current_year
    
    # Calculate date ranges
    first_day = datetime(selected_year, selected_month, 1).date()
    if selected_month == 12:
        last_day = datetime(selected_year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = datetime(selected_year, selected_month + 1, 1).date() - timedelta(days=1)
    
    # Get user's active budgets
    active_budgets = Budget.objects.filter(
        user=request.user,
        is_active=True,
        start_date__lte=last_day,
        end_date__gte=first_day
    ).prefetch_related('categories')
    
    # Get expenses for selected month
    monthly_expenses = Expense.objects.filter(
        user=request.user,
        date__year=selected_year,
        date__month=selected_month
    ).select_related('category')
    
    # Calculate total monthly expenses
    total_monthly_expenses = monthly_expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Category-wise expense breakdown
    category_expenses = {}
    for expense in monthly_expenses:
        if expense.category:
            cat_name = expense.category.name
            if cat_name not in category_expenses:
                category_expenses[cat_name] = {
                    'spent': 0, 
                    'budget': float(expense.category.allocated_amount), 
                    'category_id': expense.category.id
                }
            category_expenses[cat_name]['spent'] += float(expense.amount)
    
    # Calculate budget vs actual for each category
    budget_analysis_data = []
    total_budget = 0
    total_overspent = 0
    categories_over_budget = 0
    
    for budget in active_budgets:
        total_budget += float(budget.total_amount)
        for category in budget.categories.all():
            spent = category_expenses.get(category.name, {}).get('spent', 0)
            allocated = float(category.allocated_amount)
            remaining = allocated - spent
            percentage_used = (spent / allocated * 100) if allocated > 0 else 0
            
            is_over_budget = spent > allocated
            if is_over_budget:
                categories_over_budget += 1
                total_overspent += (spent - allocated)
            
            budget_analysis_data.append({
                'category': category.name,
                'allocated': allocated,
                'spent': spent,
                'remaining': remaining,
                'percentage_used': percentage_used,
                'is_over_budget': is_over_budget,
                'status': 'danger' if is_over_budget else ('warning' if percentage_used > 80 else 'success')
            })
    
    # Monthly comparison (last 6 months)
    monthly_comparison = []
    for i in range(6):
        date = today.replace(day=1) - timedelta(days=32*i)
        month_expenses = Expense.objects.filter(
            user=request.user,
            date__year=date.year,
            date__month=date.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_comparison.append({
            'month': date.strftime('%b %Y'),
            'amount': float(month_expenses),
            'month_num': date.month,
            'year': date.year
        })
    
    monthly_comparison.reverse()
    
    # Daily expense trends
    daily_expenses = []
    for day in range(1, calendar.monthrange(selected_year, selected_month)[1] + 1):
        day_date = datetime(selected_year, selected_month, day).date()
        day_total = monthly_expenses.filter(date=day_date).aggregate(total=Sum('amount'))['total'] or 0
        daily_expenses.append({
            'day': day,
            'amount': float(day_total)
        })
    
    # Top expense categories
    top_categories = monthly_expenses.values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]
    
    # Get user's monthly income (add error handling)
    try:
        monthly_income = float(getattr(request.user, 'monthly_income', 0) or 0)
    except (ValueError, TypeError):
        monthly_income = 0
    
    # Savings analysis
    savings_amount = monthly_income - float(total_monthly_expenses)
    savings_rate = (savings_amount / monthly_income * 100) if monthly_income > 0 else 0
    
    # Financial health score calculation
    health_score = 100
    if savings_rate < 20:
        health_score -= 30
    elif savings_rate < 10:
        health_score -= 50
    
    if categories_over_budget > 0:
        health_score -= (categories_over_budget * 15)
    
    if float(total_monthly_expenses) > monthly_income:
        health_score -= 40
    
    health_score = max(0, health_score)
    
    # Recommendations
    recommendations = []
    if savings_rate < 20:
        recommendations.append({
            'type': 'warning',
            'title': 'Low Savings Rate',
            'message': 'Try to save at least 20% of your income for better financial health.'
        })
    
    if categories_over_budget > 0:
        recommendations.append({
            'type': 'danger',
            'title': 'Budget Exceeded',
            'message': f'You have exceeded budget in {categories_over_budget} categories. Review your spending habits.'
        })
    
    if float(total_monthly_expenses) > monthly_income * 0.8:
        recommendations.append({
            'type': 'info',
            'title': 'High Expense Ratio',
            'message': 'Your expenses are quite high relative to income. Consider optimizing non-essential spending.'
        })
    
    # Recent transactions for quick review
    recent_transactions = monthly_expenses.order_by('-created_at')[:10]
    
    # Single context dictionary
    context = {
        'months_list': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'years_list': list(range(2020, 2030)),
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': calendar.month_name[selected_month],
        'total_monthly_expenses': total_monthly_expenses,
        'monthly_income': monthly_income,
        'savings_amount': savings_amount,
        'savings_rate': savings_rate,
        'budget_analysis_data': budget_analysis_data,
        'monthly_comparison': monthly_comparison,
        'daily_expenses': daily_expenses,
        'top_categories': top_categories,
        'health_score': health_score,
        'recommendations': recommendations,
        'recent_transactions': recent_transactions,
        'categories_over_budget': categories_over_budget,
        'total_overspent': total_overspent,
        'total_budget': total_budget,
    }
    
    return render(request, 'budget_analysis.html', context)
@login_required
def budget_planner(request):
    """Interactive budget planner tool"""
    from django.http import JsonResponse
    import json
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'save_budget':
                # Create new budget
                budget = Budget.objects.create(
                    user=request.user,
                    name=data.get('budget_name', 'My Budget'),
                    total_amount=Decimal(str(data.get('total_amount', 0))),
                    start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
                    end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
                )
                
                # Create budget categories
                for category_data in data.get('categories', []):
                    BudgetCategory.objects.create(
                        budget=budget,
                        name=category_data.get('name'),
                        allocated_amount=Decimal(str(category_data.get('amount', 0)))
                    )
                
                return JsonResponse({'success': True, 'budget_id': budget.id})
            
            elif action == 'update_category':
                category_id = data.get('category_id')
                new_amount = Decimal(str(data.get('amount', 0)))
                
                category = BudgetCategory.objects.get(
                    id=category_id, 
                    budget__user=request.user
                )
                category.allocated_amount = new_amount
                category.save()
                
                # Update budget total
                budget = category.budget
                budget.total_amount = budget.categories.aggregate(
                    total=Sum('allocated_amount')
                )['total'] or 0
                budget.save()
                
                return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Get user's existing budgets
    existing_budgets = Budget.objects.filter(
        user=request.user,
        is_active=True
    ).prefetch_related('categories')
    
    # Default budget categories
    default_categories = [
        {'name': 'Food & Dining', 'suggested_percent': 25, 'icon': '🍽️'},
        {'name': 'Transportation', 'suggested_percent': 15, 'icon': '🚗'},
        {'name': 'Shopping', 'suggested_percent': 10, 'icon': '🛍️'},
        {'name': 'Bills & Utilities', 'suggested_percent': 20, 'icon': '💡'},
        {'name': 'Healthcare', 'suggested_percent': 5, 'icon': '🏥'},
        {'name': 'Entertainment', 'suggested_percent': 8, 'icon': '🎬'},
        {'name': 'Savings', 'suggested_percent': 15, 'icon': '💰'},
        {'name': 'Other', 'suggested_percent': 2, 'icon': '📝'}
    ]
    
    # Budget templates
    budget_templates = {
        'conservative': {
            'name': 'Conservative Budget',
            'description': 'High savings, minimal entertainment',
            'allocations': {
                'Food & Dining': 20, 'Transportation': 10, 'Bills & Utilities': 25,
                'Healthcare': 5, 'Shopping': 5, 'Entertainment': 5, 'Savings': 25, 'Other': 5
            }
        },
        'balanced': {
            'name': 'Balanced Budget',
            'description': 'Equal focus on needs and wants',
            'allocations': {
                'Food & Dining': 25, 'Transportation': 15, 'Bills & Utilities': 20,
                'Healthcare': 5, 'Shopping': 10, 'Entertainment': 10, 'Savings': 15
            }
        },
        'lifestyle': {
            'name': 'Lifestyle Budget',
            'description': 'More spending on entertainment and shopping',
            'allocations': {
                'Food & Dining': 30, 'Transportation': 15, 'Bills & Utilities': 20,
                'Healthcare': 5, 'Shopping': 15, 'Entertainment': 10, 'Savings': 5
            }
        }
    }
    
    context = {
        'existing_budgets': existing_budgets,
        'default_categories': default_categories,
        'budget_templates': budget_templates,
        'monthly_income': float(request.user.monthly_income),
    }
    
    return render(request, 'budget_planner.html', context)

@login_required
def expense_predictor(request):
    """Predict future expenses based on historical data"""
    from django.db.models import Avg
    from datetime import datetime, timedelta
    import json
    
    if request.method == 'GET':
        # Get historical expense data for prediction
        months_back = 6
        start_date = timezone.now().date() - timedelta(days=30 * months_back)
        
        # Calculate average monthly expenses by category
        historical_expenses = Expense.objects.filter(
            user=request.user,
            date__gte=start_date
        ).values('category__name').annotate(
            avg_monthly=Avg('amount'),
            total_months=Count('date__month', distinct=True)
        )
        
        # Seasonal adjustments (basic example)
        current_month = timezone.now().month
        seasonal_multipliers = {
            12: 1.3, 1: 1.2, 2: 0.9,  # Holiday season, New Year, February
            3: 1.0, 4: 1.0, 5: 1.0,   # Spring
            6: 1.1, 7: 1.2, 8: 1.1,   # Summer (travel season)
            9: 1.0, 10: 1.1, 11: 1.2  # Fall, Holiday prep
        }
        
        predictions = []
        for expense_data in historical_expenses:
            category = expense_data['category__name'] or 'Uncategorized'
            avg_amount = expense_data['avg_monthly'] or 0
            seasonal_factor = seasonal_multipliers.get(current_month, 1.0)
            predicted_amount = avg_amount * seasonal_factor
            
            predictions.append({
                'category': category,
                'historical_avg': float(avg_amount),
                'predicted_amount': float(predicted_amount),
                'seasonal_factor': seasonal_factor,
                'confidence': 0.8 if expense_data['total_months'] >= 3 else 0.5
            })
        
        return JsonResponse({
            'success': True,
            'predictions': predictions,
            'current_month': current_month,
            'months_analyzed': months_back
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})