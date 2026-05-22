scripts = {
    "nlp": {
        "inputs": [
            {
                "location": "/raw/wikipedia/cat_articles",
                "script": "scrape-wikipedia"
            },
            {
                "location": "/processed/cat-api/breed-names.txt",
                "script": "breed-names"
            }
        ],
        "output": "/processed/cats/final_extracted_knowledge",
        "file": "nlp.py",
        "needed-by": [],
        "script-type": "spark"
    },

    "scrape-wikipedia": {
        "inputs": [],
        "output": "/raw/wikipedia/cat_articles",
        "file": "scrape-wikipedia.py",
        "script-type": "scrapper",
        "needed-by": ["nlp"]
    },

    "breed-names": { 
        "inputs": [
            {
                "location": "/processed/cat-api/breeds",
                "script": "breeds-parquet"
            }
        ],
        "output": "/processed/cat-api/breed-names.txt",
        "file": "breed-names.py",
        "script-type": "spark",
        "needed-by": ["nlp"]
    },

    "breeds-parquet": {
        "inputs": [
            {
                "location": "/raw/cat-api/breeds.json",
                "script": "cat-api-breeds"
            }
        ],
        "output": "/processed/cat-api/breeds",
        "file": "breeds-parquet.py",
        "script-type": "spark",
        "needed-by": ["breed-names"]
    },

    "cat-api-breeds": {
        "inputs": [],
        "output": "/raw/cat-api/breeds.json",
        "file": "cat-api-breeds.py",
        "script-type": "scrapper",
        "needed-by": ["breeds-parquet"]
    },

    "pubmed-breed-popularity": {
        "inputs": [
            {
                "location": "/processed/pubmed/article_list",
                "script": "pubmed-lists-parquet"
            }
        ],
        "output": "/processed/pubmed/breed_popularity",
        "file": "pubmed-breed-popularity.py",
        "script-type": "spark",
        "needed-by": []
    },

    "pubmed-lists-parquet": {
        "inputs": [
            {
                "location": "/raw/pubmed/article_list",
                "script": "pubmed-lists"
            }
        ],
        "output": "/processed/pubmed/article_list",
        "file": "pubmed-lists-parquet.py",
        "script-type": "spark",
        "needed-by": ["pubmed-breed-popularity"]
    },

    "pubmed-lists": {
        "inputs": [],
        "output": "/raw/pubmed/article_list",
        "file": "pubmed-lists.py",
        "script-type": "scrapper",
        "needed-by": ["pubmed-lists-parquet"]
    }
}

from hdfs import InsecureClient
import subprocess
import json
import sys

client = InsecureClient("http://nn:9870", user="hadoop")


def exists(path):
    return client.status(path, strict=False) is not None


def run(job_name):
    job = scripts[job_name]

    # check inputs
    for inp in job["inputs"]:
        if not exists(inp["location"]):
            print(f"Input {inp['location']} for job '{job_name}' does not exist. Run '{inp['script']}' first.")
            if scripts[inp['script']]["script-type"] == "spark":
                print(f"Run now? (y/n)")
                if input().lower() == "y":
                    run(inp['script'])
                    run(job_name)
                else:
                    sys.exit(1)
            else:
                sys.exit(1)

    # run spark
    subprocess.run(
        ["spark-submit", f'/jobs/{job["file"]}'],
        check=True
    )

if __name__ == "__main__":
    run(sys.argv[1])