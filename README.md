# unprospect-gtm
Go to market OS for unprospect

## Local classification workflow

This repo now includes a simple local workflow to classify companies into logistics subsegments using the Supabase data already available in the workspace.

### Requirements
- Python 3.10+
- Environment variables:
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY

### Run the classifier
```bash
python segment_companies.py
```

This will generate:
- segment_results.json
- segment_results.csv

### Run the subagent-style orchestrator
```bash
python subagent_workflow.py
```

This will generate:
- subagent_results.json

### Run tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```
