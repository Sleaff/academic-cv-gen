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