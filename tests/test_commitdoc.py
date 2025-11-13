import pytest
from unittest import mock
import commitdoc

SAMPLE_DIFF = """
diff --git a/app.py b/app.py
index 000..111 100644
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
+print("Hello world")
"""

def fake_response(*args, **kwargs):
    return "feat(core): add hello world\n\nAdd print statement.\n\nCloses #42"

@mock.patch("commitdoc.openai_chat_completion", side_effect=fake_response)
@mock.patch("commitdoc.openrouter_chat_completion", side_effect=fake_response)
@mock.patch("commitdoc.generic_http_provider", side_effect=fake_response)
@mock.patch("commitdoc.ollama_run", side_effect=fake_response)
def test_generate_commit_message_all_providers(*_):
    for provider in ["openai", "openrouter", "http", "ollama"]:
        msg = commitdoc.generate_commit_message(
            SAMPLE_DIFF,
            provider=provider,
            model="test-model"
        )
        assert "feat(core)" in msg
        assert "Add print" in msg
