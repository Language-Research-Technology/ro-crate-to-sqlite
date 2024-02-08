# ro-crate-to-datasette

Experimental repository for exploring RO-Crates using Datasette -- ATM this is a generic RO-Crate viewer works for single crates ATM.

The indexer script is a stand alone Python script but it could be packaged as a Datasette plugin that can read RO-Crates natively.


## Why?

This experiment is to explore whether it makes sense to use Datasette (or just sqlite) with a simple front end to host small to medium collections of data without need ing a server.

The initial proof of concept works but there are things to do.

Add search:

-  Full text
-  Metadata (this is a little tricky
 because of the data model where properties are all separate from entities)
-  Geo


## Issues

If the end goal is to host and serve data without a browser, it may be better to use a sqlite database but skip the datasette part, as the exploded RO-Crate data model is not necessarily conducive to Datasette's built in views/

## Installation (Macos)

- Make a virtual environment locally:
  `python3 -venv venv`
- Activate the virtual environment 
  `. venv/bin/activate`
- Install 
  `pip3 install -r requirements.txt`



## Usage

There's a sample dataset included which should serve as an example of usage:

```
make sample
```

Load <http://localhost:8001/browse/entity> in your browser.




