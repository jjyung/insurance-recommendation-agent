import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / "db" / "insurance.db"


GOAL_MAPPING = {
    "medical": ["medical"],
    "accident": ["accident"],
    "life": ["life"],
    "family_protection": ["life"],
    "income_protection": ["critical_illness", "life"],
}


def search_products_by_profile(age: int, budget: int, main_goal: str) -> list[dict]:
    """
    Search candidate insurance products based on user age, annual budget, and main protection goal.

    Args:
        age: User age.
        budget: Annual insurance budget.
        main_goal: Main protection goal. Supported values:
            medical, accident, life, family_protection, income_protection

    Returns:
        A list of candidate products sorted by annual_premium_min ascending.
    """
    normalized_goal = main_goal.strip().lower()
    product_types = GOAL_MAPPING.get(normalized_goal, [])

    if not product_types:
        return []

    placeholders = ",".join(["?"] * len(product_types))

    sql = f"""
    SELECT
        product_id,
        product_name,
        product_type,
        annual_premium_min,
        annual_premium_max,
        coverage_focus,
        coverage_summary,
        waiting_period_days,
        exclusions
    FROM insurance_products
    WHERE is_active = 1
      AND ? BETWEEN target_age_min AND target_age_max
      AND annual_premium_min <= ?
      AND product_type IN ({placeholders})
    ORDER BY annual_premium_min ASC
    """

    params = [age, budget, *product_types]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_product_detail(product_id: int) -> dict | None:
    """
    Get detailed information for a single insurance product by product_id.

    Args:
        product_id: Insurance product ID.

    Returns:
        Product detail as a dictionary, or None if not found.
    """
    sql = """
    SELECT
        product_id,
        product_name,
        product_type,
        target_age_min,
        target_age_max,
        annual_premium_min,
        annual_premium_max,
        coverage_focus,
        coverage_summary,
        waiting_period_days,
        exclusions,
        is_active
    FROM insurance_products
    WHERE product_id = ?
      AND is_active = 1
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(sql, (product_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_recommendation_rules(main_goal: str, has_children: bool = False) -> list[dict]:
    """
    Get recommendation rules related to the user's goal.

    Args:
        main_goal: Main protection goal.
        has_children: Whether the user has children.

    Returns:
        A list of recommendation rules sorted by priority.
    """
    normalized_goal = main_goal.strip().lower()

    candidate_types = GOAL_MAPPING.get(normalized_goal, [])
    if not candidate_types:
        return []

    placeholders = ",".join(["?"] * len(candidate_types))

    sql = f"""
    SELECT
        rule_id,
        rule_name,
        product_type,
        condition_json,
        recommendation_logic,
        priority
    FROM recommendation_rules
    WHERE is_active = 1
      AND product_type IN ({placeholders})
    ORDER BY priority ASC
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, candidate_types).fetchall()
        results = [dict(row) for row in rows]

        if has_children:
            results = sorted(
                results, key=lambda x: 0 if "家庭" in x["rule_name"] else 1
            )

        return results
    finally:
        conn.close()


def summarize_user_profile(
    age: int,
    budget: int,
    main_goal: str,
    marital_status: str = "unknown",
    has_children: bool = False,
    existing_coverage: str = "unknown",
    risk_preference: str = "balanced",
) -> dict:
    """
    Summarize normalized user profile for recommendation reasoning.

    Returns:
        A normalized user profile dictionary.
    """
    return {
        "age": age,
        "budget": budget,
        "main_goal": main_goal.strip().lower(),
        "marital_status": marital_status.strip().lower(),
        "has_children": has_children,
        "existing_coverage": existing_coverage.strip().lower(),
        "risk_preference": risk_preference.strip().lower(),
    }
