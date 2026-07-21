from datetime import date
from sqlalchemy import func

from models.database import db, Expense, Budget


def generate_spending_insights():
    """Generate rule-based financial insights for the dashboard."""

    today = date.today()
    current_month = today.month
    current_year = today.year

    current_expense = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.transaction_type == "Expense",
            func.extract("year", Expense.date) == current_year,
            func.extract("month", Expense.date) == current_month,
        )
        .scalar()
        or 0
    )

    previous_month = 12 if current_month == 1 else current_month - 1
    previous_year = current_year - 1 if current_month == 1 else current_year

    previous_expense = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.transaction_type == "Expense",
            func.extract("year", Expense.date) == previous_year,
            func.extract("month", Expense.date) == previous_month,
        )
        .scalar()
        or 0
    )

    current_income = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.transaction_type == "Income",
            func.extract("year", Expense.date) == current_year,
            func.extract("month", Expense.date) == current_month,
        )
        .scalar()
        or 0
    )

    previous_income = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.transaction_type == "Income",
            func.extract("year", Expense.date) == previous_year,
            func.extract("month", Expense.date) == previous_month,
        )
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
            func.extract("year", Expense.date) == current_year,
            func.extract("month", Expense.date) == current_month,
        )
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .first()
    )

    largest_expense = (
        Expense.query.filter(
            Expense.transaction_type == "Expense",
            func.extract("year", Expense.date) == current_year,
            func.extract("month", Expense.date) == current_month,
        )
        .order_by(Expense.amount.desc())
        .first()
    )

    budgets = Budget.query.all()

    insights = []

    expense_count = (
        Expense.query.filter(
            Expense.transaction_type == "Expense",
            func.extract("year", Expense.date) == current_year,
            func.extract("month", Expense.date) == current_month,
        ).count()
    )

    average_expense = (float(current_expense) / expense_count) if expense_count else 0

    for budget in budgets:
        spent = (
            db.session.query(func.coalesce(func.sum(Expense.amount), 0))
            .filter(
                Expense.transaction_type == "Expense",
                Expense.category == budget.category,
                func.extract("year", Expense.date) == current_year,
                func.extract("month", Expense.date) == current_month,
            )
            .scalar()
            or 0
        )

        usage = (float(spent) / float(budget.monthly_budget) * 100) if budget.monthly_budget else 0

        if usage >= 100:
            insights.append({
                "type": "danger",
                "icon": "bi-exclamation-triangle-fill",
                "title": f"{budget.category} Budget Exceeded",
                "message": f"You have exceeded your {budget.category} budget by {usage - 100:.1f}%.",
            })
        elif usage >= 80:
            insights.append({
                "type": "warning",
                "icon": "bi-speedometer2",
                "title": f"{budget.category} Near Limit",
                "message": f"You have used {usage:.1f}% of your {budget.category} budget.",
            })

    if previous_expense > 0:
        change = ((current_expense - previous_expense) / previous_expense) * 100
        if change > 5:
            insights.append({
                "type": "warning",
                "icon": "bi-arrow-up-circle",
                "title": "Spending Increased",
                "message": f"Your spending increased by {change:.1f}% compared to last month.",
            })
        elif change < -5:
            insights.append({
                "type": "success",
                "icon": "bi-arrow-down-circle",
                "title": "Great Improvement",
                "message": f"Your spending decreased by {abs(change):.1f}% compared to last month.",
            })

    if previous_income > 0:
        income_change = ((current_income - previous_income) / previous_income) * 100
        if income_change > 5:
            insights.append({
                "type": "success",
                "icon": "bi-graph-up-arrow",
                "title": "Income Increased",
                "message": f"Your income increased by {income_change:.1f}% compared to last month.",
            })
        elif income_change < -5:
            insights.append({
                "type": "warning",
                "icon": "bi-graph-down-arrow",
                "title": "Income Decreased",
                "message": f"Your income decreased by {abs(income_change):.1f}% compared to last month.",
            })

    if expense_count:
        insights.append({
            "type": "primary",
            "icon": "bi-calculator",
            "title": "Average Transaction",
            "message": f"Your average expense this month is ₹{average_expense:,.0f}.",
        })

    if top_category:
        insights.append({
            "type": "info",
            "icon": "bi-pie-chart-fill",
            "title": "Top Spending Category",
            "message": f"{top_category.category} is your highest spending category this month (₹{float(top_category.total):,.0f}).",
        })

    if largest_expense:
        insights.append({
            "type": "primary",
            "icon": "bi-cash-stack",
            "title": "Largest Expense",
            "message": f"Your largest expense this month was ₹{float(largest_expense.amount):,.0f} for {largest_expense.category}.",
        })

    if current_expense > 0 and previous_expense == 0:
        insights.append({
            "type": "info",
            "icon": "bi-stars",
            "title": "New Financial Activity",
            "message": "Great! You're building your financial history this month.",
        })

    healthy_budget_count = 0
    for budget in budgets:
        spent = (
            db.session.query(func.coalesce(func.sum(Expense.amount), 0))
            .filter(
                Expense.transaction_type == "Expense",
                Expense.category == budget.category,
                func.extract("year", Expense.date) == current_year,
                func.extract("month", Expense.date) == current_month,
            )
            .scalar()
            or 0
        )

        usage = (float(spent) / float(budget.monthly_budget) * 100) if budget.monthly_budget else 0
        if usage < 70:
            healthy_budget_count += 1

    if budgets and healthy_budget_count == len(budgets):
        insights.append({
            "type": "success",
            "icon": "bi-award-fill",
            "title": "Excellent Budget Control",
            "message": "Fantastic! All of your budgets are comfortably within their limits this month.",
        })

    if not insights:
        insights.append({
            "type": "primary",
            "icon": "bi-lightbulb",
            "title": "Getting Started",
            "message": "Add more transactions this month to receive personalized spending insights.",
        })

    return insights