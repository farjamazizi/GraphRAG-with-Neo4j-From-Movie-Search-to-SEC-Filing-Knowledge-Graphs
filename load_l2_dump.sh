#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

DUMP_FILE="$ROOT_DIR/data/neo4j_L2.dump"
STAGING_DIR="$ROOT_DIR/data/.neo4j_load"
EXPECTED_DUMP_NAME="neo4j.dump"

if [[ ! -f "$DUMP_FILE" ]]; then
  echo "Expected dump file not found at $DUMP_FILE"
  exit 1
fi

echo "Stopping Neo4j if it is running..."
docker compose down

echo "Resetting local Neo4j database files..."
rm -rf neo4j/data

echo "Preparing Lesson 2 dump for Neo4j Admin load..."
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp "$DUMP_FILE" "$STAGING_DIR/$EXPECTED_DUMP_NAME"

echo "Loading Lesson 2 dump into the neo4j database..."
docker compose run --rm \
  -v "$STAGING_DIR:/load-dump" \
  neo4j \
  neo4j-admin database load neo4j --from-path=/load-dump --overwrite-destination=true

echo "Starting Neo4j..."
docker compose up -d

echo "Cleaning up staged dump..."
rm -rf "$STAGING_DIR"

echo
echo "Lesson 2 database restored."
echo "Open http://localhost:7474 or restart the notebook kernel and rerun L2-query_with_cypher.ipynb."
