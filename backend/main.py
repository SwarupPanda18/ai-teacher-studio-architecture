from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from teacher_agent import plan_lesson, evaluate_student_answer, get_fallback_completion
from rag_engine import process_document_and_get_context

app = FastAPI(title="AI Teacher Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/start-lesson")
async def start_lesson(
    topic: str = Form(""),
    level: str = Form("Beginner"),
    time_limit: str = Form("10 mins"),
    language: str = Form("English"),
    file: UploadFile = File(None)
):
    relevant_context = ""
    
    if file:
        file_bytes = await file.read()
        # Runs the custom embedding, chunking, and cosine similarity pipeline
        relevant_context = process_document_and_get_context(
            file_bytes=file_bytes,
            query=topic,
            k=3
        )
            
    lesson_plan = plan_lesson(
        context_text=relevant_context,
        topic=topic,
        level=level,
        time_limit=time_limit,
        language=language
    )
    return {"status": "success", "data": lesson_plan}

@app.post("/api/evaluate-response")
async def evaluate_response(
    question: str = Form(...),
    correct_answer: str = Form(...),
    student_answer: str = Form(...),
    language: str = Form("English")
):
    result = evaluate_student_answer(question, correct_answer, student_answer, language)
    return {"status": "success", "feedback": result}

@app.post("/api/final-report")
async def generate_final_report(
    student_performance_data: str = Form(...),
    topic: str = Form(...)
):
    prompt = f"""
    Based on this student's performance data during the {topic} lesson:
    {student_performance_data}
    
    Generate a final learning report in JSON format with these exact keys:
    {{
      "score_percentage": number,
      "concepts_understood": ["array of strings"],
      "weak_areas": ["array of strings"],
      "recommended_revision": "string explaining what to revise",
      "suggested_next_topic": "string (next logical step in learning path)"
    }}
    """
    report = get_fallback_completion(prompt)
    return {"status": "success", "report": report}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)