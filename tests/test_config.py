import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

def test_output():
    assert config.ANTHROPIC_API_KEY is not None and config.ANTHROPIC_API_KEY != ""
