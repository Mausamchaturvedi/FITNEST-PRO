from pathlib import Path
import importlib.util

p = Path('Flask Project.py').resolve()
spec = importlib.util.spec_from_file_location('app', str(p))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
client = app.app.test_client()

scenarios = [
    ('/register', {'name': 'Test User', 'email': 'test@example.com', 'password': 'secret', 'weight': '70', 'height': '175'}),
    ('/login', {'email': 'test@example.com', 'password': 'secret'})
]

for endpoint, data in scenarios:
    resp = client.post(endpoint, data=data, follow_redirects=True)
    print(endpoint, resp.status_code, len(resp.get_data()))
    text = resp.get_data(as_text=True)
    print(text[:400])
    print('---')
