import logging
import os

import boto3


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

ENVIRONMENT = os.environ["TARGET_ENVIRONMENT"]
SCHEDULE = os.environ.get("SCHEDULE_TAG_VALUE", "office-hours")
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"


def _tag_value(tags, key):
    return next((tag["Value"] for tag in tags if tag["Key"] == key), None)


def _manage_ec2(action):
    client = boto3.client("ec2")
    response = client.describe_instances(
        Filters=[
            {"Name": "tag:Environment", "Values": [ENVIRONMENT]},
            {"Name": "tag:Schedule", "Values": [SCHEDULE]},
            {"Name": "instance-state-name", "Values": ["stopped" if action == "start" else "running"]},
        ]
    )
    instance_ids = [
        instance["InstanceId"]
        for reservation in response["Reservations"]
        for instance in reservation["Instances"]
    ]
    if instance_ids and not DRY_RUN:
        getattr(client, f"{action}_instances")(InstanceIds=instance_ids)
    return instance_ids


def _eligible_rds(client, arn):
    tags = client.list_tags_for_resource(ResourceName=arn)["TagList"]
    return _tag_value(tags, "Environment") == ENVIRONMENT and _tag_value(tags, "Schedule") == SCHEDULE


def _manage_rds(action):
    client = boto3.client("rds")
    changed = []
    wanted_status = "stopped" if action == "start" else "available"

    for database in client.describe_db_instances()["DBInstances"]:
        if database["DBInstanceStatus"] == wanted_status and _eligible_rds(client, database["DBInstanceArn"]):
            if not DRY_RUN:
                getattr(client, f"{action}_db_instance")(DBInstanceIdentifier=database["DBInstanceIdentifier"])
            changed.append(database["DBInstanceIdentifier"])

    for cluster in client.describe_db_clusters()["DBClusters"]:
        if cluster["Status"] == wanted_status and _eligible_rds(client, cluster["DBClusterArn"]):
            if not DRY_RUN:
                getattr(client, f"{action}_db_cluster")(DBClusterIdentifier=cluster["DBClusterIdentifier"])
            changed.append(cluster["DBClusterIdentifier"])

    return changed


def handler(event, _context):
    action = event.get("action")
    if action not in {"start", "stop"}:
        raise ValueError("action must be start or stop")
    if ENVIRONMENT == "prod":
        raise ValueError("production scheduling is prohibited")

    result = {
        "action": action,
        "environment": ENVIRONMENT,
        "dry_run": DRY_RUN,
        "ec2": _manage_ec2(action),
        "rds": _manage_rds(action),
    }
    LOGGER.info("Scheduler result: %s", result)
    return result
