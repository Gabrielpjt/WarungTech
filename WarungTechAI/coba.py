from typing import TypedDict, List, Dict, Any, Optional
from openai import OpenAI
import json
from datetime import datetime
import os

# ===== CONFIGURATION =====
OPENROUTER_API_KEY = "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"

# Model options (pilih yang available di OpenRouter account Anda)
AVAILABLE_MODELS = {
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "gpt-4o": "openai/gpt-4o",
    "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
    "claude-sonnet": "anthropic/claude-3.5-sonnet",
    "gemini-flash": "google/gemini-flash-1.5",
    "gpt-oss": "openai/gpt-oss-120b:free",  # Free model dengan reasoning
    "llama": "meta-llama/llama-3.1-8b-instruct:free",  # Alternative free model
}

# Default model - gunakan yang paling reliable
MODEL = "meta-llama/llama-3.2-3b-instruct:free" # Lebih stable untuk free tier

# Initialize OpenAI client dengan OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


# ===== STATE DEFINITION =====
class CryptoAgentState(TypedDict):
    user_query: str
    user_profile: Dict[str, Any]
    market_data: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    final_report: str
    conversation_history: List[Dict[str, Any]]


# ===== TOOLS IMPLEMENTATION =====
class CryptoTools:
    """Collection of tools untuk analisis cryptocurrency"""
    
    @staticmethod
    def fetch_market_data(crypto_symbols: List[str]) -> Dict[str, Any]:
        """
        Fetch real-time market data untuk cryptocurrencies.
        
        Args:
            crypto_symbols: List simbol crypto (e.g., ["BTC", "ETH", "SOL"])
        
        Returns:
            Dictionary dengan market data including price, volume, market cap
        """
        print(f"📊 Fetching market data for: {', '.join(crypto_symbols)}")
        
        # Simulasi data - dalam production gunakan API:
        # - CoinGecko: https://api.coingecko.com/api/v3/
        # - Binance: https://api.binance.com/api/v3/
        # - CoinMarketCap: https://pro-api.coinmarketcap.com/v1/
        
        sample_data = {
            "BTC": {
                "price": 45000,
                "change_24h": 2.5,
                "volume_24h": 28000000000,
                "market_cap": 880000000000,
                "high_24h": 46000,
                "low_24h": 43500,
                "circulating_supply": 19500000
            },
            "ETH": {
                "price": 2400,
                "change_24h": 3.2,
                "volume_24h": 15000000000,
                "market_cap": 290000000000,
                "high_24h": 2450,
                "low_24h": 2320,
                "circulating_supply": 120000000
            },
            "SOL": {
                "price": 110,
                "change_24h": -1.5,
                "volume_24h": 2000000000,
                "market_cap": 48000000000,
                "high_24h": 115,
                "low_24h": 108,
                "circulating_supply": 436000000
            },
            "BNB": {
                "price": 320,
                "change_24h": 1.8,
                "volume_24h": 1500000000,
                "market_cap": 49000000000,
                "high_24h": 325,
                "low_24h": 312,
                "circulating_supply": 153000000
            },
            "ADA": {
                "price": 0.58,
                "change_24h": 0.5,
                "volume_24h": 500000000,
                "market_cap": 20000000000,
                "high_24h": 0.60,
                "low_24h": 0.56,
                "circulating_supply": 35000000000
            }
        }
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "cryptocurrencies": {}
        }
        
        for symbol in crypto_symbols:
            if symbol in sample_data:
                result["cryptocurrencies"][symbol] = sample_data[symbol]
        
        return result
    
    @staticmethod
    def perform_technical_analysis(crypto_symbol: str, timeframe: str = "1d") -> Dict[str, Any]:
        """
        Perform technical analysis pada cryptocurrency.
        
        Args:
            crypto_symbol: Simbol cryptocurrency (e.g., "BTC")
            timeframe: Timeframe analisis (e.g., "1d", "1w", "1m")
        
        Returns:
            Dictionary dengan technical indicators dan signals
        """
        print(f"📈 Performing technical analysis for: {crypto_symbol}")
        
        # Simulasi - dalam production gunakan:
        # - TradingView API
        # - TA-Lib library
        # - Custom technical indicators
        
        import random
        signals = ['bullish', 'bearish', 'neutral']
        signal = random.choice(signals)
        
        analysis = {
            "symbol": crypto_symbol,
            "timeframe": timeframe,
            "indicators": {
                "RSI": round(45 + random.random() * 30, 2),  # 45-75
                "MACD": "bullish_crossover" if signal == 'bullish' else "bearish_crossover",
                "moving_averages": {
                    "MA50": "above" if signal != 'bearish' else "below",
                    "MA200": "above" if signal == 'bullish' else "below",
                    "EMA20": "bullish" if signal == 'bullish' else "neutral"
                },
                "bollinger_bands": {
                    "position": "middle",
                    "width": "normal",
                    "squeeze": False
                },
                "volume_profile": "increasing" if random.random() > 0.5 else "decreasing",
                "support_levels": [42000, 40000, 38000],
                "resistance_levels": [47000, 50000, 52000]
            },
            "signal": signal,
            "strength": random.randint(5, 10),  # 1-10 scale
            "trend": signal if signal != 'neutral' else 'sideways'
        }
        
        return analysis
    
    @staticmethod
    def analyze_sentiment(crypto_symbol: str) -> Dict[str, Any]:
        """
        Analyze market sentiment untuk cryptocurrency dari social media dan news.
        
        Args:
            crypto_symbol: Simbol cryptocurrency
        
        Returns:
            Dictionary dengan sentiment scores dan insights
        """
        print(f"🎭 Analyzing sentiment for: {crypto_symbol}")
        
        # Simulasi - dalam production gunakan:
        # - Twitter API / X API
        # - Reddit API (PRAW)
        # - News APIs (NewsAPI, CryptoPanic)
        # - LunarCrush API
        
        import random
        sentiments = ['positive', 'negative', 'neutral']
        sentiment = random.choice(sentiments)
        
        result = {
            "symbol": crypto_symbol,
            "overall_sentiment": sentiment,
            "sentiment_score": round(random.uniform(-1, 1), 2),  # -1 to 1
            "social_media": {
                "twitter_mentions": random.randint(10000, 30000),
                "reddit_sentiment": round(random.uniform(0.3, 0.9), 2),
                "reddit_posts": random.randint(500, 2000),
                "trending_score": random.randint(5, 10),
                "influencer_mentions": random.randint(10, 50)
            },
            "news_sentiment": {
                "positive_articles": random.randint(30, 60),
                "negative_articles": random.randint(5, 25),
                "neutral_articles": random.randint(15, 35),
                "major_headlines": []
            },
            "fear_greed_index": random.randint(30, 80),  # 0-100
            "market_momentum": sentiment,
            "whale_activity": "high" if random.random() > 0.7 else "moderate"
        }
        
        return result
    
    @staticmethod
    def assess_risk(user_profile: Dict[str, Any], crypto_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess investment risk berdasarkan user profile dan crypto characteristics.
        
        Args:
            user_profile: User's risk tolerance, investment goals, etc.
            crypto_data: Cryptocurrency market dan technical data
        
        Returns:
            Dictionary dengan risk assessment
        """
        print(f"⚠️ Assessing investment risk")
        
        risk_tolerance = user_profile.get("risk_tolerance", "moderate")
        
        risk_mapping = {
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
        
        import random
        volatility_score = round(20 + random.random() * 30, 1)  # 20-50%
        settings = risk_mapping[risk_tolerance]
        
        warnings = []
        recommendations = []
        
        if volatility_score > settings["max_volatility"]:
            warnings.append(
                f"⚠️ Volatilitas {volatility_score}% melebihi batas untuk profil {risk_tolerance}"
            )
            recommendations.append(
                f"💡 Pertimbangkan alokasi di bawah {settings['recommended_allocation']}%"
            )
        
        assessment = {
            "user_risk_profile": risk_tolerance,
            "crypto_volatility": "high" if volatility_score > 35 else "medium" if volatility_score > 20 else "low",
            "volatility_score": volatility_score,
            "recommended_allocation": settings["recommended_allocation"],
            "max_portfolio_exposure": settings["max_portfolio_exposure"],
            "min_diversification": settings["diversification_min"],
            "diversification_needed": True,
            "risk_level": "high" if volatility_score > 35 else "medium" if volatility_score > 20 else "low",
            "risk_score": round(volatility_score / 50 * 10, 1),  # 0-10 scale
            "warnings": warnings,
            "recommendations": recommendations,
            "liquidity_rating": random.choice(["high", "medium", "low"]),
            "regulatory_risk": random.choice(["low", "medium", "high"])
        }
        
        return assessment


# ===== WORKFLOW IMPLEMENTATION =====
class CryptoInvestmentWorkflow:
    """Main workflow orchestrator untuk crypto investment recommendations"""
    
    def __init__(self, use_reasoning: bool = False, model: str = None):
        """
        Initialize workflow
        
        Args:
            use_reasoning: Set True untuk gunakan model dengan reasoning capability
            model: Custom model name (optional). Jika None, akan gunakan default
        """
        self.state: CryptoAgentState = {
            "user_query": "",
            "user_profile": {},
            "market_data": {},
            "technical_analysis": {},
            "sentiment_analysis": {},
            "risk_assessment": {},
            "recommendations": [],
            "final_report": "",
            "conversation_history": []
        }
        self.use_reasoning = use_reasoning
        
        # Set model
        if model:
            self.model = model
        elif use_reasoning:
            # Untuk reasoning, prioritize models yang support
            self.model = MODEL
        else:
            # Default model
            self.model = model or MODEL
            
        print(f"🤖 Using model: {self.model}")
        print(f"🧠 Reasoning enabled: {self.use_reasoning}")
    
    def _call_llm(self, 
                  messages: List[Dict[str, Any]], 
                  temperature: float = 0.3,
                  preserve_reasoning: bool = True) -> tuple[str, Optional[Any]]:
        """
        Helper method untuk call LLM dengan OpenRouter
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            preserve_reasoning: Preserve reasoning_details untuk multi-turn reasoning
        
        Returns:
            Tuple of (response_content, reasoning_details)
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                extra_body = {}
                if self.use_reasoning:
                    extra_body["reasoning"] = {"enabled": True}
                
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    extra_body=extra_body if extra_body else None
                )
                
                message = response.choices[0].message
                content = message.content
                reasoning_details = getattr(message, 'reasoning_details', None) if preserve_reasoning else None
                
                return content, reasoning_details
                
            except Exception as e:
                error_msg = str(e)
                retry_count += 1
                
                # Handle specific errors
                if "404" in error_msg or "No endpoints found" in error_msg:
                    print(f"⚠️ Model {self.model} tidak tersedia. Mencoba fallback model...")
                    
                    # Fallback ke model yang lebih available
                    fallback_models = [
                        AVAILABLE_MODELS["gpt-3.5-turbo"],
                        AVAILABLE_MODELS["llama"],
                        AVAILABLE_MODELS["gemini-flash"]
                    ]
                    
                    for fallback in fallback_models:
                        if fallback != self.model:
                            print(f"🔄 Trying fallback: {fallback}")
                            self.model = fallback
                            self.use_reasoning = False  # Disable reasoning untuk fallback
                            break
                    
                    if retry_count >= max_retries:
                        print(f"❌ LLM call error after {max_retries} retries: {e}")
                        return "{}", None
                        
                elif "401" in error_msg or "authentication" in error_msg.lower():
                    print(f"❌ Authentication error. Please check your OPENROUTER_API_KEY")
                    return "{}", None
                    
                elif "429" in error_msg or "rate limit" in error_msg.lower():
                    print(f"⚠️ Rate limit hit. Waiting before retry {retry_count}/{max_retries}...")
                    import time
                    time.sleep(2 ** retry_count)  # Exponential backoff
                    
                else:
                    print(f"❌ LLM call error (retry {retry_count}/{max_retries}): {e}")
                    if retry_count >= max_retries:
                        return "{}", None
        
        return "{}", None
    
    def _call_llm_with_reasoning_continuation(self,
                                             initial_messages: List[Dict[str, Any]],
                                             followup_prompt: str,
                                             temperature: float = 0.3) -> str:
        """
        Call LLM dengan reasoning continuation (untuk gpt-oss)
        
        Args:
            initial_messages: Initial conversation messages
            followup_prompt: Follow-up prompt untuk refine reasoning
            temperature: Sampling temperature
        
        Returns:
            Final response content
        """
        if not self.use_reasoning:
            # Jika tidak pakai reasoning, langsung call biasa
            content, _ = self._call_llm(initial_messages, temperature, preserve_reasoning=False)
            return content
        
        # First call dengan reasoning
        print("  🧠 Step 1: Initial reasoning...")
        first_content, reasoning_details = self._call_llm(initial_messages, temperature, preserve_reasoning=True)
        
        # Prepare messages dengan reasoning_details untuk continuation
        continued_messages = initial_messages.copy()
        assistant_message = {
            "role": "assistant",
            "content": first_content
        }
        
        # Preserve reasoning_details jika ada
        if reasoning_details:
            assistant_message["reasoning_details"] = reasoning_details
        
        continued_messages.append(assistant_message)
        continued_messages.append({
            "role": "user",
            "content": followup_prompt
        })
        
        # Second call - model continues reasoning
        print("  🧠 Step 2: Continuing reasoning...")
        final_content, _ = self._call_llm(continued_messages, temperature, preserve_reasoning=False)
        
        return final_content
    
    def parse_user_input(self, user_query: str) -> CryptoAgentState:
        """
        Step 1: Parse dan ekstrak informasi dari query pengguna
        """
        print("\n" + "="*80)
        print("🔍 STEP 1: Parsing User Input")
        print("="*80)
        
        self.state["user_query"] = user_query
        
        prompt = f"""Analisis query pengguna berikut dan ekstrak informasi penting dalam format JSON:

Query: "{user_query}"

Ekstrak informasi berikut:
1. cryptocurrencies: Array simbol crypto yang disebutkan (BTC, ETH, SOL, BNB, ADA, dll). Jika tidak disebutkan, gunakan ["BTC", "ETH", "SOL"]
2. investment_goal: Tujuan investasi ("short_term", "medium_term", "long_term"). Default: "medium_term"
3. risk_tolerance: Toleransi risiko ("conservative", "moderate", "aggressive"). Default: "moderate"
4. investment_amount: Jumlah investasi dalam USD (number atau null)
5. time_horizon: Horizon waktu investasi dalam bulan (number atau null)
6. preferences: Array preferensi khusus lainnya (e.g., ["diversification", "low_risk", "high_growth"])

Response HARUS dalam format JSON yang valid, tanpa markdown atau backticks.
Contoh:
{{
  "cryptocurrencies": ["BTC", "ETH"],
  "investment_goal": "medium_term",
  "risk_tolerance": "moderate",
  "investment_amount": 10000,
  "time_horizon": 6,
  "preferences": ["diversification", "low_risk"]
}}"""

        messages = [
            {"role": "system", "content": "You are a JSON extraction expert. Always respond with valid JSON only, no markdown formatting."},
            {"role": "user", "content": prompt}
        ]
        
        # Gunakan reasoning continuation jika enabled
        if self.use_reasoning:
            response_content = self._call_llm_with_reasoning_continuation(
                messages,
                "Double-check the extracted information. Make sure all fields are correctly identified and the JSON is valid.",
                temperature=0
            )
        else:
            response_content, _ = self._call_llm(messages, temperature=0, preserve_reasoning=False)
        
        try:
            # Clean response dari markdown jika ada
            clean_content = response_content.replace("```json", "").replace("```", "").strip()
            user_profile = json.loads(clean_content)
            print("✅ User profile berhasil di-extract:")
            print(json.dumps(user_profile, indent=2))
        except Exception as e:
            print(f"⚠️ Error parsing JSON: {e}")
            # Fallback default profile
            user_profile = {
                "cryptocurrencies": ["BTC", "ETH", "SOL"],
                "investment_goal": "medium_term",
                "risk_tolerance": "moderate",
                "investment_amount": None,
                "time_horizon": 6,
                "preferences": ["diversification"]
            }
            print("⚠️ Using default profile:")
            print(json.dumps(user_profile, indent=2))
        
        self.state["user_profile"] = user_profile
        self.state["conversation_history"].append({
            "role": "user",
            "content": user_query
        })
        
        return self.state
    
    def gather_market_data(self) -> CryptoAgentState:
        """
        Step 2: Mengumpulkan data pasar untuk cryptocurrency yang relevan
        """
        print("\n" + "="*80)
        print("📊 STEP 2: Gathering Market Data")
        print("="*80)
        
        cryptos = self.state["user_profile"].get("cryptocurrencies", ["BTC", "ETH"])
        market_data = CryptoTools.fetch_market_data(cryptos)
        
        self.state["market_data"] = market_data
        print(f"✅ Market data gathered for: {', '.join(cryptos)}")
        
        return self.state
    
    def perform_technical_analysis(self) -> CryptoAgentState:
        """
        Step 3: Melakukan analisis teknikal untuk setiap cryptocurrency
        """
        print("\n" + "="*80)
        print("📈 STEP 3: Performing Technical Analysis")
        print("="*80)
        
        cryptos = self.state["user_profile"].get("cryptocurrencies", ["BTC"])
        technical_data = {}
        
        for crypto in cryptos:
            analysis = CryptoTools.perform_technical_analysis(crypto)
            technical_data[crypto] = analysis
            print(f"  ✓ {crypto}: Signal={analysis['signal']}, Strength={analysis['strength']}/10")
        
        self.state["technical_analysis"] = technical_data
        print("✅ Technical analysis completed")
        
        return self.state
    
    def perform_sentiment_analysis(self) -> CryptoAgentState:
        """
        Step 4: Melakukan analisis sentimen untuk setiap cryptocurrency
        """
        print("\n" + "="*80)
        print("🎭 STEP 4: Analyzing Market Sentiment")
        print("="*80)
        
        cryptos = self.state["user_profile"].get("cryptocurrencies", ["BTC"])
        sentiment_data = {}
        
        for crypto in cryptos:
            sentiment = CryptoTools.analyze_sentiment(crypto)
            sentiment_data[crypto] = sentiment
            print(f"  ✓ {crypto}: Sentiment={sentiment['overall_sentiment']}, Score={sentiment['sentiment_score']}")
        
        self.state["sentiment_analysis"] = sentiment_data
        print("✅ Sentiment analysis completed")
        
        return self.state
    
    def assess_investment_risk(self) -> CryptoAgentState:
        """
        Step 5: Menilai risiko investasi
        """
        print("\n" + "="*80)
        print("⚠️ STEP 5: Assessing Investment Risk")
        print("="*80)
        
        risk_data = CryptoTools.assess_risk(
            self.state["user_profile"],
            self.state["market_data"]
        )
        
        self.state["risk_assessment"] = risk_data
        print(f"✅ Risk assessment completed:")
        print(f"  • Risk Level: {risk_data['risk_level']}")
        print(f"  • Volatility: {risk_data['volatility_score']}%")
        print(f"  • Recommended Allocation: {risk_data['recommended_allocation']}%")
        
        return self.state
    
    def generate_recommendations(self) -> CryptoAgentState:
        """
        Step 6: Generate rekomendasi investasi berdasarkan semua analisis
        """
        print("\n" + "="*80)
        print("💡 STEP 6: Generating Investment Recommendations")
        print("="*80)
        
        context_data = {
            "user_profile": self.state["user_profile"],
            "market_data": self.state["market_data"],
            "technical_analysis": self.state["technical_analysis"],
            "sentiment_analysis": self.state["sentiment_analysis"],
            "risk_assessment": self.state["risk_assessment"]
        }
        
        prompt = f"""Anda adalah ahli investasi cryptocurrency profesional dengan pengalaman 10+ tahun. 

Berdasarkan data komprehensif berikut, berikan rekomendasi investasi yang detail dan actionable:

PROFIL PENGGUNA:
{json.dumps(context_data['user_profile'], indent=2)}

DATA PASAR:
{json.dumps(context_data['market_data'], indent=2)}

ANALISIS TEKNIKAL:
{json.dumps(context_data['technical_analysis'], indent=2)}

ANALISIS SENTIMEN:
{json.dumps(context_data['sentiment_analysis'], indent=2)}

PENILAIAN RISIKO:
{json.dumps(context_data['risk_assessment'], indent=2)}

Berikan rekomendasi dalam format JSON yang valid dengan struktur berikut:

{{
  "recommendations": [
    {{
      "symbol": "BTC",
      "crypto_name": "Bitcoin",
      "action": "BUY" | "HOLD" | "SELL",
      "allocation_percentage": 40,
      "entry_price_range": "44000-45500",
      "target_price": "52000",
      "stop_loss": "42000",
      "timeframe": "3-6 bulan",
      "confidence": 8,
      "reasoning": "Penjelasan detail mengapa rekomendasi ini diberikan. Harus mencakup: analisis teknikal, sentimen pasar, dan fundamental. Minimal 3-4 kalimat.",
      "risk_factors": [
        "Faktor risiko 1 yang spesifik",
        "Faktor risiko 2 yang spesifik"
      ],
      "catalysts": [
        "Catalyst positif 1",
        "Catalyst positif 2"
      ],
      "key_metrics": {{
        "expected_return": "15-20%",
        "risk_reward_ratio": "1:3",
        "volatility": "high"
      }}
    }}
  ],
  "portfolio_summary": {{
    "total_allocation": 100,
    "risk_score": 7.5,
    "diversification_score": 8,
    "expected_annual_return": "20-30%"
  }}
}}

PENTING:
- Total allocation_percentage untuk semua crypto harus = 100%
- Sesuaikan dengan profil risiko user ({context_data['user_profile'].get('risk_tolerance', 'moderate')})
- Berikan reasoning yang data-driven dan spesifik
- Pertimbangkan SEMUA aspek: teknikal, sentimen, fundamental, dan risiko
- Confidence score harus realistis berdasarkan data
- Response harus JSON valid tanpa markdown atau backticks"""

        messages = [
            {
                "role": "system",
                "content": "You are a professional cryptocurrency investment advisor with 10+ years experience. Provide detailed, data-driven recommendations in valid JSON format only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Gunakan reasoning continuation jika enabled
        if self.use_reasoning:
            response_content = self._call_llm_with_reasoning_continuation(
                messages,
                "Review your recommendations carefully. Ensure the allocation percentages add up to 100%, the confidence scores are realistic, and all reasoning is data-driven and specific.",
                temperature=0.3
            )
        else:
            response_content, _ = self._call_llm(messages, temperature=0.3, preserve_reasoning=False)
        
        try:
            clean_content = response_content.replace("```json", "").replace("```", "").strip()
            recommendations_data = json.loads(clean_content)
            self.state["recommendations"] = recommendations_data.get("recommendations", [])
            
            print(f"✅ Generated {len(self.state['recommendations'])} recommendations:")
            for rec in self.state["recommendations"]:
                print(f"  • {rec['symbol']}: {rec['action']} - Allocation: {rec['allocation_percentage']}% - Confidence: {rec['confidence']}/10")
        except Exception as e:
            print(f"❌ Error parsing recommendations: {e}")
            print(f"Raw response: {response_content[:500]}...")
            self.state["recommendations"] = []
        
        return self.state
    
    def create_final_report(self) -> CryptoAgentState:
        """
        Step 7: Membuat laporan akhir yang profesional dan mudah dibaca
        """
        print("\n" + "="*80)
        print("📝 STEP 7: Creating Final Report")
        print("="*80)
        
        prompt = f"""Buat laporan rekomendasi investasi cryptocurrency yang SANGAT profesional, komprehensif, dan mudah dipahami.

QUERY PENGGUNA: {self.state['user_query']}

REKOMENDASI LENGKAP:
{json.dumps(self.state['recommendations'], indent=2)}

PENILAIAN RISIKO:
{json.dumps(self.state['risk_assessment'], indent=2)}

PROFIL USER:
{json.dumps(self.state['user_profile'], indent=2)}

Format laporan dengan struktur berikut (gunakan Markdown formatting yang baik):

# 📊 LAPORAN REKOMENDASI INVESTASI CRYPTOCURRENCY

**Tanggal**: {datetime.now().strftime('%d %B %Y')}
**Profil Risiko**: {self.state['user_profile'].get('risk_tolerance', 'Moderate').title()}
**Horizon Investasi**: {self.state['user_profile'].get('investment_goal', 'Medium Term').replace('_', ' ').title()}

---

## 🎯 Ringkasan Eksekutif

[Tulis 2-3 paragraf yang mencakup:
- Overview singkat kondisi pasar saat ini
- Highlight rekomendasi utama dengan reasoning singkat
- Expected return dan risk level keseluruhan portofolio]

---

## 💰 Rekomendasi Investasi Detail

[Untuk setiap cryptocurrency, buat section detail dengan analisis komprehensif]

---

## 📊 Portfolio Overview

[Tampilkan alokasi, metrics, dan visualisasi portofolio]

---

## ⚠️ Manajemen Risiko

[Detail strategi risk management dan considerations]

---

## 📈 Strategi Diversifikasi

[Penjelasan diversifikasi dan asset allocation]

---

## 🎓 Panduan Praktis

[Tips DCA, rebalancing, taking profits, dan security]

---

## ⏰ Action Plan (30 Hari Pertama)

[Detailed week-by-week action items]

---

## 📅 Review & Monitoring Schedule

[Daily, weekly, monthly, quarterly review checklist]

---

## ⚖️ LEGAL DISCLAIMER

[Comprehensive disclaimer tentang risiko dan bukan financial advice]

Buat laporan yang informatif, actionable, professional, dan user-friendly."""

        messages = [
            {
                "role": "system",
                "content": "You are a professional financial report writer specializing in cryptocurrency investments. Create comprehensive, well-structured reports."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Gunakan reasoning untuk report generation jika enabled
        if self.use_reasoning:
            response_content = self._call_llm_with_reasoning_continuation(
                messages,
                "Review the report for completeness, accuracy, and clarity. Ensure all sections are well-developed and the report is professional and actionable.",
                temperature=0.5
            )
        else:
            response_content, _ = self._call_llm(messages, temperature=0.5, preserve_reasoning=False)
        
        self.state["final_report"] = response_content
        print("✅ Final report created")
        
        return self.state
    
    def execute(self, user_query: str) -> Dict[str, Any]:
        """
        Execute entire workflow dengan semua steps
        
        Args:
            user_query: User's investment query
        
        Returns:
            Dictionary dengan results dan final report
        """
        print("\n" + "🚀 CRYPTO INVESTMENT RECOMMENDATION WORKFLOW 🚀".center(80, "="))
        print(f"Model: {self.model}")
        print(f"Reasoning Enabled: {self.use_reasoning}")
        print("="*80)
        
        try:
            # Execute all workflow steps
            self.parse_user_input(user_query)
            self.gather_market_data()
            self.perform_technical_analysis()
            self.perform_sentiment_analysis()
            self.assess_investment_risk()
            self.generate_recommendations()
            self.create_final_report()
            
            print("\n" + "="*80)
            print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
            print("="*80)
            
            return {
                "success": True,
                "state": self.state,
                "report": self.state["final_report"],
                "recommendations": self.state["recommendations"],
                "user_profile": self.state["user_profile"],
                "risk_assessment": self.state["risk_assessment"]
            }
            
        except Exception as e:
            print("\n" + "="*80)
            print(f"❌ WORKFLOW ERROR: {e}")
            print("="*80)
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "state": self.state
            }


# ===== USAGE EXAMPLES =====
def example_basic_workflow():
    """Example: Basic workflow tanpa reasoning"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Workflow (GPT-4o-mini)")
    print("="*80)
    
    workflow = CryptoInvestmentWorkflow(use_reasoning=False)
    
    user_query = """
    Saya ingin investasi di Bitcoin, Ethereum, dan Solana untuk jangka menengah. 
    Budget saya sekitar $10,000 dan saya punya toleransi risiko moderate. 
    Saya tertarik dengan diversifikasi dan ingin fokus pada crypto dengan fundamental kuat. 
    Apa rekomendasi investasi terbaik untuk saya?
    """
    
    result = workflow.execute(user_query)
    
    if result["success"]:
        print("\n" + "="*80)
        print("📄 FINAL REPORT")
        print("="*80)
        print(result["report"])
        
        print("\n" + "="*80)
        print("📋 RECOMMENDATIONS SUMMARY (JSON)")
        print("="*80)
        print(json.dumps(result["recommendations"], indent=2))
    
    return result


def example_reasoning_workflow():
    """Example: Advanced workflow dengan reasoning (GPT-OSS)"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Advanced Workflow with Reasoning (GPT-OSS-120B)")
    print("="*80)
    
    # IMPORTANT: Ganti model ke gpt-oss untuk gunakan reasoning
    workflow = CryptoInvestmentWorkflow(use_reasoning=True)
    
    user_query = """
    Saya seorang investor aggressive dengan portfolio $50,000. 
    Saya tertarik di Bitcoin dan beberapa altcoin dengan high growth potential. 
    Saya okay dengan volatilitas tinggi dan bisa hold untuk 1-2 tahun. 
    Tolong berikan rekomendasi yang detail dengan analisis mendalam.
    """
    
    result = workflow.execute(user_query)
    
    if result["success"]:
        print("\n" + "="*80)
        print("📄 FINAL REPORT (WITH REASONING)")
        print("="*80)
        print(result["report"])
        
        print("\n" + "="*80)
        print("📋 RECOMMENDATIONS SUMMARY (JSON)")
        print("="*80)
        print(json.dumps(result["recommendations"], indent=2))
    
    return result


def example_conservative_investor():
    """Example: Conservative investor"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Conservative Investor Profile")
    print("="*80)
    
    workflow = CryptoInvestmentWorkflow(use_reasoning=False)
    
    user_query = """
    Saya investor pemula dengan risk tolerance conservative. 
    Budget saya $5,000 dan ini adalah first time saya invest di crypto. 
    Saya ingin portfolio yang aman dengan fokus di large-cap cryptocurrencies. 
    Time horizon saya 6-12 bulan untuk mulai belajar.
    """
    
    result = workflow.execute(user_query)
    
    if result["success"]:
        print("\n" + "="*80)
        print("📋 RECOMMENDATIONS FOR CONSERVATIVE INVESTOR")
        print("="*80)
        for rec in result["recommendations"]:
            print(f"\n{rec['symbol']} - {rec['crypto_name']}")
            print(f"  Action: {rec['action']}")
            print(f"  Allocation: {rec['allocation_percentage']}%")
            print(f"  Confidence: {rec['confidence']}/10")
            print(f"  Reasoning: {rec['reasoning'][:150]}...")
    
    return result


# ===== INTERACTIVE FUNCTIONS FOR JUPYTER =====
def run_workflow(query: str, use_reasoning: bool = False, verbose: bool = True):
    """
    Function untuk menjalankan workflow dari Jupyter Notebook
    
    Args:
        query: User investment query
        use_reasoning: True untuk gunakan GPT-OSS dengan reasoning
        verbose: Print detailed output
    
    Returns:
        Dictionary dengan results
    """
    workflow = CryptoInvestmentWorkflow(use_reasoning=use_reasoning)
    result = workflow.execute(query)
    
    if verbose and result["success"]:
        print("\n" + "="*80)
        print("📄 FINAL REPORT")
        print("="*80)
        print(result["report"])
        
        print("\n" + "="*80)
        print("📋 RECOMMENDATIONS SUMMARY")
        print("="*80)
        for rec in result["recommendations"]:
            print(f"\n🪙 {rec.get('symbol', 'N/A')} - {rec.get('crypto_name', 'N/A')}")
            print(f"   Action: {rec.get('action', 'N/A')}")
            print(f"   Allocation: {rec.get('allocation_percentage', 0)}%")
            print(f"   Confidence: {rec.get('confidence', 0)}/10")
            print(f"   Target: ${rec.get('target_price', 'N/A')}")
    
    return result


def quick_recommendation(budget: float, risk_level: str = "moderate", 
                        cryptos: List[str] = None, use_reasoning: bool = False):
    """
    Quick function untuk generate rekomendasi
    
    Args:
        budget: Investment budget in USD
        risk_level: "conservative", "moderate", atau "aggressive"
        cryptos: List crypto symbols (default: ["BTC", "ETH", "SOL"])
        use_reasoning: Use GPT-OSS reasoning
    
    Returns:
        Dictionary dengan recommendations
    """
    if cryptos is None:
        cryptos = ["BTC", "ETH", "SOL"]
    
    crypto_list = ", ".join(cryptos)
    
    query = f"""
    Saya ingin investasi di {crypto_list} dengan budget ${budget:,.0f}.
    Risk tolerance saya adalah {risk_level}.
    Tolong berikan rekomendasi investasi yang sesuai dengan profil saya.
    """
    
    return run_workflow(query, use_reasoning=use_reasoning)


# ===== MAIN EXECUTION =====
def main():
    """Main function untuk command line execution"""
    import sys
    
    print("\n" + "🎯 CRYPTOCURRENCY INVESTMENT RECOMMENDATION SYSTEM 🎯".center(80, "="))
    print("Powered by OpenRouter API & LangGraph Workflow")
    print("="*80)
    
    # Filter out Jupyter kernel arguments
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--f=') and not arg.startswith('-f=')]
    
    # Pilih example mana yang mau dijalankan
    if len(args) > 0:
        example_type = args[0]
        
        if example_type == "basic":
            result = example_basic_workflow()
        elif example_type == "reasoning":
            result = example_reasoning_workflow()
        elif example_type == "conservative":
            result = example_conservative_investor()
        else:
            print(f"Unknown example type: {example_type}")
            print("Available types: basic, reasoning, conservative")
    else:
        # Default: run basic workflow
        print("\n💡 Tip: Jalankan dengan argument untuk example lain:")
        print("  python script.py basic       - Basic workflow (GPT-4o-mini)")
        print("  python script.py reasoning   - Advanced with reasoning (GPT-OSS)")
        print("  python script.py conservative - Conservative investor example")
        print("\n💡 Atau gunakan di Jupyter dengan:")
        print("  result = run_workflow('your query here', use_reasoning=False)")
        print("  result = quick_recommendation(budget=10000, risk_level='moderate')")
        print("\n" + "="*80)
        
        result = example_basic_workflow()
    
    print("\n" + "="*80)
    print("🎉 EXECUTION COMPLETED!")
    print("="*80)
    
    return result


if __name__ == "__main__":
    main()