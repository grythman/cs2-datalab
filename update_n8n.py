import json

with open("n8n_data/update.json", "r") as f:
    workflows = json.load(f)

for wf in workflows:
    for node in wf["nodes"]:
        if node.get("name") in ("Message a model1", "Message a model (Long)"):
            if "typeOptions" not in node:
                node["typeOptions"] = {}
            node["retryOnFail"] = True
            node["typeOptions"]["retryOnFail"] = True
            node["typeOptions"]["maxTries"] = 10
            node["typeOptions"]["waitBetweenTries"] = 10000

with open("n8n_data/update.json", "w") as f:
    json.dump(workflows, f, indent=2)

