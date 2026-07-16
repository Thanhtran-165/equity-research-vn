"""
model_backends.py — Adapter architecture for model invocation (agent-eval §3 of owner directive).

BRANCH B (transport hardening): adds failure classification + bounded transport retry to ZAIBackend.

Base interface:
    class ModelBackend:
        def is_available(self) -> bool
        def invoke(self, prompt: str, context: dict) -> dict
        def metadata(self) -> dict

Backends:
    ZAIBackend         — GLM-native via api.z.ai/api/anthropic (kind:anthropic), key from ~/.zcode/cli/config.json
    OpenAIBackend      — OpenAI API (env OPENAI_API_KEY)
    OllamaBackend      — local Ollama runner (http://localhost:11434)
    ZCodeNativeBackend — placeholder; no public subprocess/CLI invocation interface found

HONESTY: no backend ever fabricates an inference. is_available()==False → invoke returns NO_MODEL_BOUND.
No API key is ever written to source; ZAIBackend reads it from the ZCode config at runtime.

BRANCH B — FAILURE CLASSIFICATION:
    classify_exception(e) → one of:
        API_READ_TIMEOUT     (httpx.ReadTimeout | anthropic.APITimeoutError)
        API_CONNECT_TIMEOUT  (httpx.ConnectTimeout)
        TRANSPORT_RESET      (httpx.RemoteProtocolError | ConnectionResetError | httpx.ConnectError)
        RATE_LIMIT           (anthropic.RateLimitError)
        MODEL_RESPONSE_ERROR (other anthropic.APIError subtypes)
        UNKNOWN              (everything else)

TRANSPORT RETRY:
    max 2 retries (3 total attempts), exponential backoff.
    Retried ONLY on transport classes {API_READ_TIMEOUT, API_CONNECT_TIMEOUT, TRANSPORT_RESET, RATE_LIMIT}.
    Never retried on MODEL_RESPONSE_ERROR (the model responded — badly — retrying is content-recovery,
    which is owned by agent_runner, not here).
"""
import os, json, time

CONFIG_PATH = os.path.expanduser("~/.zcode/cli/config.json")

# ---------------------------------------------------------------------------
# BRANCH B: failure classification + error sanitization
# ---------------------------------------------------------------------------

# Classes that are eligible for bounded transport retry (transient transport/rate-limit only).
TRANSPORT_RETRYABLE_CLASSES = frozenset({
    "API_READ_TIMEOUT",
    "API_CONNECT_TIMEOUT",
    "TRANSPORT_RESET",
    "RATE_LIMIT",
})

# All distinct failure classes (for classification + tests).
ALL_FAILURE_CLASSES = frozenset({
    "API_READ_TIMEOUT",
    "API_CONNECT_TIMEOUT",
    "TRANSPORT_RESET",
    "RATE_LIMIT",
    "MODEL_RESPONSE_ERROR",
    "UNKNOWN",
})


def _iter_cause_chain(exc):
    """Yield exc and every exception in its __cause__ / __context__ chain (deduped)."""
    seen = set()
    cur = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        yield cur
        cur = getattr(cur, "__cause__", None) or getattr(cur, "__context__", None)


