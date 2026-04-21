''' 
    A python version of the GCPShardJuggler script by RogueSMG
    (Ported from https://github.com/RogueSMG/GCPShardJuggler) 
    ** This is a non-manual, AI-generated code (might contain some manual changes). While it has been tested, any blaim is to go towards the AI model. ** 
'''


import argparse
import subprocess
import json
import time
import sys


def run(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return result.stdout


def gcloud(args):
    """Run gcloud command"""
    return run([r"C:\Users\Administrator\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"] + args)


def main():
    parser = argparse.ArgumentParser(description="GCP Shard Juggler")

    parser.add_argument("--dns-zone", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--dns-name", required=True)
    parser.add_argument("--shard", required=True)

    args = parser.parse_args()

    zone = args.dns_zone
    project = args.project_id
    dns_name = args.dns_name
    shard = args.shard

    count = 0

    while True:
        count += 1
        print(f"Number of Tries: {count}")

        # Create zone
        gcloud([
            "dns", "managed-zones", "create", zone,
            "--description=",
            f"--dns-name={dns_name}",
            f"--project={project}",
            "--visibility=public",
            "--dnssec-state=on",
            "--quiet"
        ])

        # Describe zone
        output = gcloud([
            "dns", "managed-zones", "describe", zone,
            f"--project={project}",
            "--format=json",
            "--quiet"
        ])

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            print("Failed to parse gcloud output")
            continue

        name_servers = data.get("nameServers", [])
        assigned_shard = name_servers[0] if name_servers else ""

        print(f"Assigned shards: {assigned_shard}")

        if shard in assigned_shard:
            print(f"Finally, {shard} shards!")
            sys.exit(0)
        else:
            print(f"Deleting zone (no match for {shard})\n")

            gcloud([
                "dns", "managed-zones", "delete", zone,
                f"--project={project}",
                "--quiet"
            ])


if __name__ == "__main__":
    main()
