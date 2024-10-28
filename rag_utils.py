from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatAnthropic
import os
import logging

def create_vector_store(text):
    """Create a vector store from the document text."""
    try:
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)

        # Create embeddings and vector store
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.from_texts(chunks, embeddings)
        
        return vector_store
    except Exception as e:
        logging.error(f"Error creating vector store: {str(e)}")
        return None

def setup_rag_chain(vector_store, api_key):
    """Set up the RAG chain with conversation memory."""
    try:
        # Initialize the language model
        llm = ChatAnthropic(
            anthropic_api_key=api_key,
            model="claude-2.1",
            temperature=0.2
        )

        # Set up conversation memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Create the chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
            memory=memory,
            return_source_documents=True,
            verbose=True
        )

        return chain
    except Exception as e:
        logging.error(f"Error setting up RAG chain: {str(e)}")
        return None

