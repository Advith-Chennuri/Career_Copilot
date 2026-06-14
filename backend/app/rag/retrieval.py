import logging
from typing import List, Dict, Any
from app.rag.chroma_client import get_kb_collection
from app.rag.embeddings import get_embedding
from app.utils.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)

def retrieve_context(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Queries ChromaDB to find the top k most semantically relevant text chunks
    matching the user query.
    """
    try:
        collection = get_kb_collection()
        
        # Guard clause if the vector database collection is completely empty
        if collection.count() == 0:
            logger.info("ChromaDB knowledge base collection is currently empty.")
            return []
            
        # Convert text query into search vector
        query_vector = get_embedding(query)
        
        # Perform cosine-similarity matching in ChromaDB
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        
        contexts = []
        if results and results.get("documents") and results["documents"][0]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
            
            for idx in range(len(documents)):
                contexts.append({
                    "text": documents[idx],
                    "source": metadatas[idx].get("source", "Unknown Notes File"),
                    "chunk_index": metadatas[idx].get("chunk_index", 0)
                })
                
        return contexts
    except Exception as e:
        logger.exception("Error executing vector query in ChromaDB")
        return []

def get_mock_grounded_response(query: str, contexts: List[Dict[str, Any]]) -> str:
    """
    Synthesizes a response locally using retrieved context strings
    to support offline validation or handle quota limits gracefully.
    """
    if not contexts:
        return f"Offline Mock Response: I couldn't find any reference materials in your notes matching '{query}'."

    # Compile a response by joining the matching statements
    bullet_points = []
    keywords = [w.lower().strip("?,.!") for w in query.split() if len(w) > 3]
    for ctx in contexts:
        text = ctx["text"]
        for line in text.split("\n"):
            line_strip = line.strip(" -*=•").strip()
            if not line_strip:
                continue
            # If any keyword matches the line, add it
            if any(kw in line_strip.lower() for kw in keywords):
                bullet_points.append(line_strip)

    # Deduplicate matching bullet points
    bullet_points = list(dict.fromkeys(bullet_points))[:5]

    if bullet_points:
        bullets_str = "\n".join([f"- {pt}" for pt in bullet_points])
        return (
            f"Grounded Response (Offline Fallback):\n\n"
            f"{bullets_str}\n\n"
            f"*(Note: This response was generated locally because your Gemini API free quota limit (429) was reached. "
            f"The sources below were correctly retrieved from your local ChromaDB store.)*"
        )
    else:
        # Fallback if no specific lines matched
        summaries = [ctx["text"][:180] + "..." for ctx in contexts]
        summary_str = "\n\n".join([f"• From {c['source']} (Part {c['chunk_index']}):\n  {s}" for c, s in zip(contexts, summaries)])
        return (
            f"Grounded Response (Offline Fallback):\n\n"
            f"{summary_str}\n\n"
            f"*(Note: This response was generated locally because your Gemini API free quota limit (429) was reached. "
            f"The sources below were correctly retrieved from your local ChromaDB store.)*"
        )

def query_knowledge_assistant(query: str, top_k: int = 4) -> Dict[str, Any]:
    """
    Retrieves candidate context, builds a grounded prompt template,
    and uses Gemini to answer the user query based strictly on retrieved notes.
    """
    contexts = retrieve_context(query, top_k)
    
    # Format the open-book contexts
    if not contexts:
        context_str = "No local study notes match this query. Explain based on general knowledge, but explicitly note that the answer is not grounded in local notes."
    else:
        context_blocks = []
        for idx, ctx in enumerate(contexts):
            context_blocks.append(
                f"--- Reference Document: {ctx['source']} (Part {ctx['chunk_index']}) ---\n"
                f"{ctx['text']}"
            )
        context_str = "\n\n".join(context_blocks)
        
    try:
        client = get_gemini_client()
        
        prompt = f"""
        You are a supportive, knowledgeable AI Career Mentor and technical interviewer.
        Your goal is to answer the student's question utilizing their uploaded notes context.
        Ground your answers directly in their reference materials. 
        If the notes do not discuss the topic, answer using your general knowledge but add a friendly disclaimer stating that the answer was not found in their uploaded materials.
        
        Student Notes Reference Context:
        {context_str}
        
        Student Question:
        {query}
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.3
            }
        )
        
        return {
            "answer": response.text,
            "sources": contexts
        }
        
    except ValueError as ve:
        logger.warning(f"Gemini client unavailable ({ve}). Falling back to offline template.")
        # Return offline validation placeholder
        mock_answer = get_mock_grounded_response(query, contexts)
        return {
            "answer": mock_answer,
            "sources": contexts
        }
    except Exception as e:
        logger.exception("Error during grounded generation (falling back to mock grounded response)")
        mock_answer = get_mock_grounded_response(query, contexts)
        return {
            "answer": mock_answer,
            "sources": contexts
        }

