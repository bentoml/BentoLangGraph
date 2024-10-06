from typing import List

import os

from langchain_exa import ExaSearchRetriever
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool

EXA_API_KEY=os.environ.get("EXA_API_KEY")

@tool
def retrieve_web_content(query: str) -> List[str]:
    """
    A wrapper around Exa Search.
    Useful for when you need to retrieve web content to answer questions about current events, current weather, latest news, up-to-date information, etc. 
    Input should be a search query.
    """
    # Initialize the Exa Search retriever
    retriever = ExaSearchRetriever(k=5, highlights=True, exa_api_key=EXA_API_KEY, use_autoprompt=True)

    # Define how to extract relevant metadata from the search results
    document_prompt = PromptTemplate.from_template(
        """
    <source>
        <url>{url}</url>
        <highlights>{highlights}</highlights>
    </source>
    """
    )

    # Create a chain to process the retrieved documents
    document_chain = (
        RunnableLambda(
            lambda document: {
                "highlights": document.metadata.get("highlights", "No highlights"),
                "url": document.metadata["url"],
            }
        )
        | document_prompt
    )

    # Execute the retrieval and processing chain
    retrieval_chain = retriever | document_chain.map()

    # Retrieve and return the documents
    documents = retrieval_chain.invoke(query)
    return documents
