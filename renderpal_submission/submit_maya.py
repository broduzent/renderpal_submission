import json
import os
import logging

from maya import cmds
from pymel import core as pm
from renderpal_submission import submission

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("Render Submission")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
LOGGER.addHandler(ch)


def submit():
    scene_path = pm.system.sceneName()
    renderjob_name = assemble_render_set_name(scene_path)
    project_name, shot, task, version, user = renderjob_name.split("_")

    path_elements = os.path.normpath(scene_path).split(os.sep)
    path_elements[0] = "L:/"

    user_mapping_path = os.path.join(os.environ.get("PIPELINE_CONFIG_PATH"), "user_mapping.json").replace("\\", "/")
    with open(user_mapping_path, "r") as f:
        user_mapping = json.load(f)
    user_abbr = user_mapping[user]["hdmabbr"]

    base_path = os.path.join(*path_elements[:-4]).replace("\\", "/")
    render_path = os.path.join(base_path, "Rendering")
    out_path = os.path.join(render_path, "3dRender", task, version)
    exr_path = os.path.join(out_path, "exr")
    mp4_path = os.path.join(out_path, "mp4")
    outfile = f"{shot}_{task}_{version}"

    LOGGER.info("Setting Render Paths")
    LOGGER.info(f"Setting exr path to {exr_path}")
    LOGGER.info(f"Setting mp4 path to {mp4_path}")
    LOGGER.info(f"Setting filename to {outfile}")

    if not run_precheck(render_path, exr_path):
        return

    os.makedirs(exr_path, exist_ok=True)
    os.makedirs(mp4_path, exist_ok=True)

    renderset_dest = f"L:/krasse_robots/00_Pipeline/Rendersets/shot_renderset_{outfile}.rset"
    renderset = submission.create_renderpal_set(
        "shot_renderset",
        renderset_dest,
        out_dir=exr_path,
        out_file=outfile,
        startframe=cmds.getAttr("defaultRenderGlobals.startFrame"),
        endframe=cmds.getAttr("defaultRenderGlobals.endFrame"),
        render_cam="testcamera",  # ToDo
    )
    render_jid = submission.submit(
        renderjob_name,
        scene_path,
        "ca-user:polytopixel",
        "Arnold Renderer/CA Maya Arnold 2024",
        import_set=renderset,
        splitmode="2,10",
        project="Robo",
        outdir=exr_path,
        outfile=outfile,
        color="125,158,192",
    )

    ffmpeg_renderset_dest = f"L:/krasse_robots/00_Pipeline/Rendersets/shot_renderset_{outfile}_ffmpeg.rset"
    ffmpeg_set = submission.create_renderpal_set(
        "ffmpeg_renderset",
        ffmpeg_renderset_dest,
        out_dir=mp4_path.replace("\\", "/"),
        out_file=f"{outfile}.mp4",
        input=f'{exr_path}\\{outfile}.%04d.exr'.replace("\\", "/"),
        start_frame=cmds.getAttr("defaultRenderGlobals.startFrame")
    )
    ffmpeg_jid = submission.submit(
        f"CONVERT_{renderjob_name}",
        "FFMPEG",
        "ca-user:polytopixel",
        "Frog FFmpeg/Default",
        import_set=ffmpeg_set,
        project="Robo",
        dependency=render_jid,
        deptype=0,
        color="125,158,192"
    )

    kitsu_renderset_dest = rf"L:\krasse_robots\00_Pipeline\Rendersets\shot_renderset_{outfile}_kitsu.rset"
    kitsu_set = submission.create_renderpal_set(
        "kitsu_shot_renderset",
        kitsu_renderset_dest,
        pythonscript=r"L:/krasse_robots/00_Pipeline/Packages/renderpal_submission/renderpal_submission/kitsu/kitsu_publish_shot.py",
        sequence_name=shot.split("-")[0],
        shot_name=shot.split("-")[1],
        task_name=outfile.split("_")[1],
        user_name=user_abbr,
        clippath=os.path.join(mp4_path, f"{outfile}.mp4").replace("\\", "/"),
        version=version,
        pipeconfig=os.getenv("PIPELINE_CONFIG_PATH").replace("\\", "/"),
        gazu_root="L:/krasse_robots/00_Pipeline/Packages/gazu_patched"
    )
    kitsu_jid = submission.submit(
        f"KITSU_{renderjob_name}",
        "Kitsu_Shot_Publish",
        "ca-user:polytopixel",
        "Python3/Kitsu Shot Publish",
        import_set=kitsu_set,
        project="Robo",
        dependency=ffmpeg_jid,
        deptype=0,
        color="125,158,192"
    )
    if kitsu_jid:
        cmds.confirmDialog(title="Render submitted", message="Submitted all jobs successfully", button=["Beep boop"])
    else:
        cmds.confirmDialog(title="Render submitted", message="Couldn't submit all jobs", button=["Beep boop :("])


def assemble_render_set_name(scene_path):
    path_elem = os.path.normpath(scene_path).split(os.sep)
    naming_elem = path_elem[-1].split("_")
    print(path_elem)
    nice_name = "_".join(
        ["Robo", path_elem[4], naming_elem[-5], naming_elem[-4], naming_elem[-2]]
    )
    return nice_name


def run_precheck(render_path, exr_path):
    status = True
    if not os.path.isdir(render_path):
        return False

    rs_framerange = (cmds.getAttr("defaultRenderGlobals.startFrame"), cmds.getAttr("defaultRenderGlobals.endFrame"))
    vp_framerange = (cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True))

    if rs_framerange != vp_framerange:
        framerange_result = cmds.confirmDialog(
            title="Framerange missmatch",
            message=f"Rendersetting framerange is {rs_framerange},\n Viewport framerange is {vp_framerange}\n"
                    f"Do you want to set render framerange to viewport framerange {vp_framerange}?",
            button=["Yes", "No"],
            defaultButton="Yes",
            cancelButton="No",
        )
        if framerange_result == "Yes":
            cmds.setAttr("defaultRenderGlobals.startFrame", cmds.playbackOptions(q=True, min=True))
            cmds.setAttr("defaultRenderGlobals.endFrame", cmds.playbackOptions(q=True, max=True))

    if os.path.isdir(exr_path):
        dialog_result = cmds.confirmDialog(
            title="Rerender version?",
            message="Brudi, diese Version wurde schon mal auf die Farm geschickt.\n"
                    "Bist du sicher, dass du mögliche Files überschreiben willst?",
            button=["Yes", "No"],
            defaultButton="Yes",
            cancelButton="No",
        )
        status = True if dialog_result == "Yes" else False

    return status
