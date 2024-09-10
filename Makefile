sample:
	venv/bin/python  index.py --db sample-crate.db  --rocrate test_data/sample-crate  ; venv/bin/datasette sample-crate.db --template-dir templates --static files:test_data/sample-crate


cooee:
	venv/bin/python  index.py --db cooee.db  --rocrate test_data/cooee --flatten ;  venv/bin/datasette cooee.db --template-dir templates --static files:test_data/cooee

f2f:
	venv/bin/python  index.py --db f2f.db  --rocrate test_data/farms-to-freeways --flatten --csv ;  venv/bin/datasette f2f.db --template-dir templates --static files:test_data/farms-to-freeways  --setting facet_suggest_time_limit_ms 500
