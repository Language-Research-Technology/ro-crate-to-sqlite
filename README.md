# ro-crate-to-datasette

Experimental repository for exploring RO-Crates as tabular data.

- Generates three tables:
  - `properties`: a general-purpose triple-store style table which contains all of the triples from the crate, but with some additional columns for convenience
  - `entities`: a helper table to to summarize an entity with name, id and a few other fielrs
  - `root`: A single-entry table pointing to the root data entity
  - *Optional*: Using a config file ( which is generated for you on first run) specify which tables you would like created with a row per entity of that `@type` - this allows you to also join in data directly and to hide fields you don't want -- doco not done yet but see the cooee example this will also pull-in indexable-text if that is present on an entity

- Starts Datasette 

The indexer script is currently a stand alone Python script but it could be packaged as a Datasette plugin that can read RO-Crates natively.


## Why?

This experiment is to explore
- whether it makes sense to use Datasette (or just sqlite) with a simple front end to host small to medium collections of data without need ing a server
- As a tool for data managers and researchers to crate custom tabular views of RO-Crate data collections

## Todo

The initial proof of concept works but there are things to do.

- Add full-text indexing
- Add some browse pages
- "Librify" (Tom Honeyman's term) so it can be included in notebooks or other workflows




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


## Example: COOEE corpus

There is a copy of the COOEE corpus as an RO-Crate in test_data/cooee


To create a sqlite database with table for RepositoryObject and Person data

```
make cooee
```

Try out making a tabular view which joins speaker data with other metadata and full text using a Datasette Custom SQL Query:

```
SELECT *
FROM Person 
JOIN RepositoryObject
on Person.name = RepositoryObject.author

```



