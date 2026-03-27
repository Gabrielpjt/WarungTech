"""
Enhanced WarungTech AI Assistant
Terintegrasi dengan WarungTech Backend API & Web3 Coupon Smart Contract
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Sequence
import operator
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# KONFIGURASI - REQUIRED API KEYS
# ============================================================================

print("🔧 Loading WarungTech AI Configuration...")

# WarungTech Backend API (Production)
WARUNGTECH_API_BASE = "https://war-tech-backend-ouiu-a3ge8s8q9.vercel.app/api"
WARUNGTECH_API_TIMEOUT = 15

# OpenRouter Configuration (REQUIRED)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("❌ ERROR: OPENROUTER_API_KEY not found in environment variables!")
    print("📝 Please add to .env file: OPENROUTER_API_KEY=sk-or-v1-your-key-here")
    print("🔗 Get your key from: https://openrouter.ai/keys")
    exit(1)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"

# Web3 & Smart Contract Configuration (OPTIONAL - for blockchain features)
INFURA_PROJECT_ID = os.getenv("INFURA_PROJECT_ID")
SEPOLIA_RPC_URL = f"https://sepolia.infura.io/v3/{INFURA_PROJECT_ID}" if INFURA_PROJECT_ID else None
COUPON_CONTRACT_ADDRESS = "0xF06e4D89A9eE9ac3522D732b3309d4b7C78b2b7a"
SEPOLIA_CHAIN_ID = 11155111

# Web3 instance (optional)
w3 = None
coupon_contract = None

if SEPOLIA_RPC_URL and INFURA_PROJECT_ID:
    try:
        w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
        print(f"✅ Web3 connected: {w3.is_connected()}")
        
        # Smart Contract ABI (minimal untuk read operations)
        COUPON_CONTRACT_ABI = [
            {
                "inputs": [],
                "name": "couponCounter",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "name": "coupons",
                "outputs": [
                    {"internalType": "address", "name": "couponOwner", "type": "address"},
                    {"internalType": "address", "name": "partnerOwner", "type": "address"},
                    {"internalType": "uint8", "name": "discountType", "type": "uint8"},
                    {"internalType": "uint256", "name": "discountValue", "type": "uint256"},
                    {"internalType": "uint256", "name": "minTransactionAmount", "type": "uint256"},
                    {"internalType": "uint256", "name": "usedTransactionAmount", "type": "uint256"},
                    {"internalType": "bytes32", "name": "barcodeHash", "type": "bytes32"},
                    {"internalType": "uint256", "name": "promoFee", "type": "uint256"},
                    {"internalType": "uint256", "name": "expiredAt", "type": "uint256"},
                    {"internalType": "uint8", "name": "status", "type": "uint8"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Contract instance
        coupon_contract = w3.eth.contract(
            address=Web3.to_checksum_address(COUPON_CONTRACT_ADDRESS),
            abi=COUPON_CONTRACT_ABI
        )
        print("✅ Smart contract initialized")
        
    except Exception as e:
        print(f"⚠️ Web3 initialization failed: {e}")
        print("💡 Blockchain features will be disabled")
else:
    print("⚠️ INFURA_PROJECT_ID not found - blockchain features disabled")
    print("📝 Add to .env file: INFURA_PROJECT_ID=your-infura-project-id")

print(f"✅ API Base URL: {WARUNGTECH_API_BASE}")
print(f"✅ OpenRouter Model: {DEFAULT_MODEL}")
print("="*80)

# ============================================================================
# API HELPER FUNCTIONS
# ============================================================================

def make_api_request(endpoint: str, method: str = "GET", headers: Dict = None, data: Dict = None) -> Dict:
    """
    Helper function untuk API requests dengan error handling
    
    Args:
        endpoint: API endpoint (e.g., "/dashboard/stats")
        method: HTTP method (GET, POST, etc.)
        headers: Request headers
        data: Request body data
    
    Returns:
        Dict dengan response data atau error
    """
    try:
        url = f"{WARUNGTECH_API_BASE}{endpoint}"
        
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
        
        print(f"🌐 API Request: {method} {url}")
        
        if method.upper() == "GET":
            response = requests.get(url, headers=default_headers, timeout=WARUNGTECH_API_TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, headers=default_headers, json=data, timeout=WARUNGTECH_API_TIMEOUT)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            return {"error": "Authentication failed - invalid or expired token"}
        elif response.status_code == 403:
            return {"error": "Access denied - insufficient permissions"}
        elif response.status_code == 404:
            return {"error": "Endpoint not found"}
        else:
            return {"error": f"API returned status {response.status_code}: {response.text}"}
            
    except requests.exceptions.Timeout:
        return {"error": "API request timeout - server may be slow"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to WarungTech API - check internet connection"}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def validate_token(token: str) -> bool:
    """Validate JWT token format"""
    if not token:
        return False
    
    parts = token.split('.')
    return len(parts) == 3 and all(len(part) > 0 for part in parts)


def validate_wallet_address(address: str) -> bool:
    """Validate Ethereum wallet address"""
    if not address:
        return False
    
    if w3:
        return Web3.is_address(address)
    else:
        # Basic validation without Web3
        return address.startswith('0x') and len(address) == 42

# ============================================================================
# BUSINESS ANALYSIS TOOLS (WarungTech API Integration)
# ============================================================================

@tool
def get_business_dashboard_stats(user_token: str) -> str:
    """
    Ambil statistik dashboard bisnis dari WarungTech API.
    
    Args:
        user_token: JWT token untuk autentikasi user (format: eyJhbGc...)
    
    Returns:
        JSON string dengan statistik bisnis (revenue, orders, products, dll)
    """
    
    # Validate token
    if not validate_token(user_token):
        return json.dumps({
            "error": "Invalid JWT token format",
            "expected_format": "eyJhbGc... (3 parts separated by dots)",
            "provided": f"Token length: {len(user_token) if user_token else 0}"
        }, ensure_ascii=False)
    
    try:
        headers = {
            "Authorization": f"Bearer {user_token}"
        }
        
        response_data = make_api_request("/dashboard/stats", headers=headers)
        
        if "error" in response_data:
            return json.dumps({
                "error": response_data["error"],
                "endpoint": "/dashboard/stats",
                "troubleshooting": {
                    "check_1": "Verify JWT token is valid and not expired",
                    "check_2": "Ensure user is logged in to WarungTech app",
                    "check_3": "Check if user has created a store"
                }
            }, ensure_ascii=False)
        
        if response_data.get("success"):
            stats = response_data.get("data", {})
            
            # Enhanced analysis
            revenue = stats.get("total_revenue", 0)
            orders = stats.get("total_orders", 0)
            products = stats.get("total_products", 0)
            stores = stats.get("total_stores", 0)
            
            avg_order_value = revenue / max(orders, 1)
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "api_status": "connected",
                "business_metrics": {
                    "total_stores": stores,
                    "total_products": products,
                    "total_orders": orders,
                    "total_revenue": revenue,
                    "average_order_value": round(avg_order_value, 2),
                    "wallet_balance": stats.get("wallet_balance", 0),
                    "active_investments": stats.get("active_investments", 0),
                    "total_invested": stats.get("total_invested", 0)
                },
                "business_analysis": {
                    "revenue_health": "excellent" if revenue > 50000000 else "good" if revenue > 10000000 else "needs_improvement",
                    "product_diversity": "sufficient" if products > 10 else "limited" if products > 5 else "very_limited",
                    "order_frequency": "high" if orders > 100 else "moderate" if orders > 20 else "low",
                    "investment_readiness": stats.get("wallet_balance", 0) > 5000000,
                    "business_maturity": "established" if (stores > 0 and products > 5 and orders > 10) else "developing"
                },
                "recommendations": {
                    "immediate": generate_business_recommendations(revenue, orders, products, stores),
                    "growth_potential": calculate_growth_potential(revenue, orders, products)
                }
            }
            
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return json.dumps({
                "error": "API returned unsuccessful response",
                "message": response_data.get("message", "Unknown error"),
                "api_response": response_data
            }, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch business stats: {str(e)}",
            "endpoint": "/dashboard/stats"
        }, ensure_ascii=False)


@tool
def get_financial_summary(user_token: str) -> str:
    """
    Ambil ringkasan keuangan user (income, expense, investment, wallet).
    
    Args:
        user_token: JWT token untuk autentikasi
    
    Returns:
        JSON string dengan summary finansial dan analisis cash flow
    """
    
    if not validate_token(user_token):
        return json.dumps({
            "error": "Invalid JWT token format"
        }, ensure_ascii=False)
    
    try:
        headers = {
            "Authorization": f"Bearer {user_token}"
        }
        
        response_data = make_api_request("/financial/summary", headers=headers)
        
        if "error" in response_data:
            return json.dumps({
                "error": response_data["error"],
                "endpoint": "/financial/summary"
            }, ensure_ascii=False)
        
        if response_data.get("success"):
            summary = response_data.get("data", {})
            
            income = summary.get("income", 0)
            expense = summary.get("expense", 0)
            investment = summary.get("investment", 0)
            gain = summary.get("gain", 0)
            wallet_balance = summary.get("wallet_balance", 0)
            net_balance = summary.get("net_balance", 0)
            
            # Advanced financial analysis
            profit_margin = ((net_balance / income) * 100) if income > 0 else 0
            investment_ratio = ((investment / income) * 100) if income > 0 else 0
            roi = ((gain / investment) * 100) if investment > 0 else 0
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "financial_health": {
                    "income": income,
                    "expense": expense,
                    "investment": investment,
                    "gain_loss": gain,
                    "wallet_balance": wallet_balance,
                    "net_balance": net_balance
                },
                "financial_ratios": {
                    "profit_margin_percentage": round(profit_margin, 2),
                    "investment_ratio_percentage": round(investment_ratio, 2),
                    "return_on_investment_percentage": round(roi, 2),
                    "expense_ratio_percentage": round((expense / income * 100) if income > 0 else 0, 2)
                },
                "risk_analysis": {
                    "cash_flow_status": "positive" if net_balance > 0 else "negative",
                    "liquidity_health": "good" if wallet_balance > expense * 0.3 else "concerning",
                    "investment_diversification": "balanced" if 10 <= investment_ratio <= 30 else "needs_adjustment",
                    "financial_stability": calculate_financial_stability(income, expense, wallet_balance)
                },
                "recommendations": {
                    "cash_management": generate_cash_management_advice(wallet_balance, expense),
                    "investment_strategy": generate_investment_advice(investment_ratio, roi),
                    "cost_optimization": generate_cost_advice(expense, income)
                }
            }
            
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return json.dumps({
                "error": "Failed to get financial summary",
                "message": response_data.get("message")
            }, ensure_ascii=False)
                
    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch financial data: {str(e)}"
        }, ensure_ascii=False)


@tool
def get_user_investments(user_token: str) -> str:
    """
    Ambil daftar investasi crypto dari database WarungTech.
    
    Args:
        user_token: JWT token untuk autentikasi
    
    Returns:
        JSON string dengan portfolio investasi dan analisis diversifikasi
    """
    
    if not validate_token(user_token):
        return json.dumps({
            "error": "Invalid JWT token format"
        }, ensure_ascii=False)
    
    try:
        headers = {
            "Authorization": f"Bearer {user_token}"
        }
        
        response_data = make_api_request("/investments", headers=headers)
        
        if "error" in response_data:
            return json.dumps({
                "error": response_data["error"],
                "endpoint": "/investments"
            }, ensure_ascii=False)
        
        if response_data.get("success"):
            investments = response_data.get("data", [])
            
            # Portfolio analysis
            active_investments = [inv for inv in investments if inv.get("status") == "active"]
            total_invested = sum(inv.get("amount", 0) for inv in active_investments)
            
            # Asset distribution
            asset_distribution = {}
            for inv in active_investments:
                asset = inv.get("asset", "Unknown")
                asset_distribution[asset] = asset_distribution.get(asset, 0) + inv.get("amount", 0)
            
            # Calculate portfolio metrics
            portfolio_diversity = len(asset_distribution)
            largest_position = max(asset_distribution.values()) if asset_distribution else 0
            concentration_risk = (largest_position / total_invested * 100) if total_invested > 0 else 0
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "portfolio_overview": {
                    "total_investments": len(investments),
                    "active_investments": len(active_investments),
                    "total_invested_amount": total_invested,
                    "number_of_assets": portfolio_diversity
                },
                "asset_allocation": asset_distribution,
                "portfolio_analysis": {
                    "diversification_score": calculate_diversification_score(portfolio_diversity, concentration_risk),
                    "concentration_risk_percentage": round(concentration_risk, 2),
                    "portfolio_balance": "well_diversified" if concentration_risk < 40 else "concentrated",
                    "risk_level": "high" if concentration_risk > 60 else "moderate" if concentration_risk > 40 else "low"
                },
                "investment_details": active_investments[:10],  # Limit for readability
                "recommendations": {
                    "diversification": generate_diversification_advice(portfolio_diversity, concentration_risk),
                    "rebalancing": generate_rebalancing_advice(asset_distribution, total_invested),
                    "risk_management": generate_risk_management_advice(concentration_risk)
                }
            }
            
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return json.dumps({
                "error": "Failed to get investments",
                "message": response_data.get("message")
            }, ensure_ascii=False)
                
    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch investments: {str(e)}"
        }, ensure_ascii=False)


# ============================================================================
# CRYPTO MARKET DATA
# ============================================================================

@tool
def get_market_data(crypto_symbols: str) -> str:
    """
    Ambil data pasar real-time cryptocurrency dari CoinGecko.
    
    Args:
        crypto_symbols: Simbol crypto (contoh: "BTC,ETH,SOL")
    
    Returns:
        JSON string dengan harga dan perubahan 24h
    """
    try:
        # Mapping symbols ke CoinGecko IDs
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "BNB": "binancecoin",
            "ADA": "cardano",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "AVAX": "avalanche-2"
        }
        
        symbols = [s.strip().upper() for s in crypto_symbols.split(",")]
        coin_ids = [symbol_map.get(s, s.lower()) for s in symbols]
        
        print(f"🪙 Fetching market data for: {', '.join(symbols)}")
        
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_market_cap": "true"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "market_data": {},
                "market_summary": {
                    "total_coins": len(symbols),
                    "data_source": "CoinGecko API"
                }
            }
            
            total_market_cap = 0
            positive_changes = 0
            
            for symbol, coin_id in zip(symbols, coin_ids):
                if coin_id in data:
                    coin_data = data[coin_id]
                    price = coin_data.get("usd", 0)
                    change_24h = coin_data.get("usd_24h_change", 0)
                    market_cap = coin_data.get("usd_market_cap", 0)
                    
                    result["market_data"][symbol] = {
                        "price_usd": price,
                        "change_24h_percentage": round(change_24h, 2),
                        "market_cap_usd": market_cap,
                        "trend": "bullish" if change_24h > 0 else "bearish",
                        "price_formatted": f"${price:,.2f}",
                        "change_formatted": f"{change_24h:+.2f}%"
                    }
                    
                    total_market_cap += market_cap
                    if change_24h > 0:
                        positive_changes += 1
            
            # Market sentiment analysis
            sentiment_ratio = positive_changes / len(symbols) if symbols else 0
            result["market_summary"].update({
                "total_market_cap": total_market_cap,
                "positive_performers": positive_changes,
                "sentiment_ratio": round(sentiment_ratio, 2),
                "market_sentiment": "bullish" if sentiment_ratio > 0.6 else "bearish" if sentiment_ratio < 0.4 else "neutral"
            })
            
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return json.dumps({
                "error": f"CoinGecko API returned status {response.status_code}",
                "message": "Failed to fetch market data"
            }, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch market data: {str(e)}",
            "fallback": "Use cached data or manual price input"
        }, ensure_ascii=False)


# ============================================================================
# HELPER FUNCTIONS FOR ANALYSIS
# ============================================================================

def generate_business_recommendations(revenue: float, orders: int, products: int, stores: int) -> List[str]:
    """Generate business recommendations based on metrics"""
    recommendations = []
    
    if stores == 0:
        recommendations.append("Buat toko pertama di tab Profile untuk mulai berjualan")
    
    if products < 5:
        recommendations.append("Tambah lebih banyak produk (target: 10+ produk) untuk menarik lebih banyak customer")
    
    if orders < 10:
        recommendations.append("Fokus pada marketing dan promosi untuk meningkatkan jumlah order")
    
    if revenue < 1000000:
        recommendations.append("Tingkatkan harga atau volume penjualan untuk mencapai revenue Rp 1 juta")
    
    avg_order = revenue / max(orders, 1)
    if avg_order < 50000:
        recommendations.append("Tingkatkan nilai rata-rata per order dengan bundling atau upselling")
    
    return recommendations


def calculate_growth_potential(revenue: float, orders: int, products: int) -> str:
    """Calculate business growth potential"""
    if revenue > 10000000 and orders > 50:
        return "High - Ready for expansion and investment"
    elif revenue > 5000000 and orders > 20:
        return "Moderate - Focus on scaling operations"
    else:
        return "Early stage - Build customer base and product range"


def calculate_financial_stability(income: float, expense: float, wallet: float) -> str:
    """Calculate financial stability score"""
    if wallet > expense * 6:  # 6 months runway
        return "excellent"
    elif wallet > expense * 3:  # 3 months runway
        return "good"
    elif wallet > expense:  # 1 month runway
        return "moderate"
    else:
        return "concerning"


def generate_cash_management_advice(wallet: float, expense: float) -> str:
    """Generate cash management advice"""
    runway_months = wallet / max(expense, 1)
    
    if runway_months > 6:
        return "Cash position strong. Consider investing surplus for growth."
    elif runway_months > 3:
        return "Adequate cash reserves. Monitor cash flow closely."
    else:
        return "Low cash reserves. Focus on increasing revenue and reducing costs."


def generate_investment_advice(investment_ratio: float, roi: float) -> str:
    """Generate investment strategy advice"""
    if investment_ratio < 5:
        return "Consider allocating 10-20% of income to investments for long-term growth."
    elif investment_ratio > 30:
        return "High investment allocation. Ensure sufficient cash for operations."
    elif roi < 0:
        return "Review investment strategy. Consider more conservative options."
    else:
        return "Investment allocation looks balanced. Monitor performance regularly."


def generate_cost_advice(expense: float, income: float) -> str:
    """Generate cost optimization advice"""
    expense_ratio = (expense / income * 100) if income > 0 else 0
    
    if expense_ratio > 80:
        return "High expense ratio. Urgent cost reduction needed."
    elif expense_ratio > 60:
        return "Moderate expense ratio. Look for cost optimization opportunities."
    else:
        return "Good cost control. Maintain current efficiency levels."


def calculate_diversification_score(num_assets: int, concentration: float) -> str:
    """Calculate portfolio diversification score"""
    if num_assets >= 5 and concentration < 30:
        return "excellent"
    elif num_assets >= 3 and concentration < 50:
        return "good"
    elif num_assets >= 2:
        return "moderate"
    else:
        return "poor"


def generate_diversification_advice(num_assets: int, concentration: float) -> str:
    """Generate diversification advice"""
    if num_assets < 3:
        return "Add more assets to reduce risk. Target 3-5 different cryptocurrencies."
    elif concentration > 60:
        return "Reduce concentration in largest position. Rebalance portfolio."
    else:
        return "Good diversification. Maintain current allocation strategy."


def generate_rebalancing_advice(distribution: Dict, total: float) -> str:
    """Generate rebalancing advice"""
    if not distribution:
        return "Start building a diversified portfolio with major cryptocurrencies."
    
    max_allocation = max(distribution.values()) / total * 100
    if max_allocation > 50:
        return "Consider rebalancing - largest position exceeds 50% of portfolio."
    else:
        return "Portfolio allocation looks balanced. Review quarterly."


def generate_risk_management_advice(concentration: float) -> str:
    """Generate risk management advice"""
    if concentration > 70:
        return "High concentration risk. Implement stop-loss orders and diversify immediately."
    elif concentration > 50:
        return "Moderate risk. Consider position sizing and risk management rules."
    else:
        return "Good risk distribution. Maintain disciplined approach."


# ============================================================================
# AGENT STATE & WORKFLOW
# ============================================================================

class EnhancedAgentState(TypedDict):
    """State untuk enhanced agent"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_query: str
    user_token: str
    wallet_address: str
    next_step: str


