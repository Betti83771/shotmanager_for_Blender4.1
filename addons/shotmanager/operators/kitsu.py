import bpy

import gazu


from os import path, listdir
from pathlib import Path
from shotmanager.config import config
from shotmanager.api import shot_manager, shot
from bpy.types import Operator
from ..kitsu_connection import cache, prefs
from  ..kitsu_shotbuilder import shotbuilder_core as core

from random import uniform
from math import radians

class KitsuScene(bpy.types.PropertyGroup):
   name: bpy.props.StringProperty(name="Scene name", default="Unknown")
   number: bpy.props.IntProperty()


class KitsuSequence(bpy.types.PropertyGroup):
   name: bpy.props.StringProperty(name="Sequence name", default="Unknown")
   scenes: bpy.props.IntVectorProperty()
   scenes_coll:  bpy.props.CollectionProperty(type=KitsuScene)

def get_kitsu_scenes(ksequence):
   """From the retrived shot data, sets up and rertrieves scenes"""
   kshots = gazu.shot.all_shots_for_sequence(ksequence)
   kscenes = {}
   for kshot in kshots:
      if not kshot["data"]: continue
      if "scene" not in kshot["data"].keys(): continue
      scene_name = kshot["data"]["scene"]
      kscene = gazu.scene.get_scene_by_name(ksequence, scene_name )
      if not kscene:
         kscene = gazu.scene.new_scene(cache.project_active_get().id, ksequence, scene_name)
      gazu.scene.add_shot_to_scene(kscene, kshot)
      if scene_name not in kscenes.keys():
         kscenes[scene_name] = kscene
   return kscenes


def gen_shots_from_kitsu(props, kitsu_props, shot_info, last_idx):
   # check if shots already exist in the current take
   current_take = shot_manager.get_current_take(props)
   shots = shot_manager.get_shots(props, shot_manager.get_take_index(props, current_take))
      
   if not current_take: 
      new_take = shot_manager.add_take(props, at_index=0, name="Main Take")

   
   

   if len(shots )> 1:
      # disable removed shots
      for sh in shots:
         if sh.name not in (si[0] for si in shot_info.values()):
            sh.enabled = False
      cursor = max(s.end for s in shots)+1
   else:
      cursor=0

   

   for i in range(0, last_idx+1):
      if i not in shot_info: continue
      shot_name = shot_info[i][0]
      shot_duration = shot_info[i][1]

      existing_shot = shot_manager.get_shot_by_name(props, shot_name)

      if existing_shot:
         # Flag differences in length
         existing_shot.kitsu_altert_duration = shot_duration

         # replace bkg animatic
         if shot_info[i][2]:
            existing_shot.removeBGImages()
            existing_shot.addBGImages(
                  shot_info[i][2], frame_start=existing_shot.start, alpha=props.shotsGlobalSettings.backgroundAlpha, addSoundFromVideo=True
            )
         
         existing_shot.bgImages_linkToShotStart = True
         #reorder following the index
         props.moveShotToIndex(existing_shot, i)
      
      else:
         # add at the end of the blender timeline,  shotmanager list matched index 
         shot_name = shot_info[i][0]
         shot_duration = shot_info[i][1]
         if "SM_Cameras" not in bpy.data.collections.keys():
            camera_coll = bpy.data.collections.new( "SM_Cameras")
            bpy.context.scene.collection.children.link(camera_coll)
         else:
            camera_coll = bpy.data.collections["SM_Cameras"]
      

         # create camera to assign to shot
         cam = bpy.data.cameras.new("Camera01")
         cam_shot_1 = bpy.data.objects.new(cam.name, cam)
         camera_coll.objects.link(cam_shot_1)
         cam_shot_1.location = (0.0, 0.0, 1.0)
         cam_shot_1.color = [uniform(0, 1), uniform(0, 1), uniform(0, 1), 1]
         cam_shot_1.rotation_euler = (radians(90), 0.0, radians(90))

         # add shot
         new_shot = shot_manager.add_shot(
            props,
            at_index=i, 
            take_index=-1,  # will be added to the current take
            name=shot_name,
            start=cursor,  # avoid using a short start value before the lenght of the handles (which is 10)
            end=cursor+shot_duration-1,
            camera=None,
            color=cam_shot_1.color, 
            enabled=True,
         )
         shot.set_camera(new_shot, cam_shot_1)
         new_shot.kitsu_altert_duration = shot_duration
         # add bkg animatic
         if shot_info[i][2]:
            new_shot.addBGImages(
                  shot_info[i][2], frame_start=cursor, alpha=props.shotsGlobalSettings.backgroundAlpha, addSoundFromVideo=True
            )
         
         new_shot.bgImages_linkToShotStart = True
         cursor = cursor + shot_duration
    
