# 🤖 WatsonX Portfolio Advisor

*AI-Powered Investment Portfolio Management System*

An enterprise-grade portfolio advisor that combines IBM WatsonX AI with quantitative finance to deliver institutional-quality investment recommendations for individual investors.

---

## 🎯 Purpose & Vision

### *The Problem*
Traditional investment advice is either:
- *Generic robo-advisors* that use simple questionnaires and basic algorithms
- *Expensive human advisors* that are inaccessible to most individual investors
- *AI chatbots* that provide opinions without mathematical backing

### *Our Solution*
WatsonX Portfolio Advisor bridges this gap by providing:
- *AI-Augmented Quantitative Finance*: Real mathematical optimization explained by AI
- *Enterprise-Grade AI*: IBM WatsonX Granite models built for financial services
- *Institutional-Quality Analysis*: Bank-level risk assessment and portfolio construction
- *Real-Time Intelligence*: Live market data integration with streaming AI analysis

### *Key Differentiators*
1. *Hybrid Intelligence*: AI explains mathematical optimization, doesn't replace it
2. *Enterprise Architecture*: Built on IBM WatsonX for regulatory compliance
3. *Comprehensive Analysis*: 15+ financial ratios, not just risk tolerance surveys
4. *Professional Reports*: Bank-quality investment reports with quantitative backing

---
## 🔧 Frontend Code Architecture

The frontend is a Next.js 14 app (App Router) focused on a clean separation between pages, reusable UI components, and a small data-access layer.

### Structure
- `frontend/app/`: Route tree and pages
  - `assessment/`: multi-step onboarding flow (goals → horizon → risk → income → liabilities → liquidity → values)
  - `dashboard/`, `market-data/`, `risk-analytics/`: main feature pages
  - `layout.tsx`: global HTML shell, fonts, Suspense and analytics
- `frontend/components/`: shared components
  - `discovery-flow.tsx`: orchestrates the assessment steps and submission
  - `ui/`: Shadcn-based primitives (button, card, input, select, etc.)
- `frontend/lib/`: app utilities
  - `api.ts`: typed API client and helpers
  - `hooks.ts`: reusable hooks for API calls and local persistence
- `frontend/styles/globals.css`: Tailwind styles

### Data Layer
- **Typed API client** in `lib/api.ts` centralizes backend calls and error handling.
- **Hook wrapper** `useAPICall` in `lib/hooks.ts` standardizes loading/error/data state.
- **Local persistence** via `useAssessment` in `lib/hooks.ts` for `localStorage` hydration, saving `assessment` and `userId` between sessions.

### Assessment Flow
- `components/discovery-flow.tsx` controls step navigation, aggregates profile state, and submits to backend (`/api/process-assessment`).
- Individual steps live in `app/assessment/*-step.tsx` and receive `profile` and `updateProfile` props.

### Pages
- `app/dashboard/page.tsx`: summary KPIs, allocation, performance.
- `app/market-data/page.tsx`: market overview via `components/market-data-widget.tsx`.
- `app/risk-analytics/page.tsx`: portfolio risk metrics and scenarios.

### UI System
- Shadcn/ui primitives in `components/ui/*` with Tailwind for styling.
- `components/step-indicator.tsx` for multi-step progress.
- `components/theme-provider.tsx` for theming if needed (dark/light).

### Cross-Cutting Concerns
- **Error handling**: central via `APIError`, `handleAPIError` and `useAPICall`.
- **Loading states**: managed in hooks; pages/components render skeletons/spinners as needed.
- **Routing**: Next.js App Router; navigation via `next/navigation`.
- **Analytics**: `@vercel/analytics` wired in `app/layout.tsx`.
- **Real-time**: backend exposes streaming endpoints; the frontend can consume via `EventSource` when needed.

---

## 🔧 Backend Code Architecture

### *Core Workflow (LangGraph Orchestration)*

The system follows a sophisticated AI workflow orchestrated by LangGraph:

### *1. Risk Analytics Agent* (backend/risk_analytics_agent/)
*Purpose*: Comprehensive financial risk assessment using AI + quantitative analysis

