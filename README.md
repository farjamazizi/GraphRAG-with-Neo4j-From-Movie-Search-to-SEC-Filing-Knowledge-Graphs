# Demo of Graphs for RAG

This project explores how Neo4j can support retrieval-augmented generation workflows, starting with a movie graph and then moving into SEC filing data and graph-based retrieval patterns.

The repo currently includes:

- Jupyter notebooks for graph querying, vector search, and graph-enhanced RAG workflows
- A local Neo4j setup powered by Docker Compose
- Lesson data and Neo4j dump files under `data/`
- A small Streamlit app for semantic movie search over tagline embeddings

## Project Contents

### Notebooks

- `Learning the Graph: A Hands-On Cypher Primer with Movies.ipynb`
  Intro notebook for connecting to Neo4j and practicing Cypher on the movie graph.
- `Turning Graph Data into Semantic Search with Vector Indexes.ipynb`
  Creates embeddings for movie taglines and queries them through a Neo4j vector index.
- `From Raw SEC Filings to a Searchable Knowledge Graph.ipynb`
  Builds a searchable graph workflow from SEC filing content using LangChain, Neo4j, and OpenAI.
- `Adding Structure: Connecting Filing Chunks into a Navigable Graph.ipynb`
  Extends the filing workflow by connecting chunks into a richer graph and retrieval pipeline.

### App

- `streamlit_part2_app.py`
  A Streamlit interface that:
  - connects to Neo4j
  - embeds the user question with OpenAI
  - runs `db.index.vector.queryNodes(...)` against the movie graph
  - uses an OpenAI chat model to summarize the retrieved movie matches

### Infrastructure and Data

- `docker-compose.yml`
  Runs a local Neo4j 5 instance with APOC and GenAI plugins enabled.
- `load_l2_dump.sh`
  Resets the local Neo4j database and restores the Lesson 2 movie graph from `data/neo4j_L2.dump`.
- `data/`
  Contains CSV/JSON inputs and Neo4j dump files used by the notebooks.

## Requirements

- Python 3.11+ is recommended
- Docker and Docker Compose are required for the local Neo4j instance
- An OpenAI-compatible API key is required for embedding and answer-generation steps

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root with values like these:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=localNeo4jPassword123
NEO4J_DATABASE=neo4j

OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4.1-mini
```

## Start Neo4j

Start the local database:

```bash
docker compose up -d
```

Neo4j Browser will be available at `http://localhost:7474`.

The container is configured with:

- APOC enabled for schema inspection used by LangChain's Neo4j integration
- GenAI plugin enabled for notebook cells that use `genai.vector.encode(...)`

If you started Neo4j before this plugin configuration was added, recreate the container:

```bash
docker compose down
docker compose up -d
```

If Neo4j still comes up without APOC or GenAI support, reset the local Neo4j folders and try again:

```bash
docker compose down
rm -rf neo4j
docker compose up -d
```

## Load the Movie Graph

The notebooks query the Neo4j database, not the files in `data/` directly. That means Neo4j must have the lesson graph restored before Cypher queries return real results.

To load the Lesson 2 movie graph:

```bash
bash load_l2_dump.sh
```

This script:

- stops the Neo4j container
- removes the current local Neo4j data directory
- stages `data/neo4j_L2.dump` as `neo4j.dump`
- runs `neo4j-admin database load neo4j`
- starts Neo4j again

After loading completes, restart your notebook kernel and rerun the relevant notebook cells from the top.

## Run the Streamlit App

Once Neo4j is running and the movie graph plus embeddings/vector index have been prepared from the notebook workflow, launch the app with:

```bash
streamlit run streamlit_part2_app.py
```

The app expects:

- the movie graph to be loaded into Neo4j
- movie nodes to have `taglineEmbedding`
- the vector index `movie_tagline_embeddings` to exist and be online

If those setup cells have not been run yet, the app will show that the vector index is not ready.

## Suggested Workflow

1. Install Python dependencies with `pip install -r requirements.txt`
2. Create a `.env` file with Neo4j and OpenAI settings
3. Start Neo4j with `docker compose up -d`
4. Load the movie graph with `bash load_l2_dump.sh`
5. Open the notebooks and run them from top to bottom
6. Launch the Streamlit app with `streamlit run streamlit_part2_app.py`

## Stop Neo4j

```bash
docker compose down
```

## Troubleshooting

If a notebook query like:

```cypher
MATCH (n)
RETURN count(n)
```

returns `0`, the most likely cause is that Neo4j is running but the graph data has not been restored into the database yet.

Fix that by running:

```bash
bash load_l2_dump.sh
```

Then restart the notebook kernel and rerun the notebook cells.
# GraphRAG-with-Neo4j-From-Movie-Search-to-SEC-Filing-Knowledge-Graphs
