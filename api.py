from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import the core function from your main module
from main import main

app = FastAPI(
    title="RetroSynthesisAgent API",
    description="API to run retrosynthetic analysis on chemical materials.",
    version="1.0.0"
)

class RetroRequest(BaseModel):
    material: str
    num_results: int
    alignment: bool = False
    expansion: bool = False
    filtration: bool = False
    retrieval_mode: str = "patent-paper"

class RetroResponse(BaseModel):
    status: str
    data: dict

@app.post("/retro-synthesis/", response_model=RetroResponse)
async def retro_synthesis(req: RetroRequest):
    """
    Run retrosynthetic analysis for the given material.

    - **material**: The target material name (e.g., chlorothiophene)
    - **num_results**: Number of PDF results to download and process
    - **alignment**: Whether to perform entity alignment
    - **expansion**: Whether to expand the reaction tree with additional literature
    - **filtration**: Whether to filter reactions/pathways
    - **retrieval_mode**: Document retrieval mode (patent-patent, paper-paper, paper-patent, patent-paper)
    """
    try:
        result = main(
            material=req.material,
            num_results=req.num_results,
            alignment=req.alignment,
            expansion=req.expansion,
            filtration=req.filtration,
            retrieval_mode=req.retrieval_mode
        )
        return {"status": "success", "data": result}
    except Exception as e:
        # Log error or handle specifically if needed
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/", response_model=dict)
async def root():
    return {"message": "RetroSynthesisAgent API is running."}
