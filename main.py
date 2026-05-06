import os
import openai
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from dotenv import load_dotenv
load_dotenv()

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
USER_AGENT = "AcademicCVGenerator/0.1 (DTU course project)"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lmstudio")

if LLM_PROVIDER == "lmstudio":
    LLM_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
    LLM_MODEL = os.getenv("LMSTUDIO_MODEL", "google/gemma-4-26b-a4b")
    LLM_API_KEY = os.getenv("LMSTUDIO_API_KEY", "lm-studio")
else:
    LLM_BASE_URL = os.getenv("CAMPUSAI_BASE_URL", "https://chat.campusai.compute.dtu.dk/api")
    LLM_MODEL = os.getenv("CAMPUSAI_MODEL", "Gemma 4")
    LLM_API_KEY = os.getenv("CAMPUSAI_API_KEY", "your-campusai-key")


app = FastAPI(
	title="Academic CV Generator API",
	version="0.1.0",
	description="Builds a starter academic CV from Wikidata and simple user preferences.",
)


class ChatMessage(BaseModel):
    role: str = Field(..., examples=["system", "user"])
    content: str = Field(..., examples=["You are an academic CV assistant."])


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ..., 
        examples=[
            [
                {"role": "system", "content": "You are an academic CV assistant."},
                {"role": "user", "content": "Draft a CV summary for a professor in NLP."},
            ]
        ],
    )

class ChatSimpleRequest(BaseModel):
    instructions: str = Field(..., examples=["Be friendly and concise."])
    input: str = Field(..., examples=["hello"])


def get_llm_client() -> openai.OpenAI:
    return openai.OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
    )


def call_llm(messages: list[ChatMessage]) -> str:
    client = get_llm_client()

    completion = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[message.model_dump() for message in messages],
    )

    if not completion.choices:
        raise HTTPException(status_code=502, detail="LLM response did not include any choices")

    message = completion.choices[0].message
    if message is None or message.content is None:
        raise HTTPException(status_code=502, detail="LLM response did not include message content")

    return message.content

def simple_call_llm(instructions: str, input: str):
    client = get_llm_client()
    response = client.responses.create(
        model=LLM_MODEL,
        instructions=instructions,
        input=input,
    )

    return response.output_text


def get_researcher_data(qid):
    query = f"""
    SELECT ?name ?orcid ?eduLabel ?awardLabel ?pubLabel WHERE {{
      BIND(wd:{qid} AS ?person)
      ?person rdfs:label ?name. FILTER(LANG(?name) = "en")

      OPTIONAL {{ ?person wdt:P496 ?orcid. }}
      
      OPTIONAL {{
        ?person wdt:P69 ?edu.
        ?edu rdfs:label ?eduLabel. FILTER(LANG(?eduLabel) = "en")
      }}
      
      OPTIONAL {{
        ?person wdt:P166 ?award.
        ?award rdfs:label ?awardLabel. FILTER(LANG(?awardLabel) = "en")
      }}

      OPTIONAL {{
        ?pub wdt:P50 ?person.
        ?pub rdfs:label ?pubLabel. FILTER(LANG(?pubLabel) = "en")
      }}
    }}
    """
    headers = {
        'User-Agent': 'AcademicCVGenerator',
        'Accept': 'application/json'
    }

    resp = requests.get(
        WIKIDATA_SPARQL_URL, 
        params={'query': query, 'format': 'json'},
        headers=headers
    )

    if resp.status_code != 200:
        print(f"Error from Wikidata: {resp.status_code}")
        print(resp.text) # This will show you the HTML error causing the crash
        return None

    response = resp.json()
    
    bindings = response.get('results', {}).get('bindings', [])
    
    if not bindings:
        return None

    cv_data = {
        "name": bindings[0].get("name", {}).get("value"),
        "orcid": bindings[0].get("orcid", {}).get("value"),
        "education": set(),
        "awards": set(),
        "publications": set()
    }

    for row in bindings:
        if "eduLabel" in row:
            cv_data["education"].add(row["eduLabel"]["value"])
        if "awardLabel" in row:
            cv_data["awards"].add(row["awardLabel"]["value"])
        if "pubLabel" in row:
            cv_data["publications"].add(row["pubLabel"]["value"])

    return {
        "name": cv_data["name"],
        "orcid": cv_data["orcid"],
        "education": sorted(list(cv_data["education"])),
        "awards": sorted(list(cv_data["awards"])),
        "publications": sorted(list(cv_data["publications"])),
    }


@app.post("/api/v1/chat")
def chat(request: ChatRequest):
    return {"response": call_llm(request.messages)}

@app.post("/api/v1/chat-simple")
def chat_simple(request: ChatSimpleRequest):
    return {"response": simple_call_llm(request.instructions, request.input)}

@app.post("/api/v1/research/{wikidata_qid}")
def research(wikidata_qid: str):
    profile = get_researcher_data(wikidata_qid)
    return profile

@app.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}
