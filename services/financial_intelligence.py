from datetime import date
from sqlalchemy import func
from models.database import db, Expense, Budget
def _safe_divide(a, b):
    return (a / b) if b else 0


def get_month_snapshot():
    """Return key financial metrics for the current month."""

    today = date.today()

    monthly_expense = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.transaction_type == "Expense",
            func.extract("year", Expense.date) == today.year,
            func.extract("month", Expense.date) == today.month,
        )
        .scalar()
        or 0
    )

    monthly_income = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.transaction_type == "Income",
            func.extract("year", Expense.date) == today.year,
            func.extract("month", Expense.date) == today.month,
        )
        .scalar()
        or 0
    )

    days_elapsed = max(today.day, 1)
    average_daily_spending = round(monthly_expense / days_elapsed, 2)

    today_spending = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.transaction_type == "Expense",
            Expense.date == today,
        )
        .scalar()
        or 0
    )

    largest_expense = (
        db.session.query(Expense)
        .filter(
            Expense.transaction_type == "Expense",
            func.extract("year", Expense.date) == today.year,
            func.extract("month", Expense.date) == today.month,
        )
        .order_by(Expense.amount.desc())
        .first()
    )

    total_budget = (
        db.session.query(func.coalesce(func.sum(Budget.monthly_budget), 0))
        .scalar()
        or 0
    )

    top_category = (
        db.session.query(
            Expense.category,
            func.sum(Expense.amount).label("total")
        )
        .filter(
            Expense.transaction_type == "Expense",
            func.extract("year", Expense.date) == today.year,
            func.extract("month", Expense.date) == today.month,
        )
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .first()
    )

    return {
        "average_daily_spending": average_daily_spending,
        "today_spending": today_spending,
        "largest_expense": largest_expense.amount if largest_expense else 0,
        "largest_expense_description": largest_expense.description if largest_expense and largest_expense.description else "-",
        "budget_remaining": max(total_budget - monthly_expense, 0),
        "monthly_savings": monthly_income - monthly_expense,
        "top_category": top_category.category if top_category else "-",
        "top_category_amount": top_category.total if top_category else 0,
    }


def get_category_performance():
    """Return budget performance for each category."""

    performance = []

    budgets = Budget.query.order_by(Budget.category.asc()).all()

    today = date.today()

    for budget in budgets:
        spent = (
            db.session.query(func.coalesce(func.sum(Expense.amount), 0))
            .filter(
                Expense.transaction_type == "Expense",
                Expense.category == budget.category,
                func.extract("year", Expense.date) == today.year,
                func.extract("month", Expense.date) == today.month,
            )
            .scalar()
            or 0
        )

        budget_amount = float(budget.monthly_budget)
        spent_amount = float(spent)
        remaining = max(budget_amount - spent_amount, 0)
        usage = round(_safe_divide(spent_amount, budget_amount) * 100, 1)

        if usage > 100:
            status = "Over Budget"
            color = "danger"
        elif usage >= 80:
            status = "Near Limit"
            color = "warning"
        else:
            status = "Healthy"
            color = "success"

        performance.append({
            "category": budget.category,
            "budget": budget_amount,
            "spent": spent_amount,
            "remaining": remaining,
            "usage": min(usage, 100),
            "actual_usage": usage,
            "status": status,
            "color": color,
        })

    return performance


def generate_financial_insights():
    """Return all dashboard intelligence in one dictionary."""

    today = date.today()

    monthly_income = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.transaction_type == "Income",
        func.extract("year", Expense.date) == today.year,
        func.extract("month", Expense.date) == today.month,
    ).scalar() or 0

    monthly_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.transaction_type == "Expense",
        func.extract("year", Expense.date) == today.year,
        func.extract("month", Expense.date) == today.month,
    ).scalar() or 0

    total_budget = db.session.query(func.coalesce(func.sum(Budget.monthly_budget), 0)).scalar() or 0

    savings = monthly_income - monthly_expense
    savings_rate = round(_safe_divide(savings, monthly_income) * 100, 1)
    budget_usage = round(_safe_divide(monthly_expense, total_budget) * 100, 1)

    score = 100
    if savings_rate < 20:
        score -= 15
    elif savings_rate >= 35:
        score += 5

    if budget_usage > 100:
        score -= 20
    elif budget_usage <= 80:
        score += 5

    if monthly_expense > monthly_income:
        score -= 20

    score = max(0, min(100, score))

    if score >= 85:
        health = "Excellent"
    elif score >= 70:
        health = "Good"
    elif score >= 50:
        health = "Fair"
    else:
        health = "Needs Attention"

    highest_category = (
        db.session.query(
            Expense.category,
            func.sum(Expense.amount).label("total")
        )
        .filter(
            Expense.transaction_type == "Expense",
            func.extract("year", Expense.date) == today.year,
            func.extract("month", Expense.date) == today.month,
        )
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .first()
    )

    recommendations = []
    featured_insight = {
        "title": "Today's Financial Insight",
        "message": "Keep tracking your finances consistently.",
        "type": "info",
        "icon": "bi-lightbulb-fill",
        "badge": "Info",
        "action": "View Transactions",
        "action_url": "/expenses",
    }

    if budget_usage > 100:
        recommendations.append("You have exceeded your monthly budget.")
    elif budget_usage > 80:
        recommendations.append("You are approaching your monthly budget limit.")

    if savings_rate < 20:
        recommendations.append("Increase your monthly savings to at least 20% of income.")
    else:
        recommendations.append("Your savings rate is healthy. Keep it up.")

    # Featured insight logic
    if highest_category:
        featured_insight = {
            "title": "Top Spending Category",
            "message": f"Your highest spending this month is on {highest_category.category} (₹{highest_category.total:,.0f}).",
            "type": "warning" if budget_usage > 80 else "info",
            "icon": "bi-pie-chart-fill",
            "badge": "Insight",
            "action": "View Spending",
            "action_url": "/expenses",
        }

    if budget_usage > 100:
        featured_insight = {
            "title": "Budget Alert",
            "message": f"You have already used {budget_usage}% of your total monthly budget. Consider reducing discretionary spending.",
            "type": "danger",
            "icon": "bi-exclamation-triangle-fill",
            "badge": "Critical",
            "action": "Manage Budget",
            "action_url": "/budgets",
        }
    elif savings_rate >= 30:
        featured_insight = {
            "title": "Savings Achievement",
            "message": f"Excellent work! You're saving {savings_rate}% of your income this month.",
            "type": "success",
            "icon": "bi-trophy-fill",
            "badge": "Excellent",
            "action": "View Dashboard",
            "action_url": "/dashboard",
        }
    elif monthly_income > monthly_expense:
        surplus = monthly_income - monthly_expense
        featured_insight = {
            "title": "Positive Cash Flow",
            "message": f"You're currently ahead by ₹{surplus:,.0f} this month. Keep up the disciplined spending.",
            "type": "success",
            "icon": "bi-graph-up-arrow",
            "badge": "Healthy",
            "action": "See Report",
            "action_url": "/reports",
        }

    return {
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,
        "monthly_savings": savings,
        "savings_rate": savings_rate,
        "budget_usage": budget_usage,
        "financial_health_score": score,
        "health_status": health,
        "highest_category": highest_category.category if highest_category else "-",
        "highest_category_amount": highest_category.total if highest_category else 0,
        "featured_insight": featured_insight,
        "recommendations": recommendations,
    }