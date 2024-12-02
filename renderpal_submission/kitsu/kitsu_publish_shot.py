"""Publishes shot renderings to kitsu"""

import json
import logging
import os
import sys

logger = logging.getLogger("Kitsu Shot Publish")
logging.basicConfig(level=logging.DEBUG)

logger.info("Start Publishing Kitsu Shot")

if len(sys.argv[1:]) != 7:
    logger.error("Unexpected number of arguments")

sequence_name, shot_name, task_name, user_name, clippath, version, pipeconfig, gazu_root = sys.argv[1:]

logger.info(f"Publishing {sequence_name}-{shot_name}_{task_name}_v{version} by {user_name}")
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
    sequence = gazu.shot.get_sequence_by_name(project, sequence_name)
except Exception as e:
    logger.error(f"Asset {sequence_name} is not existing in Kitsu")
    logger.error(e)

try:
    shot = gazu.shot.get_shot_by_name(sequence, shot_name)
except Exception as e:
    logger.error(f"Asset {shot_name} is not existing in Kitsu")
    logger.error(e)

task_type = gazu.task.get_task_type_by_name(task_name)
task = gazu.task.get_task_by_name(shot, task_type, "main")
wfa = gazu.task.get_task_status_by_short_name("wfa")
user_mail = f"{user_name}@hdm-stuttgart.de"
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
    logger.info("Published Kitsu Shot successfully")
except Exception as e:
    logger.error("Could not publish Shot to Kitsu.")
    logger.error(e)
