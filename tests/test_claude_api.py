import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
import config

def test_claude_api():
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=100, messages=[{"role": "user", "content": "Say hello!"}])
    assert response.content[0].text is not None