def classify_exception(exc) -> str:
    """Map an exception to a stable failure class string.

    Checks the full cause chain so that an anthropic.APIError wrapping an underlying
    httpx.ReadTimeout (the normal SDK behaviour) is still classified by its root cause.
    Ordering: most-specific transport roots first, then anthropic surface types,
    then generic anthropic APIError → MODEL_RESPONSE_ERROR, then UNKNOWN.
    """
    if exc is None:
        return "UNKNOWN"

    try:
        import anthropic
    except Exception:
        anthropic = None
    try:
        import httpx
    except Exception:
        httpx = None

    chain = list(_iter_cause_chain(exc))

    # 1) Root transport causes (walk chain so wrapped httpx errors classify by root).
    for e in chain:
        if httpx is not None and isinstance(e, httpx.ReadTimeout):
            return "API_READ_TIMEOUT"
    for e in chain:
        if httpx is not None and isinstance(e, httpx.ConnectTimeout):
            return "API_CONNECT_TIMEOUT"
    for e in chain:
        if httpx is not None and isinstance(e, httpx.RemoteProtocolError):
            return "TRANSPORT_RESET"
        if isinstance(e, ConnectionResetError):
            return "TRANSPORT_RESET"
        if httpx is not None and isinstance(e, httpx.ConnectError):
            return "TRANSPORT_RESET"
    # 2) anthropic surface types.
    if anthropic is not None:
        for e in chain:
            if isinstance(e, anthropic.APITimeoutError):
                return "API_READ_TIMEOUT"
        for e in chain:
            if isinstance(e, anthropic.RateLimitError):
                return "RATE_LIMIT"
        # Any other anthropic APIError (model returned a non-2xx, validation error, etc.).
        for e in chain:
            if isinstance(e, anthropic.APIError):
                return "MODEL_RESPONSE_ERROR"
    # 3) Fallback.
    return "UNKNOWN"


def sanitize_error_string(exc) -> str:
    """Return a safe, key-free error string for logs / run-result.

    Uses type name + class (not the message, which may echo request headers / URL
    containing key material in some SDK versions). Keeps a short root-cause hint
    for diagnosis but never the raw exception str().
    """
    if exc is None:
        return ""
    cls = type(exc).__name__
    fclass = classify_exception(exc)
    return f"{fclass}: {cls}"


# ---------------------------------------------------------------------------
# Base + backends
# ---------------------------------------------------------------------------

class ModelBackend:
    name = "base"
    def is_available(self) -> bool: return False
    def metadata(self) -> dict: return {"backend": self.name, "available": self.is_available()}
    def invoke(self, prompt: str, context: dict) -> dict:
        return {"output": None, "metadata": self.metadata(), "tool_calls": [],
                "error": "NO_MODEL_BOUND", "inference_occurred": False,
                # BRANCH B fields (present on every result for uniform handling).
                "failure_class": None, "transport_retries": 0,
                "transport_recovered": False}


