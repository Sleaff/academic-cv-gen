# Academic CV Generator using LLM and Knowledge Graphs
Kenneth Plum Toft - s195171
## Project Description
This project is a web service that automatically builds acadmic CVs by pulling data directly from Knowledge Graphs (Wikidata). Instead of a user typing everything in, the system uses SPARQL to fetch facts about a researcher, such as their publications, affiliation and awards. I will be using a Large Language Model (Gemma 4) to take this information and user related input, turning it into formal summeries, formatted in LaTeX, Markdown or PDF.

The main goal is to use "Graph-to-Text" generation to make sure the CV is grounded in real data, which helps stop the LLM from making up fake papers or titles.

## Tools and Technologies
- NLP & LLM: Gemma4 accessed via the DTU CampusAI/Ollama for text generation.
- Knowledge Graph: Wikidata as the primary data source, queried using SPARQL.
- Backend: FastAPI to handle web service logic
- Frontend: Simple React application or SPA
- Environment: Docker for containerization to ensure the service can run anywhere.
- Graph Management: rdflib for handling RDF data and triples.

## LLM Configuration
The API can run against either CampusAI or a local LM Studio server.

Set `LLM_PROVIDER=lmstudio` to use a local model, then configure:
- `LMSTUDIO_BASE_URL=http://localhost:1234/v1`
- `LMSTUDIO_MODEL=<your-local-model-name>`
- `LMSTUDIO_API_KEY=lm-studio` if your local server expects a key

Leave `LLM_PROVIDER` unset, or set it to `campusai`, to use the DTU CampusAI endpoint.

## Data Sources:
Wikidata
Scholia/Direct SPARQL

## API Description
The service runs in a Docker container and exposes a REST API.
- POST /api/v1/generate: Accepts a Wikidata QID, (possibly user input, like formed data) and returns a generated CV.
Temporary input example:
{
  "wikidata_id": "Q12345",
  "template": "academic_standard",
  "format": "pdf",
  "limit_publications": 5
}

Temporary output example:
{
  "status": "success",
  "download_url": "/files/cv_output.pdf",
}

- POST /api/v1/research: Accepts a Wikidata QID and return data related to the person from Wikidata.
Temporary input example:
{ 
    "wikidata_id": "Q42" 
}
Temporary output example
{
    "name": [],
    "affiliations": [],
    "publications": []
}

## CV Structural requirements (B20)
Using the DFF CV template
- Length: Maximum 3 pages.
- Formatting: Times New Roman, size 12.
  - Margins: At least 2 cm on all sides.
  - Line spacing 1,5.
Content Restriction: No links to external material.
  - No bibliometric indicators other than citations.

### Mandatory Content Sections
Name
Current Position(s)
Previous Positions
Education
Career Breaks: Manually input
Research Statement: Generate draft
Personal Context: Generate draft
Grants and Awards: Auto
Supervision, teaching and research leadership: Auto
Collaborations and teamwork: Auto
Contributions to the research community
Contributions to the wider society


Career Breaks: Document any periods of leave (maternity leave, sick leave, etc.).
Research Satement: A narrative description of your research profile and goals.
Personal Context: Factors that have influenced your research career.
Grants and Awards: Noteable fonding and honors.
Supervision, Teaching and Leadership: Evidence of your role in developing others managing projects.
Collaboration and Teamwork: Description of your national and international networks.
Contributions to the Research Community: Peer review, committee work, or organizing conferences.
Contributions to the Wider Society: Dissemination, patents, or policy work. 


## Testing
The project will include unit tests to verify:
- The SPARQL retrieval logic correctly identifies researcher entities.
- The FastAPI endpoints return the correct status code and file paths.
- (Optional) The LLM generation stays faithful to the retrieved triples.


## Example User Flow
1. Input: User enters a Wikidata QID (e.g., Q12345) into a search bar.
2. Review: The /search endpoint populates a "Data Review" section showing what the graph knows about them.
3. Configure: User selects "Limit to 5 papers" and "Format: PDF".
4. Generate: User clicks "Generate CV," triggering the /generate endpoint.
5. Download: The UI provides a direct download link for the final document.




## SPARQL queries

### Education
SELECT ?name ?educationLabel ?degreeLabel ?eduStart ?eduEnd
WHERE {
  BIND(wd:Q20980928 AS ?researcher)
  ?researcher rdfs:label ?name .
  FILTER(LANG(?name) = "en")

  ?researcher p:P69 ?eduStatement .
  ?eduStatement ps:P69 ?education .
  OPTIONAL { ?eduStatement pq:P512 ?degree . }
  OPTIONAL { ?eduStatement pq:P580 ?eduStart . }
  OPTIONAL { ?eduStatement pq:P582 ?eduEnd . }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?eduEnd) DESC(?eduStart)

### Employment
SELECT ?name ?employerLabel ?roleLabel ?empStart ?empEnd
WHERE {
  BIND(wd:Q20980928 AS ?researcher)
  ?researcher rdfs:label ?name .
  FILTER(LANG(?name) = "en")

  ?researcher p:P108 ?empStatement .
  ?empStatement ps:P108 ?employer .
  OPTIONAL { ?empStatement pq:P39 ?role . }
  OPTIONAL { ?empStatement pq:P580 ?empStart . }
  OPTIONAL { ?empStatement pq:P582 ?empEnd . }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?empStart)

### Awards and Grants
SELECT ?name ?awardLabel ?awardDate
WHERE {
  BIND(wd:Q20980928 AS ?researcher)
  ?researcher rdfs:label ?name .
  FILTER(LANG(?name) = "en")

  ?researcher p:P166 ?awardStatement .
  ?awardStatement ps:P166 ?award .
  OPTIONAL { ?awardStatement pq:P585 ?awardDate . }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?awardDate)


### Supervision
SELECT ?role ?personLabel 
WHERE {
  BIND(wd:Q20980928 AS ?researcher)
  
  {
    ?researcher wdt:P185 ?person .
    BIND("Supervised Student" AS ?role)
  }
  UNION
  {
    ?researcher wdt:P184 ?person .
    BIND("Academic Advisor" AS ?role)
  }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}

### Contributions to research community