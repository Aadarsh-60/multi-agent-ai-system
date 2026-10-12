import unittest
from tools.llm import GroqFallbackWrapper


class MockResponse:
    def __init__(self, content):
        self.content = content


class MockModel:
    def invoke(self, prompt):
        return MockResponse("This is a response\n\n\n\nwith extra newlines cleaned.")


class TestLLMFallbackWrapper(unittest.TestCase):
    def test_fallback_wrapper_cleans_newlines(self):
        wrapper = GroqFallbackWrapper(MockModel())
        response = wrapper.invoke("Test prompt")
        self.assertIn("extra newlines", response.content)
        self.assertNotIn("\n\n\n", response.content)


if __name__ == "__main__":
    unittest.main()
