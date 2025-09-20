# urls.py (main project urls)
from django.contrib import admin
from django.urls import path, include
# ore/urls.py
from django.urls import path
from main import views

urlpatterns = [
    # Authentication URLs
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    
    # Learning Module URLs
    path('learn/', views.learning_modules, name='learning_modules'),
    path('learn/module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('learn/module/<int:module_id>/complete/', views.complete_module, name='complete_module'),
    path('learn/module/<int:module_id>/quiz/', views.take_quiz, name='take_quiz'),
    
    # Portfolio URLs
    path('portfolio/', views.portfolio_view, name='portfolio_view'),
    path('portfolio/stocks/', views.stock_list, name='stock_list'),
    path('portfolio/trade/<int:stock_id>/', views.trade_stock, name='trade_stock'),
    
    path('budget/', views.budget_management, name='budget_management'),
    path('budget/analysis/', views.budget_analysis, name='budget_analysis'),
    path('budget/planner/', views.budget_planner, name='budget_planner'),
    path('expenses/', views.expense_tracking, name='expense_tracking'),
    path('expenses/predictor/', views.expense_predictor, name='expense_predictor'),
    path('goals/', views.financial_goals, name='financial_goals'),
    
    # Fraud Prevention URLs
    path('fraud/', views.fraud_scenarios, name='fraud_scenarios'),
    path('fraud/scenario/<int:scenario_id>/', views.fraud_scenario_detail, name='fraud_scenario_detail'),
    
    # API URLs
    path('api/stock/<int:stock_id>/price/', views.api_stock_price, name='api_stock_price'),
    path('api/portfolio/summary/', views.api_portfolio_summary, name='api_portfolio_summary'),
    path('api/user/stats/', views.api_user_stats, name='api_user_stats'),
]