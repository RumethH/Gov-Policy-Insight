import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from backend.core.chains import RAGChain

app = FastAPI(title="ChatGPI Backend")

# Initialize the RAG chain
chain = RAGChain()

class ChatRequest(BaseModel):
    prompt: str
    conversation_id: str
    stream: bool = False

class ChatResponse(BaseModel):
    answer: str
    citations: List[dict]
    metadata: Optional[dict] = {}

class GreetingRequest(BaseModel):
    conversation_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, x_gemini_api_key: Optional[str] = Header(default=None)):
    api_key = x_gemini_api_key or None
    if request.stream:
        response = chain.run(request.prompt, stream=False, api_key=api_key)
        return ChatResponse(
            answer=response["answer"],
            citations=response["citations"],
            metadata=response.get("metadata") or {"mode": "api_fallback_from_stream"},
        )

    try:
        response = chain.run(request.prompt, stream=False, api_key=api_key)
        return ChatResponse(
            answer=response["answer"],
            citations=response["citations"],
            metadata=response.get("metadata") or {"mode": "api"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/greeting")
async def greeting(request: GreetingRequest):
    try:
        response = chain.llm.invoke(
            "Write one concise welcome message for chatGPI, a Government Policy "
            "Intelligence assistant specializing in NSW Government policies. "
            "Tone: calm, professional, and helpful. "
            "Max 35 words. Invite the user to ask a NSW policy question."
        )
        return {"greeting": response.content}
    except Exception:
        return {"greeting": "Hello, I am chatGPI. How can I help you with NSW policies today?"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
