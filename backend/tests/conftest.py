import os

# The test suite uses deterministic fake provider responses and must not contact Aiven.
os.environ.setdefault("AGENTFORGE_TESTING", "1")
