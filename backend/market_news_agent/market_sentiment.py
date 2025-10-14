import os
import requests
import json
import re
from dotenv import load_dotenv
from typing import Any, Dict


load_dotenv()


def get_iam_token(api_key: str) -> str:
    """Exchange an IBM Cloud API key for an IAM access token."""
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"apikey": api_key, "grant_type": "urn:ibm:params:oauth:grant-type:apikey"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("access_token", "")


def call_watsonx_deployment(deployment_url: str, api_token: str, prompt: str) -> Dict[str, Any]:
    """Call a watsonx deployment (non-streaming) and return the parsed JSON-like output.

    The model is expected to return JSON-like text using [[ and ]] as braces (legacy behavior
    in this codebase). We try to clean and parse it into a Python object.
    """
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_token}
    payload = {"messages": [{"role": "user", "content": prompt}]}

    resp = requests.post(deployment_url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()

    result = None
    model_output = None
    try:
        result = resp.json()
    except ValueError:
        # If response is plain text (for example an SSE/streamed response), try to
        # extract model text fragments from the stream. IBM watsonx streaming often
        # returns server-sent events with lines like:
        # id: 1\nevent: message\ndata: {"choices": [{"index": 0, "delta": {"content": "..."}}]}
        raw = resp.text

        fragments: list[str] = []

        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            payload_text = line[5:].strip()
            try:
                obj = json.loads(payload_text)
            except Exception:
                # Not JSON inside data: line, skip
                continue

            # If the payload contains incremental choices/deltas, collect 'content'
            choices = obj.get("choices") if isinstance(obj, dict) else None
            if isinstance(choices, list):
                for choice in choices:
                    delta = choice.get("delta") or {}
                    if isinstance(delta, dict):
                        content = delta.get("content")
                        if isinstance(content, str):
                            fragments.append(content)

        # Join fragments into a single model output if any were found
        if fragments:
            model_output = "".join(fragments)
        else:
            # Fallback: return full raw text as a helpful error
            raise RuntimeError(f"Failed to decode JSON response: {raw}")

    # Extract model output text from common response shapes when not streaming
    if model_output is None:
        # Handle 'choices' response shape (common for some LLM APIs)
        if isinstance(result, dict) and "choices" in result and isinstance(result["choices"], list):
            fragments = []
            for choice in result["choices"]:
                # Try common locations for incremental content
                content = None
                if isinstance(choice, dict):
                    msg = choice.get("message") or {}
                    if isinstance(msg, dict):
                        content = msg.get("content")
                    if content is None:
                        delta = choice.get("delta") or {}
                        if isinstance(delta, dict):
                            content = delta.get("content")
                    if content is None:
                        # Older shapes may have 'text' or 'generated_text'
                        content = choice.get("text") or choice.get("generated_text")
                if isinstance(content, str):
                    fragments.append(content)

            if fragments:
                model_output = "".join(fragments)
        # Fallback to other shapes
        if model_output is None:
            if isinstance(result, dict) and "results" in result and len(result["results"]) > 0:
                model_output = result["results"][0].get("generated_text", "")
            else:
                model_output = result.get("generated_text", str(result))

    # Clean model output that uses [[ ... ]] for braces and single quotes
    clean_text = re.sub(r"\[\[", "{", model_output)
    clean_text = re.sub(r"\]\]", "}", clean_text)
    # Some models stream single quotes or escaped sequences; normalize to double quotes
    clean_text = clean_text.replace("'", '"')

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        # Provide helpful debugging info if parsing fails
        raise RuntimeError(f"Failed to parse model output as JSON. Cleaned text:\n{clean_text}")


def get_model_json(prompt: str, api_key: str | None = None, deployment_url: str | None = None) -> Dict[str, Any]:
    """Convenience wrapper: call the watsonx deployment and return a Python dict.

    If `api_key` or `deployment_url` are not provided, the function will read
    `WATSONX_APIKEY` and `WATSONX_DEPLOYMENT_URL` from the environment.

    The model is expected to return text that uses [[ and ]] to indicate JSON
    braces; this function will clean and parse that into a Python object.
    """
    api_key = api_key or os.getenv("WATSONX_APIKEY")
    deployment_url = deployment_url or os.getenv("WATSONX_DEPLOYMENT_URL")

    if not api_key:
        raise ValueError("WATSONX_APIKEY is required (pass api_key or set env var)")

    token = get_iam_token(api_key)
    return call_watsonx_deployment(deployment_url, token, prompt)


def wrap_as_market_sentiment(json_output: Any, default_tickers: str = "UNKNOWN") -> Any:
    """Return a MarketSentiment-shaped JSON object.

    If the model returns a mapping of tickers to reports, convert each entry. If it
    returns a single report with keys like `news_list` and `hotnews_summary`, wrap it
    into one MarketSentiment dict.
    """
    def make_entry(ticker: str, report: Any) -> Dict[str, Any]:
        return {
            "ticker": ticker,
            "watsonx_sentiment": None,
            "news_sentiment_ddg": None,
            "fear_greed_index": None,
            "average_sentiment_score": None,
            "news_report": report,
        }

    # If the model returned a dict where top-level keys look like tickers (or are arbitrary),
    # try to map them to MarketSentiment entries.
    if isinstance(json_output, dict):
        if "news_list" in json_output or "hotnews_summary" in json_output:
            # Single report
            ticker = default_tickers.split(",")[0] if default_tickers else "UNKNOWN"
            return make_entry(ticker, json_output)
        else:
            # Assume mapping ticker -> report
            out = {}
            for k, v in json_output.items():
                out[k] = make_entry(k, v if isinstance(v, dict) else {"hotnews_summary": str(v)})
            return out

    if isinstance(json_output, list):
        # List of reports -> return list of wrapped entries
        return [make_entry("UNKNOWN", item) for item in json_output]

    # Fallback: wrap anything else into a minimal report
    return make_entry("UNKNOWN", {"hotnews_summary": str(json_output)})


def main() -> None:
    # Read required env vars
    API_KEY = os.getenv("WATSONX_APIKEY")
    DEPLOYMENT_URL = os.getenv(
        "WATSONX_DEPLOYMENT_URL",
        "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/51fc3439-3e3d-4e08-8621-7d5fb5f01553/ai_service?version=2021-05-01",
    )
    TICKERS = os.getenv("WATSONX_TICKERS", "AAPL,TSLA,MSFT")

    if not API_KEY:
        raise ValueError("❌ WATSONX_APIKEY not found in environment variables!")

    token = get_iam_token(API_KEY)

    prompt_text = (
        f"You are a financial news summarization assistant. For tickers {TICKERS},"
        " return the output as JSON using [[ ]] instead of {}. Include `news_list` and `hotnews_summary`."
    )

    json_output = call_watsonx_deployment(DEPLOYMENT_URL, token, prompt_text)
    wrapped = wrap_as_market_sentiment(json_output, default_tickers=TICKERS)

    print(json.dumps(wrapped, indent=2))


if __name__ == "__main__":
    main()


def get_yahoo_news_description(ticker: str, max_articles: int = 5) -> Dict[str, Any]:
    """Return a dict matching the frontend `news` shape for a single ticker.

    This will call the deployed watsonx model when WATSONX_APIKEY and
    WATSONX_DEPLOYMENT_URL are set. Otherwise, it returns a minimal
    placeholder structure.
    """
    api_key = os.getenv("WATSONX_APIKEY")
    deployment_url = os.getenv("WATSONX_DEPLOYMENT_URL")

    prompt = (
        f"You are a financial news summarization assistant. Return a JSON object with keys `news_list` and `hotnews_summary` for ticker {ticker}. Include up to {max_articles} recent articles in news_list. Use [[ ]] for braces."
    )

    if api_key and deployment_url:
        token = get_iam_token(api_key)
        try:
            json_output = call_watsonx_deployment(deployment_url, token, prompt)
            # If the model returned a mapping of tickers, extract this ticker
            if isinstance(json_output, dict) and ticker in json_output:
                report = json_output[ticker]
            else:
                report = json_output

            # Ensure the report has expected keys
            if not isinstance(report, dict):
                report = {"hotnews_summary": str(report), "news_list": []}

            return report
        except Exception:
            # On failure, fall back to minimal structure
            return {"news_list": [], "hotnews_summary": f"No news available for {ticker}"}

    # Fallback when no deployment configured
    return {"news_list": [], "hotnews_summary": f"No news service configured for {ticker}"}
