import glob

renames = {
    "__init__": "__init__",  # No change needed; it's the constructor
    "get_url": "get_connection_url",
    "update_connection": "configure_connection",
    "connect": "establish_connection",
    "dump_schema": "export_schema_as_string",
    "get_current_schema": "fetch_current_schema",
    "list_databases": "retrieve_databases",
    "list_tables": "retrieve_tables",
    "create_database": "create_new_database",
    "delete_database": "remove_database",
    "get_table_contents": "fetch_table_data",
    "execute_custom_query": "run_query",
    "get_tables_and_fields_and_types": "retrieve_table_field_details",
    "get_tables_and_fields": "retrieve_table_field_names",
    "get_fields": "retrieve_fields_for_table",
    "export_table_to_parquet": "export_table_to_parquet_file",
    "export_db_to_parquet_dir": "export_database_to_parquet_directory",
    "import_parquet_to_table": "load_parquet_into_table",
    "imort_parquet_dir_to_db": "load_parquet_directory_into_database"
}


# Use glob to find all .py files recursively
for file in glob.glob("**/*.py", recursive=True):
    print(f"Processing file: {file}")
    # Open the file for reading
    if file != "rename.py":
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            # Perform the replacements
            for old, new in renames.items():
                old = old + "("
                new = new + "("
                text = text.replace(old, new)

        # Open the file for writing and save the changes
        with open(file, "w", encoding="utf-8") as f:
            f.write(text)
