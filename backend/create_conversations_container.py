"""Create Conversations container in Cosmos DB."""
import asyncio
import os
from azure.cosmos.aio import CosmosClient
from dotenv import load_dotenv

load_dotenv()

async def create_container():
    endpoint = os.getenv("COSMOS_ENDPOINT")
    key = os.getenv("COSMOS_KEY")
    database_name = os.getenv("COSMOS_DATABASE_NAME", "SangikyoDB")
    
    async with CosmosClient(endpoint, key) as client:
        database = client.get_database_client(database_name)
        
        try:
            # Create Conversations container with partition key /id (serverless mode)
            container = await database.create_container(
                id="Conversations",
                partition_key={"paths": ["/id"], "kind": "Hash"}
            )
            print(f"✅ Created container: Conversations (partition key: /id)")
        except Exception as e:
            if "Conflict" in str(e):
                print("ℹ️  Container 'Conversations' already exists")
            else:
                print(f"❌ Error: {e}")
                raise

if __name__ == "__main__":
    asyncio.run(create_container())
