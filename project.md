Project
=======

Requirements
------------
The project:

- Must include elements from the course: natural language
processing, large language models and/or knowledge graphs.
- Must include a Python-based Web service in a docker container.
- Should be sufficiently complex for a four week period. 
- Should contain tests in the form of unit tests.
- Can include a Web application for human interaction.

The Web service must be able to run on another Linux computer than
your own. If you are constructing a Web service that uses special
data, then provide a dataset (which may be small and/or fictitious).

If your Web service uses an LLM API, it must be runnable via
CampusAI. You must not add your API key to the repository, but 
instead set up the API key outside the repository in the .env file
that should then be loaded via dotenv.

If you use external services, we expect that you behave in accordance
with terms of service and good Internet practice. This includes
setting an appropriate User-Agent for Web requests, honoring 
robots.txt, retry-after and rate limit. 

Minimum technical components
----------------------------
The project must expose functionality through one or more API
endpoints and include a non-trivial data processing pipeline. 

The project must include at least two of the following components:
- NLP preprocessing or extraction (e.g., PDF -> text, entity recognition)
- Use of an LLM (via API or local model)
- Information retrieval (sparse/dense/hybrid)
- Knowledge graph construction, querying, or entity linking

README.md
---------
- The README.md in the handin must include:
  - Description of the project
  - System architecture (diagram optional)
  - How to run (including Docker)
  - API documentation (endpoints)
  - Description of dataset
  - Evaluation/results (quantitative and/or qualitative)

This could be the same as the README.md from the project proposal, -
edited and extended.

Handin
------
- Gzipped repository (git archive -o latest.zip HEAD)
- In the root: README.md file in Markdown format (.md). 
 