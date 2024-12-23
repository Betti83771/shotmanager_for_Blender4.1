import bpy
from bpy.types import Operator
from shotmanager.config import config   
from os.path import exists
from shotmanager.retimer.retimer import retimeScene

def build_single_shot_file(context, shot_name, save_path):
    props = config.getAddonProps(context.scene)
    current_take = props.getCurrentTake()
    shot = props.getShotByName(shot_name)
    start = shot.start
    end = shot.end
    duration = end - start + 1
    for scene in bpy.data.scenes:
        if scene != context.scene:
            bpy.data.scenes.remove(scene)

    take_index = props.getTakeIndex(current_take)
    shots = [shot.name for shot in current_take.getShotsList(ignoreDisabled=False)]
    for sh_name in shots:
        if sh_name != shot_name:
            sh = props.getShotByName(sh_name)
            sh_index = props.getShotIndex(sh)
            props.removeShotByIndex(sh_index, deleteCamera=True, takeIndex=take_index) 
    
    props.setSelectedShot(shot)
    props.setCurrentShot(shot)

    new_start = 1001
    new_end = new_start + duration - 1
    offset = new_start - start
    retimerApplyToSettings=props.retimer.getCurrentApplyToSettings()
    retimerApplyToSettings.initialize('SCENE')
    retimerApplyToSettings.applyToStoryboardShotRanges = True
    context.scene.frame_current = 0
    retimeScene(context=context,
                retimeMode="GLOBAL_OFFSET",
                retimerApplyToSettings=retimerApplyToSettings,
                objects=context.scene.objects,
                start_incl=0,
                duration_incl=offset,
                join_gap=True,
    )

    
    context.scene.frame_start = 1001
    context.scene.frame_end = new_end
    context.scene.frame_current = 1001

    if bpy.ops.wm.save_as_mainfile.poll():
        bpy.ops.wm.save_as_mainfile(filepath=save_path)
        return True
    else:
        return False

def build_shot_files(context, ignoreDisabled=True):
    props = config.getAddonProps(context.scene)
    save_dir = props.build_shots_save_dir
    if bpy.data.is_dirty:
        if bpy.data.filepath != "":
            bpy.ops.wm.save_mainfile('INVOKE_DEFAULT')
        else:
            temp_path =  f"{save_dir}/sequence.blend"
            bpy.ops.wm.save_as_mainfile(filepath=temp_path)
    current_file_path = bpy.data.filepath
    current_take = props.getCurrentTake()
    shots = [shot.name for shot in current_take.getShotsList(ignoreDisabled=ignoreDisabled)]
    saved_shots = []
    for shot_name in shots:
        save_path = f"{save_dir}/{shot_name}.blend"
        if  build_single_shot_file(context, shot_name, save_path):
            saved_shots.append(shot_name)
        bpy.ops.wm.open_mainfile(filepath=current_file_path)
       # config.getAddonProps(context.scene).initialize_shot_manager()
    return saved_shots

class UAS_OT_BuildShotFiles(Operator):
    bl_idname = "uas_shot_manager.build_shot_files"
    bl_label = "Build Shot Files"
    bl_description = "Build shot files for the current scene"

   # save_dir: bpy.props.StringProperty(name="Save Directory", default="\\", subtype="DIR_PATH")

    @classmethod
    def poll(cls, context):
        scene = context.scene
        props = config.getAddonProps(scene)
        return props.getNumShots() > 0 and exists(props.build_shots_save_dir)

    def execute(self, context):
        saved_shots = build_shot_files(context)
        if len(saved_shots) > 0:
            self.report({"INFO"}, f"Saved {len(saved_shots)} shot files")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, "Failed to save shot files")
            return {"CANCELLED"}

def register():
    bpy.utils.register_class(UAS_OT_BuildShotFiles)

def unregister():
    bpy.utils.unregister_class(UAS_OT_BuildShotFiles)

if __name__ == "__main__":
    register()