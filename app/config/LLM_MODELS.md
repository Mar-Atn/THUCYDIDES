# LLM Model Reference — TTT Project

**Last updated:** 2026-04-01 | **Next review:** 2026-07-01 (or when new models launch)

---

## Anthropic Claude

### Current Generation (USE THESE)

| Model | Model ID | Context | Max Output | Input $/MTok | Output $/MTok | Use For |
|-------|----------|---------|------------|-------------|--------------|---------|
| **Opus 4.6** | `claude-opus-4-20250514` | 1M | 128K (300K batch) | $5 | $25 | Super-Moderator, complex multi-step reasoning |
| **Sonnet 4.6** | `claude-sonnet-4-20250514` | 1M | 64K (300K batch) | $3 | $15 | AI agent decisions, Tier 3 conversations |
| **Haiku 4.5** | `claude-haiku-4-5-20251001` | 200K | 64K | $1 | $5 | High-volume Tier 1-2, classification, simple turns |

### Aliases (always point to latest)
- `claude-opus-4-0` → Opus 4.6
- `claude-sonnet-4-0` → Sonnet 4.6
- `claude-haiku-4-5` → Haiku 4.5

### Cost Optimization
- **Prompt caching:** 90% savings on cached input (critical for 4-block model context)
- **Batch API:** 50% discount (use for unmanned runs — no real-time needed)
- **Combined caching + batch:** up to 95% cost reduction

### SDK
```python
from anthropic import Anthropic
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}]
)
```

### Legacy (avoid)
- `claude-opus-4-5`, `claude-sonnet-4-5` — previous gen, strictly worse than 4.6
- `claude-3-haiku-20240307` — cheapest ($0.25/$1.25) but 4K max output, use only for trivial tasks
- All `claude-3-5-*` and `claude-3-7-*` models are **deprecated**

---

## Google Gemini

### Production-Ready (USE THESE)

| Model | Model ID | Context | Max Output | Input $/MTok | Output $/MTok | Use For |
|-------|----------|---------|------------|-------------|--------------|---------|
| **2.5 Pro** | `gemini-2.5-pro` | 1M | 65K | $1.25 (≤200K) / $2.50 (>200K) | $10 / $15 | Complex reasoning, alternative to Claude Sonnet |
| **2.5 Flash** | `gemini-2.5-flash` | 1M | 65K | $0.30 | $2.50 | Agent conversations, bulk processing |
| **2.5 Flash-Lite** | `gemini-2.5-flash-lite` | 1M | 65K | $0.10 | $0.40 | Cheapest option, Tier 1 quick-scan |

### Gemini 3.x Family (Preview — Cutting Edge)

| Model | Model ID | Context | Max Output | Input $/MTok | Output $/MTok | Use For |
|-------|----------|---------|------------|-------------|--------------|---------|
| **3.1 Pro** | `gemini-3.1-pro-preview` | 1M | 65K | $2 (≤200K) / $4 (>200K) | $12 / $18 | Most capable Gemini, complex agentic tasks |
| **3.1 Pro CustomTools** | `gemini-3.1-pro-preview-customtools` | 1M | 65K | same as 3.1 Pro | same | Optimized for function calling / tool use |
| **3.1 Flash Lite** | `gemini-3.1-flash-lite-preview` | 1M | 65K | $0.25 | $1.50 | Budget frontier model, high volume |
| **3.1 Flash Live** | `gemini-3.1-flash-live-preview` | 131K | 65K | $0.75 | $4.50 | Real-time dialogue, bidirectional audio |
| **Nano Banana 2** | `gemini-3.1-flash-image-preview` | 65K | 65K | $0.50 | $3 text / $60 images | Native image gen + editing (up to 2K) |
| **3.0 Flash** | `gemini-3-flash-preview` | 1M | 65K | $0.50 | $3.00 | Mid-tier workhorse |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | 131K | 32K | $2.00 | $12 text / $120 images | Pro image gen, up to 4K, advanced reasoning |

### Cost Optimization
- **Batch API:** 50% discount on all Gemini models
- **Context caching:** Available, similar savings to Anthropic

### SDK
```python
from google import genai
client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="..."
)
```

### Deprecated (DO NOT USE)
- `gemini-2.0-flash`, `gemini-2.0-flash-lite` — **shut down June 1, 2026**
- All `gemini-1.5-*` models — no longer available to new users

---

## TTT Cost Strategy

### Per-Tier Model Assignment

| SIM Tier | Claude Model | Gemini Model | Est. Cost/Round |
|----------|-------------|-------------|-----------------|
| Tier 1 (quick-scan) | Haiku 4.5 | 2.5 Flash-Lite | ~$0.05 |
| Tier 2 (modelled) | Haiku 4.5 | 2.5 Flash | ~$0.30 |
| Tier 3 (full text) | Sonnet 4.6 | 2.5 Flash | ~$1-2 |
| Tier 4 (+ voice) | Sonnet 4.6 | 2.5 Pro | ~$3-5 |
| Super-Moderator | Opus 4.6 or Sonnet 4.6 | 2.5 Pro | included above |

