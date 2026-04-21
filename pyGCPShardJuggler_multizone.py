''' A python version of the GCPShardJuggler script by RogueSMG
    (Ported from https://github.com/RogueSMG/GCPShardJuggler) 
    ** This is a non-manual, AI-generated code (might contain some manual changes). While it has been tested, any blaim is to go towards the AI model. ** 
'''

''' Improved to work with 5 zone at once, as per official google quota limits described here: https://docs.cloud.google.com/dns/quotas#name-server-limits '''

import argparse
import subprocess
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

GCLOUD = r"C:\Users\Administrator\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"


def run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return result.stdout


def gcloud(args):
    return run([GCLOUD] + args)


def create_zone(zone, project, dns_name):
    gcloud([
        "dns", "managed-zones", "create", zone,
        "--description=",
        f"--dns-name={dns_name}",
        f"--project={project}",
        "--visibility=public",
        "--dnssec-state=on",
        "--quiet"
    ])


def describe_zone(zone, project):
    output = gcloud([
        "dns", "managed-zones", "describe", zone,
        f"--project={project}",
        "--format=json",
        "--quiet"
    ])

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None


def delete_zone(zone, project):
    gcloud([
        "dns", "managed-zones", "delete", zone,
        f"--project={project}",
        "--quiet"
    ])


def worker(i, zone_base, project, dns_name, shard):
    zone_name = f"{zone_base}-{i}"

    create_zone(zone_name, project, dns_name)
    data = describe_zone(zone_name, project)

    if not data:
        delete_zone(zone_name, project)
        return False, zone_name, None

    name_servers = data.get("nameServers", [])
    assigned = name_servers[0] if name_servers else ""

    print(f"[{zone_name}] Assigned: {assigned}")

    if shard in assigned:
        return True, zone_name, assigned

    delete_zone(zone_name, project)
    return False, zone_name, assigned


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dns-zone", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--dns-name", required=True)
    parser.add_argument("--shard", required=True)

    args = parser.parse_args()

    base_zone = args.dns_zone
    project = args.project_id
    dns_name = args.dns_name
    shard = args.shard

    attempt = 0

    while True:
        attempt += 1
        print(f"\n=== Batch attempt {attempt} (5 parallel zones) ===")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(worker, i, base_zone, project, dns_name, shard)
                for i in range(5)
            ]

            for f in as_completed(futures):
                success, zone_name, assigned = f.result()

                if success:
                    print(f"\n🎯 MATCH FOUND!")
                    print(f"Zone: {zone_name}")
                    print(f"Shard: {assigned}")
                    sys.exit(0)

        print("No match in this batch, retrying...\n")


if __name__ == "__main__":
    main()
