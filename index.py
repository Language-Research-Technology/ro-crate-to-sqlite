import click
from rocrate.rocrate import ROCrate
from sqlite_utils import Database
import json
import os
import re

file_path = "your_text_file.txt"
output_folder = "output_ro_crate/"

# Create an RO-Crate instance


@click.command()
@click.option("--db", default="ro-crate-metadata.db", prompt="Database", help="name of the output database")
@click.option("--rocrate", prompt="Path to RO-Crate directory", help="A path to an RO-Crates directory")
@click.option("--flatten", is_flag=True, help="Flatten the entities table")
def build(db, rocrate, flatten=False):
    print("flattening", flatten)
    # File path for the configuration file
    config_file = f'{db}-config.json'

    # Load or create the configuration file
    if not os.path.exists(config_file):
        # Default configuration
        default_config = {
            "tables": {

                "RepositoryObject":  {"all_props": [],  # All properties found for all RepositoryObject entities
                                      "ignore_props": [],  # Properties to ignore
                                      # Default properties to expand
                                      "expand_props": ["citation"]},
                "Person": {"all_props": [], "ignore_props": [], "expand_props": []}
            }

        }
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        print(f"Created default config file: {config_file}")

    # Read configuration
    with open(config_file, 'r') as f:
        config = json.load(f)

    """Load a list of paths to RO-Crates"""
    print("Building database")
    data = Database(db, recreate=True)
    # Set up some tables
    entities = data["entities"]
    root_table = data["root"]
    properties = data["properties"].create(
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
        types = asList(entity["@type"])
        types.sort()
        for prop in entity:
            for val in asList(entity[prop]):
                target = ""
                value = val
                url = ""
                if isinstance(val, dict):
                    this_id = val.get("@id")
                    t = crate.get(this_id)
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
                        "target":  target,
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
    print(data.schema)
    if flatten:
        flatten_entities(data, config, config_file, rocrate)


def flatten_entities(db, main_config, config_file, rocrate):
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
        config  = main_config['tables'][table]
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
                property_target = prop['target']
                props.append(property_name)

                if property_name == 'indexableText':
                    # Check if the value is a valid file name
                    text_file = os.path.join(rocrate, property_target)
                    if os.path.isfile(text_file):
                        # Read the text from the file
                        with open(text_file, 'r') as f:
                            text = f.read()
                        # Add the text to the entity_data dictionary
                        entity_data[property_name] = text
                    else:
                        print(f"File not found: {text_file}")

                # If the property is in the props_to_expand list, expand it
                if property_name in config['expand_props'] and property_target:
                    # Query to get the
                    sub_query = f"""
                        SELECT p.name, p.value
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
                            setProperty(
                                entity_data, expanded_property_name,  expanded_prop['value'])
                else:
                    # If it's a normal property, just add it to the entity_data dictionary
                    if property_name not in config['ignore_props']:
                        setProperty(entity_data, property_name, property_value)

            config['all_props'] = list(set(config['all_props'] + props))
            # Step 4: Insert the flattened properties into the 'flat_entites' table

            db[f'{table}'].insert(entity_data, pk="@id", replace=True, alter=True),

    print("Flattened entities table created")
    # Save the updated configuration file
    with open(config_file, 'w') as f:
        json.dump(main_config, f, indent=4)
    print(f"Updated config file: {config_file}, edit this file to change the flattening configuration or deleted it to start over")


def setProperty(entity_data, property_name, property_value):
    if property_name in entity_data:
        # Find the first available integer to append to property_name
        i = 1
        while f"{property_name}_{i}" in entity_data:
            i += 1
        property_name = f"{property_name}_{i}"
    entity_data[property_name] = property_value


def asList(thing):
    if not thing:
        return []
    if not isinstance(thing, list):
        return [thing]
    return thing


if __name__ == '__main__':
    build()
