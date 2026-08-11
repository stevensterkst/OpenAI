from fastapi.testclient import TestClient
from app import APP

client = TestClient(APP)

def test_system_contract():
    r=client.get('/system'); assert r.status_code==200
    d=r.json(); assert d['port']==8765; assert d['chat_persistence']['deletion_policy']=='NEVER'

def test_provider_registry():
    d=client.get('/api/providers').json()['providers']
    for pid in ['ollama','jan','lmstudio','openrouter','huggingface','venice','openai','anthropic','google','xai','deepseek','mistral','moonshot','zai','qwen','perplexity']:
        assert pid in d

def test_console_routes():
    assert client.get('/').status_code==200
    assert client.get('/console').status_code==200
    assert client.get('/providers').status_code==200

def test_routing_is_explicit():
    d=client.post('/api/route',json={'task':'analyse a confidential local document'}).json()
    assert d['privacy'] is True
    assert d['candidates'][0] in ['ollama','lmstudio','jan']
