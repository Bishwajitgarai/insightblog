from vespa.application import Vespa
from vespa.package import ApplicationPackage, Field, Schema, Document, HNSW, RankProfile
from app.core.config import get_settings
import asyncio

settings = get_settings()

class VespaService:
    def __init__(self):
        self.app_url = settings.VESPA_URL
        # In a real scenario, we would initialize the Vespa client here.
        # For this demo, we assume the app is deployed or we use HTTP requests.
        # We can use the pyvespa Vespa class to interact if we have the endpoint.
        self.client = Vespa(url=self.app_url)

    async def feed_content(self, content_id: str, fields: dict):
        # Async wrapper for synchronous pyvespa feed
        # response = self.client.feed_data_point(schema="content_item", data_id=content_id, fields=fields)
        # return response
        # For now, mocking the call as we might not have a running Vespa instance yet
        print(f"Feeding content {content_id} to Vespa: {fields.keys()}")
        return {"status": "success", "id": content_id}

    async def feed_user_profile(self, user_id: str, fields: dict):
        print(f"Feeding user {user_id} to Vespa: {fields.keys()}")
        return {"status": "success", "id": user_id}

    async def query_content(self, user_embedding: list[float], top_k: int = 10):
        # Construct YQL query for nearest neighbor search
        # yql = "select * from sources content_item where ({targetHits:10}nearestNeighbor(embedding,user_embedding))"
        # response = self.client.query(body={
        #     "yql": yql,
        #     "ranking.features.query(user_embedding)": user_embedding,
        #     "hits": top_k
        # })
        # return response.hits
        print(f"Querying Vespa with embedding length {len(user_embedding)}")
        return [
            {"id": "doc1", "fields": {"title": "Gen-AI Trends", "body": "..."}},
            {"id": "doc2", "fields": {"title": "FastAPI Guide", "body": "..."}}
        ]

    def create_package(self) -> ApplicationPackage:
        # Define the schema for deployment (utility function)
        return ApplicationPackage(
            name="insightblog",
            schema=[
                Schema(
                    name="content_item",
                    document=Document(
                        fields=[
                            Field(name="id", type="string", indexing=["summary", "attribute"]),
                            Field(name="title", type="string", indexing=["summary", "index"]),
                            Field(name="body", type="string", indexing=["summary", "index"]),
                            Field(name="embedding", type="tensor<float>(x[1536])", indexing=["attribute", "index", "summary"], attribute=["distance-metric: angular"])
                        ]
                    ),
                    rank_profiles=[
                        RankProfile(
                            name="default",
                            first_phase="closeness(field, embedding)"
                        )
                    ]
                )
            ]
        )

vespa_service = VespaService()