def download_preview(kshot):
   
   if bpy.data.filepath == "":
      file_base_path = prefs.project_root_dir_get(bpy.context)
   else:
      file_base_path  = Path(bpy.data.filepath).parent
   preview_base_path = path.join(file_base_path,  "_PREVIEWS", "")
   preview =  kshot["preview_file_id"] 
   if not preview: return
   preview_file= gazu.files.get_preview_file(preview)
   preview_path = path.join(preview_base_path, preview_file["original_name"]+"."+preview_file["extension"])
   Path(preview_base_path).mkdir(parents=True, exist_ok=True)
   gazu.files.download_preview_file(preview, preview_path)
   return preview_path


def scene_coll_from_array(sequence):
   for number in sequence.scenes:
      if number == 0: continue # temp soultion
      scene = sequence.scenes_coll.add()
      scene.name = str(number).zfill(4)
      scene.number = number

def retrieve_shot_info_from_kitsu(kscene):
   """ Returns a dict: {
   "0": (shot name, shot duration, preview path, assets) 
   }
   the index is the shot index 
   also returns the biggest index
   the shots outside index get an index assigned
   """
   info = {}
   outside_idx = []
   biggest_idx = 0
   for kshot in gazu.scene.all_shots_for_scene(kscene):
      preview_path = download_preview(kshot)
      if kshot["data"]:
         if ("index" in kshot["data"].keys()) and (kshot["data"]["index"] is not None) and kshot["nb_frames"]:
            info[kshot["data"]["index"]] = (kshot["name"], kshot["nb_frames"], preview_path, gazu.asset.all_assets_for_shot(kshot))
            if kshot["data"]["index"] > biggest_idx:
               biggest_idx = kshot["data"]["index"]
         elif kshot["nb_frames"]:
            outside_idx.append((kshot["name"], kshot["nb_frames"], preview_path,  gazu.asset.all_assets_for_shot(kshot)))
      elif kshot["nb_frames"]:
         outside_idx.append((kshot["name"], kshot["nb_frames"], preview_path,  gazu.asset.all_assets_for_shot(kshot)))
      

   for sh in outside_idx:
      biggest_idx += 1
      info[biggest_idx] = sh

   return info, biggest_idx

def popup_chose_prod_timer_func():
   if bpy.context.window_manager.choose_prod_popup_running:
      return 0.5
   else:
      return

   
def retrieve_scene_info_from_kitsu(sequences):
   """Retrieve info on sequence and scene from Kitsu, to prompt sequence to the user
   and check wether the prompted shot exists. 
   Fills the sequences collection passed as argument and returns true if successful"""

   project = cache.project_active_get()
   if not project: 
      bpy.ops.kitsu.con_productions_load('INVOKE_DEFAULT')
      return False
   ksequences = gazu.shot.all_sequences_for_project(project.id)
   for ksequence in ksequences:
      seq1 = sequences.add()
      seq1.name=ksequence["name"]
      for i, kscene in enumerate(get_kitsu_scenes(ksequence).values()):
         scene = seq1.scenes_coll.add()
         scene.name = kscene["name"]
         scene_num = int(scene.name)
         seq1.scenes[i] = scene_num
   return True

