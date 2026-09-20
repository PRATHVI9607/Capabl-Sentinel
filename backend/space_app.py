"""Entry point for the Hugging Face Gradio Space.

The Space SDK is Gradio, but SENTINEL is an API, not a Gradio app. So the real
FastAPI service is served as-is and a small Gradio page is mounted on top of it
purely so the Space URL shows something useful instead of a 404 — every API
route keeps its normal path.

Deliberately not named `app.py`: that would collide with the `app/` package in
this same directory. `app_file: space_app.py` in README.md points the Space here.
"""

from __future__ import annotations

import os

import gradio as gr
import uvicorn

from app import __version__
from app.config import settings
from app.llm import any_provider_configured
from app.main import app as api
from app.rag import vector_store

# Spaces routes public traffic to this port.
PORT = int(os.environ.get("PORT", 7860))

# ZeroGPU terminates any Space that declares no GPU function, even one serving
# happily on CPU -- the platform exists to time-share GPUs and will not host a
# workload that never asks for one. SENTINEL is CPU-only (ONNX embeddings, an
# ONNX reranker, numpy search), so this satisfies the check and is never called
# on a request path. `spaces` is injected by the platform and absent locally.
try:
    import spaces

    @spaces.GPU(duration=1)
    def _zerogpu_probe() -> str:
        """Exists so ZeroGPU keeps the Space alive. Nothing calls it."""
        return "ok"

except ImportError:  # running anywhere other than a ZeroGPU Space
    _zerogpu_probe = None

LANDING = f"""
# 🦺 SENTINEL — API

**Safety ENTRy INcident Threat Early-warning Layer** · v{__version__}

Upload a workplace safety incident report and get the precursor conditions it
shares with past investigations, the regulatory clauses that apply, and an
explainable risk score — streamed stage by stage.

This Space runs the backend only. The interface is deployed separately.

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | [`/health`](/health) | liveness and configuration |
| `POST` | `/analyze` | upload a PDF, start an analysis |
| `GET` | `/analyze/{{id}}/stream` | server-sent events, one per stage |
| `GET` | `/analyze/{{id}}` | the finished report |
| `GET` | [`/history`](/history) | completed analyses |
| `GET` | [`/tools`](/tools) | the ten agent tools and their schemas |

### How it works

Retrieval runs BM25 and dense vectors in parallel, fuses them with reciprocal
rank fusion, reranks with a cross-encoder, then trims each passage to the
sentences that earned the match — so every citation is traceable to its source.

The risk score is deterministic Python, not a model output: four weighted
components, each shown with its weight, summing to the total. Regulatory clauses
are retrieved text rather than generated, so the system cannot invent a citation.

Corpus: 26 US Chemical Safety Board investigations and 15 OSHA standards pulled
verbatim from the federal eCFR API. Both public domain.
"""


def status() -> str:
    """Rendered once at page load, so the Space shows whether it is configured."""
    ready = vector_store.configured()
    return (
        f"- **LLM configured:** {'yes' if any_provider_configured() else 'no'}\n"
        f"- **Vector backend:** `{vector_store.backend()}`"
        f" ({'index loaded' if ready else 'no index'})\n"
        f"- **Environment:** `{settings.environment}`"
    )


with gr.Blocks(title="SENTINEL API", theme=gr.themes.Soft()) as landing:
    gr.Markdown(LANDING)
    gr.Markdown(status())

    # Wired into the Blocks so the platform's startup scan finds it. Hidden,
    # because it is an artefact of the hosting tier, not a feature.
    if _zerogpu_probe is not None:
        probe_button = gr.Button("probe", visible=False)
        probe_output = gr.Textbox(visible=False)
        probe_button.click(fn=_zerogpu_probe, inputs=None, outputs=probe_output)

# Gradio is mounted onto the API rather than the other way round: the FastAPI
# routes are registered first and keep their paths.
space = gr.mount_gradio_app(api, landing, path="/")

if __name__ == "__main__":
    uvicorn.run(space, host="0.0.0.0", port=PORT)
