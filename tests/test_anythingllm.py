"""End-to-end tests for AnythingLLM integration.

Runs actual inference through the documented chain:
SS → AnythingLLM → Ollama → phi4-mini:3.8b → response

Does NOT report PASS for code compilation or endpoint existence.
Only PASS when real inference returns actual model output.
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
    print(f"✓ Endpoint discovered: {result['endpoint']} ({result['source']})")


@pytest.mark.asyncio
async def test_endpoint_reachable():
    """Test: AnythingLLM is online at endpoint."""
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    result = await adapter.ping()
    assert result["ok"] is True, f"AnythingLLM not reachable: {result.get('error')}"
    print(f"✓ AnythingLLM online at {adapter.base_url}")
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
        assert key is not None, "AnythingLLM API key not configured. Configure with: keyring.set_password('SS-Second-Brain', 'anythingllm', '<key>')"
        print(f"✓ API key configured (length: {len(key)} chars)")
    except ImportError:
        pytest.skip("keyring not available")


@pytest.mark.asyncio
async def test_workspaces_available():
    """Test: At least one workspace is configured."""
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    result = await adapter.list_workspaces()
    assert result["ok"] is True, f"Failed to list workspaces: {result.get('error')}"
    assert result["count"] > 0, "No workspaces configured in AnythingLLM"
    print(f"✓ {result['count']} workspace(s) found")
    for ws in result["workspaces"][:3]:
        print(f"  - {ws.get('name')} (slug: {ws.get('slug')})")


@pytest.mark.asyncio
async def test_workspace_selection():
    """Test: Workspace can be selected (defaults to first)."""
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    result = await adapter.select_workspace()
    assert result["ok"] is True, f"Workspace selection failed: {result.get('error')}"
    assert adapter.workspace_slug is not None
    print(f"✓ Workspace selected: {adapter.workspace_name} ({adapter.workspace_slug})")


@pytest.mark.asyncio
async def test_ollama_configured():
    """Test: Selected workspace has Ollama configured."""
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    await adapter.select_workspace()
    result = await adapter.workspace_settings()
    assert result["ok"] is True, f"Settings fetch failed: {result.get('error')}"
    assert result["ollama_configured"] is True, "Ollama not configured in workspace"
    print(f"✓ Ollama configured as LLM provider")
    print(f"  LLM Provider: {result.get('llm_provider')}")


@pytest.mark.asyncio
async def test_real_inference():
    """Test: Real inference through AnythingLLM → Ollama.
    
    CRITICAL: This test FAILS if inference returns empty/no actual model output.
    Code compilation is NOT sufficient. We need a real response.
    """
    adapter = AnythingLLMAdapter()
    adapter.discover_endpoint()
    await adapter.select_workspace()
    settings = await adapter.workspace_settings()
    assert settings["ok"] is True
    
    # Real test: send actual message
    messages = [{"role": "user", "content": "What is 2+2? Answer with just the number."}]
    result = await adapter.chat_inference(messages)
    
    # MUST have actual response
    assert result["ok"] is True, f"Inference failed: {result.get('error')}"
    assert result.get("text"), "No response text returned"
    assert len(result["text"]) > 0, "Response is empty string"
    
    print(f"✓ Real inference PASSED")
    print(f"  Workspace: {adapter.workspace_slug}")
    print(f"  Latency: {result['latency_ms']}ms")
    print(f"  Response: {result['text'][:100]}...")
    print(f"  Chain: {result.get('chain')}")


@pytest.mark.asyncio
async def test_full_health_check():
    """Test: Complete end-to-end health check passes."""
    adapter = AnythingLLMAdapter()
    result = await adapter.full_health_check()
    
    assert result["ok"] is True, f"Health check failed at: {result.get('blocker')}"
    assert result["ready"] is True
    assert result["final_status"] == "READY"
    
    print(f"✓ Full health check PASSED")
    print(f"  Endpoint: {result.get('endpoint')}")
    print(f"  Workspace: {result.get('workspace')}")
    print(f"  Status: {result.get('final_status')}")


if __name__ == "__main__":
    # Run tests synchronously for quick testing
    print("\n=== AnythingLLM Integration Tests ===")
    async def run_all():
        adapter = AnythingLLMAdapter()
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
        print("\n6. Ollama Configured")
        await test_ollama_configured()
        print("\n7. Real Inference")
        await test_real_inference()
        print("\n8. Full Health Check")
        await test_full_health_check()
    
    asyncio.run(run_all())
