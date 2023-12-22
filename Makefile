sample:
	venv/bin/python  index.py --db sample-crate.db  --rocrate test_data/sample-crate  ; venv/bin/datasette sample-crate.db --template-dir templates --static files:test_data/sample-crate