*Key Features*:
- *15+ Financial Ratios*: Debt-to-asset, savings rate, liquidity ratio, etc.
- *Risk Capacity vs Tolerance*: Distinguishes objective ability from psychological comfort
- *WatsonX Integration*: Uses granite-3-8b-instruct for detailed analysis
- *Quantitative Scoring*: Generates risk scores (1-100) and volatility targets

```python
class RiskAnalyticsAgent(BaseAgent):
    def __init__(self, llm: ChatWatsonx):
        # Uses IBM WatsonX Granite model for risk analysis
        self.llm = llm
        self.ratio_engine = FinancialRatioEngine()
```

*Outputs*: Risk blueprint with capacity, tolerance, requirement assessments

### *2. Selection Agent* (backend/selection/)
*Purpose*: Asset class and security selection based on risk profile

*Key Features*:
- *Risk-Based Selection*: Uses risk blueprint to determine appropriate asset classes
- *Regional/Sector Filtering*: Considers user preferences and ESG criteria
- *Quantitative Screening*: Filters securities based on financial metrics
- *AI Enhancement*: Qualitative analysis via WatsonX

```python
def run_selection_agent(regions, sectors, risk_blueprint):
    # Selects appropriate asset classes and securities
    # Based on risk profile and user preferences
```

*Outputs*: Security selections by asset class with rationale

### *3. Portfolio Construction Agent* (backend/portfolio_construction_and_market_sentiment/)
*Purpose*: Mathematical portfolio optimization using Modern Portfolio Theory

*Key Features*:
- *PyPortfolioOpt Integration*: Efficient frontier optimization
- *SciPy Optimization*: Sharpe ratio maximization with constraints
- *Risk Management*: Volatility targeting based on risk assessment
- *Market Sentiment*: Real-time news analysis for market conditions

```python
# Mathematical optimization - not just AI opinions
optimal_weights = EfficientFrontier(mu, cov_matrix).max_sharpe()
sharpe_ratio = (expected_return - risk_free_rate) / portfolio_volatility
```

*Outputs*: Optimized portfolio allocation with performance metrics

### *4. Communication Agent* (backend/communication_agent.py)
*Purpose*: Generate professional investment reports using AI

*Key Features*:
- *Bank-Quality Reports*: Professional investment analysis and recommendations
- *WatsonX LLM*: Uses granite-3-8b-instruct for report generation
- *Comprehensive Explanations*: Detailed rationale for all decisions
- *Q&A System*: Interactive explanations of portfolio choices

python
class CommunicationAgent:
    def __init__(self):
        self.llm = WatsonxLLM(model_id="ibm/granite-3-8b-instruct")
        # Generates professional investment reports


*Outputs*: Professional investment report with explanations

### *5. Main Agent Orchestrator* (backend/main_agent.py)
*Purpose*: LangGraph workflow coordination and state management

*Key Features*:
- *State Management*: Passes data between agents seamlessly
- *Error Handling*: Robust error recovery and fallback mechanisms
- *Streaming Support*: Real-time progress updates to frontend
- *Configuration Management*: Centralized agent configuration

```python
class MainAgent:
    def create_workflow(self) -> CompiledStateGraph:
        workflow = StateGraph(MainAgentState)
        # Orchestrates the complete AI workflow
```

### *Supporting Infrastructure*

#### *WatsonX Integration* (backend/watsonx_utils.py)
- *Enterprise AI*: IBM WatsonX Granite models for financial services
- *Multiple Configurations*: Task-optimized AI parameters
- *Credential Management*: Secure API key handling

#### *Data Processing* (backend/services/)
- *Financial Ratios Engine*: Comprehensive quantitative analysis
- *Market Data Integration*: Yahoo Finance, FRED API integration
- *Data Sharing*: Inter-agent communication system

#### *API Layer* (backend/main.py)
- *FastAPI Server*: High-performance async API
- *Streaming Endpoints*: Real-time workflow progress
- *Validation*: Comprehensive input validation

---

## 🚀 Getting Started

### *Prerequisites*
- Python 3.9+
- Node.js 18+
- IBM WatsonX API credentials

### *Environment Setup*

1. *Clone Repository*
```bash
git clone <repository-url>
cd watsonx-portfolio-advisor
```

