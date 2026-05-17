import json
from unittest.mock import patch
from backend.app.chat.intent import classify_intent, ChatDirection


def _mock_llm_response(phase, next_question, direction=None, ready=False):
    """Build a JSON response the classifier LLM would return."""
    return json.dumps({
        "phase": phase,
        "next_question": next_question,
        "direction": direction or {},
        "ready_to_analyze": ready,
    })


def test_classify_intent_discovery():
    with patch("backend.app.chat.intent._call_classifier_llm") as mock_llm:
        mock_llm.return_value = _mock_llm_response(
            "discovery", "Are you researching specific stocks?"
        )
        result = classify_intent(
            message="Hi, I want to invest in tech stocks",
            history=[],
            current_direction=None,
        )
        assert result["phase"] == "discovery"
        assert isinstance(result["next_question"], str)
        assert len(result["next_question"]) > 5
        assert result["ready_to_analyze"] is False


def test_classify_intent_proposal():
    with patch("backend.app.chat.intent._call_classifier_llm") as mock_llm:
        mock_llm.return_value = _mock_llm_response(
            "proposal", "Here's what I'm hearing... Ready to run this?",
            direction={"goal": "comparison", "tickers": ["AAPL", "MSFT"],
                       "criteria": ["fundamentals"], "report_type": "comparison"},
        )
        direction = {
            "goal": "comparison",
            "tickers": ["AAPL", "MSFT"],
            "criteria": ["fundamentals"],
            "report_type": "comparison",
        }
        result = classify_intent(
            message="Long-term growth, moderate risk",
            history=[{"role": "user", "content": "compare AAPL and MSFT"}],
            current_direction=direction,
        )
        assert result["phase"] in ("proposal", "execute")


def test_classify_intent_execute():
    with patch("backend.app.chat.intent._call_classifier_llm") as mock_llm:
        mock_llm.return_value = _mock_llm_response(
            "execute", "",
            direction={"goal": "deep_dive", "tickers": ["AAPL"],
                       "criteria": ["fundamentals"], "report_type": "full_report"},
            ready=True,
        )
        direction = {
            "goal": "deep_dive",
            "tickers": ["AAPL"],
            "criteria": ["fundamentals"],
            "report_type": "full_report",
        }
        result = classify_intent(
            message="Yes, go ahead and run the analysis",
            history=[
                {"role": "user", "content": "analyze Apple"},
                {"role": "assistant",
                 "content": "I'll run a full fundamentals report on AAPL. Ready to run this?"},
            ],
            current_direction=direction,
        )
        assert result["phase"] == "execute"
        assert result["ready_to_analyze"] is True


def test_direction_merges_tickers():
    with patch("backend.app.chat.intent._call_classifier_llm") as mock_llm:
        mock_llm.return_value = _mock_llm_response(
            "discovery", "Any other tickers?",
            direction={"tickers": ["MSFT"]},
        )
        direction = {
            "goal": "deep_dive",
            "tickers": ["AAPL"],
            "criteria": [],
            "report_type": "snapshot",
        }
        result = classify_intent(
            message="Also add MSFT to the list",
            history=[],
            current_direction=direction,
        )
        assert "MSFT" in result["direction"]["tickers"]
        assert "AAPL" in result["direction"]["tickers"]


def test_classify_intent_invalid_json_fallback():
    """If LLM returns garbage, fallback to discovery."""
    with patch("backend.app.chat.intent._call_classifier_llm") as mock_llm:
        mock_llm.return_value = "not valid json {{{"
        result = classify_intent(
            message="Hello",
            history=[],
            current_direction=None,
        )
        assert result["phase"] == "discovery"


def test_classify_intent_no_api_key_fallback():
    """If the classifier raises an error (e.g., RuntimeError), fallback to discovery."""
    with patch("backend.app.chat.intent._build_classifier_llm") as mock_build:
        mock_build.side_effect = RuntimeError("No API key")
        result = classify_intent(
            message="Help me analyze stocks",
            history=[],
            current_direction=None,
        )
        assert result["phase"] == "discovery"
        assert result["ready_to_analyze"] is False
