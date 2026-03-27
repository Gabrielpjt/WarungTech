"""
WarungTech AI API Server
Powered by OpenRouter LLM (from coba.py workflow)
Provides: product recommendations, investment analysis, coupon recommendations
Integrates with WarungTechAPI for real business data
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time
import requests
from datetime import datetime
from openai import OpenAI

app = Flask(__name__)
CORS(app, origins=['*'])

# ===== LLM CONFIGURATION (from coba.py) =====
OPENROUTER_API_KEY = "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"
MODEL = "meta-llama/llama-3.2-3b-instruct:free"
FALLBACK_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "openai/gpt-3.5-turbo",
]

llm_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ===== WARUNGTECH API CONFIGURATION =====
WARUNGTECH_API_BASE = "https://war-tech-backend-k6hg.vercel.app/api"


# ===== LLM HELPER =====
def call_llm(messages: list, temperature: float = 0.3, model: str = None) -> str:
    """Call LLM with fallback support (from coba.py pattern)"""
    current_model = model or MODEL
    all_models = [current_model] + FALLBACK_MODELS

    for attempt_model in all_models:
        try:
            response = llm_client.chat.completions.create(
                model=attempt_model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            err = str(e)
            print(f"⚠️ Model {attempt_model} failed: {err[:80]}")
            if "401" in err or "authentication" in err.lower():
                print("❌ Auth error — check OPENROUTER_API_KEY")
                break
            continue

    return ""


# ===== WARUNGTECH API HELPERS =====
def fetch_warungtech_data(endpoint: str, token: str = None) -> dict:
    """Fetch real data from WarungTechAPI"""
    try:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = requests.get(f"{WARUNGTECH_API_BASE}{endpoint}", headers=headers, timeout=8)
        if resp.ok:
            return resp.json()
    except Exception as e:
        print(f"⚠️ WarungTechAPI fetch failed ({endpoint}): {e}")
    return {}


def get_business_context(token: str = None) -> dict:
    """Fetch dashboard stats, transactions, wallet from WarungTechAPI"""
    context = {}
    if not token:
        return context

    stats = fetch_warungtech_data("/dashboard/stats", token)
    if stats.get("success"):
        context["stats"] = stats.get("data", {})

    wallet = fetch_warungtech_data("/wallet", token)
    if wallet.get("success"):
        context["wallet"] = wallet.get("data", {})

    history = fetch_warungtech_data("/transaction-history?limit=10", token)
    if history.get("success"):
        context["recent_transactions"] = history.get("data", {}).get("transactions", [])

    return context


# ===== RECOMMENDATION ENGINES =====

def generate_product_recommendations(business_context: dict, user_message: str) -> dict:
    """Generate product recommendations using LLM + real business data"""
    stats = business_context.get("stats", {})
    transactions = business_context.get("recent_transactions", [])

    prompt = f"""Kamu adalah konsultan bisnis warung/UMKM profesional.

Data bisnis pengguna:
- Total Revenue: Rp {stats.get('total_revenue', 0):,.0f}
- Total Transaksi: {stats.get('total_transactions', 0)}
- Total Produk: {stats.get('total_products', 0)}
- Wallet Balance: Rp {stats.get('wallet_balance', 0):,.0f}
- Transaksi terbaru: {len(transactions)} transaksi

Pertanyaan pengguna: "{user_message}"

Berikan rekomendasi produk dalam format JSON:
{{
  "recommendations": [
    {{
      "product_name": "nama produk",
      "category": "kategori",
      "estimated_price": 15000,
      "reason": "alasan rekomendasi",
      "expected_profit_margin": "30%",
      "priority": "high/medium/low"
    }}
  ],
  "summary": "ringkasan rekomendasi",
  "action_plan": "langkah konkret yang harus dilakukan"
}}

