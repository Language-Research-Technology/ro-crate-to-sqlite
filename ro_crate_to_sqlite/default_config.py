default_config = {
    "export-query": "SELECT * FROM RepositoryObject",

    "tables": {

        "RepositoryObject": {"all_props": [],  # All properties found for all RepositoryObject entities
                             "ignore_props": [],  # Properties to ignore
                             # Default properties to expand
                             "expand_props": ["citation"]},
        "Person": {"all_props": [], "ignore_props": [], "expand_props": []}
    }

}