def create_llm(temperature: float = 0.3):
    """Create LLM instance"""
    return ChatOpenAI(
        model=DEFAULT_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=temperature,
        max_tokens=4000
    )


def parse_query(state: EnhancedAgentState) -> EnhancedAgentState:
    """Parse user query"""
    messages = state["messages"]
    return {
        "messages": messages,
        "user_query": messages[-1].content if messages else "",
        "user_token": state.get("user_token", ""),
        "wallet_address": state.get("wallet_address", ""),
        "next_step": "analyze"
    }


def should_continue(state: EnhancedAgentState):
    """Check if need to call tools or generate report"""
    last_message = state["messages"][-1]
    
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return "generate_report"


def call_model(state: EnhancedAgentState) -> EnhancedAgentState:
    """Call LLM with tools"""
    
    messages = state["messages"]
    
    if len([m for m in messages if isinstance(m, SystemMessage)]) == 0:
        system_msg = SystemMessage(content=f"""Anda adalah AI Assistant WarungTech untuk analisis bisnis dan investasi.

User Info:
- Token: {'✅ Provided' if state.get('user_token') else '❌ Missing'}
- Wallet: {state.get('wallet_address', 'Not connected')}

TOOLS TERSEDIA:

**📊 Business Analysis (WarungTech API):**
1. get_business_dashboard_stats - Statistik bisnis real-time dari database
2. get_financial_summary - Ringkasan keuangan & cash flow analysis
3. get_user_investments - Portfolio investasi crypto dari database

**💰 Market Data:**
4. get_market_data - Harga crypto real-time dari CoinGecko

**🎫 Blockchain Features (Currently Disabled):**
Note: Blockchain coupon analysis features are under development

PRIORITAS PENGGUNAAN:
- Query tentang BISNIS/REVENUE → Gunakan tools 1, 2, 3
- Query tentang INVESTASI/CRYPTO → Gunakan tools 3, 4
- Query tentang PROMO/KUPON → Fokus pada business analysis saja
- Query KOMPREHENSIF → Gunakan SEMUA tools yang tersedia

PENTING:
- JWT token WAJIB untuk business & investment tools
- Berikan rekomendasi ACTIONABLE berdasarkan data REAL
- Fokus pada business analysis dan market data
""")
        
        messages = [system_msg] + list(messages)
    
    llm = create_llm()
    
    # Available tools (blockchain tools only if Web3 is configured)
    available_tools = [
        get_business_dashboard_stats,
        get_financial_summary,
        get_user_investments,
        get_market_data
    ]
    
    # Note: Blockchain tools are disabled for now
    # TODO: Implement get_blockchain_coupon_statistics and get_active_blockchain_coupons
    # if w3 and coupon_contract:
    #     available_tools.extend([
    #         get_blockchain_coupon_statistics,
    #         get_active_blockchain_coupons
    #     ])
    
    model_with_tools = llm.bind_tools(available_tools)
    
    response = model_with_tools.invoke(messages)
    
    return {"messages": [response]}