Berikan 3-5 rekomendasi produk yang relevan. Response harus JSON valid."""

    content = call_llm([
        {"role": "system", "content": "You are a business consultant. Respond only with valid JSON."},
        {"role": "user", "content": prompt}
    ], temperature=0.4)

    try:
        clean = content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception:
        return {
            "recommendations": [
                {"product_name": "Minuman Kekinian", "category": "Minuman", "estimated_price": 8000,
                 "reason": "Margin tinggi, permintaan stabil", "expected_profit_margin": "40%", "priority": "high"},
                {"product_name": "Snack Lokal", "category": "Makanan", "estimated_price": 5000,
                 "reason": "Modal rendah, perputaran cepat", "expected_profit_margin": "35%", "priority": "high"},
            ],
            "summary": "Fokus pada produk dengan margin tinggi dan perputaran cepat",
            "action_plan": "Mulai dengan 2-3 produk unggulan, evaluasi setiap minggu"
        }


def generate_investment_recommendations(business_context: dict, wallet_address: str = None) -> dict:
    """Generate investment recommendations using LLM (from coba.py workflow)"""
    wallet = business_context.get("wallet", {})
    stats = business_context.get("stats", {})
    wallet_balance = float(wallet.get("balance", 0))

    prompt = f"""Kamu adalah advisor investasi cryptocurrency profesional.

Data keuangan pengguna:
- Saldo Wallet WarungTech: Rp {wallet_balance:,.0f}
- Total Revenue Bisnis: Rp {stats.get('total_revenue', 0):,.0f}
- MetaMask Address: {wallet_address or 'Belum terhubung'}

Berikan rekomendasi investasi dalam format JSON:
{{
  "portfolio": [
    {{
      "coin": "BTC",
      "allocation_percent": 40,
      "amount_idr": "Rp 4.000.000",
      "risk_level": "Low-Medium",
      "expected_return": "15-25%",
      "dca_weekly": "Rp 400.000",
      "support_level": "$65,000",
      "resistance_level": "$75,000",
      "rsi": "58 (Neutral)",
      "fundamental_score": "9/10",
      "reasoning": "Store of value terbukti, adopsi institusional meningkat"
    }}
  ],
  "total_recommended_investment": "Rp 10.000.000",
  "emergency_reserve": "20% dari saldo",
  "strategy": "Dollar Cost Averaging (DCA) mingguan",
  "market_sentiment": {{
    "fear_greed_index": "45 (Neutral)",
    "bitcoin_dominance": "52%",
    "trend": "Recovery Phase"
  }},
  "risk_warning": "Hanya investasi dana yang siap hilang"
}}

Rekomendasikan 4 crypto (BTC, ETH, BNB, SOL) dengan alokasi total 100%. JSON valid."""

    content = call_llm([
        {"role": "system", "content": "You are a crypto investment advisor. Respond only with valid JSON."},
        {"role": "user", "content": prompt}
    ], temperature=0.3)

    try:
        clean = content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception:
        return {
            "portfolio": [
                {"coin": "BTC", "allocation_percent": 40, "amount_idr": "Rp 4.000.000",
                 "risk_level": "Low-Medium", "expected_return": "15-25%", "dca_weekly": "Rp 400.000",
                 "support_level": "$65,000", "resistance_level": "$75,000", "rsi": "58 (Neutral)",
                 "fundamental_score": "9/10", "reasoning": "Store of value, adopsi institusional tinggi"},
                {"coin": "ETH", "allocation_percent": 30, "amount_idr": "Rp 3.000.000",
                 "risk_level": "Medium", "expected_return": "20-35%", "dca_weekly": "Rp 300.000",
                 "support_level": "$3,200", "resistance_level": "$4,200", "rsi": "62 (Bullish)",
                 "fundamental_score": "9/10", "reasoning": "Platform DeFi #1, Ethereum 2.0"},
                {"coin": "BNB", "allocation_percent": 20, "amount_idr": "Rp 2.000.000",
                 "risk_level": "Medium", "expected_return": "18-30%", "dca_weekly": "Rp 200.000",
                 "support_level": "$580", "resistance_level": "$720", "rsi": "Volume Increasing",
                 "fundamental_score": "8/10", "reasoning": "Exchange utility, burn mechanism"},
                {"coin": "SOL", "allocation_percent": 10, "amount_idr": "Rp 1.000.000",
                 "risk_level": "High", "expected_return": "25-50%", "dca_weekly": "Rp 100.000",
                 "support_level": "$180", "resistance_level": "$260", "rsi": "45 (Recovery)",
                 "fundamental_score": "7/10", "reasoning": "High TPS, growing DeFi ecosystem"},
            ],
            "total_recommended_investment": "Rp 10.000.000",
            "emergency_reserve": "20% dari saldo",
            "strategy": "Dollar Cost Averaging (DCA) mingguan",
            "market_sentiment": {"fear_greed_index": "45 (Neutral)", "bitcoin_dominance": "52%", "trend": "Recovery Phase"},
            "risk_warning": "Hanya investasi dana yang siap hilang"
        }


def generate_coupon_recommendations(business_context: dict, user_message: str) -> dict:
    """Generate coupon/promo recommendations using LLM + real business data"""
    stats = business_context.get("stats", {})
    transactions = business_context.get("recent_transactions", [])
    total_savings = float(stats.get("total_savings", 0))
    total_revenue = float(stats.get("total_revenue", 0))

    prompt = f"""Kamu adalah marketing strategist untuk UMKM/warung.

