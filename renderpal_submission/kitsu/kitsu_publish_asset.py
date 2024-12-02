"""Publishes asset renderings to kitsu"""

import json
import logging
import os
import sys

logger = logging.getLogger("Kitsu Asset Publish")
logging.basicConfig(level=logging.DEBUG)

logger.info("Start Publishing Kitsu Asset")

if len(sys.argv[1:]) != 7:
    logger.error("Unexpected number of arguments")

asset, task, user, clippath, version, pipeconfig, gazu_root = sys.argv[1:]

logger.info(f"Publishing {asset}_{task}_v{version} by {user}")
logger.info(f"Clippath: {clippath}")
logger.debug(f"Pipeline config: {pipeconfig}")
logger.debug(f"Gazu root: {gazu_root}")

sys.path.append(gazu_root)
try:
    import gazu
except ImportError:
    logger.error("gazu package not found")

gazu.set_host("http://141.62.110.217/api")
gazu_config = os.path.join(pipeconfig, "gazu.json").replace("\\", "/")
with open(gazu_config) as f:
    d = json.load(f)
    gazu_token = d["token"]
if gazu_token:
    logger.info("Obtained gazu token")
    gazu.set_token(gazu_token)
else:
    logger.error("Failed to obtain gazu token")


project = gazu.project.get_project_by_name("robot")

try:
    asset = gazu.asset.get_asset_by_name(project, asset)
except Exception as e:
    logger.error(f"Asset {asset} is not existing in Kitsu")
    logger.error(e)

task_type = gazu.task.get_task_type_by_name(task)
task = gazu.task.get_task_by_name(asset, task_type, "main")
wfa = gazu.task.get_task_status_by_short_name("wfa")
user_mail = f"{user}@hdm-stuttgart.de"
person = gazu.person.get_person_by_email(user_mail)

try:
    gazu.task.publish_preview(
        task,
        wfa,
        comment="Pyblish autopublish",
        person=person,
        revision=int(version),
        preview_file_path=clippath.replace("\\", "/"),
        set_thumbnail=True,
    )
    logger.info("Published Kitsu Asset successfully")
except Exception as e:
    logger.error("Could not publish turntable to Kitsu.")
    logger.error(e)