class ZAIBackend(ModelBackend):
    """GLM-native backend — the model actually running the skill in production.

    Interface is kind:anthropic (api.z.ai/api/anthropic). Key sourced from ZCode config.
    BRANCH B: invoke() performs bounded transport retry (max 2) on transient transport
    classes only and reports a stable failure_class. MODEL_RESPONSE_ERROR is never retried
    here (content recovery is the runner's job).
    """
    name = "zai-glm-native"

    # Transport retry policy.
    MAX_TRANSPORT_RETRIES = 2

    def __init__(self, model_id="GLM-5.2", config_path=CONFIG_PATH):
        self.model_id = model_id
        self.config_path = config_path
        self._opts = None

    def _load_opts(self):
        if self._opts is not None: return self._opts
        try:
            c = json.load(open(self.config_path))
            self._opts = c["provider"]["builtin:zai-coding-plan"]["options"]
        except Exception:
            self._opts = {}
        return self._opts

    def is_available(self) -> bool:
        opts = self._load_opts()
        return bool(opts.get("apiKey") and opts.get("baseURL"))

    def metadata(self) -> dict:
        opts = self._load_opts()
        return {"backend": self.name, "model": self.model_id, "available": self.is_available(),
                "base_url": opts.get("baseURL"), "interface": "anthropic",
                "key_source": "ZCode config (not source code)"}

    def _single_inference(self, prompt, ctx_str, attempt):
        """One model call. Raises on any error; returns the success dict on success.

        Kept separate from invoke() so invoke() can wrap it in the retry loop.
        `attempt` is 1-based and recorded in attempt metadata.
        """
        import anthropic
        opts = self._load_opts()
        client = anthropic.Anthropic(api_key=opts["apiKey"], base_url=opts["baseURL"])
        out_parts = []
        stop_reason = None; usage_in = None; usage_out = None; resp_model = None
        with client.messages.stream(
                model=self.model_id, max_tokens=32768, temperature=0.2,
                system=f"You are a subagent for equity-research-vn. Context-isolated. Do ONLY the assigned phase.",
                messages=[{"role": "user", "content": f"CONTEXT:\n{ctx_str}\n\nPHASE PROMPT:\n{prompt}"}]) as stream:
            for text in stream.text_stream:
                out_parts.append(text)
            # IDEMPOTENCY: the text stream completed normally — the artifact is fully received.
            # If the *metadata* fetch (get_final_message) then times out, do NOT raise: we
            # already have the content. Retrying would issue a duplicate model call and risk a
            # divergent artifact. Return degraded-success (stop_reason=None) instead. Only
            # exceptions raised DURING the stream loop (mid-stream cut) propagate to the retry
            # logic — those represent incomplete content and ARE retryable.
            try:
                final = stream.get_final_message()
                stop_reason = final.stop_reason
                usage_in = getattr(final.usage, 'input_tokens', None)
                usage_out = getattr(final.usage, 'output_tokens', None)
                resp_model = final.model
            except Exception:
                stop_reason = None  # content complete, usage/stop_reason unavailable
        out = "".join(out_parts)
        return out, stop_reason, usage_in, usage_out, resp_model

    def invoke(self, prompt: str, context: dict) -> dict:
        if not self.is_available():
            return {"output": None, "metadata": self.metadata(), "tool_calls": [],
                    "error": "NO_MODEL_BOUND", "inference_occurred": False,
                    "failure_class": None, "transport_retries": 0,
                    "transport_recovered": False}
        t0 = time.time()
        ctx_str = json.dumps(context, ensure_ascii=False)[:4000]

        attempts_meta = []
        transport_retries = 0
        transport_recovered = False
        last_exc = None
        last_failure_class = None

        for attempt in range(1, self.MAX_TRANSPORT_RETRIES + 2):  # 1 + MAX_TRANSPORT_RETRIES
            at_t0 = time.time()
            try:
                out, stop_reason, usage_in, usage_out, resp_model = self._single_inference(
                    prompt, ctx_str, attempt)
                # If this success followed one or more transport retries, mark recovery.
                if transport_retries > 0:
                    transport_recovered = True
                attempts_meta.append({
                    "attempt_number": attempt,
                    "outcome": "success",
                    "failure_class": None,
                    "duration_s": round(time.time() - at_t0, 2),
                })
                return {
                    "output": out,
                    "metadata": {
                        **self.metadata(),
                        "latency_s": round(time.time() - t0, 2),
                        "usage": {"in": usage_in, "out": usage_out},
                        "stop_reason": stop_reason, "resp_model": resp_model,
                        "failure_class": None,
                        "transport_retries": transport_retries,
                        "attempts": attempts_meta,
                    },
                    "tool_calls": [],
                    "error": None,
                    "inference_occurred": True,
                    "failure_class": None,
                    "transport_retries": transport_retries,
                    "transport_recovered": transport_recovered,
                }
            except Exception as e:
                fc = classify_exception(e)
                attempts_meta.append({
                    "attempt_number": attempt,
                    "outcome": "failure",
                    "failure_class": fc,
                    "error": sanitize_error_string(e),
                    "duration_s": round(time.time() - at_t0, 2),
                })
                last_exc = e
                last_failure_class = fc
                # Only retry transport-class failures, and only if budget remains.
                if fc not in TRANSPORT_RETRYABLE_CLASSES:
                    break
                if attempt > self.MAX_TRANSPORT_RETRIES:
                    break
                # Transport retry: exponential backoff. sleep is skipped under tests via env override.
                backoff = 0.5 * (2 ** (attempt - 1))  # 0.5s, 1.0s
                env_skip = os.environ.get("BRANCH_B_SKIP_RETRY_SLEEP")
                if env_skip != "1":
                    time.sleep(backoff)
                transport_retries += 1

        # All attempts exhausted (or non-retryable failure). Report honestly.
        return {
            "output": None,
            "metadata": {
                **self.metadata(),
                "latency_s": round(time.time() - t0, 2),
                "failure_class": last_failure_class,
                "transport_retries": transport_retries,
                "transport_recovered": transport_recovered,
                "attempts": attempts_meta,
            },
            "tool_calls": [],
            # SANITIZED: no raw exception str (which may contain URL/headers). failure_class carries the signal.
            "error": sanitize_error_string(last_exc) if last_exc else "INFERENCE_FAILED",
            "inference_occurred": False,
            "failure_class": last_failure_class,
            "transport_retries": transport_retries,
            "transport_recovered": transport_recovered,
        }