Data bisnis:
- Revenue: Rp {total_revenue:,.0f}
- Total Transaksi: {stats.get('total_transactions', 0)}
- Total Penghematan Kupon: Rp {total_savings:,.0f}
- Transaksi dengan kupon: {stats.get('transactions_with_coupons', 0)}

Pertanyaan: "{user_message}"

Berikan rekomendasi kupon/promo dalam format JSON:
{{
  "coupons": [
    {{
      "name": "nama kupon",
      "type": "percentage/fixed/bogo",
      "discount_value": "20%",
      "min_purchase": 50000,
      "validity_days": 7,
      "target_segment": "pelanggan baru/setia/semua",
      "expected_redemption_rate": "30%",
      "estimated_revenue_boost": "+15%",
      "reason": "alasan strategi ini efektif"
    }}
  ],
  "strategy_summary": "ringkasan strategi promosi",
  "best_timing": "waktu terbaik untuk launch promo",
  "blockchain_benefit": "keuntungan menggunakan IDRX blockchain coupon"
}}

Berikan 3-4 rekomendasi kupon. JSON valid."""

    content = call_llm([
        {"role": "system", "content": "You are a marketing strategist. Respond only with valid JSON."},
        {"role": "user", "content": prompt}
    ], temperature=0.4)

    try:
        clean = content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception:
        return {
            "coupons": [
                {"name": "Flash Sale Weekend", "type": "percentage", "discount_value": "20%",
                 "min_purchase": 50000, "validity_days": 2, "target_segment": "semua",
                 "expected_redemption_rate": "35%", "estimated_revenue_boost": "+25%",
                 "reason": "Weekend traffic tinggi, diskon menarik impulse buyers"},
                {"name": "Loyalty Reward", "type": "fixed", "discount_value": "Rp 10.000",
                 "min_purchase": 75000, "validity_days": 30, "target_segment": "pelanggan setia",
                 "expected_redemption_rate": "60%", "estimated_revenue_boost": "+15%",
                 "reason": "Meningkatkan retention pelanggan lama"},
                {"name": "Bundle Deal", "type": "bogo", "discount_value": "Buy 2 Get 1",
                 "min_purchase": 30000, "validity_days": 7, "target_segment": "semua",
                 "expected_redemption_rate": "40%", "estimated_revenue_boost": "+20%",
                 "reason": "Meningkatkan average order value"},
            ],
            "strategy_summary": "Kombinasi flash sale dan loyalty program untuk maksimalkan revenue",
            "best_timing": "Jumat sore - Minggu malam",
            "blockchain_benefit": "Kupon IDRX tidak bisa dipalsukan, transparan, dan auto-redeem"
        }


# ===== CHAT RESPONSE GENERATOR =====

def generate_chat_response(user_message: str, business_context: dict, wallet_address: str = None) -> dict:
    """Generate contextual chat response using LLM"""
    stats = business_context.get("stats", {})
    context_summary = f"""