def generate_report(state: EnhancedAgentState) -> EnhancedAgentState:
    """Generate final report"""
    
    messages = state["messages"]
    
    report_prompt = """Buat laporan DALAM BAHASA INDONESIA berdasarkan data dari tools.

Format:

# 📊 LAPORAN WARUNGTECH AI

## 🏪 Status Bisnis
[Data dari get_business_dashboard_stats]
- Revenue & orders
- Product count & diversity
- Business maturity level

## 💰 Kondisi Keuangan
[Data dari get_financial_summary]
- Cash flow analysis
- Investment ratio
- Financial stability

## 📈 Portfolio Investasi
[Data dari get_user_investments dan get_market_data]
- Asset allocation
- Diversification analysis
- Market performance

## 🎫 Promo Blockchain (jika tersedia)
[Data dari blockchain tools jika ada]

## 💡 REKOMENDASI STRATEGIS

### Bisnis:
1. [Berdasarkan business metrics]
2. [Growth opportunities]

### Keuangan:
1. [Cash management]
2. [Investment strategy]

### Timeline Eksekusi:
- Minggu 1-2: [Aksi prioritas tinggi]
- Bulan 1-3: [Strategi jangka menengah]

Gunakan HANYA data real dari tools yang berhasil dijalankan!"""
    
    final_messages = list(messages) + [HumanMessage(content=report_prompt)]
    
    llm = create_llm(temperature=0.5)
    response = llm.invoke(final_messages)
    
    return {
        "messages": [response],
        "next_step": "complete"
    }


