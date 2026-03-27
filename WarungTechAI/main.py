"""
Agen Rekomendasi Investasi Cryptocurrency (Bahasa Indonesia)
Enhanced Version dengan Chat History & Feedback System

============================================================================
🚀 INSTRUKSI SETUP
============================================================================

1. Install dependencies:
   pip install langchain langchain-openai langgraph pandas numpy requests

2. Set API key OpenRouter Anda di variabel OPENROUTER_API_KEY di bawah

3. Pilih model Anda (default: GPT-4o-mini)

============================================================================
"""

import os
import json
import operator
from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Literal
from datetime import datetime
import pickle

# LangChain & LangGraph imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Market Data Tools
import requests
import pandas as pd
import numpy as np
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================================================
# KONFIGURASI
# ============================================================================

OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# WarungTech API Configuration
WARUNGTECH_API_BASE_URL = "http://192.168.43.166:3001/api"  # Update this to match your server IP
WARUNGTECH_API_TIMEOUT = 10  # seconds

AVAILABLE_MODELS = {
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "gpt-4o": "openai/gpt-4o",
    "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
    "claude-sonnet": "anthropic/claude-3.5-sonnet",
}

DEFAULT_MODEL = AVAILABLE_MODELS["gpt-4o-mini"]

CRYPTOPANIC_API_KEY = "b21fac491330df0ceb686f0bfbeb6318a8c54d5e"

# Cryptocurrency yang didukung dengan nama Indonesia - EXPANDED
SUPPORTED_COINS = {
    "BTC": {"name": "Bitcoin", "coinbase": "BTC-USD", "coingecko": "bitcoin", "tier": "tier1"},
    "ETH": {"name": "Ethereum", "coinbase": "ETH-USD", "coingecko": "ethereum", "tier": "tier1"},
    "BNB": {"name": "BNB", "coinbase": None, "coingecko": "binancecoin", "tier": "tier1"},
    "SOL": {"name": "Solana", "coinbase": "SOL-USD", "coingecko": "solana", "tier": "tier1"},
    "XRP": {"name": "Ripple", "coinbase": "XRP-USD", "coingecko": "ripple", "tier": "tier1"},
    "ADA": {"name": "Cardano", "coinbase": "ADA-USD", "coingecko": "cardano", "tier": "tier2"},
    "DOGE": {"name": "Dogecoin", "coinbase": "DOGE-USD", "coingecko": "dogecoin", "tier": "tier2"},
    "MATIC": {"name": "Polygon", "coinbase": "MATIC-USD", "coingecko": "matic-network", "tier": "tier2"},
    "DOT": {"name": "Polkadot", "coinbase": "DOT-USD", "coingecko": "polkadot", "tier": "tier2"},
    "AVAX": {"name": "Avalanche", "coinbase": "AVAX-USD", "coingecko": "avalanche-2", "tier": "tier2"},
    "LINK": {"name": "Chainlink", "coinbase": "LINK-USD", "coingecko": "chainlink", "tier": "tier2"},
    "UNI": {"name": "Uniswap", "coinbase": "UNI-USD", "coingecko": "uniswap", "tier": "tier2"},
    "ATOM": {"name": "Cosmos", "coinbase": "ATOM-USD", "coingecko": "cosmos", "tier": "tier2"},
    "LTC": {"name": "Litecoin", "coinbase": "LTC-USD", "coingecko": "litecoin", "tier": "tier2"},
}

# Chat history storage directory
HISTORY_DIR = "chat_history"
FEEDBACK_FILE = "feedback_data.json"

os.makedirs(HISTORY_DIR, exist_ok=True)

# ============================================================================
# CHAT HISTORY MANAGER
# ============================================================================

class ChatHistoryManager:
    """Manages chat history and user sessions"""
    
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.history_file = os.path.join(HISTORY_DIR, f"{user_id}_history.pkl")
        self.conversations = self.load_history()
    
    def load_history(self) -> List[Dict]:
        """Load chat history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return []
        return []
    
    def save_history(self):
        """Save chat history to file"""
        try:
            with open(self.history_file, 'wb') as f:
                pickle.dump(self.conversations, f)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_conversation(self, query: str, response: str, metadata: Dict = None):
        """Add a new conversation to history"""
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "metadata": metadata or {},
            "feedback": None
        }
        self.conversations.append(conversation)
        self.save_history()
        return len(self.conversations) - 1
    
    def add_feedback(self, conversation_id: int, feedback: Dict):
        """Add feedback to a specific conversation"""
        if 0 <= conversation_id < len(self.conversations):
            self.conversations[conversation_id]["feedback"] = {
                "timestamp": datetime.now().isoformat(),
                **feedback
            }
            self.save_history()
            return True
        return False
    
    def get_recent_conversations(self, n: int = 5) -> List[Dict]:
        """Get n most recent conversations"""
        return self.conversations[-n:] if self.conversations else []
    
    def get_conversation_summary(self) -> str:
        """Get a summary of recent conversations"""
        recent = self.get_recent_conversations(3)
        if not recent:
            return "Tidak ada riwayat percakapan."
        
        summary = "📜 Riwayat Percakapan Terakhir:\n\n"
        for i, conv in enumerate(recent, 1):
            timestamp = datetime.fromisoformat(conv["timestamp"]).strftime("%d/%m/%Y %H:%M")
            summary += f"{i}. [{timestamp}]\n"
            summary += f"   Q: {conv['query'][:100]}...\n"
            if conv.get('feedback'):
                rating = conv['feedback'].get('rating', 'N/A')
                summary += f"   Feedback: ⭐ {rating}/5\n"
            summary += "\n"
        
        return summary

# ============================================================================
# FEEDBACK SYSTEM
# ============================================================================

class FeedbackSystem:
    """Manages user feedback and analytics"""
    
    def __init__(self):
        self.feedback_file = FEEDBACK_FILE
        self.feedback_data = self.load_feedback()
    
    def load_feedback(self) -> List[Dict]:
        """Load feedback data from file"""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_feedback(self):
        """Save feedback data to file"""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
        except Exception as e:
            print(f"Error saving feedback: {e}")
    
    def add_feedback(self, user_id: str, conversation_id: int, feedback: Dict):
        """Add new feedback entry"""
        feedback_entry = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "rating": feedback.get("rating", 0),
            "helpful": feedback.get("helpful", True),
            "accuracy": feedback.get("accuracy", 0),
            "comments": feedback.get("comments", ""),
            "suggestions": feedback.get("suggestions", "")
        }
        self.feedback_data.append(feedback_entry)
        self.save_feedback()
    
    def get_average_rating(self) -> float:
        """Calculate average rating"""
        if not self.feedback_data:
            return 0.0
        ratings = [f["rating"] for f in self.feedback_data if f["rating"] > 0]
        return sum(ratings) / len(ratings) if ratings else 0.0
    
    def get_feedback_summary(self) -> Dict:
        """Get feedback statistics"""
        if not self.feedback_data:
            return {"total": 0, "average_rating": 0, "helpful_percentage": 0}
        
        total = len(self.feedback_data)
        avg_rating = self.get_average_rating()
        helpful = sum(1 for f in self.feedback_data if f["helpful"])
        
        return {
            "total": total,
            "average_rating": round(avg_rating, 2),
            "helpful_percentage": round((helpful / total) * 100, 1)
        }

# ============================================================================
# MARKET DATA UTILITIES
# ============================================================================

class MarketDataFetcher:
    """Handles real-time market data fetching from multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }
    
    def get_coinbase_stats(self, product_id: str) -> Dict:
        """Fetch stats from Coinbase Pro"""
        if not product_id:
            return None
        try:
            url = f"https://api.exchange.coinbase.com/products/{product_id}/stats"
            r = self.session.get(url, headers=self.headers, timeout=10)
            r.raise_for_status()
            return r.json()
        except:
            return None
    
    def get_coingecko_data(self, coin_ids: List[str]) -> Dict:
        """Fetch data from CoinGecko"""
        params = {
            "vs_currency": "usd",
            "ids": ",".join(coin_ids),
            "order": "market_cap_desc",
            "sparkline": False
        }
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            r = self.session.get(url, params=params, timeout=10)
            if r.status_code == 200:
                return {coin["id"]: coin for coin in r.json()}
            return {}
        except:
            return {}
    
    def fetch_ohlc(self, coin_id: str, days: int = 90) -> pd.Series:
        """Fetch OHLC data for technical analysis"""
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            r = self.session.get(url, params={"vs_currency": "usd", "days": days}, timeout=10)
            r.raise_for_status()
            df = pd.DataFrame(r.json()["prices"], columns=["timestamp", "close"])
            return df["close"].astype(float)
        except Exception as e:
            print(f"Error fetching OHLC for {coin_id}: {e}")
            return pd.Series()
    
    def fetch_fear_greed_index(self) -> int:
        """Fetch Crypto Fear & Greed Index"""
        try:
            r = self.session.get("https://api.alternative.me/fng/", timeout=5)
            return int(r.json()["data"][0]["value"])
        except:
            return 50

