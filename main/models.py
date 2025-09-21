from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

class User(AbstractUser):
    """Extended User model for PaisaBuddy"""
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(16), MaxValueValidator(35)])
    occupation = models.CharField(max_length=100, blank=True)
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    financial_experience = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='beginner'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    """User profile for gamification features"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    streak_days = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Achievement(models.Model):
    """Achievements for gamification"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='🏆')
    points_required = models.IntegerField(default=0)
    condition_type = models.CharField(
        max_length=50,
        choices=[
            ('modules_completed', 'Modules Completed'),
            ('points_earned', 'Points Earned'),
            ('streak_days', 'Streak Days'),
            ('portfolio_profit', 'Portfolio Profit'),
            ('budget_followed', 'Budget Followed')
        ]
    )
    condition_value = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    """User earned achievements"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"

class LearningModule(models.Model):
    """Learning modules for financial education"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField()
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ]
    )
    points_reward = models.IntegerField(default=10)
    estimated_time = models.IntegerField(help_text="Estimated time in minutes")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

class Quiz(models.Model):
    """Quiz for learning modules"""
    module = models.OneToOneField(LearningModule, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    passing_score = models.IntegerField(default=70)
    
    def __str__(self):
        return f"Quiz: {self.title}"

class QuizQuestion(models.Model):
    """Questions for quizzes"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )
    explanation = models.TextField(blank=True)
    
    def __str__(self):
        return f"Q: {self.question_text[:50]}..."

class UserProgress(models.Model):
    """Track user progress through modules"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(LearningModule, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    quiz_score = models.IntegerField(null=True, blank=True)
    time_spent = models.IntegerField(default=0, help_text="Time spent in minutes")
    
    class Meta:
        unique_together = ['user', 'module']

class VirtualPortfolio(models.Model):
    """Virtual portfolio for stock simulation"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    virtual_cash = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100000.00'))
    total_invested = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Portfolio"

class Stock(models.Model):
    """Stock information for simulation"""
    symbol = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    previous_close = models.DecimalField(max_digits=10, decimal_places=2)
    market_cap = models.BigIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.symbol} - {self.company_name}"

class VirtualTransaction(models.Model):
    """Virtual stock transactions"""
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(VirtualPortfolio, on_delete=models.CASCADE, related_name='transactions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

class Holding(models.Model):
    """User's current stock holdings"""
    portfolio = models.ForeignKey(VirtualPortfolio, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    invested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['portfolio', 'stock']

class Budget(models.Model):
    """User budget management"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class BudgetCategory(models.Model):
    """Budget categories"""
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class Expense(models.Model):
    """User expenses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(BudgetCategory, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class FraudScenario(models.Model):
    """Fraud identification scenarios"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    scenario_content = models.TextField()
    fraud_type = models.CharField(
        max_length=50,
        choices=[
            ('phishing', 'Phishing'),
            ('upi_fraud', 'UPI Fraud'),
            ('fake_investment', 'Fake Investment'),
            ('identity_theft', 'Identity Theft'),
            ('lottery_scam', 'Lottery Scam')
        ]
    )
    correct_action = models.TextField()
    points_reward = models.IntegerField(default=15)
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ]
    )
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class FraudRedFlag(models.Model):
    """Red flags for fraud scenarios"""
    scenario = models.ForeignKey(FraudScenario, on_delete=models.CASCADE, related_name='red_flags')
    description = models.CharField(max_length=300)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.scenario.title} - {self.description}"

class UserFraudProgress(models.Model):
    """Track user progress in fraud scenarios"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scenario = models.ForeignKey(FraudScenario, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    user_response = models.TextField()
    is_correct = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'scenario']

class FinancialGoal(models.Model):
    """User financial goals"""
    GOAL_TYPES = [
        ('emergency_fund', 'Emergency Fund'),
        ('travel', 'Travel'),
        ('gadget', 'Gadget Purchase'),
        ('education', 'Education'),
        ('investment', 'Investment'),
        ('other', 'Other')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    saved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField()
    is_achieved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 0
        return min((self.saved_amount / self.target_amount) * 100, 100)
    
class Token(models.Model):
    """Token system for rewards and purchases"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tokens')
    balance = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    total_earned = models.IntegerField(default=0)
    total_spent = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def _str_(self):
        return f"{self.user.username} - {self.balance} tokens"

class TokenTransaction(models.Model):
    """Track all token transactions"""
    TRANSACTION_TYPES = [
        ('earned_quiz', 'Quiz Completion'),
        ('earned_module', 'Module Completion'),
        ('earned_scenario', 'Fraud Scenario'),
        ('earned_goal', 'Goal Achievement'),
        ('earned_streak', 'Streak Bonus'),
        ('earned_investment', 'Investment Profit'),
        ('purchased', 'Token Purchase'),
        ('spent_coupon', 'Coupon Purchase'),
        ('bonus', 'Bonus Reward'),
        ('refund', 'Refund')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField()  # Positive for earned, negative for spent
    balance_after = models.IntegerField()
    description = models.CharField(max_length=200)
    related_object_id = models.CharField(max_length=50, blank=True)  # For linking to specific modules, quizzes, etc.
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def _str_(self):
        return f"{self.user.username} - {self.amount} tokens ({self.transaction_type})"

class TokenPackage(models.Model):
    """Token purchase packages"""
    name = models.CharField(max_length=100)
    token_amount = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    bonus_tokens = models.IntegerField(default=0)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'price']
    
    @property
    def total_tokens(self):
        return self.token_amount + self.bonus_tokens
    
    @property
    def value_per_rupee(self):
        return self.total_tokens / float(self.price)
    
    def _str_(self):
        return f"{self.name} - {self.total_tokens} tokens for ₹{self.price}"

class Coupon(models.Model):
    """Coupons that can be purchased with tokens"""
    COUPON_TYPES = [
        ('discount', 'Discount Coupon'),
        ('cashback', 'Cashback Offer'),
        ('freebie', 'Free Product/Service'),
        ('experience', 'Experience Voucher')
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('out_of_stock', 'Out of Stock'),
        ('inactive', 'Inactive')
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPES)
    brand_name = models.CharField(max_length=100)
    brand_logo = models.URLField(blank=True)
    token_cost = models.IntegerField(validators=[MinValueValidator(1)])
    original_value = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    stock_quantity = models.IntegerField(default=0)
    used_quantity = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    terms_conditions = models.TextField()
    coupon_code_prefix = models.CharField(max_length=10, default='PB')
    is_featured = models.BooleanField(default=False)
    category = models.CharField(max_length=50, default='General')
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def is_available(self):
        return (self.status == 'active' and 
                self.stock_quantity > self.used_quantity and 
                timezone.now() < self.valid_until)
    
    @property
    def stock_remaining(self):
        return max(0, self.stock_quantity - self.used_quantity)
    
    def _str_(self):
        return f"{self.title} - {self.token_cost} tokens"

class UserCoupon(models.Model):
    """User's purchased coupons"""
    REDEMPTION_STATUS = [
        ('purchased', 'Purchased'),
        ('redeemed', 'Redeemed'),
        ('expired', 'Expired'),
        ('refunded', 'Refunded')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    coupon_code = models.CharField(max_length=50, unique=True)
    tokens_spent = models.IntegerField()
    purchase_date = models.DateTimeField(auto_now_add=True)
    redemption_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=REDEMPTION_STATUS, default='purchased')
    
    def save(self, *args, **kwargs):
        if not self.coupon_code:
            # Generate unique coupon code
            import random
            import string
            while True:
                code = f"{self.coupon.coupon_code_prefix}{random.randint(1000, 9999)}"
                if not UserCoupon.objects.filter(coupon_code=code).exists():
                    self.coupon_code = code
                    break
        
        if not self.expiry_date:
            self.expiry_date = self.coupon.valid_until
            
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expiry_date
    
    @property
    def days_until_expiry(self):
        if self.is_expired:
            return 0
        return (self.expiry_date - timezone.now()).days
    
    def _str_(self):
        return f"{self.user.username} - {self.coupon.title} ({self.coupon_code})"

class TokenEarningRule(models.Model):
    """Rules for earning tokens from various activities"""
    activity_type = models.CharField(max_length=30, unique=True)
    tokens_per_action = models.IntegerField()
    max_daily_tokens = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=200)
    
    def _str_(self):
        return f"{self.activity_type} - {self.tokens_per_action} tokens"