from pprint import pprint

from app.tools.insurance_tools import (
    search_products_by_profile,
    get_product_detail,
    get_recommendation_rules,
)


def main():
    print("=== search_products_by_profile ===")
    result = search_products_by_profile(age=30, budget=15000, main_goal="medical")
    pprint(result)

    print("\n=== get_product_detail ===")
    detail = get_product_detail(product_id=1)
    pprint(detail)

    print("\n=== get_recommendation_rules ===")
    rules = get_recommendation_rules(main_goal="family_protection", has_children=True)
    pprint(rules)


if __name__ == "__main__":
    main()