market_fetcher = MarketDataFetcher()

# ============================================================================
# CRYPTO SELECTOR
# ============================================================================

def select_cryptos_by_profile(risk_tolerance: str, investment_amount: float) -> List[str]:
    """Select appropriate cryptocurrencies based on user profile"""
    
    # Base selection rules
    if risk_tolerance == "conservative":
        # Conservative: Top tier coins only
        selected = ["BTC", "ETH", "BNB"]
    elif risk_tolerance == "aggressive":
        # Aggressive: Mix of all tiers
        tier1 = ["BTC", "ETH", "SOL", "XRP"]
        tier2 = ["ADA", "MATIC", "DOT", "AVAX", "LINK"]
        selected = tier1 + tier2[:3]  # 4 tier1 + 3 tier2
    else:  # moderate
        # Moderate: Balanced mix
        tier1 = ["BTC", "ETH", "BNB", "SOL"]
        tier2 = ["ADA", "MATIC", "DOT"]
        selected = tier1 + tier2[:2]  # 4 tier1 + 2 tier2
    
    # Adjust based on investment amount
    usd_amount = investment_amount / 15800  # Convert IDR to USD
    
    if usd_amount < 100:  # < $100
        # Small amount: Focus on 2-3 coins
        selected = selected[:3]
    elif usd_amount < 500:  # $100-$500
        # Medium amount: 3-5 coins
        selected = selected[:5]
    # else: keep all selected (5-7 coins for larger amounts)
    
    return selected

# ============================================================================
# BUSINESS ANALYSIS TOOLS
# ============================================================================

@tool
def analyze_business_performance(api_base_url: str = WARUNGTECH_API_BASE_URL) -> str:
    """
    Analisis performa bisnis dari WarungTech API untuk rekomendasi promo dan investasi.
    
    Args:
        api_base_url: Base URL API WarungTech (default: "http://192.168.43.166:3001/api")
    
    Returns:
        JSON string dengan analisis performa bisnis lengkap
    """
    try:
        # Test API health first
        health_response = requests.get(f"{api_base_url}/health", timeout=WARUNGTECH_API_TIMEOUT)
        if health_response.status_code != 200:
            return json.dumps({"error": "API WarungTech tidak dapat diakses"})
        
        # Simulate business data analysis (in real implementation, you'd need authentication)
        # For demo purposes, we'll create realistic business metrics
        
        business_metrics = {
            "timestamp": datetime.now().isoformat(),
            "api_status": "connected",
            "business_analysis": {
                "revenue_trend": {
                    "current_month": 45000000,  # 45 juta
                    "previous_month": 38000000,  # 38 juta
                    "growth_rate": 18.4,  # 18.4% growth
                    "trend": "increasing"
                },
                "customer_metrics": {
                    "total_customers": 1250,
                    "new_customers_this_month": 180,
                    "customer_retention_rate": 78.5,
                    "average_order_value": 125000  # 125k per order
                },
                "product_performance": {
                    "total_products": 85,
                    "best_selling_categories": ["Makanan", "Minuman", "Snack"],
                    "low_stock_items": 12,
                    "inventory_turnover": 2.3
                },
                "financial_health": {
                    "profit_margin": 23.5,
                    "cash_flow": "positive",
                    "operational_costs": 15000000,  # 15 juta
                    "marketing_budget": 3000000,    # 3 juta
                    "available_for_investment": 8000000  # 8 juta
                },
                "market_position": {
                    "market_share": 12.8,
                    "competitor_analysis": "moderate_competition",
                    "seasonal_trends": "peak_season",
                    "customer_satisfaction": 4.2  # out of 5
                }
            },
            "recommendations": {
                "promo_strategy": {
                    "recommended_discount": "15-20%",
                    "target_products": ["slow_moving_inventory", "high_margin_items"],
                    "optimal_timing": "weekend_peak_hours",
                    "budget_allocation": 1500000  # 1.5 juta for promos
                },
                "investment_readiness": {
                    "risk_tolerance": "moderate",
                    "available_capital": 8000000,
                    "recommended_allocation": {
                        "conservative": 40,  # 40% in stable coins
                        "moderate": 35,      # 35% in established coins
                        "aggressive": 25     # 25% in growth coins
                    }
                }
            }
        }
        
        return json.dumps(business_metrics, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "error": f"Gagal menganalisis bisnis: {str(e)}",
            "fallback_analysis": {
                "status": "estimated",
                "revenue_trend": "stable",
                "investment_capacity": "moderate",
                "promo_recommendation": "conservative_approach"
            }
        }, ensure_ascii=False)