Data bisnis pengguna:
- Revenue: Rp {stats.get('total_revenue', 0):,.0f}
- Transaksi: {stats.get('total_transactions', 0)}
- Wallet: Rp {stats.get('wallet_balance', 0):,.0f}
- Produk: {stats.get('total_products', 0)}
""" if stats else "Data bisnis belum tersedia."

    prompt = f"""Kamu adalah WarTech AI, asisten bisnis cerdas untuk warung/UMKM Indonesia.
Kamu membantu dengan: analisis bisnis, rekomendasi produk, strategi promo, investasi crypto, dan pembayaran IDRX.

{context_summary}

Pesan pengguna: "{user_message}"

Berikan respons yang helpful, singkat, dan actionable dalam Bahasa Indonesia.
Jika tentang crypto/investasi, berikan analisis singkat.
Jika tentang bisnis/omzet, berikan insight dari data.
Jika tentang promo/kupon, berikan rekomendasi konkret."""

    content = call_llm([
        {"role": "system", "content": "Kamu adalah asisten bisnis AI yang helpful dan profesional."},
        {"role": "user", "content": prompt}
    ], temperature=0.5)

    return content or "Maaf, saya tidak dapat memproses permintaan Anda saat ini. Silakan coba lagi."


# ===== INTENT DETECTION =====
def detect_intent(message: str) -> str:
    """Detect user intent from message"""
    msg = message.lower()
    if any(k in msg for k in ['produk', 'jual', 'dagangan', 'barang', 'stok']):
        return 'product_recommendation'
    if any(k in msg for k in ['crypto', 'investasi', 'bitcoin', 'ethereum', 'btc', 'eth', 'invest']):
        return 'investment'
    if any(k in msg for k in ['promo', 'kupon', 'diskon', 'voucher', 'cashback']):
        return 'coupon_recommendation'
    if any(k in msg for k in ['omzet', 'pendapatan', 'revenue', 'penjualan', 'untung']):
        return 'business_analysis'
    if any(k in msg for k in ['bayar', 'qr', 'payment', 'idrx', 'transfer']):
        return 'payment'
    if any(k in msg for k in ['risiko', 'aman', 'risk', 'bahaya']):
        return 'risk_analysis'
    return 'general'


# ===== ENDPOINTS =====

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'WarungTech AI API is running',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0',
        'features': ['product_recommendations', 'investment_analysis', 'coupon_recommendations', 'business_analysis']
    })


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'Message is required'}), 400

        user_message = data['message'].strip()
        user_id = data.get('user_id', 'mobile_user')
        conversation_id = data.get('conversation_id', 1)
        user_token = data.get('user_token')
        wallet_address = data.get('wallet_address')

        print(f"📨 Chat from {user_id}: {user_message[:60]}")

        # Fetch real business data if token provided
        business_context = get_business_context(user_token)

        intent = detect_intent(user_message)
        print(f"🎯 Intent: {intent}")

        response_data = {
            'conversation_id': conversation_id + 1,
            'user_profile': {'user_id': user_id},
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'general',
            'intent': intent,
        }

        if intent == 'product_recommendation':
            recs = generate_product_recommendations(business_context, user_message)
            response_data.update({
                'message': '🛍️ Rekomendasi Produk untuk Bisnis Anda',
                'full_report': json.dumps(recs, ensure_ascii=False, indent=2),
                'analysis_type': 'product',
                'product_recommendations': recs.get('recommendations', []),
                'action_plan': recs.get('action_plan', ''),
            })

        elif intent == 'investment':
            inv = generate_investment_recommendations(business_context, wallet_address)
            response_data.update({
                'message': '📈 Analisis Investasi Crypto Komprehensif',
                'full_report': json.dumps(inv, ensure_ascii=False, indent=2),
                'analysis_type': 'crypto',
                'crypto_recommendations': [
                    {
                        'coin': p['coin'],
                        'allocation': f"{p['allocation_percent']}%",
                        'amount': p.get('amount_idr', ''),
                        'risk': p.get('risk_level', ''),
                        'expected_return': p.get('expected_return', ''),
                        'dca_weekly': p.get('dca_weekly', ''),
                        'support_level': p.get('support_level', ''),
                        'resistance_level': p.get('resistance_level', ''),
                        'rsi': p.get('rsi', ''),
                        'fundamental_score': p.get('fundamental_score', ''),
                        'reasoning': p.get('reasoning', ''),
                    } for p in inv.get('portfolio', [])
                ],
                'wallet_info': {
                    'current_balance': f"Rp {float(business_context.get('wallet', {}).get('balance', 0)):,.0f}",
                    'available_for_investment': inv.get('total_recommended_investment', ''),
                    'emergency_reserve': inv.get('emergency_reserve', '20%'),
                },
                'market_analysis': inv.get('market_sentiment', {}),
            })

        elif intent == 'coupon_recommendation':
            coup = generate_coupon_recommendations(business_context, user_message)
            response_data.update({
                'message': '🎯 Rekomendasi Kupon & Strategi Promo',
                'full_report': json.dumps(coup, ensure_ascii=False, indent=2),
                'analysis_type': 'coupon',
                'coupon_recommendations': coup.get('coupons', []),
                'strategy_summary': coup.get('strategy_summary', ''),
                'best_timing': coup.get('best_timing', ''),
                'blockchain_benefit': coup.get('blockchain_benefit', ''),
            })

        elif intent == 'business_analysis':
            stats = business_context.get('stats', {})
            ai_insight = generate_chat_response(user_message, business_context)
            response_data.update({
                'message': '📊 Analisis Bisnis Anda',
                'full_report': ai_insight,
                'analysis_type': 'business',
                'revenue_data': {
                    'today': f"Rp {float(stats.get('total_revenue', 0)):,.0f}",
                    'transactions': stats.get('total_transactions', 0),
                    'wallet_balance': f"Rp {float(stats.get('wallet_balance', 0)):,.0f}",
                    'total_savings': f"Rp {float(stats.get('total_savings', 0)):,.0f}",
                    'trend': 'increasing' if float(stats.get('total_revenue', 0)) > 0 else 'no_data',
                },
            })

        else:
            ai_response = generate_chat_response(user_message, business_context, wallet_address)
            response_data.update({
                'message': '🤖 WarTech AI',
                'full_report': ai_response,
                'analysis_type': 'general',
            })

        return jsonify({'success': True, 'data': response_data})

    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/quick-action', methods=['POST'])
def quick_action_endpoint():
    try:
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify({'success': False, 'error': 'Action is required'}), 400

        action = data['action']
        user_token = data.get('user_token')
        wallet_address = data.get('wallet_address')
        print(f"⚡ Quick action: {action}")

        business_context = get_business_context(user_token)
        stats = business_context.get('stats', {})

        base = {'conversation_id': 1, 'timestamp': datetime.now().isoformat(), 'action': action}

        if action == 'check_revenue':
            response_data = {
                **base,
                'message': f"📊 Revenue: Rp {float(stats.get('total_revenue', 0)):,.0f}",
                'full_report': f"Total {stats.get('total_transactions', 0)} transaksi. Wallet: Rp {float(stats.get('wallet_balance', 0)):,.0f}",
                'analysis_type': 'business',
                'revenue_data': {
                    'today': f"Rp {float(stats.get('total_revenue', 0)):,.0f}",
                    'transactions': stats.get('total_transactions', 0),
                    'wallet_balance': f"Rp {float(stats.get('wallet_balance', 0)):,.0f}",
                    'trend': 'increasing',
                },
            }

        elif action == 'product_recommendation':
            recs = generate_product_recommendations(business_context, "rekomendasi produk terbaik untuk bisnis saya")
            response_data = {
                **base,
                'message': '🛍️ Rekomendasi Produk Terbaik',
                'full_report': recs.get('summary', ''),
                'analysis_type': 'product',
                'product_recommendations': recs.get('recommendations', []),
                'action_plan': recs.get('action_plan', ''),
            }

        elif action == 'create_promo':
            coup = generate_coupon_recommendations(business_context, "buat promo terbaik untuk meningkatkan penjualan")
            response_data = {
                **base,
                'message': '🎯 Rekomendasi Promo & Kupon',
                'full_report': coup.get('strategy_summary', ''),
                'analysis_type': 'coupon',
                'coupon_recommendations': coup.get('coupons', []),
                'strategy_summary': coup.get('strategy_summary', ''),
                'best_timing': coup.get('best_timing', ''),
            }

        elif action == 'payment_qr':
            response_data = {
                **base,
                'message': '💳 QR Payment IDRX siap digunakan',
                'full_report': 'Sistem pembayaran QR code dengan blockchain IDRX memberikan keamanan tinggi dan biaya transaksi rendah.',
                'analysis_type': 'general',
                'qr_info': {'method': 'IDRX Blockchain', 'benefits': ['Biaya rendah', 'Transparan', 'Aman', 'Real-time']},
            }

        elif action == 'crypto_analysis':
            inv = generate_investment_recommendations(business_context, wallet_address)
            response_data = {
                **base,
                'message': '📈 Analisis Crypto & Rekomendasi Portfolio',
                'full_report': json.dumps(inv, ensure_ascii=False),
                'analysis_type': 'crypto',
                'crypto_recommendations': [
                    {
                        'coin': p['coin'],
                        'allocation': f"{p['allocation_percent']}%",
                        'amount': p.get('amount_idr', ''),
                        'risk': p.get('risk_level', ''),
                        'expected_return': p.get('expected_return', ''),
                        'dca_weekly': p.get('dca_weekly', ''),
                        'support_level': p.get('support_level', ''),
                        'resistance_level': p.get('resistance_level', ''),
                        'rsi': p.get('rsi', ''),
                        'fundamental_score': p.get('fundamental_score', ''),
                    } for p in inv.get('portfolio', [])
                ],
                'wallet_info': {
                    'current_balance': f"Rp {float(business_context.get('wallet', {}).get('balance', 0)):,.0f}",
                    'available_for_investment': inv.get('total_recommended_investment', ''),
                },
                'market_analysis': inv.get('market_sentiment', {}),
            }

        elif action == 'explain_risk':
            response_data = {
                **base,
                'message': '⚠️ Manajemen Risiko Investasi',
                'full_report': 'Crypto memiliki volatilitas tinggi. Maksimal 5-10% dari total aset. Selalu DYOR dan set stop-loss.',
                'analysis_type': 'general',
            }

        else:
            response_data = {
                **base,
                'message': '🤖 Aksi tidak dikenali',
                'full_report': 'Silakan gunakan aksi yang tersedia.',
                'analysis_type': 'general',
            }

        return jsonify({'success': True, 'data': response_data})

    except Exception as e:
        print(f"❌ Quick action error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/recommendations', methods=['POST'])
def recommendations_endpoint():
    """Dedicated endpoint for all recommendation types"""
    try:
        data = request.get_json()
        rec_type = data.get('type', 'all')  # product, investment, coupon, all
        user_token = data.get('user_token')
        wallet_address = data.get('wallet_address')

        business_context = get_business_context(user_token)
        result = {}

        if rec_type in ('product', 'all'):
            result['product'] = generate_product_recommendations(business_context, "rekomendasi produk terbaik")

        if rec_type in ('investment', 'all'):
            result['investment'] = generate_investment_recommendations(business_context, wallet_address)

        if rec_type in ('coupon', 'all'):
            result['coupon'] = generate_coupon_recommendations(business_context, "rekomendasi promo terbaik")

        return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})

    except Exception as e:
        print(f"❌ Recommendations error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 WARUNGTECH AI API v3.0 — LLM-Powered")
    print("="*70)
    print("📡 Endpoints:")
    print("   POST /chat              — AI chat with intent detection")
    print("   POST /quick-action      — Quick action handler")
    print("   POST /recommendations   — Product/Investment/Coupon recs")
    print("   GET  /health            — Health check")
    print("="*70)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
