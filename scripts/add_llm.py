import json

with open('static/files/app/chatbot.json', 'r') as f:
    models = json.load(f)

with open('static/files/llm/config.json', 'r') as f:
    config = json.load(f)


models['local'] = { model["model_alias"]: model["n_ctx"] for model in config["models"] }

with open('static/files/app/chatbot.json', 'w') as f:
    json.dump(models, f, indent=2)