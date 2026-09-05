import ollama
import json
from video_generator import generate_scene_images

def get_fallback_completion(prompt: str) -> dict:
    try:
        print("\n[+] Sending prompt to local OpenHermes model...")
        response = ollama.chat(model='openhermes', format='json', messages=[
            {
                'role': 'system', 
                'content': 'You output strictly raw valid JSON. No markdown, no explanations.'
            },
            {
                'role': 'user', 
                'content': prompt
            }
        ])
        
        raw_text = response['message']['content'].strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1).strip()
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3].strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```", "", 1).strip()
            
        return json.loads(raw_text)
        
    except json.JSONDecodeError as e:
        print(f"[-] JSON PARSING FAILED. Error: {str(e)}")
        return {"error": "Failed to parse JSON"}
    except Exception as e:
        print(f"[-] LOCAL LLM FAILED. Error: {str(e)}")
        return {"error": "Local AI server is unresponsive."}

def plan_lesson(context_text: str, topic: str, level: str, time_limit: str, language: str) -> dict:
    prompt = f"""
    Topic: {topic or 'Based on provided document'}
    Learner Level: {level} 
    Requested Duration: {time_limit} minutes
    Language: {language}
    Context: {context_text[:2000]}
    
    You are an AI teacher. Design an uninterrupted, cinematic lesson. 
    Format output strictly as JSON with this schema. Generate EXACTLY 4 scenes in the 'lesson_sections' array to match the story flow:
    {{
      "topic_title": "string",
      "lesson_sections": [
        {{
          "script": "A long paragraph of conversational speech for the teacher to speak for this scene.",
          "image_prompt": "A highly detailed visual description of what is happening in this exact moment. (e.g., 'Ancient humans huddled around a sparking fire in a dark cave, cinematic')"
        }}
      ],
      "final_quiz": [
        {{
          "question": "string",
          "options": ["A", "B", "C", "D"],
          "correct_option_index": 0
        }},
        {{
          "question": "string",
          "options": ["A", "B", "C", "D"],
          "correct_option_index": 1
        }}
      ]
    }}
    Ensure 'final_quiz' contains exactly 3 questions testing the material.
    """
    lesson_data = get_fallback_completion(prompt)

    if "lesson_sections" in lesson_data:
        # Extract all prompts and generate the images in bulk
        prompts = [section.get("image_prompt", "abstract educational background") for section in lesson_data["lesson_sections"]]
        image_paths = generate_scene_images(prompts)
        
        # Attach the generated image URLs back to the JSON payload for the frontend
        for i, section in enumerate(lesson_data["lesson_sections"]):
            if i < len(image_paths):
                section["image_url"] = image_paths[i]

    return lesson_data

def evaluate_student_answer(question: str, correct_answer: str, student_answer: str, language: str) -> dict:
    prompt = f"""
    Evaluate student response.
    Question: {question}
    Correct: {correct_answer}
    Student: {student_answer}
    Language: {language}
    
    Format output strictly as JSON: 
    {{"is_correct": boolean, "teacher_remediation": "string"}}
    """
    return get_fallback_completion(prompt)