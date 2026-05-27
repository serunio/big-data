from hdfs import InsecureClient
import subprocess
import json
import sys

client = InsecureClient("http://nn:9870", user="hadoop")

with open('/jobs/scripts.json') as json_file:
    scripts = json.load(json_file)


def exists(path):
    return client.status(path, strict=False) is not None


def run(job_name:str):
    if job_name not in scripts:
        print(f"Job '{job_name}' does not exist. (Drop the .py extension when running)")
        sys.exit(1)

    job = scripts[job_name]

    # check inputs
    for inp in job["inputs"]:
        if not exists(inp["location"]):
            print(f"Input {inp['location']} for job '{job_name}' does not exist. Run '{inp['script']}' first.")
            print(f"Run now? (y/n)")
            if input().lower() == "y":
                run(inp['script'])
                run(job_name)
            else:
                sys.exit(1)
            
        
    script_type = scripts[job_name]["script-type"]

    # run spark
    if script_type == "spark":
        subprocess.run(
            ["spark-submit", f'/jobs/{job["file"]}'],
            check=True
        )
    elif script_type == "python":
        subprocess.run(
            ["python3", f'/scraper/{job["file"]}'],
            check=True
        )
    elif script_type == "scrapy":
        subprocess.run(
            ["scrapy", "crawl", job_name],
            cwd="/scraper/scrapy",
            check=True
        )
    else:
        print(f"Unrecognized script type '{script_type}'")
        sys.exit(1)

if __name__ == "__main__":
    run(sys.argv[1])