class UAS_GenShotsFromKitsu(Operator):
   bl_idname = "uas_shot_manager.gen_shots_from_kitsu"
   bl_label = "Update shots from Kitsu"
   bl_description = "Sets up the shots according to the Kitsu structure"
   bl_options = { "UNDO_GROUPED"}

   @classmethod
   def poll(cls, context):
      return context.scene.kitsu.scene_active_name != ""


   def execute(self, context):
      props = config.getAddonProps(context.scene)
      kitsu_props = context.scene.kitsu
      if kitsu_props.sequence_active_name == "":
         self.report('ERROR', "Kitsu update shots error: Active sequence name missing. ")
         return {'CANCELLED'}
      session = prefs.session_get(context)
      current_proj_name = cache.project_active_get().name
      session.end()
      gazu.cache.clear_all()
      cache.clear_cache_variables()
      session.start()
      proj = gazu.project.get_project_by_name(current_proj_name)
      cache.project_active_set_by_id(context, proj["id"])
      cache.init_cache_variables()
      kseq = gazu.shot.get_sequence_by_name(proj, kitsu_props.sequence_active_name)
      shot_info, last_idx  = retrieve_shot_info_from_kitsu(gazu.scene.get_scene_by_name(kseq, kitsu_props.scene_active_name))
      gen_shots_from_kitsu(props, kitsu_props, shot_info, last_idx)

      return {"FINISHED"}
    

    