2. *Backend Setup*
```bash
cd backend
conda env create -f wx-langgraph-env.yml


# Create .env file with WatsonX credentials
cp .env.example .env
# Edit .env with your IBM WatsonX credentials
```

3. *Frontend Setup*
```bash
cd frontend
npm install
```

### *Configuration*

Create backend/.env with your IBM WatsonX credentials:
```env
WATSONX_APIKEY=your_api_key_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
PROJ_ID=your_project_id_here
```

### *Running the Application*

1. *Start Backend*
```bash
cd backend
python main.py
# Server runs on http://localhost:8000
```

2. *Start Frontend*
```bash
cd frontend
pnpm run dev
# Frontend runs on http://localhost:3000
```

---

## 📊 API Documentation

### *Main Endpoints*

#### *Assessment Validation*
```http
POST /api/validate-assessment
Content-Type: application/json

{
  "goals": [...],
  "riskTolerance": "medium",
  "annualIncome": 75000,
  "monthlySavings": 1000
}
```

#### *Generate Portfolio Report (Streaming)*
```http
POST /api/generate-report/stream
Content-Type: application/json

# Returns Server-Sent Events with real-time progress
```

#### *Portfolio Q&A*
```http
POST /api/ask-question
Content-Type: application/json

{
  "question": "Why was this allocation chosen for my portfolio?"
}
```

---

## 🔒 Security & Compliance

### *Enterprise-Grade Security*
- *IBM WatsonX*: Built for regulated financial services
- *Credential Management*: Secure environment variable handling
- *API Security*: CORS protection and input validation

### *Regulatory Considerations*
- *Financial Services Ready*: IBM WatsonX compliance features
- *Audit Trail*: Comprehensive logging of all decisions
- *Explainable AI*: Full transparency in recommendation rationale

---

## 🎯 Key Features

### *For Investors*
- ✅ *Comprehensive Risk Assessment*: 15+ financial ratios analysis
- ✅ *Mathematical Optimization*: Modern Portfolio Theory implementation
- ✅ *AI-Powered Explanations*: Understand why decisions were made
- ✅ *Real-Time Updates*: Live market data integration
- ✅ *Professional Reports*: Bank-quality investment analysis

### *For Developers*
- ✅ *Enterprise AI Stack*: IBM WatsonX integration
- ✅ *LangGraph Orchestration*: Sophisticated workflow management
- ✅ *Modular Architecture*: Easy to extend and maintain
- ✅ *API-First Design*: RESTful with streaming support

---

## 🛠 Technology Stack

### *Backend*
- *Framework*: FastAPI (Python)
- *AI Platform*: IBM WatsonX (Granite Models)
- *Workflow*: LangGraph for agent orchestration
- *Optimization*: PyPortfolioOpt, SciPy
- *Data*: Yahoo Finance, FRED API

### *Frontend*
- *Framework*: Next.js 14 (React)
- *UI Components*: Tailwind CSS, Shadcn/ui
- *Charts*: Recharts
- *Real-time*: Server-Sent Events

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- *IBM WatsonX*: Enterprise AI platform
- *LangGraph*: AI workflow orchestration
- *PyPortfolioOpt*: Modern Portfolio Theory implementation
- *FastAPI*: High-performance web framework
- *Next.js*: React framework for production

---

*Built with ❤ using IBM WatsonX AI and Modern Portfolio Theory*


## Git commit procedure
Git and GitHub are two different things. You have to install Git first.

Use source control tab for easier management but the logic is same as using command line, self-learn how to use source control tab

Only commit working code and do not directly commit to main branch

Command line reference for each commit:
```Bash
git pull #always pull before commit
git status #check that you are on the correct branch
git checkout branch #to change branch
git status #double check the branch, super large files should not be committed, add the corresponding file type to .gitignore
git add . #add all remaining files to the commit
git status #always double check
git commit -m "message" # write meaningful commit message
git status #always double check
git push #this is the action to upload to the "drive"
```

Final reminder: GitHub can be disastrous. If any error occurs find github copilot, it is very good at command line actions. If github copilot want to perform dangerous actions such as revert commit, ask in group first we might face similar things before TT
