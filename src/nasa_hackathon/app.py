from collections.abc import AsyncGenerator
from ragbits.agents import Agent, ToolCallResult
from ragbits.chat.api import RagbitsAPI
from ragbits.chat.interface import ChatInterface
from ragbits.chat.interface.types import ChatContext, ChatResponse, LiveUpdateType
from ragbits.core.embeddings import LiteLLMEmbedder
from ragbits.core.llms import LiteLLM, ToolCall
from ragbits.core.prompt import ChatFormat
from ragbits.core.vector_stores import InMemoryVectorStore
from ragbits.core.vector_stores.qdrant import QdrantVectorStore
from ragbits.document_search import DocumentSearch
from ragbits.document_search.ingestion.parsers.router import DocumentParserRouter
from ragbits.document_search.documents.document import DocumentType
from ragbits.chat.interface.ui_customization import (
    UICustomization,
    HeaderCustomization,
    PageMetaCustomization
)

from qdrant_client import AsyncQdrantClient
from ragbits.document_search.ingestion.parsers.docling import DoclingDocumentParser

from docling.document_converter import DocumentConverter, MarkdownFormatOption
from docling.datamodel.base_models import InputFormat

embedder = LiteLLMEmbedder(model_name="azure/text-embedding-3-large")
#vector_store = InMemoryVectorStore(embedder=embedder)
vector_store = QdrantVectorStore(AsyncQdrantClient(), index_name="global", embedder=embedder)
from docling.datamodel.pipeline_options import ConvertPipelineOptions, PipelineOptions

format_options = {
    InputFormat.MD: MarkdownFormatOption(pipeline_options=ConvertPipelineOptions())
}
document_router_parser = DocumentParserRouter({
    DocumentType.MD: DoclingDocumentParser(format_options=format_options, ignore_images=True)
})
document_search = DocumentSearch(vector_store=vector_store, parser_router=document_router_parser)

llm = LiteLLM(model_name="azure/gpt-4.1-mini")
agent = Agent(llm=llm, tools=[document_search.search])

class MyChat(ChatInterface):
    ui_customization = UICustomization(
        # Header customization
        header=HeaderCustomization(
            title="NASA AI Assistant",
            subtitle="",
            logo="🚀"
        ),

        # Welcome message shown when chat starts
        welcome_message=(
            "Hello! I'm your AI assistant.\n\n"
            "How can I help you today? You can ask me **anything**! "
            "I can provide information, answer questions, and assist with various tasks."
        ),

        # Page metadata
        meta=PageMetaCustomization(
            favicon="🚀",
            page_title="NASA AI Assistant"
        )
    )

    async def setup(self) -> None:
        pass
        #await document_search.ingest("local://data/test.md")
        #await document_search.ingest("web://https://arxiv.org/pdf/1706.03762")

    async def chat(
        self,
        message: str,
        history: ChatFormat,
        context: ChatContext,
    ) -> AsyncGenerator[ChatResponse]:
        async for result in agent.run_streaming(message):
            match result:
                case str():
                    yield self.create_live_update(
                        update_id="1",
                        type=LiveUpdateType.START,
                        label="Answering...",
                    )
                    yield self.create_text_response(result)
                case ToolCall():
                    yield self.create_live_update(
                        update_id="2",
                        type=LiveUpdateType.START,
                        label="Searching...",
                    )
                case ToolCallResult():
                    yield self.create_live_update(
                        update_id="2",
                        type=LiveUpdateType.FINISH,
                        label="Search",
                        description=f"Found {len(result.result)} relevant chunks.",
                    )

        yield self.create_live_update(
            update_id="1",
            type=LiveUpdateType.FINISH,
            label="Answer",
        )

import asyncio

async def ingest():
    await document_search.ingest("local://data/test.md")

if __name__ == "__main__":
    #asyncio.run(ingest())
    api = RagbitsAPI(MyChat)
    api.run()