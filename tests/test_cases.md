# Insurance Recommendation Agent Test Cases

## Case 1: Medical protection / complete info
Input:
我 30 歲，年度保險預算 15000，想加強醫療保障，有什麼推薦？

Expected:
- Use insurance-specific tools
- Recommend 安心住院醫療方案 A
- Mention waiting period and exclusions
- Include disclaimer

## Case 2: Missing information
Input:
我想買保險，幫我推薦。

Expected:
- Ask follow-up questions
- Do not recommend immediately
- Do not call product search tool yet

## Case 3: Family protection
Input:
我 42 歲，已婚有小孩，年度預算 30000，想補家庭保障。

Expected:
- Map family_protection to life
- Recommend 家庭定期壽險方案 C
- Use recommendation rule about family responsibility
- Include disclaimer

## Case 4: Low budget young user
Input:
我 27 歲，年度預算 8000，想先補意外保障。

Expected:
- Recommend 新鮮人基礎保障方案 F or 安心意外防護方案 D
- Prefer lower entry budget product
- Include exclusions reminder

## Case 5: Income protection
Input:
我 38 歲，已婚有小孩，年度預算 25000，想加強收入中斷風險保障。

Expected:
- Map to critical_illness or life
- Recommend a reasonable candidate from available products
- Explain rule basis if available
- Include disclaimer

## Case 6: No exact match
Input:
我 68 歲，年度預算 10000，想加強醫療保障。

Expected:
- Explain no exact match if necessary
- Offer closest candidate carefully
- Do not fabricate unavailable products
- Include disclaimer