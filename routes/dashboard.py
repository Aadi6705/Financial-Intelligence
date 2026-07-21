from flask import Blueprint, render_template
from services.analytics import get_dashboard_summary
from services.financial_intelligence import (
    generate_financial_insights,
    get_month_snapshot,
    get_category_performance,
)
from services.greeting_service import get_dashboard_greeting
from services.insights_engine import generate_spending_insights

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)


@dashboard_bp.route("/")
def dashboard():
    summary = get_dashboard_summary()
    intelligence = generate_financial_insights()
    greeting_data = get_dashboard_greeting()
    snapshot = get_month_snapshot()
    category_performance = get_category_performance()
    spending_insights = generate_spending_insights()

    return render_template(
        "pages/dashboard.html",
        total_income=summary["total_income"],
        total_expense=summary["total_expense"],
        total_balance=summary["total_balance"],
        transaction_count=summary["transaction_count"],
        recent_transactions=summary["recent_transactions"],
        category_summary=summary["category_summary"],
        monthly_summary=summary["monthly_summary"],
        financial_insights=summary["financial_insights"],
        financial_health_score=intelligence["financial_health_score"],
        health_status=intelligence["health_status"],
        savings_rate=intelligence["savings_rate"],
        budget_usage=intelligence["budget_usage"],
        monthly_savings=intelligence["monthly_savings"],
        featured_insight=intelligence["featured_insight"],
        recommendations=intelligence["recommendations"],
        greeting_data=greeting_data,
        snapshot=snapshot,
        category_performance=category_performance,
        spending_insights=spending_insights,
    )