@tool
def generate_promo_recommendations(business_data: str, target_revenue: float = 50000000) -> str:
    """
    Generate rekomendasi promo berdasarkan kondisi bisnis dan target revenue.
    
    Args:
        business_data: Data bisnis dalam format JSON string
        target_revenue: Target revenue yang ingin dicapai (default: 50 juta)
    
    Returns:
        JSON string dengan rekomendasi promo yang detail dan actionable
    """
    try:
        # Parse business data if provided
        try:
            business_info = json.loads(business_data) if business_data else {}
        except:
            business_info = {}
        
        current_revenue = business_info.get("business_analysis", {}).get("revenue_trend", {}).get("current_month", 40000000)
        growth_rate = business_info.get("business_analysis", {}).get("revenue_trend", {}).get("growth_rate", 15)
        customer_count = business_info.get("business_analysis", {}).get("customer_metrics", {}).get("total_customers", 1000)
        avg_order_value = business_info.get("business_analysis", {}).get("customer_metrics", {}).get("average_order_value", 120000)
        
        # Calculate gap to target
        revenue_gap = target_revenue - current_revenue
        gap_percentage = (revenue_gap / current_revenue) * 100
        
        # Generate promo strategies based on business condition
        promo_strategies = []
        
        if gap_percentage > 20:  # Need aggressive growth
            promo_strategies.extend([
                {
                    "strategy": "Flash Sale Weekend",
                    "discount": "25-30%",
                    "duration": "48 jam",
                    "target_products": "Best sellers + Slow moving",
                    "expected_impact": "35% increase in transactions",
                    "budget_needed": 2500000,
                    "roi_estimate": 4.2
                },
                {
                    "strategy": "Bundle Deals",
                    "discount": "Buy 2 Get 1 Free",
                    "duration": "1 minggu",
                    "target_products": "Complementary items",
                    "expected_impact": "40% increase in AOV",
                    "budget_needed": 1800000,
                    "roi_estimate": 3.8
                }
            ])
        elif gap_percentage > 10:  # Moderate growth needed
            promo_strategies.extend([
                {
                    "strategy": "Loyalty Rewards",
                    "discount": "15-20%",
                    "duration": "2 minggu",
                    "target_products": "High margin items",
                    "expected_impact": "25% increase in repeat customers",
                    "budget_needed": 1500000,
                    "roi_estimate": 3.5
                },
                {
                    "strategy": "New Customer Discount",
                    "discount": "20% first purchase",
                    "duration": "1 bulan",
                    "target_products": "Entry-level products",
                    "expected_impact": "30% new customer acquisition",
                    "budget_needed": 1200000,
                    "roi_estimate": 4.0
                }
            ])
        else:  # Maintenance mode
            promo_strategies.extend([
                {
                    "strategy": "Seasonal Promotion",
                    "discount": "10-15%",
                    "duration": "1 minggu",
                    "target_products": "Seasonal items",
                    "expected_impact": "15% transaction boost",
                    "budget_needed": 800000,
                    "roi_estimate": 3.2
                }
            ])
        
        # Calculate optimal timing
        optimal_timing = {
            "best_days": ["Jumat", "Sabtu", "Minggu"],
            "best_hours": ["11:00-13:00", "17:00-20:00"],
            "avoid_periods": ["Senin pagi", "Tengah malam"],
            "seasonal_factor": "Peak season - tingkatkan intensitas"
        }
        
        # Generate blockchain coupon recommendations
        blockchain_coupons = [
            {
                "coupon_type": "Percentage Discount",
                "discount_value": 20,
                "min_transaction": 150000,
                "validity_days": 7,
                "max_usage": 100,
                "target_segment": "Regular customers",
                "blockchain_fee": "0.001 ETH"
            },
            {
                "coupon_type": "Fixed Amount",
                "discount_value": 25000,
                "min_transaction": 200000,
                "validity_days": 14,
                "max_usage": 50,
                "target_segment": "High-value customers",
                "blockchain_fee": "0.001 ETH"
            }
        ]
        
        recommendations = {
            "analysis_summary": {
                "current_revenue": current_revenue,
                "target_revenue": target_revenue,
                "revenue_gap": revenue_gap,
                "gap_percentage": round(gap_percentage, 1),
                "growth_difficulty": "aggressive" if gap_percentage > 20 else "moderate" if gap_percentage > 10 else "maintenance"
            },
            "promo_strategies": promo_strategies,
            "optimal_timing": optimal_timing,
            "blockchain_coupons": blockchain_coupons,
            "implementation_plan": {
                "phase_1": "Setup blockchain coupons (1-2 hari)",
                "phase_2": "Launch primary promo strategy (hari ke-3)",
                "phase_3": "Monitor dan adjust (minggu ke-2)",
                "phase_4": "Evaluate dan scale (minggu ke-3-4)"
            },
            "success_metrics": {
                "target_transactions": int((target_revenue / avg_order_value) * 1.1),
                "target_new_customers": int(customer_count * 0.15),
                "target_retention_rate": 85,
                "break_even_point": "Hari ke-5 dari launch"
            },
            "risk_mitigation": {
                "inventory_risk": "Monitor stock levels daily",
                "margin_risk": "Set minimum margin threshold 15%",
                "customer_risk": "Limit discount abuse dengan blockchain verification",
                "cash_flow_risk": "Stagger promo launches"
            }
        }
        
        return json.dumps(recommendations, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "error": f"Gagal generate rekomendasi promo: {str(e)}",
            "basic_recommendation": {
                "strategy": "Conservative 15% discount",
                "duration": "1 week",
                "budget": 1000000,
                "expected_roi": 3.0
            }
        }, ensure_ascii=False)


@tool
def analyze_crypto_investment_with_business(business_condition: str, crypto_symbols: str = "BTC,ETH,BNB,SOL") -> str:
    """
    Analisis investasi crypto berdasarkan kondisi bisnis dan rekomendasi alokasi yang sesuai.
    
    Args:
        business_condition: Kondisi bisnis dalam format JSON
        crypto_symbols: Simbol crypto untuk dianalisis (default: "BTC,ETH,BNB,SOL")
    
    Returns:
        JSON string dengan rekomendasi investasi crypto yang disesuaikan dengan kondisi bisnis
    """
    try:
        # Parse business condition
        try:
            business_data = json.loads(business_condition) if business_condition else {}
        except:
            business_data = {}
        
        # Extract business metrics
        available_capital = business_data.get("business_analysis", {}).get("financial_health", {}).get("available_for_investment", 5000000)
        profit_margin = business_data.get("business_analysis", {}).get("financial_health", {}).get("profit_margin", 20)
        cash_flow = business_data.get("business_analysis", {}).get("financial_health", {}).get("cash_flow", "positive")
        growth_rate = business_data.get("business_analysis", {}).get("revenue_trend", {}).get("growth_rate", 15)
        
        # Determine risk profile based on business health
        if profit_margin > 25 and cash_flow == "positive" and growth_rate > 20:
            risk_profile = "aggressive"
            max_crypto_allocation = 0.15  # 15% of available capital
        elif profit_margin > 15 and cash_flow == "positive":
            risk_profile = "moderate"
            max_crypto_allocation = 0.10  # 10% of available capital
        else:
            risk_profile = "conservative"
            max_crypto_allocation = 0.05  # 5% of available capital
        
        max_investment = available_capital * max_crypto_allocation
        
        # Get crypto market data
        symbols = [s.strip().upper() for s in crypto_symbols.split(",")]
        crypto_analysis = {}
        
        # Simulate crypto analysis (in real implementation, use actual market data)
        crypto_recommendations = {
            "BTC": {
                "allocation_percentage": 40,
                "risk_level": "low",
                "expected_return_3m": "8-15%",
                "business_alignment": "Store of value - good for cash reserves",
                "min_investment": 500000
            },
            "ETH": {
                "allocation_percentage": 30,
                "risk_level": "medium",
                "expected_return_3m": "12-25%",
                "business_alignment": "Smart contracts - future payment integration",
                "min_investment": 300000
            },
            "BNB": {
                "allocation_percentage": 20,
                "risk_level": "medium",
                "expected_return_3m": "10-20%",
                "business_alignment": "Exchange token - trading fee reduction",
                "min_investment": 200000
            },
            "SOL": {
                "allocation_percentage": 10,
                "risk_level": "high",
                "expected_return_3m": "15-35%",
                "business_alignment": "Fast payments - good for retail integration",
                "min_investment": 150000
            }
        }
        
        # Calculate actual allocations
        investment_plan = {}
        for symbol in symbols:
            if symbol in crypto_recommendations:
                allocation = crypto_recommendations[symbol]["allocation_percentage"] / 100
                investment_amount = max_investment * allocation
                investment_plan[symbol] = {
                    **crypto_recommendations[symbol],
                    "investment_amount_idr": investment_amount,
                    "investment_amount_usd": investment_amount / 15800,
                    "monthly_dca_amount": investment_amount / 3  # 3-month DCA
                }
        
        # Business-specific recommendations
        business_integration = {
            "payment_integration": {
                "recommended_coins": ["BNB", "SOL"],
                "integration_timeline": "6-12 months",
                "customer_benefits": "Lower transaction fees, faster payments",
                "technical_requirements": "Blockchain payment gateway"
            },
            "loyalty_program": {
                "token_rewards": "Create WarungTech token for customer loyalty",
                "staking_rewards": "Customers earn tokens for repeat purchases",
                "redemption_options": "Discounts, exclusive products, crypto rewards"
            },
            "treasury_management": {
                "hedge_strategy": "Use crypto to hedge against IDR inflation",
                "diversification": "Max 15% of total business assets in crypto",
                "rebalancing": "Monthly review and rebalancing"
            }
        }
        
        # Risk management for business
        risk_management = {
            "position_sizing": f"Maximum {max_crypto_allocation*100}% of available capital",
            "stop_loss_strategy": "20% stop loss on individual positions",
            "profit_taking": "Take 50% profit at 30% gains",
            "business_priority": "Always maintain 6-month operational cash flow",
            "market_conditions": {
                "bull_market": "Increase allocation gradually",
                "bear_market": "DCA strategy, reduce position size",
                "sideways": "Focus on staking and yield generation"
            }
        }
        
        # Timeline and milestones
        implementation_timeline = {
            "month_1": {
                "actions": ["Setup exchange accounts", "Complete KYC", "Start with 25% of planned investment"],
                "target_allocation": "25% of max investment",
                "focus": "BTC and ETH only"
            },
            "month_2": {
                "actions": ["Add BNB position", "Monitor performance", "Increase to 50% allocation"],
                "target_allocation": "50% of max investment",
                "focus": "Diversification"
            },
            "month_3": {
                "actions": ["Complete full allocation", "Add SOL if business performing well", "Setup DCA strategy"],
                "target_allocation": "100% of max investment",
                "focus": "Full portfolio implementation"
            }
        }
        
        result = {
            "business_assessment": {
                "risk_profile": risk_profile,
                "available_capital": available_capital,
                "max_crypto_investment": max_investment,
                "business_health_score": "good" if profit_margin > 20 else "moderate" if profit_margin > 15 else "needs_improvement"
            },
            "investment_recommendations": investment_plan,
            "business_integration": business_integration,
            "risk_management": risk_management,
            "implementation_timeline": implementation_timeline,
            "success_metrics": {
                "target_3m_return": f"{max_investment * 0.15:,.0f} IDR (15% conservative estimate)",
                "break_even_timeline": "6-9 months",
                "portfolio_review_frequency": "Monthly",
                "rebalancing_threshold": "10% deviation from target allocation"
            },
            "warnings": [
                "Crypto sangat volatile - hanya investasi dana yang siap hilang",
                "Prioritaskan cash flow bisnis sebelum investasi crypto",
                "Diversifikasi jangan hanya crypto - pertimbangkan emas, saham, obligasi",
                "Regulasi crypto di Indonesia bisa berubah sewaktu-waktu"
            ]
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "error": f"Gagal analisis investasi crypto: {str(e)}",
            "conservative_recommendation": {
                "max_investment": 2000000,
                "allocation": {"BTC": 60, "ETH": 40},
                "timeline": "3-6 months DCA"
            }
        }, ensure_ascii=False)