class UAS_BuildSceneFileFromKitsu(Operator):
   """Draw a menu that prompts sequence from the ones available on Kitsu,
    and scene is a string property with search prop.
    """
   bl_idname = "uas_shot_manager.build_scene_file_from_kitsu"
   bl_label = "Build new SCENE file"
   bl_description = "Sets up the scene according to the Kitsu structure"
   bl_options = { "UNDO_GROUPED"}
   
   sequences: bpy.props.CollectionProperty(type=KitsuSequence, name="Sequences")

   def chosen_seq_items(self, context):
      items = []
      for item in self.sequences:
         items.append((item.name, item.name, item.name))
      return items
   
   

   chosen_seq: bpy.props.EnumProperty(items=chosen_seq_items)
   chosen_scene: bpy.props.StringProperty("Scene")

   def get_chosen_seq(self):
      return next((item for item in self.sequences if item.name==self.chosen_seq), None)

   def build_scene_file_from_kitsu(self, context, props, kitsu_props, shot_info, last_idx):
      """See Blender Kitsu scene builder"""
      

      scene = context.scene
      scene.name = self.chosen_scene
      project_root_dir = prefs.project_root_dir_get(context)

      assets_to_link = []
      for i in range(0, last_idx+1):
         if i not in shot_info: continue
         shot_name = shot_info[i][0]
         shot_duration = shot_info[i][1]

         kitsu_assets = shot_info[i][3]
         assets_to_link.extend(a for a in kitsu_assets if a not in assets_to_link)
         
      for asset in assets_to_link:
         if asset["data"]["filepath"].startswith(path.sep):
            asset["data"]["filepath"] = asset["data"]["filepath"][1:]
         filepath = project_root_dir.joinpath(asset["data"]["filepath"])#.absolute()
         asset_name = asset["name"]
         if not filepath.exists():
            print(f"Asset '{asset_name}' filepath '{str(filepath)}' does not exist. Skipping")
            continue
         collection = asset["data"]["collection"]
         
         print(collection)
         asset_type = gazu.asset.get_asset_type(asset["entity_type_id"])["name"]
         if asset_type == '3D Set Asset':
            linked_collection = core.link_data_block(
                file_path=str(filepath),
                data_block_name=collection,
                data_block_type="Collection",
            )
            print(f"'{collection}': Succesfully Linked")
         elif asset_type == '3D Character Asset ':
            linked_collection = core.link_and_override_collection(
                collection_name=collection, file_path=str(filepath), scene=scene
            )
            core.add_action_to_armature(linked_collection, shot)
            print(f"'{collection}': Succesfully Linked & Overriden") 
      return


   @classmethod
   def poll(cls, context):
      # this file is not already a Kitsu scene
      
      return context.scene.kitsu.scene_active_name == ""
   
   def invoke(self, context, event):
      self.prod = cache.project_active_get()

      if not retrieve_scene_info_from_kitsu(self.sequences): return {"CANCELLED"}

      return context.window_manager.invoke_props_dialog(self, width=300)

   def draw(self, context):
      props = config.getAddonProps(context.scene)
      layout = self.layout
      col=layout.column()
      col.label(text=f"Production: {self.prod.name}")
      col.label(text="Choose a sequence:")
      col.prop(self, "chosen_seq", text="")
      col.label(text="Choose a scene:")
      chosen_seq = self.get_chosen_seq()
      if len(chosen_seq.scenes_coll) > 0:
         if self.chosen_scene=="":
            self.chosen_scene = chosen_seq.scenes_coll[0].name
         col.prop_search(self, "chosen_scene", chosen_seq, "scenes_coll", text='', results_are_suggestions=False)
         if self.chosen_scene not in chosen_seq.scenes_coll:
            col.label(text="No Kitsu data found on this scene.", icon='ERROR')
      else:
         col.label(text="No Kitsu data found on this sequence.", icon='ERROR')

  

   def execute(self, context):
      props = config.getAddonProps(context.scene)
      project_root_dir = prefs.project_root_dir_get(context)
      kitsu_props = context.scene.kitsu
      kseq = gazu.shot.get_sequence_by_name(cache.project_active_get().id, self.chosen_seq)

      

      # delete all existing  objects
      for obj in reversed(bpy.data.objects):
         bpy.data.objects.remove(obj)
      bpy.data.orphans_purge()
      shot_info, last_idx  = retrieve_shot_info_from_kitsu(gazu.scene.get_scene_by_name(kseq, self.chosen_scene))
      self.build_scene_file_from_kitsu(context, props, kitsu_props, shot_info, last_idx)
      gen_shots_from_kitsu(props, kitsu_props, shot_info, last_idx)
      
      
      # TODO save file in correct location
      savefile_path = path.join(project_root_dir, self.chosen_seq, "")
      Path(savefile_path).mkdir(parents=True, exist_ok=True)
      filepath =path.join(savefile_path, "SH" +self.chosen_scene )
      if Path(filepath+".blend").exists():
         count=1
         filepath = filepath + "_V000"
         biggest_ver_found = filepath
         n_of_files = len(listdir(savefile_path))
         for i in range(1, n_of_files+1):
            filepath = filepath[:-3] + str(int(filepath[-3:]) + 1).zfill(3)
            if  Path(filepath+".blend").exists():
               biggest_ver_found = filepath
         
         filepath = biggest_ver_found[:-3] + str(int(biggest_ver_found[-3:]) + 1).zfill(3)
      filepath = filepath+".blend"

      # set file path
      props.kitsu_current_file_path = bpy.data.filepath.replace(str(project_root_dir), path.sep)
      kitsu_props.scene_active_name = self.chosen_scene
      kitsu_props.sequence_active_name = self.chosen_seq
      bpy.ops.wm.save_as_mainfile(filepath=filepath, check_existing=True)
      return {"FINISHED"}
   
