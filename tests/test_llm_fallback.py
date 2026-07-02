from tools.llm import GeminiFallbackWrapper


class RaisingModel:
    def invoke(self, prompt):
        raise RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")


def test_fallback_wrapper_returns_plan_when_quota_error_occurs():
    wrapper = GeminiFallbackWrapper(RaisingModel())

    response = wrapper.invoke("You are the Planner Agent. Task: build a spam detector")

    assert response.content
    assert "quota" in response.content.lower()
    assert "plan" in response.content.lower()