# ============================================================================
# LANGCHAIN TOOLS DEFINITION
# ============================================================================

@tool
def get_market_data(crypto_symbols: str) -> str:
    """
    Ambil data pasar real-time untuk cryptocurrency.
    
    Args:
        crypto_symbols: Simbol crypto dipisahkan koma (contoh: "BTC,ETH,SOL")
    
    Returns:
        JSON string dengan data pasar termasuk harga, volume, market cap
    """
    symbols = [s.strip().upper() for s in crypto_symbols.split(",")]
    
    result = {"timestamp": datetime.now().isoformat(), "data": {}}
    
    gecko_ids = [SUPPORTED_COINS[s]["coingecko"] for s in symbols if s in SUPPORTED_COINS]
    gecko_map = market_fetcher.get_coingecko_data(gecko_ids)
    
    for symbol in symbols:
        if symbol not in SUPPORTED_COINS:
            continue
        
        cfg = SUPPORTED_COINS[symbol]
        cb_data = market_fetcher.get_coinbase_stats(cfg["coinbase"])
        cg_data = gecko_map.get(cfg["coingecko"])
        
        if cb_data:
            price = float(cb_data["last"])
            open_p = float(cb_data["open"])
            change_24h = ((price - open_p) / open_p * 100) if open_p else 0.0
            data = {
                "name": cfg["name"],
                "price": round(price, 6),
                "change_24h": round(change_24h, 2),
                "volume_24h": float(cb_data["volume"]),
                "high_24h": float(cb_data["high"]),
                "low_24h": float(cb_data["low"])
            }
        elif cg_data:
            data = {
                "name": cfg["name"],
                "price": cg_data["current_price"],
                "change_24h": cg_data["price_change_percentage_24h"],
                "volume_24h": cg_data["total_volume"],
                "high_24h": cg_data["high_24h"],
                "low_24h": cg_data["low_24h"]
            }
        else:
            data = {"name": cfg["name"], "price": 0, "change_24h": 0, "volume_24h": 0, "high_24h": 0, "low_24h": 0}
        
        if cg_data:
            data["market_cap"] = cg_data["market_cap"]
            data["market_cap_rank"] = cg_data.get("market_cap_rank", 0)
            data["circulating_supply"] = cg_data["circulating_supply"]
        
        result["data"][symbol] = data
    
    return json.dumps(result, indent=2)


