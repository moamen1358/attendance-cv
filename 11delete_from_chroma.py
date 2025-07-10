import chromadb

CHROMA_STORE_PATH = "./store"
COLLECTION_NAME = "face_recognition"

# Initialize ChromaDB client and collection
client = chromadb.PersistentClient(path=CHROMA_STORE_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)

def delete_by_id(ids):
    """Delete entries by their unique ChromaDB IDs."""
    collection.delete(ids=ids)
    print(f"Deleted IDs: {ids}")

def delete_by_name(name):
    """Delete all entries with a given name (metadata 'name')."""
    count = collection.count()
    if count == 0:
        print("Collection is empty.")
        return
    all_data = collection.get(limit=count)
    ids_to_delete = [idx for idx, meta in zip(all_data['ids'], all_data['metadatas']) if meta.get('name') == name]
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
        print(f"Deleted all entries with name: {name}")
    else:
        print(f"No entries found with name: {name}")

if __name__ == "__main__":
    # Example: Delete by ID
    ids_to_remove = [
        "6147e774-0ed0-40aa-a541-be1850e78fd2",
        "881521d9-479f-44ec-b8fc-312661050b32",
        "234ff391-393f-444a-906b-44049c921dbf",
        "386fc5c3-3eea-43dd-92b7-85a10c0876fc",
        "4bebf1dc-f456-4efa-8e06-86360b4db857",
        "c83d0222-d77b-4a92-9f3e-a0e68b4265b0"
    ]
    delete_by_id(ids_to_remove)

    # Example: Delete by name
    # delete_by_name("moa2")