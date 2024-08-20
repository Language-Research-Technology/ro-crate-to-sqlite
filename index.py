import click
from rocrate.rocrate import ROCrate
from pathlib import Path
from sqlite_utils import Database
import sqlite3
import re

file_path = "your_text_file.txt"
output_folder = "output_ro_crate/"

# Create an RO-Crate instance


@click.command()
@click.option("--db", default="ro-crate-metadata.db", prompt="Database", help="name of the output database")
@click.option("--rocrate", prompt="Path to RO-Crate directory", help="A path to an RO-Crates directory")

def build(db, rocrate):
    """Load a list of paths to RO-Crates"""
    
    data = Database(db, recreate=True)
    # Set up some tables
    entities = data["entities"]
    root_table = data["root"]
    properties = data["properties"]


    file_table = data["files"]

    crate_path = rocrate;
    crate = ROCrate(crate_path)
    root = crate.root_dataset
 
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
                value =  val
                url = ""
                if isinstance(val,dict):
                    this_id = val.get("@id")
                    t = crate.get(this_id)
                    if t:
                        target = val.get("@id")
                        value = t.get("name") or val
                    elif  re.match("http(s?)://", this_id):
                        url = this_id
                        
                #elif not target and re.match("http(s?)://", val):
                #    url = val


                
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

    entities.insert_all(entityList, pk="@id", alter=True)#, foreign_keys=[   ("sourceOf", "properties", "source")])

    properties.insert_all(propList, pk="@id", alter=True, foreign_keys=[("source", "entities", "@id"),("target", "entities", "@id")])
    root_table.insert({"id": root.properties()["@id"]})
    #speakers.insert_all(speaker_array, pk="id", alter=True)


def asList(thing):
    if not thing:
        return []
    if not isinstance(thing, list):
        return [thing]
    return thing


if __name__ == '__main__':
    build()
