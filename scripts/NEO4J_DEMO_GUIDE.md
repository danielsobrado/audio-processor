# Neo4j Graph Visualization Demo Guide

This guide provides step-by-step instructions to run the graph visualization demo, populate your Neo4j database with sample data, and explore the resulting conversation graph.

## Prerequisites

1.  **Docker**: Ensure Docker is installed and running on your system.
2.  **Project Dependencies**: Make sure you have installed the project's dependencies by running `uv sync --dev` in the project root.
3.  **Application Configuration**: Your application must be configured to connect to the Neo4j instance.

## Step 1: Start Neo4j with Docker

If you don't have a Neo4j instance running, open a terminal and run the following command. This will start a Neo4j 5 Community Edition container.

**This is a single command, safe to copy and paste:**
```bash
docker run -d --name neo4j-demo -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password --rm neo4j:5-community
```

-   `--name neo4j-demo`: Gives the container a memorable name.
-   `-p 7474:7474`: Exposes the Neo4j Browser web interface.
-   `-p 7687:7687`: Exposes the Bolt protocol for the application to connect.
-   `-e NEO4J_AUTH=neo4j/password`: Sets the username to `neo4j` and the password to `password`.
-   `--rm`: Automatically removes the container when you stop it.

## Step 2: Configure the Application

You need to tell the application to enable graph processing and how to connect to the Neo4j container.

1.  **Open your environment configuration file**. This is typically `.env` at the project root. If you are using environment-specific YAML files, you might edit `config/development.yaml`.

2.  **Ensure the following settings are present and correct** in your `.env` file:

    ```env
    # --- GRAPH DATABASE SETTINGS ---
    GRAPH_ENABLED=true
    GRAPH_DATABASE_TYPE=neo4j
    GRAPH_DATABASE_URL=bolt://localhost:7687
    GRAPH_DATABASE_USERNAME=neo4j
    GRAPH_DATABASE_PASSWORD=password
    GRAPH_DATABASE_NAME=neo4j
    ```

    *These settings match the Docker container we started in Step 1.*

## Step 3: Run the Demo Script

Now, run the visualization demo script from the project root directory. It will process a sample transcript and populate the Neo4j database.

```bash
uv run python scripts/demo_neo4j_visualization.py
```

## Step 4: Explore the Graph in Neo4j Browser

After the script successfully populates the database, you can explore the newly created conversation graph.

1.  **Open your web browser** and navigate to [http://localhost:7474](http://localhost:7474).
2.  You will see the Neo4j Browser login screen.
3.  For the **Connect URL**, ensure it is `bolt://localhost:7687`.
4.  Enter the **Username** `neo4j` and **Password** `password`.
5.  Click **Connect**.
6.  Copy the Cypher queries below and paste them into the query editor at the top of the screen. Click the blue "Play" button (or press `Ctrl+Enter`) to execute.

After running a query, click the **Graph** icon on the left side of the results panel to see the visual representation.

---

### Recommended Cypher Queries for Visualization

#### Query 1: View the Full Conversation Graph

This query shows the central `Conversation` node and all directly and indirectly connected nodes (speakers, segments, topics, etc.) within two hops. It's a great starting point to see the overall structure.

```cypher
MATCH (c:Conversation {id: 'demo-visualization-001'})-[*1..2]-(n)
RETURN c, n
```

#### Query 2: View Speakers and their Segments

This shows which speaker is responsible for each segment of the transcript in this conversation.

```cypher
MATCH (c:Conversation {id: 'demo-visualization-001'})-[:CONTAINS]->(seg:TranscriptSegment)
MATCH (sp:Speaker {id: seg.speaker_id})
RETURN sp, seg
```

#### Query 3: View Topics Discussed by Speakers

This query links speakers to the specific topics they discussed during the conversation.

```cypher
MATCH (sp:Speaker)-[d:DISCUSSES]->(t:Topic)
WHERE (sp)-[:SPEAKS_IN]->(:Conversation {id: 'demo-visualization-001'})
RETURN sp, d, t
```

#### Query 4: View Entities Mentioned in Segments

See which entities (like emails, phone numbers, etc.) were mentioned and in which transcript segment.

```cypher
MATCH (c:Conversation {id: 'demo-visualization-001'})-[:CONTAINS]->(seg:TranscriptSegment)-[m:MENTIONS]->(e:Entity)
RETURN seg, m, e
```

#### Query 5: View the Sequential Flow of the Conversation

This query uses the `FOLLOWS` relationship to show the chronological path of the conversation from one segment to the next.

```cypher
MATCH p=(:Conversation {id: 'demo-visualization-001'})-[:CONTAINS]->(seg1:TranscriptSegment)-[:FOLLOWS*]->(seg2:TranscriptSegment)
RETURN p
```

---

## (Optional) Step 5: Stop and Clean Up

Once you are finished exploring, you can stop and remove the Neo4j Docker container to free up system resources.

```bash
docker stop neo4j-demo
```

Because we used the `--rm` flag when starting the container, it will be automatically removed when stopped.
