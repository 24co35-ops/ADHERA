import sys
import os
from unittest.mock import patch

# Suppress Sentry BEFORE app module is imported
os.environ["ENVIRONMENT"] = "test"
os.environ["SENTRY_DSN"] = ""

# Patch sentry_sdk.init so it is a no-op during tests
_sentry_patcher = patch("sentry_sdk.init")
_sentry_patcher.start()

# Ensure repo root is on sys.path so pytest can resolve `app.*` imports
sys.path.insert(0, os.path.dirname(__file__))