class OpenAIBackend(ModelBackend):
    name = "openai"
    def __init__(self, model_id="gpt-4o-mini"): self.model_id = model_id
    def is_available(self) -> bool: return bool(os.environ.get("OPENAI_API_KEY"))
    def metadata(self) -> dict:
        return {"backend": self.name, "model": self.model_id, "available": self.is_available()}
    def invoke(self, prompt: str, context: dict) -> dict:
        if not self.is_available():
            return {"output": None, "metadata": self.metadata(), "tool_calls": [],
                    "error": "NO_MODEL_BOUND", "inference_occurred": False,
                    "failure_class": None, "transport_retries": 0, "transport_recovered": False}
        t0 = time.time()
        try:
            import openai
            client = openai.OpenAI()
            resp = client.chat.completions.create(model=self.model_id, temperature=0.2,
                messages=[{"role":"system","content":"subagent for equity-research-vn"},
                          {"role":"user","content": f"CONTEXT:\n{json.dumps(context,ensure_ascii=False)[:4000]}\n\nPHASE PROMPT:\n{prompt}"}])
            return {"output": resp.choices[0].message.content, "metadata": {**self.metadata(),
                    "latency_s": round(time.time()-t0,2)}, "tool_calls": [],
                    "error": None, "inference_occurred": True,
                    "failure_class": None, "transport_retries": 0, "transport_recovered": False}
        except Exception as e:
            return {"output": None, "metadata": self.metadata(), "tool_calls": [],
                    "error": f"INFERENCE_FAILED: {type(e).__name__}", "inference_occurred": False,
                    "failure_class": classify_exception(e), "transport_retries": 0, "transport_recovered": False}

class OllamaBackend(ModelBackend):
    name = "ollama"
    def __init__(self, model_id="llama3"): self.model_id = model_id
    def is_available(self) -> bool:
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
            return True
        except Exception: return False
    def metadata(self) -> dict:
        return {"backend": self.name, "model": self.model_id, "available": self.is_available(),
                "base_url": "http://localhost:11434"}

class ZCodeNativeBackend(ModelBackend):
    """Placeholder — inspected the ZCode app for a CLI/subprocess/session-API invocation
    surface and found NONE that exposes a programmatic agent call from outside the interactive
    app. The ZAI HTTP API (ZAIBackend) IS the native GLM path. This backend stays UNSUPPORTED."""
    name = "zcode-native"
    status = "UNSUPPORTED_NO_INVOCATION_INTERFACE_FOUND"
    def is_available(self) -> bool: return False
    def metadata(self) -> dict:
        return {"backend": self.name, "available": False, "status": self.status,
                "note": "ZCode ships an interactive macOS app; no headless CLI/subprocess agent-invocation interface found. Use ZAIBackend (same GLM model via api.z.ai)."}

def get_backend(name: str, model_id: str = None) -> ModelBackend:
    """Factory. Default = zai-glm-native (the actual model running the skill)."""
    name = (name or "").lower()
    if name in ("zai", "glm", "zai-glm-native"): return ZAIBackend(model_id or "GLM-5.2")
    if name == "openai": return OpenAIBackend(model_id or "gpt-4o-mini")
    if name == "ollama": return OllamaBackend(model_id or "llama3")
    if name in ("zcode-native","zcode"): return ZCodeNativeBackend()
    return ModelBackend()
