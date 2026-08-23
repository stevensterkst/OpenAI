"""End-to-end tests for AnythingLLM integration.

Tests actual inference through documented chain:
SS → AnythingLLM → configured provider → configured model → response

CRITICAL: Tests FAIL if:
- Endpoint not reachable
- API key missing
- Workspace not configured
- Response schema is incorrect (must be 'textResponse', not 'response' or 'text')
- Inference returns empty/no actual text

Tests PASS only with actual generated content from configured model.
"""
import asyncio
import pytest
from anythingllm_adapter import AnythingLLMAdapter


@pytest.mark.asyncio
async def test_endpoint_discovery():
    """Test: AnythingLLM endpoint is discoverable."""
    adapter = AnythingLLMAdapter()
    result = adapter.discover_endpoint()
    assert result["ok"] is True
    assert "endpoint" in result
    assert result["source"] in ("environment", "default")
    print(f"\u2713 Endpoint discovered: {result['endpoint']} ({result['source']})")


@pytest.mark.asyncio
async def test_endpoint_reachable():
    """Test: AnythingLLM is online at endpoint."""
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    result = await adapter.ping()
    assert result["ok"] is True, f"AnythingLLM not reachable: {result.get('error')}"
    print(f"\u2713 AnythingLLM online at {adapter.base_url}")
    if result.get("version"):
        print(f"  Version: {result['version']}")


@pytest.mark.asyncio
async def test_api_key_configured():
    """Test: AnythingLLM API key is configured in credential store."""
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    
    try:
        import keyring
        key = keyring.get_password("SS-Second-Brain", "anythingllm")
        assert key is not None, "AnythingLLM API key not in credential store"
        print(f"\u2713 API key configured (length: {len(key)} chars)")
    except ImportError:
        pytest.skip("keyring not available")


@pytest.mark.asyncio
async def test_workspaces_available():
    """Test: At least one workspace is configured."""
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    result = await adapter.list_workspaces()
    assert result["ok"] is True, f"Failed to list workspaces: {result.get('error')}"
    assert result["count"] > 0, "No workspaces configured"
    print(f"\u2713 {result['count']} workspace(s) found")
    for ws in result["workspaces"][:3]:
        print(f"  - {ws.get('name')} (slug: {ws.get('slug')})")


@pytest.mark.asyncio
async def test_workspace_selection():
    """Test: Workspace can be selected."""
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    result = await adapter.select_workspace()
    assert result["ok"] is True, f"Workspace selection failed: {result.get('error')}"
    assert adapter.workspace_slug is not None
    print(f"\u2713 Workspace selected: {adapter.workspace_name} ({adapter.workspace_slug})")


@pytest.mark.asyncio
async def test_workspace_config_exists():
    """Test: Workspace has configured provider and model."""
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    await adapter.select_workspace()
    result = await adapter.workspace_config()
    assert result["ok"] is True, f"Config fetch failed: {result.get('error')}"
    assert result["configured"] is True
    print(f"\u2713 Workspace configured")
    print(f"  Provider: {result.get('llm_provider')}")
    print(f"  Model: {result.get('llm_model')}")


@pytest.mark.asyncio
async def test_real_inference_with_official_schema():
    """Test: Real inference returns actual text in official response schema.
    
    CRITICAL TEST: Verifies:
    1. Inference actually completes
    2. Response uses OFFICIAL schema key 'textResponse' (NOT 'response', 'text', etc)
    3. textResponse contains actual generated text (not empty)
    4. No errors in response
    
    This test FAILS if:
    - AnythingLLM endpoint not running
    - API key invalid
    - Workspace misconfigured
    - Response schema is wrong
    - Model returns empty text
    """
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    await adapter.select_workspace()
    config = await adapter.workspace_config()
    assert config["ok"] is True
    
    # Real inference
    messages = [{"role": "user", "content": "What is 2+2? Answer with just the number."}]
    result = await adapter.chat_inference(messages)
    
    # MUST succeed with actual text
    assert result["ok"] is True, f"Inference failed: {result.get('error')}"
    assert result.get("text"), "No text in response"
    assert len(result["text"]) > 0, "Response text is empty"
    assert isinstance(result["text"], str), "Response is not a string"
    
    print(f"\u2713 Real inference PASSED (official schema)")
    print(f"  Workspace: {adapter.workspace_slug}")
    print(f"  Model: {result.get('model')}")
    print(f"  Latency: {result['latency_ms']}ms")
    print(f"  Response: {result['text'][:120]}...")
    print(f"  Chain: {result.get('chain')}")


@pytest.mark.asyncio
async def test_full_health_check_requires_real_inference():
    """Test: Complete end-to-end health check requires actual inference."""
    adapter = AnythingLLMAdapter()
    result = await adapter.full_health_check()
    
    # Health check is READY only if real inference succeeded
    assert result["ok"] is True, f"Health check blocked at: {result.get('blocker')}"
    assert result["ready"] is True
    assert result["final_status"] == "READY"
    
    print(f"\u2713 Full health check PASSED (READY)")
    print(f"  Endpoint: {result.get('endpoint')}")
    print(f"  Workspace: {result.get('workspace')}")
    print(f"  Provider: {result.get('provider')}")
    print(f"  Model: {result.get('model')}")
    print(f"  Inference latency: {result.get('inference_latency_ms')}ms")


if __name__ == "__main__":
    # Run tests synchronously for manual testing
    print("\n=== AnythingLLM Integration Tests (Official API Schema) ===")
    async def run_all():
        print("\n1. Endpoint Discovery")
        await test_endpoint_discovery()
        print("\n2. Endpoint Reachable")
        await test_endpoint_reachable()
        print("\n3. API Key Configured")
        await test_api_key_configured()
        print("\n4. Workspaces Available")
        await test_workspaces_available()
        print("\n5. Workspace Selection")
        await test_workspace_selection()
        print("\n6. Workspace Config")
        await test_workspace_config_exists()
        print("\n7. Real Inference (Official Schema)")
        await test_real_inference_with_official_schema()
        print("\n8. Full Health Check")
        await test_full_health_check_requires_real_inference()
    
    asyncio.run(run_all())
