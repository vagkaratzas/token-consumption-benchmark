"""Single, consistent tokenizer for every scenario.

We use tiktoken's ``o200k_base`` encoding (the GPT-4o / modern BPE) as a stable
proxy applied identically to all scenarios. Absolute token counts are
tokenizer-dependent; the *ratios* between scenarios — the thing this benchmark
reports — are robust across tokenizers.
"""

from __future__ import annotations

import tiktoken

_ENC = tiktoken.get_encoding("o200k_base")


def count_tokens(text: str) -> int:
    """Return the number of tokens in ``text`` (empty/None -> 0)."""
    if not text:
        return 0
    return len(_ENC.encode(text))