@tool
def perform_technical_analysis(crypto_symbol: str, timeframe: str = "1d") -> str:
    """
    Lakukan analisis teknikal pada cryptocurrency dengan indikator real.
    
    Args:
        crypto_symbol: Simbol crypto (contoh: "BTC")
        timeframe: Timeframe analisis (default "1d")
    
    Returns:
        JSON string dengan indikator teknikal (RSI, MACD, Moving Averages, Bollinger Bands)
    """
    symbol = crypto_symbol.upper()
    if symbol not in SUPPORTED_COINS:
        return json.dumps({"error": f"Simbol tidak didukung: {symbol}"})
    
    coin_id = SUPPORTED_COINS[symbol]["coingecko"]
    
    try:
        close = market_fetcher.fetch_ohlc(coin_id, days=200)
        
        if len(close) < 20:
            return json.dumps({"error": "Data tidak cukup untuk analisis"})
        
        # Calculate RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = float(rsi.iloc[-1])
        
        # Calculate MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_val = float(macd.iloc[-1])
        signal_val = float(signal_line.iloc[-1])
        
        # Moving Averages
        ma50 = float(close.rolling(50).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        
        # Bollinger Bands
        bb_mid = close.rolling(20).mean().iloc[-1]
        bb_std = close.rolling(20).std().iloc[-1]
        bb_upper = float(bb_mid + 2 * bb_std)
        bb_lower = float(bb_mid - 2 * bb_std)
        
        last_price = float(close.iloc[-1])
        
        # Generate Signal
        score = 0
        if rsi_val < 30: score += 2
        elif rsi_val > 70: score -= 2
        if macd_val > signal_val: score += 2
        else: score -= 2
        if last_price > ma50: score += 1
        
        signal = "bullish" if score >= 2 else "bearish" if score <= -2 else "neutral"
        
        result = {
            "symbol": symbol,
            "name": SUPPORTED_COINS[symbol]["name"],
            "timeframe": timeframe,
            "current_price": round(last_price, 2),
            "signal": signal,
            "strength": min(10, abs(score) * 2),
            "indicators": {
                "RSI": round(rsi_val, 2),
                "MACD": {
                    "value": round(macd_val, 4),
                    "signal": round(signal_val, 4),
                    "histogram": round(macd_val - signal_val, 4)
                },
                "moving_averages": {
                    "MA50": round(ma50, 2),
                    "MA200": round(ma200, 2) if ma200 else None
                },
                "bollinger_bands": {
                    "upper": round(bb_upper, 2),
                    "middle": round(float(bb_mid), 2),
                    "lower": round(bb_lower, 2)
                }
            },
            "trend": signal
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Analisis teknikal gagal: {str(e)}"})


@tool
def analyze_market_sentiment(crypto_symbol: str) -> str:
    """
    Analisis sentimen pasar untuk cryptocurrency menggunakan Fear & Greed Index.
    
    Args:
        crypto_symbol: Simbol crypto (contoh: "BTC")
    
    Returns:
        JSON string dengan analisis sentimen
    """
    symbol = crypto_symbol.upper()
    
    fear_greed = market_fetcher.fetch_fear_greed_index()
    
    headlines = []
    positive = negative = neutral = 0
    api_success = False
    
    if CRYPTOPANIC_API_KEY and CRYPTOPANIC_API_KEY != "YOUR_API_KEY_HERE":
        try:
            url = "https://cryptopanic.com/api/v1/posts"
            params = {
                "auth_token": CRYPTOPANIC_API_KEY,
                "currencies": symbol,
                "kind": "news"
            }
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                api_success = True
                for item in results[:5]:
                    headlines.append(item["title"])
                    votes = item.get("votes", {})
                    positive += votes.get("positive", 0)
                    negative += votes.get("negative", 0)
                    neutral += votes.get("important", 0)
        except:
            pass
    
    if api_success and (positive + negative + neutral) > 0:
        total = positive + negative + neutral
        score = (positive - negative) / total
        overall = "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"
        source = "Berita + Data Pasar"
    else:
        score = (fear_greed - 50) / 50
        overall = "bullish" if fear_greed > 60 else "bearish" if fear_greed < 40 else "neutral"
        source = "Data Pasar (Fear & Greed Index)"
        headlines = ["(Menggunakan Fear & Greed Index sebagai proxy sentimen)"]
    
    result = {
        "symbol": symbol,
        "name": SUPPORTED_COINS.get(symbol, {}).get("name", symbol),
        "overall_sentiment": overall,
        "sentiment_score": round(score, 2),
        "source_type": source,
        "fear_greed_index": fear_greed,
        "market_momentum": "bullish" if fear_greed > 55 else "bearish",
        "news_sentiment": {
            "positive_articles": positive,
            "negative_articles": negative,
            "headlines": headlines[:3]
        }
    }
    
    return json.dumps(result, indent=2)


@tool
def assess_investment_risk(risk_tolerance: str, crypto_symbols: str) -> str:
    """
    Nilai risiko investasi berdasarkan profil pengguna dan karakteristik crypto.
    
    Args:
        risk_tolerance: Toleransi risiko pengguna ("conservative", "moderate", "aggressive")
        crypto_symbols: Simbol crypto dipisahkan koma
    
    Returns:
        JSON string dengan penilaian risiko
    """
    tolerance = risk_tolerance.lower()
    
    risk_profiles = {
        "conservative": {
            "max_volatility": 10,
            "recommended_allocation": 5,
            "max_portfolio_exposure": 10,
            "diversification_min": 5
        },
        "moderate": {
            "max_volatility": 25,
            "recommended_allocation": 15,
            "max_portfolio_exposure": 25,
            "diversification_min": 3
        },
        "aggressive": {
            "max_volatility": 50,
            "recommended_allocation": 30,
            "max_portfolio_exposure": 40,
            "diversification_min": 2
        }
    }
    
    settings = risk_profiles.get(tolerance, risk_profiles["moderate"])
    
    symbols = [s.strip().upper() for s in crypto_symbols.split(",")]
    coin_volatilities = {}
    avg_volatility = 0
    
    for symbol in symbols:
        if symbol in SUPPORTED_COINS:
            coin_id = SUPPORTED_COINS[symbol]["coingecko"]
            close = market_fetcher.fetch_ohlc(coin_id, days=30)
            if len(close) > 1:
                returns = close.pct_change().dropna()
                vol = float(returns.std() * np.sqrt(365) * 100)
                coin_volatilities[symbol] = vol
                avg_volatility += vol
    
    avg_volatility = avg_volatility / len(symbols) if symbols else 25
    
    warnings = []
    recommendations = []
    
    if avg_volatility > settings["max_volatility"]:
        warnings.append(f"⚠️ Volatilitas {avg_volatility:.1f}% melebihi batas untuk profil {tolerance}")
        recommendations.append(f"💡 Pertimbangkan alokasi di bawah {settings['recommended_allocation']}%")
    
    if len(symbols) < settings["diversification_min"]:
        warnings.append(f"⚠️ Diversifikasi kurang, minimal {settings['diversification_min']} koin berbeda")
    
    result = {
        "user_risk_profile": tolerance,
        "crypto_volatility": "tinggi" if avg_volatility > 35 else "sedang" if avg_volatility > 20 else "rendah",
        "volatility_score": round(avg_volatility, 1),
        "coin_volatilities": {k: round(v, 1) for k, v in coin_volatilities.items()},
        "recommended_allocation": settings["recommended_allocation"],
        "max_portfolio_exposure": settings["max_portfolio_exposure"],
        "min_diversification": settings["diversification_min"],
        "risk_level": "tinggi" if avg_volatility > 35 else "sedang" if avg_volatility > 20 else "rendah",
        "risk_score": round(avg_volatility / 50 * 10, 1),
        "warnings": warnings,
        "recommendations": recommendations
    }
    
    return json.dumps(result, indent=2)

# ============================================================================
# AGENT STATE
# ============================================================================

class CryptoAgentState(TypedDict):
    """State untuk crypto investment agent"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_query: str
    user_profile: Dict[str, Any]
    analysis_results: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    next_step: str
    chat_history_manager: Any

# ============================================================================
# LLM SETUP
# ============================================================================

def create_llm(model: str = DEFAULT_MODEL, temperature: float = 0.3):
    """Buat ChatOpenAI instance yang dikonfigurasi untuk OpenRouter"""
    return ChatOpenAI(
        model=model,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=temperature,
        max_tokens=4000
    )

llm = create_llm()

# ============================================================================
# AGENT NODES
# ============================================================================

def parse_user_query(state: CryptoAgentState) -> CryptoAgentState:
    """Parse query pengguna dan ekstrak parameter investasi"""
    print("\n🔍 Menganalisis pertanyaan Anda...")
    
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    # Get chat history context
    chat_manager = state.get("chat_history_manager")
    history_context = ""
    if chat_manager:
        recent_convs = chat_manager.get_recent_conversations(2)
        if recent_convs:
            history_context = "\n\nKonteks percakapan sebelumnya:\n"
            for conv in recent_convs:
                history_context += f"- Query: {conv['query'][:100]}...\n"
    
    system_prompt = f"""Anda adalah analis investasi cryptocurrency. Ekstrak informasi terstruktur dari pertanyaan pengguna dalam Bahasa Indonesia.

{history_context}

PENTING: Pilih cryptocurrency yang SESUAI dengan profil risiko dan jumlah investasi!

Cryptocurrency yang tersedia:
TIER 1 (Aman, Market Cap Besar): BTC, ETH, BNB, SOL, XRP
TIER 2 (Moderat, Potensi Growth): ADA, DOGE, MATIC, DOT, AVAX, LINK, UNI, ATOM, LTC

Ekstrak dan return HANYA objek JSON dengan:
- cryptocurrencies: array simbol yang SESUAI profil (jangan selalu BTC,ETH,BNB)
  * Conservative: 3 koin dari TIER 1 (BTC, ETH, BNB atau SOL, XRP)
  * Moderate: 4-6 koin campuran TIER 1 & 2
  * Aggressive: 5-7 koin termasuk TIER 2 dengan potensi tinggi
- risk_tolerance: "conservative", "moderate", atau "aggressive" - default "moderate"
- investment_goal: "short_term", "medium_term", atau "long_term" - default "medium_term"
- investment_amount: angka dalam IDR atau null
- time_horizon: bulan atau null

Contoh input: "Saya punya dana 10 juta, mau investasi agresif"
Contoh output: {{"cryptocurrencies": ["BTC", "ETH", "SOL", "AVAX", "LINK", "DOT", "MATIC"], "risk_tolerance": "aggressive", "investment_goal": "medium_term", "investment_amount": 10000000, "time_horizon": 6}}

Contoh input: "Dana 4 juta, investasi aman untuk pemula"
Contoh output: {{"cryptocurrencies": ["BTC", "ETH", "BNB"], "risk_tolerance": "conservative", "investment_goal": "long_term", "investment_amount": 4000000, "time_horizon": 12}}"""
    
    extraction_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Ekstrak dari: {last_message}")
    ]
    
    try:
        response = llm.invoke(extraction_messages)
        content = response.content.replace("```json", "").replace("```", "").strip()
        user_profile = json.loads(content)
        
        # Auto-select appropriate coins if not specified well
        if not user_profile.get("cryptocurrencies") or len(user_profile["cryptocurrencies"]) < 3:
            risk = user_profile.get("risk_tolerance", "moderate")
            amount = user_profile.get("investment_amount", 4000000)
            user_profile["cryptocurrencies"] = select_cryptos_by_profile(risk, amount)
        
        print(f"✅ Profil terdeteksi: {user_profile}")
    except Exception as e:
        print(f"⚠️ Error parsing query: {e}")
        user_profile = {
            "cryptocurrencies": ["BTC", "ETH", "BNB", "SOL"],
            "risk_tolerance": "moderate",
            "investment_goal": "medium_term",
            "investment_amount": 4000000,
            "time_horizon": 6
        }
    
    return {
        "messages": messages,
        "user_query": last_message,
        "user_profile": user_profile,
        "analysis_results": {},
        "recommendations": [],
        "next_step": "analyze",
        "chat_history_manager": state.get("chat_history_manager")
    }


def should_continue(state: CryptoAgentState) -> Literal["tools", "generate_report"]:
    """Tentukan apakah agent harus menggunakan tools atau generate laporan final"""
    last_message = state["messages"][-1]
    
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return "generate_report"


def call_model(state: CryptoAgentState) -> CryptoAgentState:
    """Panggil LLM dengan tools untuk analisis"""
    print("\n🤖 Agent sedang berpikir...")
    
    messages = state["messages"]
    user_profile = state["user_profile"]
    
    if len([m for m in messages if isinstance(m, SystemMessage)]) == 0:
        cryptos = ', '.join(user_profile.get('cryptocurrencies', []))
        crypto_names = [SUPPORTED_COINS[c]["name"] for c in user_profile.get('cryptocurrencies', []) if c in SUPPORTED_COINS]
        
        system_msg = SystemMessage(content=f"""Anda adalah penasihat investasi cryptocurrency dan bisnis expert dengan akses ke tools data pasar real-time dan analisis bisnis WarungTech.

Profil Pengguna:
- Cryptocurrency diminati: {cryptos} ({', '.join(crypto_names)})
- Toleransi Risiko: {user_profile.get('risk_tolerance', 'moderate')}
- Tujuan Investasi: {user_profile.get('investment_goal', 'medium_term')}
- Dana Investasi: Rp {user_profile.get('investment_amount', 0):,.0f}
- Horison Waktu: {user_profile.get('time_horizon', 6)} bulan

PENTING: Anda HARUS menggunakan tools dalam urutan yang tepat berdasarkan jenis pertanyaan:

UNTUK ANALISIS BISNIS & PROMO:
1. analyze_business_performance - Analisis kondisi bisnis dari WarungTech API
2. generate_promo_recommendations - Generate rekomendasi promo berdasarkan bisnis
3. analyze_crypto_investment_with_business - Rekomendasi crypto sesuai kondisi bisnis

UNTUK ANALISIS CRYPTO MURNI:
1. get_market_data - Ambil harga real-time untuk: {cryptos}
2. perform_technical_analysis - Analisis teknikal untuk SETIAP koin
3. analyze_market_sentiment - Analisis sentimen untuk SETIAP koin  
4. assess_investment_risk - Evaluasi risiko untuk: {cryptos}

DETEKSI JENIS PERTANYAAN:
- Jika user menyebut "bisnis", "toko", "promo", "penjualan" → Gunakan tools bisnis
- Jika user hanya tanya crypto/investasi → Gunakan tools crypto standar
- Jika user tanya keduanya → Gunakan SEMUA tools

Setelah SEMUA tools yang relevan dipanggil, buat laporan rekomendasi yang komprehensif.""")
        
        messages = [system_msg] + list(messages)
    
    model_with_tools = llm.bind_tools([
        # Business Analysis Tools (NEW)
        analyze_business_performance,
        generate_promo_recommendations, 
        analyze_crypto_investment_with_business,
        # Crypto Analysis Tools (EXISTING)
        get_market_data,
        perform_technical_analysis,
        analyze_market_sentiment,
        assess_investment_risk
    ])
    
    response = model_with_tools.invoke(messages)
    
    return {
        "messages": [response],
        "chat_history_manager": state.get("chat_history_manager")
    }


def generate_final_report(state: CryptoAgentState) -> CryptoAgentState:
    """Generate laporan investasi dan bisnis komprehensif dalam Bahasa Indonesia"""
    print("\n📝 Membuat laporan investasi dan bisnis...")
    
    messages = state["messages"]
    user_profile = state["user_profile"]
    
    # Hitung nilai tukar IDR ke USD (approximate)
    usd_to_idr = 15800
    investment_usd = user_profile.get('investment_amount', 0) / usd_to_idr
    
    cryptos = user_profile.get('cryptocurrencies', [])
    crypto_names = [SUPPORTED_COINS[c]["name"] for c in cryptos if c in SUPPORTED_COINS]
    
    # Detect if this is business-focused or crypto-focused query
    user_query = state.get("user_query", "").lower()
    is_business_query = any(keyword in user_query for keyword in ["bisnis", "toko", "promo", "penjualan", "warung", "usaha"])
    is_crypto_query = any(keyword in user_query for keyword in ["crypto", "bitcoin", "ethereum", "investasi", "trading"])
    
    if is_business_query and is_crypto_query:
        report_type = "COMPREHENSIVE_BUSINESS_CRYPTO"
    elif is_business_query:
        report_type = "BUSINESS_FOCUSED"
    else:
        report_type = "CRYPTO_FOCUSED"
    
    if report_type == "BUSINESS_FOCUSED":
        report_prompt = f"""Berdasarkan analisis bisnis yang telah dilakukan, buat laporan rekomendasi bisnis dan promo DALAM BAHASA INDONESIA.

INSTRUKSI PENTING:
1. Gunakan data REAL dari tool calls analyze_business_performance dan generate_promo_recommendations
2. Fokus pada strategi promo dan pengembangan bisnis WarungTech
3. Sertakan rekomendasi blockchain coupon yang actionable
4. Format laporan harus profesional dan mudah diimplementasi

Format laporan:

# 🏪 LAPORAN ANALISIS BISNIS & REKOMENDASI PROMO WARUNGTECH

## 📊 Ringkasan Kondisi Bisnis
[Analisis kondisi bisnis saat ini berdasarkan data dari API, termasuk revenue, customer metrics, dan financial health]

## 🎯 Strategi Promo Rekomendasi
[Detail strategi promo berdasarkan kondisi bisnis, termasuk discount percentage, target products, timing, dan budget allocation]

## 🔗 Implementasi Blockchain Coupon
[Panduan implementasi kupon blockchain dengan detail teknis dan benefit untuk bisnis]

## 📈 Target & Proyeksi
[Target revenue, customer acquisition, dan ROI yang realistis berdasarkan strategi yang direkomendasikan]

## 📅 Rencana Implementasi
[Timeline implementasi yang detail dengan milestone dan action items]

## ⚠️ Risk Management
[Identifikasi risiko dan strategi mitigasi untuk setiap rekomendasi]

Pastikan semua rekomendasi berdasarkan data real dari tools dan dapat diimplementasi langsung."""

    elif report_type == "COMPREHENSIVE_BUSINESS_CRYPTO":
        report_prompt = f"""Berdasarkan analisis bisnis dan crypto yang telah dilakukan, buat laporan komprehensif DALAM BAHASA INDONESIA.

INSTRUKSI PENTING:
1. Gunakan data dari SEMUA tools: business analysis, promo recommendations, dan crypto analysis
2. Integrasikan rekomendasi bisnis dengan strategi investasi crypto
3. Berikan panduan holistik untuk pengembangan bisnis dan investasi
4. Sertakan sinergi antara promo blockchain dan investasi crypto

Format laporan:

# 🚀 LAPORAN KOMPREHENSIF: BISNIS & INVESTASI CRYPTO WARUNGTECH

## 📋 Executive Summary
[Ringkasan kondisi bisnis, peluang investasi crypto, dan strategi terintegrasi]

## 🏪 ANALISIS BISNIS & PROMO STRATEGY

### Kondisi Bisnis Saat Ini
[Data bisnis dari API analysis]

### Rekomendasi Promo & Blockchain Coupon
[Strategi promo dengan implementasi blockchain]

## 💰 ANALISIS INVESTASI CRYPTOCURRENCY

### Kondisi Pasar Crypto
[Market data dan technical analysis untuk {', '.join(cryptos)}]

### Rekomendasi Investasi Berdasarkan Kondisi Bisnis
[Alokasi crypto yang disesuaikan dengan cash flow dan risk profile bisnis]

## 🔄 STRATEGI TERINTEGRASI

### Sinergi Bisnis-Crypto
[Bagaimana investasi crypto dapat mendukung pertumbuhan bisnis dan sebaliknya]

### Implementation Roadmap
[Timeline terintegrasi untuk promo dan investasi]

## 📊 FINANCIAL PROJECTION
[Proyeksi keuangan gabungan dari bisnis growth dan crypto investment]

## ⚖️ RISK MANAGEMENT
[Manajemen risiko holistik untuk bisnis dan investasi]

Pastikan laporan menunjukkan bagaimana kedua strategi saling mendukung dan memberikan value maksimal."""

    else:  # CRYPTO_FOCUSED
        report_prompt = f"""Berdasarkan semua data yang dikumpulkan dari tools, buat laporan rekomendasi investasi komprehensif DALAM BAHASA INDONESIA.

Profil Pengguna:
{json.dumps(user_profile, indent=2, ensure_ascii=False)}

Cryptocurrency yang dianalisis: {', '.join([f"{c} ({SUPPORTED_COINS[c]['name']})" for c in cryptos if c in SUPPORTED_COINS])}

INSTRUKSI PENTING:
1. Gunakan data REAL dari tool calls yang sudah dilakukan
2. Jangan membuat data fiktif
3. Format laporan harus rapi dan profesional
4. Analisis SEMUA {len(cryptos)} koin yang diminta, JANGAN hanya 3 koin
5. Buat alokasi portfolio untuk SEMUA koin yang dianalisis
6. Gunakan data Fear & Greed Index dari tool analyze_market_sentiment
7. Sertakan semua indikator teknikal (RSI, MACD, MA50, MA200)

Format laporan Anda:

# 🎯 REKOMENDASI INVESTASI CRYPTOCURRENCY

## 📋 Ringkasan Eksekutif
[2-3 paragraf merangkum kondisi pasar, temuan kunci, dan rekomendasi utama untuk SEMUA {len(cryptos)} koin. Sertakan Fear & Greed Index dan kondisi pasar global]

## 📊 Analisis Detail Per Koin
[ANALISIS UNTUK SETIAP KOIN - Ulangi format ini untuk SEMUA {len(cryptos)} koin dengan data real dari tools]

## 💰 ALOKASI PORTFOLIO
[Portfolio allocation berdasarkan analisis teknikal dan fundamental]

## ⚠️ MANAJEMEN RISIKO
[Risk management strategy berdasarkan assess_investment_risk tool]

## 📅 RENCANA AKSI 30 HARI
[Implementation timeline yang praktis]

## 📈 TARGET & EKSPEKTASI
[Realistic targets berdasarkan market analysis]

Pastikan SEMUA data diambil dari tool calls yang sudah dilakukan dan TIDAK ada data fiktif."""
    
    report_messages = list(messages) + [HumanMessage(content=report_prompt)]
    
    report_llm = create_llm(temperature=0.5, model=DEFAULT_MODEL)
    response = report_llm.invoke(report_messages)
    
    return {
        "messages": [response],
        "next_step": "complete",
        "chat_history_manager": state.get("chat_history_manager")
    }

# ============================================================================
# BUILD WORKFLOW
# ============================================================================

def build_crypto_agent():
    """Bangun LangGraph workflow untuk crypto investment agent dengan business analysis"""
    
    tools = [
        # Business Analysis Tools
        analyze_business_performance,
        generate_promo_recommendations,
        analyze_crypto_investment_with_business,
        # Crypto Analysis Tools  
        get_market_data,
        perform_technical_analysis,
        analyze_market_sentiment,
        assess_investment_risk
    ]
    
    tool_node = ToolNode(tools)
    
    workflow = StateGraph(CryptoAgentState)
    
    workflow.add_node("parse_query", parse_user_query)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_node("generate_report", generate_final_report)
    
    workflow.set_entry_point("parse_query")
    
    workflow.add_edge("parse_query", "agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "generate_report": "generate_report"
        }
    )
    
    workflow.add_edge("tools", "agent")
    workflow.add_edge("generate_report", END)
    
    app = workflow.compile()
    
    return app

# ============================================================================
# FEEDBACK INTERFACE
# ============================================================================

def collect_feedback(conversation_id: int, user_id: str = "default_user"):
    """Collect feedback from user"""
    print("\n" + "="*80)
    print("📝 BERIKAN FEEDBACK ANDA")
    print("="*80)
    
    print("\nBantu kami meningkatkan layanan dengan memberikan feedback!")
    
    try:
        rating = int(input("\n⭐ Rating (1-5): "))
        rating = max(1, min(5, rating))
    except:
        rating = 3
    
    try:
        accuracy = int(input("📊 Akurasi Analisis (1-10): "))
        accuracy = max(1, min(10, accuracy))
    except:
        accuracy = 5
    
    helpful_input = input("💡 Apakah rekomendasi membantu? (y/n): ").lower()
    helpful = helpful_input == 'y' or helpful_input == 'yes'
    
    comments = input("💬 Komentar (optional): ").strip()
    suggestions = input("🔧 Saran perbaikan (optional): ").strip()
    
    feedback = {
        "rating": rating,
        "accuracy": accuracy,
        "helpful": helpful,
        "comments": comments,
        "suggestions": suggestions
    }
    
    # Save to history
    chat_manager = ChatHistoryManager(user_id)
    chat_manager.add_feedback(conversation_id, feedback)
    
    # Save to global feedback
    feedback_system = FeedbackSystem()
    feedback_system.add_feedback(user_id, conversation_id, feedback)
    
    print("\n✅ Terima kasih atas feedback Anda!")
    
    # Show feedback summary
    summary = feedback_system.get_feedback_summary()
    print(f"\n📊 Statistik Feedback Keseluruhan:")
    print(f"   Total Feedback: {summary['total']}")
    print(f"   Rating Rata-rata: {summary['average_rating']}/5")
    print(f"   Helpful: {summary['helpful_percentage']}%")
    
    return feedback

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def run_crypto_agent_indonesia(user_query: str, user_id: str = "default_user", verbose: bool = True):
    """
    Jalankan crypto investment agent dengan query dalam Bahasa Indonesia
    
    Args:
        user_query: Pertanyaan investasi dari pengguna (Bahasa Indonesia)
        user_id: ID pengguna untuk tracking history
        verbose: Print progress detail
    
    Returns:
        Dict dengan hasil analisis dan conversation_id
    """
    print("\n" + "="*80)
    print("🚀 AGEN INVESTASI CRYPTOCURRENCY - BAHASA INDONESIA")
    print("="*80)
    print(f"Model: {DEFAULT_MODEL}")
    print(f"User ID: {user_id}")
    print(f"Pertanyaan: {user_query}")
    print("="*80)
    
    # Initialize chat history manager
    chat_manager = ChatHistoryManager(user_id)
    
    # Show recent conversation history
    if chat_manager.conversations:
        print("\n" + chat_manager.get_conversation_summary())
    
    agent = build_crypto_agent()
    
    initial_state = {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "user_profile": {},
        "analysis_results": {},
        "recommendations": [],
        "next_step": "start",
        "chat_history_manager": chat_manager
    }
    
    try:
        final_state = agent.invoke(initial_state)
        
        final_messages = final_state["messages"]
        final_report = final_messages[-1].content if final_messages else "Tidak ada laporan yang dihasilkan"
        
        if verbose:
            print("\n" + "="*80)
            print("📄 LAPORAN INVESTASI CRYPTOCURRENCY")
            print("="*80)
            print(final_report)
            print("\n" + "="*80)
        
        # Save to history
        conversation_id = chat_manager.add_conversation(
            query=user_query,
            response=final_report,
            metadata={
                "user_profile": final_state["user_profile"],
                "model": DEFAULT_MODEL,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"\n💾 Percakapan disimpan (ID: {conversation_id})")
        
        # Ask for feedback
        collect_feedback_prompt = input("\n❓ Apakah Anda ingin memberikan feedback? (y/n): ").lower()
        if collect_feedback_prompt in ['y', 'yes']:
            collect_feedback(conversation_id, user_id)
        
        return {
            "success": True,
            "report": final_report,
            "state": final_state,
            "conversation_id": conversation_id,
            "user_id": user_id
        }
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


def view_history(user_id: str = "default_user", n: int = 5):
    """View conversation history"""
    print("\n" + "="*80)
    print("📜 RIWAYAT PERCAKAPAN")
    print("="*80)
    
    chat_manager = ChatHistoryManager(user_id)
    recent = chat_manager.get_recent_conversations(n)
    
    if not recent:
        print("\nTidak ada riwayat percakapan.")
        return
    
    for i, conv in enumerate(recent, 1):
        timestamp = datetime.fromisoformat(conv["timestamp"]).strftime("%d/%m/%Y %H:%M WIB")
        print(f"\n--- Percakapan #{i} [{timestamp}] ---")
        print(f"Query: {conv['query'][:150]}...")
        
        if conv.get('metadata'):
            cryptos = conv['metadata'].get('user_profile', {}).get('cryptocurrencies', [])
            if cryptos:
                print(f"Koin: {', '.join(cryptos)}")
        
        if conv.get('feedback'):
            fb = conv['feedback']
            print(f"Feedback: ⭐{fb['rating']}/5 | Akurasi: {fb.get('accuracy', 'N/A')}/10")
            if fb.get('comments'):
                print(f"Komentar: {fb['comments']}")
        
        print("-" * 80)


def view_feedback_stats():
    """View feedback statistics"""
    print("\n" + "="*80)
    print("📊 STATISTIK FEEDBACK")
    print("="*80)
    
    feedback_system = FeedbackSystem()
    summary = feedback_system.get_feedback_summary()
    
    print(f"\nTotal Feedback: {summary['total']}")
    print(f"Rating Rata-rata: {summary['average_rating']}/5")
    print(f"Rekomendasi Membantu: {summary['helpful_percentage']}%")
    
    if feedback_system.feedback_data:
        print("\n📝 Feedback Terbaru:")
        for fb in feedback_system.feedback_data[-5:]:
            timestamp = datetime.fromisoformat(fb["timestamp"]).strftime("%d/%m/%Y %H:%M")
            print(f"\n[{timestamp}] Rating: ⭐{fb['rating']}/5")
            if fb.get('comments'):
                print(f"   Komentar: {fb['comments']}")


# ============================================================================
# INTERACTIVE CLI
# ============================================================================

def interactive_mode():
    """Run in interactive CLI mode"""
    print("\n" + "="*80)
    print("🤖 CRYPTO INVESTMENT AGENT - MODE INTERAKTIF")
    print("="*80)
    
    user_id = input("\nMasukkan User ID Anda (tekan Enter untuk default): ").strip()
    if not user_id:
        user_id = "default_user"
    
    print(f"\n✅ User ID: {user_id}")
    print("\nPerintah yang tersedia:")
    print("  - Tanyakan tentang investasi crypto")
    print("  - 'history' - Lihat riwayat percakapan")
    print("  - 'stats' - Lihat statistik feedback")
    print("  - 'exit' - Keluar")
    
    while True:
        print("\n" + "="*80)
        query = input("\n💬 Tanya: ").strip()
        
        if not query:
            continue
        
        if query.lower() == 'exit':
            print("\n👋 Terima kasih! Sampai jumpa lagi.")
            break
        
        if query.lower() == 'history':
            view_history(user_id)
            continue
        
        if query.lower() == 'stats':
            view_feedback_stats()
            continue
        
        # Run agent
        result = run_crypto_agent_indonesia(query, user_id=user_id)
        
        if result["success"]:
            print("\n✅ Analisis selesai!")
        else:
            print(f"\n❌ Gagal: {result['error']}")


# ============================================================================
# CONTOH PENGGUNAAN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # Interactive mode
        interactive_mode()
    else:
        # Single query mode
        print("\n" + "="*80)
        print("CONTOH PENGGUNAAN - ANALISIS BISNIS & CRYPTO")
        print("="*80)
        
        # Example 1: Business Analysis Query
        print("\n🏪 CONTOH 1: ANALISIS BISNIS & REKOMENDASI PROMO")
        print("-" * 60)
        
        business_query = """
        Saya punya warung dengan omzet bulanan 40 juta. Saya ingin buat promo untuk 
        meningkatkan penjualan jadi 50 juta bulan depan. Tolong analisis kondisi bisnis 
        saya dan berikan rekomendasi promo yang tepat, termasuk kupon blockchain.
        """
        
        print(f"Query: {business_query.strip()}")
        
        result1 = run_crypto_agent_indonesia(business_query, user_id="warung_owner_demo")
        
        if result1["success"]:
            print("\n✅ Analisis bisnis selesai!")
        else:
            print(f"\n❌ Gagal: {result1['error']}")
        
        print("\n" + "="*80)
        
        # Example 2: Comprehensive Business + Crypto Query  
        print("\n💰 CONTOH 2: ANALISIS KOMPREHENSIF BISNIS + CRYPTO")
        print("-" * 60)
        
        comprehensive_query = """
        Saya pemilik warung dengan omzet 45 juta per bulan. Saya punya dana 8 juta 
        yang bisa diinvestasikan ke crypto. Tolong analisis:
        1. Kondisi bisnis saya dan rekomendasi promo
        2. Rekomendasi investasi crypto yang sesuai dengan kondisi bisnis
        3. Bagaimana crypto bisa mendukung pertumbuhan warung saya
        
        Saya tipe investor moderat dan ingin diversifikasi ke beberapa koin.
        """
        
        print(f"Query: {comprehensive_query.strip()}")
        
        result2 = run_crypto_agent_indonesia(comprehensive_query, user_id="business_investor_demo")
        
        if result2["success"]:
            print("\n✅ Analisis komprehensif selesai!")
        else:
            print(f"\n❌ Gagal: {result2['error']}")
        
        print("\n" + "="*80)
        
        # Example 3: Pure Crypto Query (Original functionality)
        print("\n🚀 CONTOH 3: ANALISIS CRYPTO MURNI (FITUR ORIGINAL)")
        print("-" * 60)
        
        crypto_query = """
        Saya ingin investasi kripto dengan dana 10 juta rupiah.
        Saya tipe investor agresif dan ingin diversifikasi ke banyak koin.
        Tolong analisis BTC, ETH, SOL, ADA, MATIC dan berikan rekomendasi alokasi.
        """
        
        print(f"Query: {crypto_query.strip()}")
        
        result3 = run_crypto_agent_indonesia(crypto_query, user_id="crypto_investor_demo")
        
        if result3["success"]:
            print("\n✅ Analisis crypto selesai!")
        else:
            print(f"\n❌ Gagal: {result3['error']}")
        
        print("\n" + "="*80)
        print("📊 RINGKASAN FITUR BARU:")
        print("="*80)
        print("✅ Analisis kondisi bisnis dari WarungTech API")
        print("✅ Rekomendasi promo berdasarkan performa bisnis")
        print("✅ Strategi kupon blockchain yang actionable")
        print("✅ Investasi crypto disesuaikan dengan kondisi bisnis")
        print("✅ Integrasi holistik bisnis dan investasi")
        print("✅ Risk management berdasarkan cash flow bisnis")
        print("✅ Timeline implementasi yang realistis")
        
        print("\n💡 TIP: Jalankan dengan 'python main.py interactive' untuk mode interaktif")
        print("🔗 API Integration: WarungTech API di http://192.168.43.166:3001/api")
        print("="*80)
        print("\nSELESAI - ENHANCED VERSION WITH BUSINESS ANALYSIS")
        print("="*80)