class UAS_OpenKitsuSceneFile(Operator):
   """Draw a menu that prompts sequence and scene from the ones available on Kitsu."""
   bl_idname = "uas_shot_manager.open_kitsu_scene_file"
   bl_label = "Open existing SCENE file"
   bl_description = "Prompts sequence and scene from Kitsu database to be opened."
   bl_options = { "UNDO_GROUPED"}
   
   sequences: bpy.props.CollectionProperty(type=KitsuSequence, name="Sequences")

   

   def chosen_seq_items(self, context):
      items = []
      for item in self.sequences:
         items.append((item.name, item.name, item.name))
      return items
   
   
   chosen_seq: bpy.props.EnumProperty(items=chosen_seq_items)

   def get_chosen_seq(self):
      return next((item for item in self.sequences if item.name==self.chosen_seq), None)

   def scene_search(self, context, edit_text):
      chosen_seq = UAS_OpenKitsuSceneFile.get_chosen_seq(self)
      scenes = []
      project_root_dir = prefs.project_root_dir_get(context)
      openfile_path = path.join(project_root_dir, self.chosen_seq, "")
      files = listdir(openfile_path)
      for scene in chosen_seq.scenes_coll:
         for f in files:
            if scene.name in f:
               scenes.append(scene.name)
               break

      return scenes
   
   
   chosen_scene: bpy.props.StringProperty("Scene", search=scene_search,)
   


   @classmethod
   def poll(cls, context):
      # this file is not already a Kitsu scene
      return context.scene.kitsu.scene_active_name == ""
   
   def invoke(self, context, event):
      self.prod = cache.project_active_get()

      if not retrieve_scene_info_from_kitsu(self.sequences): return {"CANCELLED"}

      return context.window_manager.invoke_props_dialog(self, width=300)

   def draw(self, context):
      props = config.getAddonProps(context.scene)
      layout = self.layout
      col=layout.column()
      col.label(text=f"Production: {self.prod.name}")
      col.label(text="Choose a sequence:")
      col.prop(self, "chosen_seq", text="")
      col.label(text="Choose a scene:")
      chosen_seq = self.get_chosen_seq()
      if len(chosen_seq.scenes_coll) > 0:
         if self.chosen_scene=="":
            self.chosen_scene = self.scene_search(context, "")[0]
        # col.prop_search(self, "chosen_scene", chosen_seq, "scenes_coll", text='', results_are_suggestions=False)
         col.prop(self, "chosen_scene",  text='')
         if self.chosen_scene not in chosen_seq.scenes_coll:
            col.label(text="No Kitsu scene data found on this scene.", icon='ERROR')
      else:
         col.label(text="No Kitsu data found on this sequence.", icon='ERROR')

 

   def execute(self, context):
      props = config.getAddonProps(context.scene)
      kitsu_props = context.scene.kitsu
      project_root_dir = prefs.project_root_dir_get(context)
      # TODO open file in correct location
      openfile_path = path.join(project_root_dir, self.chosen_seq, "")
      if not Path(openfile_path).exists():
         self.report(type='ERROR', message=f"Path not found: {openfile_path}.")
         return {'CANCELLED'}
      filepath = path.join(openfile_path, "SH" +self.chosen_scene )
      scenes_in_folder = tuple(f for f in listdir(openfile_path) if "SH" +self.chosen_scene in f)
      if len(scenes_in_folder)>1:
         filepath = filepath+ "_V001"
         biggest_ver_found = filepath
         for f in scenes_in_folder:
            filepath = filepath[:-3] + str(int(filepath[-3:]) + 1).zfill(3)
            if  Path(filepath+".blend").exists():
               biggest_ver_found = filepath
         
         filepath = biggest_ver_found
      filepath = filepath+".blend"
      bpy.ops.wm.open_mainfile(filepath=filepath)
      return {"FINISHED"}

_classes = (
   KitsuScene,
   KitsuSequence,
   UAS_GenShotsFromKitsu,
   UAS_BuildSceneFileFromKitsu,
   UAS_OpenKitsuSceneFile
)


def register():
   for clss in _classes:
        
      bpy.utils.register_class(clss)


def unregister():
   for cls in reversed(_classes):
      bpy.utils.unregister_class(cls)
