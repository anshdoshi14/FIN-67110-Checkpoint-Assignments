Filings: 10-K 0000909832-26-000093; 10-Q 0000909832-26-000051; 8-K / EX-99.1 0000909832-26-000084.

# COST — clean baseline

**SYNTHETIC SOURCE-BASED VERIFIER FIXTURE. This is NOT a model-produced Lab 04 run.**

## Overview

Offline test built from saved SEC source files.

## Market Positioning and Growth Outlook

Human judgement required.

## Valuation Insights

FY revenue: $303,154,000,000 [C:revenue]

Prior FY revenue: $275,235,000,000 [C:revenue_prior]

FY operating income: $11,685,000,000 [C:operating_income]

FY net income: $9,226,000,000 [C:net_income]

FY diluted EPS: $20.76 [C:diluted_eps]

FY closing shareholder equity: $35,803,000,000 [C:equity]

FY revenue growth: 10.14% [C:revenue_growth]

FY operating margin: 3.85% [C:operating_margin]

Return on average equity: 28.40% [C:roe]

Debt to equity (including current maturities): 0.1721x [C:debt_equity]

Free cash flow (CFO less capex): $9,382,000,000 [C:free_cash_flow]

## Future Developments and Strategic Recommendations

Not part of synthetic test.

## Investment Recommendation

Not part of synthetic test.

## Numeric evidence registry