def build_agent():
    """Build workflow"""
    
    # Base tools
    tools = [
        get_business_dashboard_stats,
        get_financial_summary,
        get_user_investments,
        get_market_data
    ]
    
    # Note: Blockchain tools are disabled for now
    # TODO: Implement get_blockchain_coupon_statistics and get_active_blockchain_coupons
    # if w3 and coupon_contract:
    #     tools.extend([
    #         get_blockchain_coupon_statistics,
    #         get_active_blockchain_coupons
    #     ])
    
    tool_node = ToolNode(tools)
    
    workflow = StateGraph(EnhancedAgentState)
    
    workflow.add_node("parse", parse_query)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_node("report", generate_report)
    
    workflow.set_entry_point("parse")
    workflow.add_edge("parse", "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "generate_report": "report"})
    workflow.add_edge("tools", "agent")
    workflow.add_edge("report", END)
    
    return workflow.compile()


# ============================================================================
# MAIN RUNNER & API ENDPOINT
# ============================================================================

def run_agent(
    query: str,
    user_token: str = "",
    wallet_address: str = ""
):
    """Run agent dengan query"""
    
    print("\n" + "="*80)
    print("🤖 WARUNGTECH AI ASSISTANT")
    print("="*80)
    print(f"Query: {query}")
    print(f"Token: {'✅ Valid' if validate_token(user_token) else '❌ Invalid/Missing'}")
    print(f"Wallet: {wallet_address or 'Not connected'}")
    print(f"Blockchain: {'✅ Available' if w3 and coupon_contract else '❌ Disabled'}")
    print("="*80)
    
    try:
        agent = build_agent()
        
        result = agent.invoke({
            "messages": [HumanMessage(content=query)],
            "user_query": query,
            "user_token": user_token,
            "wallet_address": wallet_address,
            "next_step": "start"
        })
        
        report = result["messages"][-1].content
        print("\n" + "="*80)
        print("📄 LAPORAN")
        print("="*80)
        print(report)
        print("\n" + "="*80)
        
        return {
            "success": True, 
            "report": report,
            "timestamp": datetime.now().isoformat(),
            "features_used": {
                "business_analysis": bool(user_token),
                "blockchain_coupons": bool(w3 and coupon_contract and wallet_address),
                "market_data": True
            }
        }
        
    except Exception as e:
        error_msg = f"Error running agent: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# FLASK API ENDPOINT (untuk integrasi dengan mobile app)
# ============================================================================

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """API endpoint untuk mobile app"""
    try:
        data = request.get_json()
        
        query = data.get('message', '')
        user_token = data.get('user_token', '')
        wallet_address = data.get('wallet_address', '')
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Message is required"
            }), 400
        
        print(f"🔍 Processing chat request: {query[:50]}...")
        print(f"🔑 Token provided: {'Yes' if user_token else 'No'}")
        print(f"💰 Wallet provided: {'Yes' if wallet_address else 'No'}")
        
        # Run agent with better error handling
        try:
            result = run_agent(query, user_token, wallet_address)
            print(f"✅ Agent completed: {result.get('success', False)}")
            return jsonify(result)
        except ImportError as ie:
            print(f"❌ Import Error: {ie}")
            # Return a simplified response without the problematic agent
            return jsonify({
                "success": True,
                "report": f"Maaf, terjadi masalah teknis dengan sistem AI. Pesan Anda: '{query}' telah diterima. Tim teknis sedang memperbaiki masalah ini.",
                "timestamp": datetime.now().isoformat(),
                "features_used": {
                    "business_analysis": False,
                    "blockchain_coupons": False,
                    "market_data": False
                },
                "error_details": f"Import error: {str(ie)}"
            })
        except Exception as agent_error:
            print(f"❌ Agent Error: {agent_error}")
            return jsonify({
                "success": False,
                "error": f"Agent processing error: {str(agent_error)}"
            }), 500
        
    except Exception as e:
        print(f"❌ Endpoint Error: {e}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "WarungTech AI Assistant is running",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "business_analysis": True,
            "market_data": True,
            "blockchain_coupons": False  # Disabled for now
        },
        "requirements": {
            "OPENROUTER_API_KEY": bool(OPENROUTER_API_KEY),
            "INFURA_PROJECT_ID": bool(INFURA_PROJECT_ID)
        }
    })


# ============================================================================
# CONTOH PENGGUNAAN & TESTING
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run Flask server
        print("🚀 Starting WarungTech AI API Server...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # Run test examples
        print("\n🧪 TESTING WARUNGTECH AI ASSISTANT")
        
        # Test 1: Business Analysis (requires token)
        print("\n📊 TEST 1: BUSINESS ANALYSIS")
        test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"  # Replace with real token
        run_agent(
            query="Analisis kondisi bisnis saya dan berikan rekomendasi untuk meningkatkan revenue",
            user_token=test_token
        )
        
        # Test 2: Investment Analysis
        print("\n💰 TEST 2: INVESTMENT & MARKET ANALYSIS")
        run_agent(
            query="Bagaimana performa portfolio investasi crypto saya? Berikan rekomendasi diversifikasi",
            user_token=test_token
        )
        
        # Test 3: Comprehensive Analysis
        print("\n🎯 TEST 3: COMPREHENSIVE ANALYSIS")
        run_agent(
            query="""Tolong analisis lengkap:
            1. Kondisi bisnis dan keuangan saya
            2. Performa investasi crypto
            3. Rekomendasi strategi untuk 3 bulan ke depan
            """,
            user_token=test_token,
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        )