### Full 8-Round SIM Cost Estimate
- Tier 1: ~$0.40 per run
- Tier 2: ~$2.50 per run
- Tier 3: ~$8-16 per run
- Tier 4: ~$25-40 per run (incl. ElevenLabs voice)

### Dual-Provider Failover
Primary provider configurable per model role. If one provider rate-limits or errors, automatic fallback to the other. Both providers support 1M context.

---

## Image Generation (Same Gemini API Key)

### Nano Banana — Native Image Gen (Text + Image in one call)

Google's "Nano Banana" family = Gemini models with native image generation built in.
They generate images inline with text, support multi-turn editing, up to 4K resolution, and accept up to 14 reference images.

| Model | Model ID | Resolution | Use For |
|-------|----------|------------|---------|
| **Nano Banana 2** | `gemini-3.1-flash-image-preview` | up to 2K (+ 512) | Fast, cheap image gen/edit — VERIFIED WORKING |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | up to 4K | High-quality contextual image gen, pro assets |
| **Nano Banana** | `gemini-2.5-flash-image` | up to 2K | Stable, speed-optimized |

```python
from google import genai
from google.genai import types
client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])

# Nano Banana — generates images inline with text
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",  # or gemini-3-pro-image-preview for 4K
    contents="Draw a hex map of the Mashriq theater with labeled zones",
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",   # also: 1:1, 4:3, 3:4, 9:16, 1:4, 4:1, etc.
            image_size="2K"        # options: "512", "1K", "2K", "4K" (4K = Pro only)
        )
    )
)
for part in response.candidates[0].content.parts:
    if part.inline_data:
        # part.inline_data.data = image bytes (PNG), part.inline_data.mime_type
        with open("output.png", "wb") as f:
            f.write(part.inline_data.data)
    elif part.text:
        print(part.text)
```

**Key features:**
- Multi-turn conversational editing (refine images across turns)
- Up to 14 reference images for composition guidance
- Built-in "thinking" for complex prompts (`thinkingLevel`: "minimal" or "High")
- Google Search grounding for real-world visual references
- Advanced text rendering in images
- SynthID watermark on all generated images

### Imagen 4.0 (Dedicated image-only models — VERIFIED WORKING)

| Model | Model ID | Price | Use For |
|-------|----------|-------|---------|
| **Imagen 4.0 Fast** | `imagen-4.0-fast-generate-001` | $0.02/image | Quick drafts, iteration |
| **Imagen 4.0** | `imagen-4.0-generate-001` | $0.04/image | Standard quality |
| **Imagen 4.0 Ultra** | `imagen-4.0-ultra-generate-001` | $0.06/image | Highest quality, final assets |

```python
# Imagen 4.0 — dedicated image generation (no text context, just prompt → image)
response = client.models.generate_images(
    model="imagen-4.0-generate-001",
    prompt="A strategic military map in fantasy cartography style",
    config=types.GenerateImagesConfig(number_of_images=1)
)
image_bytes = response.generated_images[0].image.image_bytes
```

**When to use which:**
- **Nano Banana** for contextual generation (text + image together, editing, multi-turn)
- **Imagen 4.0** for standalone image generation (simple prompt → image, batch production)

### Video & Audio Generation

| Model | Model ID | Price | Use For |
|-------|----------|-------|---------|
| **Veo 3.1** | `veo-3.1-generate-preview` | $0.40-0.60/sec | Cinematic video generation |
| **Veo 3.1 Fast** | `veo-3.1-fast-generate-preview` | $0.15-0.35/sec | Quick video drafts |
| **Veo 3.1 Lite** | `veo-3.1-lite-generate-preview` | $0.05-0.08/sec | Budget video |
| **Lyria 3 Pro** | `lyria-3-pro-preview` | $0.08/request | Full song generation |
| **Lyria 3 Clip** | `lyria-3-clip-preview` | $0.04/request | 30s music clip |

---

## Other Specialty Models

| Model | Provider | Use Case |
|-------|----------|----------|
| `gemini-embedding-001` | Google | Semantic search over game events |
| `gemini-2.5-flash-preview-tts` | Google | Text-to-speech (alternative to ElevenLabs) |
| `deep-research-pro-preview` | Google | Autonomous multi-step research |
| `gemini-2.5-computer-use-preview` | Google | UI automation / computer use |

---

## Maintenance

This file is maintained by the **KNOWLEDGE agent** as part of the biweekly API review cycle.
Every 2 weeks: check for new model releases, deprecations, and pricing changes.
Update this file + notify the team via session notes.

**How to check for new models:**
```python
from google import genai
client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])
for m in client.models.list():
    print(f"{m.name} | in={m.input_token_limit} | out={m.output_token_limit}")
```

For Anthropic: check https://docs.anthropic.com/en/docs/about-claude/models
