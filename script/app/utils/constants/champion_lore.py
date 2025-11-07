from app.data_extraction.fetch_from_s3 import fetch_data_from_s3

def get_lore(name):
    name = name.replace(" ", "_")
    lore = fetch_data_from_s3(name, "background")
    return lore