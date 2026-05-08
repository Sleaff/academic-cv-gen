import os
import openai
import requests
import time
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from loguru import logger

from dotenv import load_dotenv
load_dotenv()

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
USER_AGENT = "AcademicCVGenerator"
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

def execute_sparql(query: str):
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json'}
    resp = requests.get(WIKIDATA_SPARQL_URL, params={'query': query, 'format': 'json'}, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Wikidata error: {resp.status_code}")
        return []
    return resp.json().get('results', {}).get('bindings', [])

def format_for_llm(raw_sparql: dict) -> dict:
    cleaned_data = {"name": raw_sparql.get("name", "Unknown")}
    
    for section, items in raw_sparql.items():
        if section == "name":
            continue
            
        cleaned_list = []
        for item in items:
            clean_item = {}
            for key, data_dict in item.items():
                value = data_dict.get("value", "")
                
                if value.startswith("http://www.wikidata.org/entity/"):
                    continue
                
                if "T00:00:00Z" in value:
                    value = value.replace("T00:00:00Z", "")
                    
                clean_item[key] = value
            
            if clean_item and clean_item not in cleaned_list:
                cleaned_list.append(clean_item)
                
        cleaned_data[section] = cleaned_list
        
    return cleaned_data

def get_researcher_data(qid: str):
    queries = {
        "education": f"""
            SELECT ?name ?educationLabel ?degreeLabel ?eduStart ?eduEnd WHERE {{
            BIND(wd:{qid} AS ?researcher)
            ?researcher rdfs:label ?name . FILTER(LANG(?name) = "en")
            ?researcher p:P69 ?eduStatement . ?eduStatement ps:P69 ?education .
            OPTIONAL {{ ?eduStatement pq:P512 ?degree . }}
            OPTIONAL {{ ?eduStatement pq:P580 ?eduStart . }}
            OPTIONAL {{ ?eduStatement pq:P582 ?eduEnd . }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }} ORDER BY DESC(?eduEnd) DESC(?eduStart)
        """,
        "employment": f"""
            SELECT ?name ?employerLabel ?roleLabel ?empStart ?empEnd WHERE {{
            BIND(wd:{qid} AS ?researcher)
            ?researcher rdfs:label ?name . FILTER(LANG(?name) = "en")
            ?researcher p:P108 ?empStatement . ?empStatement ps:P108 ?employer .
            OPTIONAL {{ ?empStatement pq:P39 ?role . }}
            OPTIONAL {{ ?empStatement pq:P580 ?empStart . }}
            OPTIONAL {{ ?empStatement pq:P582 ?empEnd . }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }} ORDER BY DESC(?empStart)
        """,
        "awards": f"""
            SELECT ?name ?awardLabel ?awardDate WHERE {{
            BIND(wd:{qid} AS ?researcher)
            ?researcher rdfs:label ?name . FILTER(LANG(?name) = "en")
            ?researcher p:P166 ?awardStatement . ?awardStatement ps:P166 ?award .
            OPTIONAL {{ ?awardStatement pq:P585 ?awardDate . }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }} ORDER BY DESC(?awardDate)
        """,
        "supervision": f"""
            SELECT ?role ?personLabel WHERE {{
            BIND(wd:{qid} AS ?researcher)
            {{ ?researcher wdt:P185 ?person . BIND("Supervised Student" AS ?role) }}
            UNION
            {{ ?researcher wdt:P184 ?person . BIND("Academic Advisor" AS ?role) }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
        """,
        "collaborations": f"""
            SELECT DISTINCT ?coauthorLabel WHERE {{
            BIND(wd:{qid} AS ?researcher)
            ?work wdt:P50 ?researcher .
            ?work wdt:P50 ?coauthor .
            FILTER(?coauthor != ?researcher)
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }} LIMIT 50
        """,
        "track_record": f"""
            SELECT DISTINCT ?workLabel ?date WHERE {{
            BIND(wd:{qid} AS ?researcher)
            ?work wdt:P50 ?researcher .
            OPTIONAL {{ ?work wdt:P577 ?date . }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }} ORDER BY DESC(?date) LIMIT 50
        """
    }

    logger.info(f"Querying wikidata for QID: {qid}")
    results = {}
    for key, q in queries.items():
        results[key] = execute_sparql(q)
        logger.info(f"Fetched {len(results[key])} results for {key}")
        time.sleep(1)
    
    name = "Unknown"
    for res in results.values():
        if res and "name" in res[0]:
            name = res[0]["name"]["value"]
            break

    raw_data = {
        "name": name,
        "education": results["education"],
        "employment": results["employment"],
        "awards": results["awards"],
        "supervision": results["supervision"],
        "collaborations": results["collaborations"],
        "track_record": results["track_record"]
    }

    return format_for_llm(raw_data)

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

@app.post("/api/v1/generate/{wikidata_qid}")
def generate_cv(wikidata_qid: str, previous_cv: UploadFile = File(None)):
    profile = get_researcher_data(wikidata_qid)
    if not profile:
        raise HTTPException(status_code=404, detail="Researcher not found or no data available.")
    logger.info(f"Generating CV for {profile['name']} (QID: {wikidata_qid}) with previous CV: {previous_cv.filename if previous_cv else 'None'}")
    logger.debug(f"Wikidata profile data: {profile}")
    
    # TODO: Extract text from uploaded PDF
    previous_cv_text = ""
    if previous_cv:
        pass

    system_instruction = """You are an expert academic consultant specializing in the Independent Research Fund Denmark (DFF) 2026 call. 
    Your task is to draft a narrative CV following the CoARA principles and DFF B20/B21 templates.
    Strict Constraints:
    1. Do NOT include H-index, Impact Factors, or other bibliometrics (only citations allowed).
    2. Focus on narrative descriptions of impact, scientific quality, and leadership.
    3. Format into mandatory categories: Research Statement, Career, Grants/Awards, Supervision & Leadership, Community Contributions, and a B21 Track Record (last 10 years)."""

    user_prompt = f"""
    Draft a DFF 2026 narrative CV using this Wikidata profile:
    
    Name: {profile['name']}
    Date of Birth: {profile['dob']}
    Employers: {', '.join(profile['employers'])}
    Education: {', '.join(profile['education'])}
    Awards: {', '.join(profile['awards'])}
    Mentored Students: {', '.join(profile['students'])}
    Memberships: {', '.join(profile['memberships'])}
    
    Publications (Past 10 Years):
    {chr(10).join('- ' + p for p in profile['publications'])}
    """

    # TODO: If previous_cv_text is available, include it in the prompt to guide the LLM in improving the existing CV draft.
    if previous_cv_text:
        user_prompt += f"\n\nAdditionally, incorporate relevant narrative details from the applicant's previous CV:\n{previous_cv_text}"

    messages = [
        ChatMessage(role="system", content=system_instruction),
        ChatMessage(role="user", content=user_prompt)
    ]

    cv_text = call_llm(messages)
    
    return {
        "cv_draft": cv_text,
        "raw_data": profile
    }