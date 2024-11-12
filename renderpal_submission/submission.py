import os
import logging
import subprocess
from string import Template
from pathlib import Path


LOGGER = logging.getLogger("Render Submission")


def submit(
    render_name,
    scene_path,
    username,
    renderer,
    import_set=None,
    project=None,
    chunk_size=100,
    dry_run=False,
    dependant_job=None,
    dependency_type=0,
    import_set_file_path="",
    ):
    """Submits a render to renderpal and returns job id of render."""
    cmd = assemble_cmd(
        render_name,
        scene_path,
        username,
        renderer,
        import_set=import_set,
        project=project,
        chunk_size=chunk_size,
        dependant_job=dependant_job,
        dependency_type=dependency_type,
        import_set_file_path=import_set_file_path,

    )

    LOGGER.info(f"Submitting to Renderpal with: {cmd}")

    if dry_run:
        LOGGER.info("Dry Run enabled, not submitting to Renderpal")
        return None

    child = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout_data, stderr_data = child.communicate()

    if child.returncode == 1:
        LOGGER.error(f"Submission failed with {stderr_data}")
        return None

    job_id = child.returncode
    LOGGER.info(f"Submitted {render_name} (id: {job_id})")
    return job_id


def assemble_cmd(
    render_name,
    scene_path,
    username,
    renderer,
    import_set=None,
    project=None,
    chunk_size=100,
    dependant_job=None,
    dependency_type=0,
    import_set_file_path="",
    ):
    cmd = [
        get_renderpal_exe(),
        f'-login="{username}"',
        f'-nj_renderer="{renderer}"',
        "-retnjid",
        f'-nj_name="{render_name}"',
        f'-nj_splitmode="2,{chunk_size}"',
    ]

    if import_set:
        cmd.append(f'-importset="{import_set}"')
    
    if project:
        cmd.append(f'-nj_project="{project}"')

    if dependant_job:
        cmd.append(f"-nj_dependency {dependant_job}")
        cmd.append(f"-nj_deptype {dependency_type}")

    if import_set_file_path:
        cmd.append(f'-importset="{import_set_file_path}"',)

    return " ".join(cmd)


def create_renderpal_set(set_template, destination, **kwargs):
    file = os.path.join(get_package_root(), "sets", set_template)

    with open(file, "r") as f:
        src = Template(f.read())
    
    result = src.substitute(kwargs)
    r_set_file = os.path.join(destination)

    with open(r_set_file, "w") as r_set:
        r_set.write(result)

    return r_set_file


def get_renderpal_exe():
    return "C:\Program Files (x86)\RenderPal V2\CmdRC\RpRcCmd.exe"


def get_package_root():
    return Path(os.path.dirname(os.path.abspath(__file__))).parent
