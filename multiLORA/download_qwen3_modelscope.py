python -c "
from modelscope.hub.api import HubApi
api = HubApi()
results = api.list_models(author='Qwen', limit=20)
for m in results:
    if 'Qwen3-4B' in m.model_id:
        print(m.model_id)
"
