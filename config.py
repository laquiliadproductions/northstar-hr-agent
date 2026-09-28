"""Shared deterministic settings for the Northstar HR Agent."""

from __future__ import annotations
import os
import random
import numpy as np

RANDOM_SEED = 42
RETRIEVAL_TOP_K = 4

def set_reproducible_seed(seed: int = RANDOM_SEED) -> None:
    """Set supported random-number generators to a fixed seed."""

    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
