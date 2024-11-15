"""Simple submission api for Renderpal."""
import os
import json
import logging
import subprocess
from string import Template
from pathlib import Path


LOGGER = logging.getLogger("Render Submission")


def submit(job_name, scene_path, login, renderer, dry_run=False, **kwargs):
    """Submits a render to renderpal and returns job id of render.

    Args:
        job_name: The net job name.
        scene_path: Full filepath to scene which should be rendered.
        login: Specifies the login to use, format: "user:password"
        renderer: Sets the renderer to use.
            The syntax for the renderer name is "Renderer/Version";
            if no version is supplied, the default version will be used.
        dry_run: If enabled, only shows the command the job would be submitted with.

    Keyword Args:
        import_set: Imports the specified render set.
        userdir: Overrides the user directory
            (the directory where all log files and temporary fileswill be located).
        defsection: Overrides the name of the section to use from the RpRcDefaults.conf file.
        log: Enables logging of all output to a log file (RpRcCmd.log)
        preset: Imports the specified net job preset. This can be a list of filepaths.
        priority: The net job priority to use (1-10).
        rendercores: Specifies the number of parallel renderings (on a client).
        noemails: If specified, no email notifications will be sent about this net job.
        emailusers: Adds additional users who should also receive email notifications about this job.
        emailrecpt: Sets additional email recipients for this net job.
        splitmode: Sets the frame splitting mode to use. "<mode>,<count>".
        slicemode: Sets the image slicing mode to use. "<mode>,<x>,<y>,[overlap],[format]".
        extsplitting: Specifies parameters used for additional splitting.
        notes: Sets the notes for this net jobs.
        tags: Specifies tags for the net job.
        pools: Names of the pools to use. Separated by semicolons or commas.
        paused: If specified, the net job will be started paused.
        clientlimit: The client limit.
        minclientpriority: Sets the minimum client priority to use.
        mindispatchdelay: Sets the minimum delay between chunk dispatches in seconds.
        dependency: Sets the ID of the net job the new net job should depend on. Can be a list of job ids.
            If dependency is defined, deptype has to be defined as well.
        deptype: The dependency type (0 = Job, 1 = Chunk IDs, 2 = Frames, 3 = Image slices)
        depunfinishedasdone: If specified, unfinished net jobs will be treated as done when checking for dependencies.
        firstlastfirst: If specified, renders the first and last chunk first.
        blockedclients: The specified clients will be blocked from this net job.
        color: Display color of the net job (r,g,b).
        urgent: If specified, the net job will be marked as urgent.

    Returns:
        job_id: The ID of the submitted job.
    """
    cmd = _assemble_cmd(
        job_name,
        scene_path,
        login,
        renderer,
        **kwargs
    )

    LOGGER.info(f"Submitting to Renderpal with: {cmd}")

    if dry_run:
        LOGGER.info("Dry Run enabled, not submitting to Renderpal")
        return

    child = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout_data, stderr_data = child.communicate()

    if child.returncode == 1:
        LOGGER.error(f"Submission failed with {stderr_data}")
        return

    job_id = child.returncode
    LOGGER.info(f"Submitted {job_name} (id: {job_id})")

    return job_id


def create_renderpal_set(set_template, destination, **kwargs):
    """Generates a renderpal set from Set template.

    Args:
        set_template: Name of the set template to use (should be lokated in this repo).
        destination: Destination file to write set to.
        **kwargs: Dictionary to replace keys in set template.

    Returns:
        r_set_file: Filepath to generated set.
    """
    file = os.path.join(_get_package_root(), "resources", "sets", set_template)

    with open(file, "r") as f:
        src = Template(f.read())

    result = src.substitute(kwargs)
    r_set_file = os.path.join(destination)

    with open(r_set_file, "w") as r_set:
        r_set.write(result)

    return r_set_file


def _assemble_cmd(job_name, scene_path, login, renderer, **kwargs):
    """Assembles the renderpal command which can be used for submission."""
    cmd = [
        _get_renderpal_exe(),
        f'-login="{login}"',
        f'-nj_renderer="{renderer}"',
        "-retnjid",
        f'-nj_name="{job_name}"',
    ]

    flag_lookup = _get_flag_lookup()

    for flag, value in kwargs.items():
        cmd_flag = flag_lookup.get(flag)
        if not cmd_flag:
            LOGGER.warning(f"Unknown flag specified: {flag}")
            continue
        if isinstance(value, list):
            for v in value:
                cmd.append(f'{cmd_flag}="{v}"')
        elif isinstance(value, bool):
            cmd.append(cmd_flag)
        elif flag in ["splitmode"]:
            cmd.append(f'{cmd_flag} "{value}"')
        elif flag in ["project"]:
            cmd.append(f'{cmd_flag} {value}')
        elif isinstance(value, str):
            cmd.append(f'{cmd_flag}="{value}"')
        else:
            cmd.append(f'{cmd_flag} {value}')

    cmd.append(scene_path)

    return " ".join(cmd)


def _get_renderpal_exe():
    """Returns Renderpal executable."""
    # ToDo: Make this actually search for RpRcCmd
    return r"C:\Program Files (x86)\RenderPal V2\CmdRC\RpRcCmd.exe"


def _get_package_root():
    """Returns root of this package which can be used to assemble paths."""
    return Path(os.path.dirname(os.path.abspath(__file__))).parent


def _get_flag_lookup():
    """Returns dict to lookup renderpal cmd flags from python flags."""
    file = os.path.join(_get_package_root(), "resources", "flag_lookup.json")

    with open(file, "r") as f:
        flag_lookup = json.load(f)

    return flag_lookup
