import json
import os
import re
import csv as csvlib
from rocrate.rocrate import ROCrate
from sqlite_utils import Database

from .default_config import default_config


def build(dbname, rocrate, flatten=False, csv=False):
    config_file = f'{dbname}-config.json'
    if not os.path.exists(config_file):
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
    with open(config_file, 'r') as f:
        config = json.load(f)
    db = Database(dbname, recreate=True)
    # Set up some tables
    entities = db["entities"]
    root_table = db["root"]
    properties = db["properties"].create(
        {"source": str, "source_name": str, "source_types": str, "name": str, "target": str, "url": str, "value": str})

    crate_path = rocrate
    crate = ROCrate(crate_path)
    root = crate.root_dataset

    # Build the database - entities and properties
    # Entity table contains basic finder and summary information about the entity (this is redundant with the properties table)
    # Properties table contains all properties of in the RO-Crate graph this is sufficient to represent the graph
    # The root table contains the id of the root data entity in the RO-Crate graph -- so we can easily query for the root entity
    entityList = []
    propList = []
    for ent in crate.get_entities():
        entity = ent.as_jsonld()
        entity_name = entity.get("name") or entity["@id"]
        types = as_list(entity["@type"])
        types.sort()
        for prop in entity:
            for val in as_list(entity[prop]):
                target = ""
                value = val
                url = ""
                if isinstance(val, dict):
                    this_id = val.get("@id")
                    try:
                        t = crate.get(this_id)
                    except:
                        t = None
                        print(f"Could not find {this_id} in {entity['@id']}")
                    if t:
                        target = val.get("@id")
                        value = t.get("name") or val
                    elif re.match("http(s?)://", this_id):
                        url = this_id

                propList.append(
                    {
                        "source": entity["@id"],
                        "source_name": entity_name,
                        "source_types": types,
                        "name": prop,
                        "target": target,
                        "url": url,
                        "value": value
                    })

            e = {
                "@id": entity["@id"],
                "name": entity_name,
                "types": types
            }
        entityList.append(e)

    entities.insert_all(entityList, pk="@id", alter=True,
                        foreign_keys=[("sourceOf", "properties", "source")])
    properties.insert_all(propList, pk="@id", alter=True, foreign_keys=[
        ("source", "entities", "@id"), ("target", "entities", "@id")])
    root_table.insert({"id": root.properties()["@id"]})
    print("Database built")
    # print(db.schema)
    if flatten:
        flatten_entities(db, dbname, config, config_file, rocrate, csv)


def flatten_entities(db, dbname, main_config, config_file, rocrate, csv):
    print("Building flat tables")
    for table in main_config['tables']:
        # Step 1: Query to get list of @id for entities with @type = table
        print(f"Flattening table for entites of type: {table}")
        repository_objects = db.query(f"""
            SELECT e.[@id]
            FROM entities e
            JOIN properties p ON e.[@id] = p.source
            WHERE p.name = '@type' AND p.value = '{table}'
        """)
        config = main_config['tables'][table]
        # Convert the result to a list of @id values
        entity_ids = [row['@id'] for row in repository_objects]

        # Step 2: For each @id, retrieve all its associated properties
        for entity_id in entity_ids:
            # Query to get all properties for the specific @id
            properties = db.query(f"""
                SELECT p.name, p.value, p.target
                FROM properties p
                WHERE p.source = '{entity_id.replace("'", "''")}'
            """)

            # Create a dictionary to hold the properties for this entity
            entity_data = {}

            # Step 3: Loop through properties and add them to entity_data
            props = []
            for prop in properties:
                property_name = prop['name']
                property_value = prop['value']
                # ID of the target entity
                property_target = prop['target']
                props.append(property_name)

                if property_name == 'indexableText':
                    print("indexableText", property_target, property_value)
                    # Check if the value is a valid file name

                    ### HACK: Work around for the fact that the RO-Crate libary does not import File entities it does not like
                    if not property_target:
                        p = json.loads(property_value)
                        property_target = p.get("@id")

                    text_file = os.path.join(rocrate, property_target)
                    if os.path.isfile(text_file):
                        # Read the text from the file
                        with open(text_file, 'r') as f:
                            text = f.read()
                        # Add the text to the entity_data dictionary
                        entity_data[property_name] = text
                        if csv:
                            # Check if the text is a CSV file
                            if text_file.endswith('.csv'):
                                # Add the CSV file to the database
                                add_csv(db, text_file, f"{table}_csv", property_target)
                    else:
                        print(f"File not found: {text_file}")

                # If the property is in the props_to_expand list, expand it
                if property_name in config['expand_props'] and property_target:
                    # Query to get the
                    sub_query = f"""
                        SELECT p.name, p.value, p.target
                        FROM properties p
                        WHERE p.source = '{property_target.replace("'", "''")}' 
                    """
                    expanded_properties = db.query(sub_query)

                    # Add each sub-property (e.g., author.name, author.age) to the entity_data dictionary
                    # Is this the indexableText property?

                    for expanded_prop in expanded_properties:
                        expanded_property_name = f"{property_name}.{expanded_prop['name']}"
                        props.append(expanded_property_name)
                        # Special case - if this is indexable text then we want to read t

                        if expanded_property_name not in config['ignore_props']:
                            set_property(
                                entity_data, expanded_property_name, expanded_prop['value'])
                            if expanded_prop['target']:
                                set_property(
                                    entity_data, f"{expanded_property_name}_id", expanded_prop['target'])
                else:
                    # If it's a normal property, just add it to the entity_data dictionary
                    if property_name not in config['ignore_props']:
                        set_property(entity_data, property_name, property_value)
                        if property_target:
                            set_property(entity_data, f"{property_name}_id", property_target)

            config['all_props'] = list(set(config['all_props'] + props))
            # Step 4: Insert the flattened properties into the 'flat_entites' table

            db[f'{table}'].insert(entity_data, pk="@id", replace=True, alter=True),

    # Save the updated configuration file
    with open(config_file, 'w') as f:
        json.dump(main_config, f, indent=4)
    print(
        f"Updated config file: {config_file}, edit this file to change the flattening configuration or deleted it to start over")
    # export "main" csv

    # run a query to get the "main" export for this dataset
    query = main_config['export-query']

    result = list(db.query(query))
    # Convert result into a CSV file using csv writer
    csv_file = f"{dbname}-output.csv"
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csvlib.DictWriter(csvfile, fieldnames=result[0].keys(), quoting=csvlib.QUOTE_MINIMAL)
        writer.writeheader()
        for row in result:
            for key, value in row.items():
                if isinstance(value, str):
                    row[key] = value.replace('\n', '\\n').replace('\r', '\\r')
            writer.writerow(row)

    print(f"Exported data to {csv_file}")


def set_property(entity_data, property_name, property_value):
    if property_name in entity_data:
        # Find the first available integer to append to property_name
        i = 1
        while f"{property_name}_{i}" in entity_data:
            i += 1
        property_name = f"{property_name}_{i}"
    entity_data[property_name] = property_value


def as_list(thing):
    if not thing:
        return []
    if not isinstance(thing, list):
        return [thing]
    return thing


def add_csv(db, csv_path, table_name, property_target):
    with open(csv_path, newline='') as f:
        reader = csvlib.DictReader(f)  # Use DictReader to read each row as a dictionary
        rows = list(reader)
        if rows:
            for row in rows:
                row['_file_id'] = property_target  # ID of the target entity

            # Insert rows into the table (the table will be created if it doesn't exist)
            db[table_name].insert_all(rows, alter=True, ignore=True)
            print(f"Added {len(rows)} rows to {table_name}")
