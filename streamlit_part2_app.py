from __future__ import annotations

import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI


load_dotenv(".env", override=True)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
ANSWER_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
VECTOR_INDEX_NAME = "movie_tagline_embeddings"


@st.cache_resource
def get_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
    )


@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


def embed_text(question: str) -> list[float]:
    client = get_openai_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=question)
    return response.data[0].embedding


def retrieve_movies(question: str, top_k: int) -> list[dict[str, Any]]:
    question_embedding = embed_text(question)
    query = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $question_embedding)
    YIELD node AS movie, score
    RETURN movie.title AS title, movie.tagline AS tagline, score
    ORDER BY score DESC
    """

    driver = get_driver()
    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run(
            query,
            index_name=VECTOR_INDEX_NAME,
            top_k=top_k,
            question_embedding=question_embedding,
        )
        return [record.data() for record in result]


def graph_status() -> dict[str, Any]:
    driver = get_driver()
    with driver.session(database=NEO4J_DATABASE) as session:
        try:
            movie_count = session.run("MATCH (m:Movie) RETURN count(m) AS count").single()["count"]
            embedded_count = session.run(
                "MATCH (m:Movie) WHERE m.taglineEmbedding IS NOT NULL RETURN count(m) AS count"
            ).single()["count"]
            indexes = session.run(
                """
                SHOW VECTOR INDEXES
                YIELD name, state
                WHERE name = $index_name
                RETURN name, state
                """,
                index_name=VECTOR_INDEX_NAME,
            ).data()

            ready = bool(indexes) and indexes[0]["state"] == "ONLINE" and embedded_count > 0
            return {
                "movies": movie_count,
                "embedded": embedded_count,
                "ready": ready,
                "index_state": indexes[0]["state"] if indexes else "MISSING",
            }
        except Exception as exc:
            movie_count = session.run("MATCH (m:Movie) RETURN count(m) AS count").single()["count"]
            embedded_count = session.run(
                "MATCH (m:Movie) WHERE m.taglineEmbedding IS NOT NULL RETURN count(m) AS count"
            ).single()["count"]
            return {
                "movies": movie_count,
                "embedded": embedded_count,
                "ready": False,
                "error": str(exc),
            }


def generate_answer(question: str, matches: list[dict[str, Any]]) -> str:
    if not matches:
        return "I could not find any matching movies in the graph."

    context = "\n".join(
        f"- Title: {item['title']}\n  Tagline: {item['tagline']}\n  Similarity score: {item['score']:.4f}"
        for item in matches
    )

    client = get_openai_client()
    response = client.responses.create(
        model=ANSWER_MODEL,
        input=[
            {
                "role": "system",
                "content": (
                    "You answer movie-search questions using only the retrieved movie results. "
                    "Keep the answer concise, mention 2-4 relevant movies, and explain briefly why they fit."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nRetrieved movies:\n{context}",
            },
        ],
    )
    return response.output_text.strip()


st.set_page_config(page_title="Movie Graph RAG", page_icon="🎬", layout="wide")

st.title("Movie Graph RAG")
st.caption("Ask about a theme, mood, or idea, and the app will search the Neo4j movie graph by tagline embeddings.")

with st.sidebar:
    st.subheader("Settings")
    top_k = st.slider("Top matches", min_value=3, max_value=10, value=5)
    st.text_input("Embedding model", value=EMBEDDING_MODEL, disabled=True)
    st.text_input("Answer model", value=ANSWER_MODEL, disabled=True)

status = graph_status()

col1, col2 = st.columns(2)
with col1:
    st.metric("Movies in graph", status["movies"])
with col2:
    st.metric("Movies with embeddings", status["embedded"])

if status.get("index_state"):
    st.caption(f"Vector index `{VECTOR_INDEX_NAME}`: {status['index_state']}")

if not status["ready"]:
    st.error(
        "The Neo4j vector index is not ready yet. Make sure the lesson graph is loaded and the Part 2 setup cells have run."
    )
    if status.get("error"):
        st.code(status["error"])

question = st.text_input(
    "Ask a movie question",
    placeholder="What movies are about love and sacrifice?",
)

examples = st.pills(
    "Try an example",
    options=[
        "What movies are about love?",
        "What movies are about adventure?",
        "What movies feel dark and intense?",
        "What movies are about friendship?",
    ],
)

if examples and not question:
    question = examples

if st.button("Search", type="primary", use_container_width=True) and question:
    with st.spinner("Searching the graph..."):
        matches = retrieve_movies(question, top_k)

    if not matches:
        st.warning("No matching movies were found.")
    else:
        try:
            with st.spinner("Writing the answer..."):
                answer = generate_answer(question, matches)
            st.subheader("Answer")
            st.write(answer)
        except Exception as exc:
            st.warning("I found matches, but the final answer generation step failed. Showing the raw results instead.")
            st.code(str(exc))

        st.subheader("Retrieved Movies")
        for item in matches:
            with st.container(border=True):
                st.markdown(f"**{item['title']}**")
                st.write(item["tagline"])
                st.caption(f"Similarity score: {item['score']:.4f}")

st.markdown(
    """
    Run the app with:

    ```bash
    streamlit run streamlit_part2_app.py
    ```
    """
)
