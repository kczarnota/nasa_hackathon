"""This example illustrates how to get started easily with the SimpleKGPipeline
and ingest text into a Neo4j Knowledge Graph.

This example assumes a Neo4j db is up and running. Update the credentials below
if needed.

NB: when building a KG from text, no 'Document' node is created in the Knowledge Graph.
"""

import asyncio
import logging
import os

import neo4j
from neo4j_graphrag.embeddings import AzureOpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.pipeline.pipeline import PipelineResult
from neo4j_graphrag.llm import LLMInterface
from neo4j_graphrag.llm import AzureOpenAILLM

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig()
logging.getLogger("neo4j_graphrag").setLevel(logging.DEBUG)


# Neo4j db infos
URI = "neo4j://localhost:7687"
AUTH = (os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])


NODE_TYPES = [
    {"label": "AstronautGroup", "properties": [
        {"name": "name", "type": "STRING"}
    ], "description": "A cohort of astronauts based on flight experience (e.g., LEO, Apollo, Non-flight)."},
    {"label": "AstronautCharacteristic", "properties": [
        {"name": "trait", "type": "STRING"}
    ], "description": "Characteristics of the astronaut cohorts, such as age or time in space."},
    {"label": "MissionType", "properties": [
        {"name": "type", "type": "STRING"}
    ], "description": "Classification of the mission's location (e.g., LEO, Deep Space/Beyond LEO)."},
    {"label": "Mission", "properties": [
        {"name": "name", "type": "STRING"}
    ], "description": "Specific spaceflight program or accident (e.g., Apollo 1, Space Shuttle)."},
    {"label": "HealthOutcome", "properties": [
        {"name": "cause_of_death", "type": "STRING"}
    ], "description": "The specific cause of death analyzed (e.g., CVD, Cancer, Accidents)."},
    {"label": "MortalityRate", "properties": [
        {"name": "rate", "type": "STRING"},
        {"name": "comparison_group", "type": "STRING"}
    ], "description": "The proportional mortality rate for a cause of death within a group."},
    {"label": "RadiationExposure", "properties": [
        {"name": "type", "type": "STRING"},
        {"name": "location", "type": "STRING"}
    ], "description": "Type and location of radiation experienced (e.g., Galactic cosmic rays in Deep Space)."},
    {"label": "AnimalModel", "properties": [
        {"name": "species", "type": "STRING"}
    ], "description": "The species used in the experimental studies (C57BL/6 mice)."},
    {"label": "ExperimentalTreatment", "properties": [
        {"name": "treatment", "type": "STRING"},
        {"name": "dose", "type": "STRING"}
    ], "description": "Simulated space conditions applied to the animal model (e.g., TBI, HU)."},
    {"label": "VascularResponse", "properties": [
        {"name": "response_type", "type": "STRING"},
        {"name": "mediator", "type": "STRING"}
    ], "description": "Physiological measurement of artery function (e.g., Endothelium-dependent vasodilation)."},
    {"label": "Protein", "properties": [
        {"name": "name", "type": "STRING"}
    ], "description": "Specific protein analyzed in the arteries (e.g., XO, eNOS)."},
    {"label": "Vessel", "properties": [
        {"name": "location", "type": "STRING"}
    ], "description": "The artery type from which measurements or content were taken."},
    {"label": "ReferencePopulation", "properties": [
        {"name": "name", "type": "STRING"}
    ], "description": "A comparison group outside of the astronaut cohorts (e.g., US population 55–64)."}
]

RELATIONSHIP_TYPES = [
    # Astronaut Cohort and Mission Relationships
    {"label": "INCLUDES_SUBGROUP", "description": "Links a larger group to its sub-cohorts."},
    "TRAVELED_IN",
    "FLEW_ON_MISSION",

    # Health and Mortality Relationships
    "HAD_MORTALITY_RATE_FOR",
    "RESULTING_IN",
    "COMPARED_TO",
    "SHOWS_DIFFERENCE_IN",
    "USED_AS_REFERENCE",

    # Space Environment and Physiological Effects
    "EXPOSED_TO",
    {"label": "LINKED_TO_DYSFUNCTION",
     "description": "Indicates a long-term effect of radiation on a vascular response."},

    # Experimental Relationships
    "APPLIED_TREATMENT",
    "AFFECTS",

    # Physiological Measurements
    "MEASURED_IN",
    "SHOWS_LEVELS_OF",
    "CLASSIFIED_AS"
]

PATTERNS = [
    # Core Mortality Findings
    ("AstronautGroup", "TRAVELED_IN", "MissionType"),
    ("AstronautGroup", "HAD_MORTALITY_RATE_FOR", "MortalityRate"),
    ("MortalityRate", "RESULTING_IN", "HealthOutcome"),
    ("MortalityRate", "COMPARED_TO", "AstronautGroup"),
    ("MortalityRate", "COMPARED_TO", "ReferencePopulation"),

    # Radiation and Risk Hypothesis
    ("AstronautGroup", "EXPOSED_TO", "RadiationExposure"),
    ("RadiationExposure", "LINKED_TO_DYSFUNCTION", "VascularResponse"),

    # Experimental (Animal) Study Structure
    ("AnimalModel", "APPLIED_TREATMENT", "ExperimentalTreatment"),
    ("ExperimentalTreatment", "EXPOSED_TO", "RadiationExposure"),
    ("ExperimentalTreatment", "AFFECTS", "VascularResponse"),

    # Physiological Mechanism
    ("VascularResponse", "MEASURED_IN", "Vessel"),
    ("Vessel", "SHOWS_LEVELS_OF", "Protein"),

    # Group and Mission Context
    ("AstronautGroup", "INCLUDES_SUBGROUP", "AstronautGroup"),
    ("AstronautGroup", "FLEW_ON_MISSION", "Mission"),
    ("Mission", "CLASSIFIED_AS", "MissionType"),
    ("AstronautGroup", "SHOWS_DIFFERENCE_IN", "AstronautCharacteristic"),

    # Specific Mechanisms (e.g., Protein involvement)
    ("Protein", "MEASURED_IN", "Vessel"),
    ("VascularResponse", "AFFECTS", "Protein")  # Implied, as dysfunction is mediated by increased XO/NO scavenging.
]

async def define_and_run_pipeline(
    neo4j_driver: neo4j.Driver,
    llm: LLMInterface,
) -> PipelineResult:
    # Create an instance of the SimpleKGPipeline
    kg_builder = SimpleKGPipeline(
        llm=llm,
        driver=neo4j_driver,
        embedder=AzureOpenAIEmbeddings("text-embedding-3-large"),
        schema={
            "node_types": NODE_TYPES,
            "relationship_types": RELATIONSHIP_TYPES,
            "patterns": PATTERNS,
        },
        from_pdf=False,
    )

    for path in ["data/PMC4964660.md", "data/PMC5666799.md", "data/PMC6387434.md", "data/PMC7072278.md"]:
        with open(path, "r") as f:
            text = f.read()
        result = await kg_builder.run_async(text=text)

    return result


async def main() -> PipelineResult:
    llm = AzureOpenAILLM(model_name="gpt-4.1-mini",
                            model_params={
                                "max_tokens": 2000,
                                "response_format": {"type": "json_object"},
                            },
                         )
    with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
        res = await define_and_run_pipeline(driver, llm)
    await llm.async_client.close()
    return res


if __name__ == "__main__":
    res = asyncio.run(main())
    print(res)