import click
import ro_crate_to_sqlite


@click.command()
@click.option("--dbname", default="ro-crate-metadata.db", prompt="Database", help="name of the output database")
@click.option("--rocrate", prompt="Path to RO-Crate directory", help="A path to an RO-Crates directory")
@click.option("--flatten", is_flag=True, help="Flatten the entities table")
@click.option("--csv", is_flag=True, help="Treat indexableText as CSV files to be concatenated into a new table")
def build(dbname, rocrate, flatten=False, csv=False):
    ro_crate_to_sqlite.build(dbname, rocrate, flatten=flatten, csv=csv)


if __name__ == '__main__':
    build()
