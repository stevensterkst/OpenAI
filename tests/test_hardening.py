from fastapi.testclient import TestClient
from app_integrated import APP

client=TestClient(APP)

def test_release_stays_084():
    r=client.get('/api/release');assert r.status_code==200;assert r.json()['version']=='0.8.4'

def test_model_get_compatibility_route_exists():
    r=client.get('/api/models/does-not-exist');assert r.status_code==404

def test_identity_is_deterministic_and_does_not_call_model():
    r=client.post('/api/chat-safe',json={'provider':'ollama','model':'phi4-mini:3.8b','messages':[{'role':'user','content':'What model are you using?'}]})
    assert r.status_code==200
    d=r.json();assert d['provider']=='ollama';assert d['model']=='phi4-mini:3.8b';assert d['identity_source']=='SS route metadata'

def test_no_destructive_workspace_routes():
    paths={getattr(x,'path','') for x in APP.routes}
    assert '/api/workspace/scan' in paths
    assert '/api/workspace/duplicates' in paths
    assert not any(p in paths for p in ('/api/workspace/delete','/api/workspace/move','/api/workspace/rename','/api/workspace/overwrite'))
