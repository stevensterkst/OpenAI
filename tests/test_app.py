from fastapi.testclient import TestClient
from app import APP

client = TestClient(APP)

def test_system_contract():
    r=client.get('/system'); assert r.status_code==200
    d=r.json(); assert d['port']==8765; assert d['version']=='0.8.4'
    assert d['policy']['auto_delete_chats'] is False
    assert d['policy']['silent_provider_fallback'] is False

def test_provider_registry():
    d=client.get('/api/providers').json()
    for pid in ['ollama','jan','lmstudio','openrouter','huggingface','venice','openai','anthropic','google','xai','deepseek','mistral','moonshot','zai','qwen','perplexity']:
        assert pid in d['providers']
    for cid in ['brave','higgsfield','duckduckgo','tor','huggingchat','metaai']:
        assert cid in d['connectors']

def test_console_routes():
    assert client.get('/').status_code==200
    assert client.get('/console').status_code==200
    assert client.get('/providers').status_code==200

def test_routing_is_explicit():
    d=client.post('/api/route',json={'task':'analyse a confidential local document'}).json()
    assert d['privacy'] is True
    assert d['candidates'][0] in ['ollama','lmstudio','jan']

def test_chat_archive_contract():
    r=client.post('/api/chats',json={'id':'test-permanent-chat','title':'test','messages':[{'role':'user','content':'hello'}]})
    assert r.status_code==200
    assert r.json()['never_delete'] is True
    r2=client.get('/api/chats/test-permanent-chat')
    assert r2.status_code==200
    assert r2.json()['messages'][0]['content']=='hello'