```evidence-json
[
  {
    "id": "revenue",
    "label": "FY revenue",
    "value": 303154000000,
    "display": "$303,154,000,000",
    "source": {
      "kind": "xbrl",
      "field": "revenue",
      "period": "current",
      "tag": "RevenueFromContractWithCustomerExcludingAssessedTax",
      "end": "2026-08-30",
      "accession": "0000909832-26-000093"
    }
  },
  {
    "id": "revenue_prior",
    "label": "Prior FY revenue",
    "value": 275235000000,
    "display": "$275,235,000,000",
    "source": {
      "kind": "xbrl",
      "field": "revenue",
      "period": "prior",
      "tag": "RevenueFromContractWithCustomerExcludingAssessedTax",
      "end": "2025-08-31",
      "accession": "0000909832-26-000093"
    }
  },
  {
    "id": "operating_income",
    "label": "FY operating income",
    "value": 11685000000,
    "display": "$11,685,000,000",
    "source": {
      "kind": "xbrl",
      "field": "operating_income",
      "period": "current",
      "tag": "OperatingIncomeLoss",
      "end": "2026-08-30",
      "accession": "0000909832-26-000093"
    }
  },
  {
    "id": "net_income",
    "label": "FY net income",
    "value": 9226000000,
    "display": "$9,226,000,000",
    "source": {
      "kind": "xbrl",
      "field": "net_income",
      "period": "current",
      "tag": "NetIncomeLoss",
      "end": "2026-08-30",
      "accession": "0000909832-26-000093"
    }
  },
  {
    "id": "diluted_eps",
    "label": "FY diluted EPS",
    "value": 20.76,
    "display": "$20.76",
    "source": {
      "kind": "xbrl",
      "field": "diluted_eps",
      "period": "current",
      "tag": "EarningsPerShareDiluted",
      "end": "2026-08-30",
      "accession": "0000909832-26-000093",
      "document": "10-K",
      "line": 1057,
      "quote": "Net income increased 14% to $9,226, $20.76 per diluted share"
    }
  },
  {
    "id": "equity",
    "label": "FY closing shareholder equity",
    "value": 35803000000,
    "display": "$35,803,000,000",
    "source": {
      "kind": "xbrl",
      "field": "equity",
      "period": "current",
      "tag": "StockholdersEquity",
      "end": "2026-08-30",
      "accession": "0000909832-26-000093"
    }
  },
  {
    "id": "revenue_growth",
    "label": "FY revenue growth",
    "value": 10.14,
    "display": "10.14%",
    "source": {
      "kind": "ratio",
      "definition": "(2026 total revenue - 2025 total revenue)/2025 total revenue \u00d7100",
      "formula": "(a-b)/b*100",
      "inputs": {
        "a": {
          "value": 303154000000,
          "source": {
            "kind": "xbrl",
            "field": "revenue",
            "period": "current",
            "tag": "RevenueFromContractWithCustomerExcludingAssessedTax",
            "end": "2026-08-30",
            "accession": "0000909832-26-000093"
          }
        },
        "b": {
          "value": 275235000000,
          "source": {
            "kind": "xbrl",
            "field": "revenue",
            "period": "prior",
            "tag": "RevenueFromContractWithCustomerExcludingAssessedTax",
            "end": "2025-08-31",
            "accession": "0000909832-26-000093"
          }
        }
      }
    },
    "round_decimals": 2
  },
  {
    "id": "operating_margin",
    "label": "FY operating margin",
    "value": 3.85,
    "display": "3.85%",
    "source": {
      "kind": "ratio",
      "definition": "FY operating income / FY total revenue \u00d7100",
      "formula": "a/b*100",
      "inputs": {
        "a": {
          "value": 11685000000,
          "source": {
            "kind": "xbrl",
            "field": "operating_income",
            "period": "current",
            "tag": "OperatingIncomeLoss",
            "end": "2026-08-30",
            "accession": "0000909832-26-000093"
          }
        },
        "b": {
          "value": 303154000000,
          "source": {
            "kind": "xbrl",
            "field": "revenue",
            "period": "current",
            "tag": "RevenueFromContractWithCustomerExcludingAssessedTax",
            "end": "2026-08-30",
            "accession": "0000909832-26-000093"
          }
        }
      }
    },
    "round_decimals": 2
  },
  {
    "id": "roe",
    "label": "Return on average equity",
    "value": 28.4,
    "display": "28.40%",
    "source": {
      "kind": "ratio",
      "definition": "net income / average of end-2026 and end-2025 stockholders equity \u00d7100",
      "formula": "a/((b+c)/2)*100",
      "inputs": {
        "a": {
          "value": 9226000000,
          "source": {
            "kind": "xbrl",
            "field": "net_income",
            "period": "current",
            "tag": "NetIncomeLoss",
            "end": "2026-08-30",
            "accession": "0000909832-26-000093"
          }
        },
        "b": {
          "value": 35803000000,
          "source": {
            "kind": "xbrl",
            "field": "equity",
            "period": "current",
            "tag": "StockholdersEquity",
            "end": "2026-08-30",
            "accession": "0000909832-26-000093"
          }
        },
        "c": {
          "value": 29164000000,
          "source": {
            "kind": "xbrl",
            "field": "equity",
            "period": "prior",
            "tag": "StockholdersEquity",
            "end": "2025-08-31",
            "accession": "0000909832-26-000093"
          }
        }
      }
    },
    "round_decimals": 2
  },
  {
    "id": "debt_equity",
    "label": "Debt to equity (including current maturities)",
    "value": 0.1721,
    "display": "0.1721x",
    "source": {
      "kind": "ratio",
      "definition": "(current and noncurrent long-term debt) / closing equity",
      "formula": "(a+b)/c",
      "inputs": {
        "a": {
          "value": 3914000000,
          "source": {
            "kind": "xbrl",
            "field": "long_term_debt_noncurrent",
            "period": "current",
            "tag": "LongTermDebtNoncurrent",
            "end": "2026-08-30",
            "accession": "0000909832-26-000093"
          }
        },
        "b": {
          "value": 2248000000,
          "source": {
            "kind": "xbrl",
            "field": "long_term_debt_current",
            "period": "current",
            "tag": "LongTermDebtCurrent",
            "end": "2026-08-30",
            "accession": "0000909832-26-000093"
          }
        },
        "c": {
          "value": 35803000000,
          "source": {
            "kind": "xbrl",
            "field": "equity",
            "period": "current",
            "tag": "StockholdersEquity",
            "end": "2026-08-30",
            "accession": "0000909832-26-000093"
          }
        }
      }
    },
    "round_decimals": 4
  },
  {
    "id": "free_cash_flow",
    "label": "Free cash flow (CFO less capex)",
    "value": 9382000000,
    "display": "$9,382,000,000",
    "source": {
      "kind": "ratio",
      "definition": "cash from operations less capital expenditures USD",
      "formula": "a-b",
      "inputs": {
        "a": {
          "value": 15817000000,
          "source": {
            "kind": "xbrl",
            "field": "cash_from_operations",
            "period": "current",
            "tag": "NetCashProvidedByUsedInOperatingActivities",
            "end": "2026-08-30",
            "accession": "0000909832-26-000093"
          }
        },
        "b": {
          "value": 6435000000,
          "source": {
            "kind": "xbrl",
            "field": "capex",
            "period": "current",
            "tag": "PaymentsToAcquirePropertyPlantAndEquipment",
            "end": "2026-08-30",
            "accession": "0000909832-26-000093"
          }
        }
      }
    },
    "round_decimals": 0
  }
]
```
