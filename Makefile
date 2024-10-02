sample:
	venv/bin/python  index.py --dbname sample-crate.db  --rocrate test_data/sample-crate  ; venv/bin/datasette sample-crate.db --template-dir templates --static files:test_data/sample-crate


cooee:
	venv/bin/python  index.py --dbname cooee.db  --rocrate test_data/cooee --flatten ;  venv/bin/datasette cooee.db --template-dir templates --static files:test_data/cooee

f2f:
	venv/bin/python  index.py --dbname f2f.db  --rocrate test_data/farms-to-freeways --flatten --csv ;  venv/bin/datasette f2f.db --template-dir templates --static files:test_data/farms-to-freeways  --setting facet_suggest_time_limit_ms 500



native:
	venv/bin/python  native.py --dbname f2f.db  --rocrate test_data/farms-to-freeways --flatten --csv ;  venv/bin/datasette f2f.db --template-dir templates --static files:test_data/farms-to-freeways  --setting facet_suggest_time_limit_ms 500



syds:
	venv/bin/python  index.py --dbname syds.db  --rocrate test_data/ss/SydS --flatten --csv ;  venv/bin/datasette syds.db 
