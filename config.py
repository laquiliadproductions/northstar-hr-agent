"""Shared deterministic settings for the Northstar HR Agent."""



import os

import random



import numpy as np





RANDOM_SEED = 42

CHUNK_SIZE = 1000

CHUNK_OVERLAP = 200

RETRIEVAL_TOP_K = 4
EVALUATION_SAMPLE_SIZE = 20

def set_reproducible_seed(seed: int = RANDOM_SEED) -> None:

    """Set supported random-number generators to a fixed seed."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
