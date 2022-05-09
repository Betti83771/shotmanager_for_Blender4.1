# GPLv3 License
#
# Copyright (C) 2021 Ubisoft
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Shot Manager grease pencil tools and specific operators
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty

from random import uniform

from shotmanager.utils import utils


class UAS_ShotManager_CreateNStoryboardShots(Operator):
    bl_idname = "uas_shot_manager.create_n_storyboard_shots"
    bl_label = "Create Specifed Number of Storyboard Shots..."
    bl_description = "Create a specified number of storyboard shots, each one with its own camera"
    bl_options = {"REGISTER", "UNDO"}

    name: StringProperty(name="Name")
    # cameraName: EnumProperty(items=list_cameras, name="Camera", description="Select a Camera")
    start: IntProperty(
        name="Start",
        subtype="TIME",
    )
    duration: IntProperty(
        name="Duration",
        min=1,
        subtype="TIME",
    )
    offsetFromPrevious: IntProperty(
        name="Time Offset Between Shots",
        description="Number of frames from which the start of a storyboard frame will be offset from the end of the one preceding it",
        subtype="TIME",
        default=1,
    )
    count: IntProperty(name="Number of Shots to Create", min=1, soft_max=20, default=10)

    # color: FloatVectorProperty(
    #     name="Color",
    #     subtype="COLOR",
    #     size=3,
    #     description="Shot Color",
    #     min=0.0,
    #     max=1.0,
    #     precision=2,
    #     # default=(uniform(0, 1), uniform(0, 1), uniform(0, 1)),
    #     default=(1.0, 1.0, 1.0),
    # )

    def invoke(self, context, event):
        wm = context.window_manager
        props = context.scene.UAS_shot_manager_props
        prefs = context.preferences.addons["shotmanager"].preferences

        # self.name = f"{props.new_shot_prefix}{len ( props.getShotsList() ) + 1:02}" + "0"
        # self.name = (props.project_shot_format.split("_")[2]).format((len(props.getShotsList()) + 1) * 10)
        self.name = props.getShotPrefix((len(props.getShotsList()) + 1) * 10)

        # self.start = max(context.scene.frame_current, 10)
        self.start = prefs.storyboard_default_start_frame

        self.duration = prefs.storyboard_new_shot_duration

        # default interval is set to 1 seconde
        # self.offsetFromPrevious = context.scene.render.fps

        # all the shots start at the same time
        self.offsetFromPrevious = 0

        # camName = props.getActiveCameraName()
        # if "" != camName:
        #     self.cameraName = camName

        #  self.color = (uniform(0, 1), uniform(0, 1), uniform(0, 1))

        return wm.invoke_props_dialog(self, width=360)

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.row(align=True)
        grid_flow = row.grid_flow(align=True, row_major=True, columns=2, even_columns=False)

        col = grid_flow.column(align=False)
        col.label(text="Number of Shots:")
        col = grid_flow.column(align=False)
        col.prop(self, "count", text="")

        # col.separator(factor=2)
        # col = grid_flow.column(align=False)
        # col.scale_x = 0.6
        # col.label(text="New Shot Name:")
        # col = grid_flow.column(align=False)
        # col.prop(self, "name", text="")
        # col = grid_flow.column(align=False)
        # col.label(text="Camera:")
        # col = grid_flow.column(align=False)
        # col.prop(self, "cameraName", text="")

        col.separator(factor=1)

        col = grid_flow.column(align=False)
        col.label(text="Start:")
        col = grid_flow.column(align=False)
        col.prop(self, "start", text="")

        col = grid_flow.column(align=False)
        col.label(text="Duration:")
        col = grid_flow.column(align=False)
        col.prop(self, "duration", text="")

        # col = grid_flow.column(align=False)
        # col.label(text="Time Offset From Previous:")
        # col = grid_flow.column(align=False)
        # col.prop(self, "offsetFromPrevious", text="")

        # if not context.scene.UAS_shot_manager_props.use_camera_color:
        #     col = grid_flow.column(align=False)
        #     col.label(text="Color:")
        #     col = grid_flow.column(align=True)
        #     col.prop(self, "color", text="")

        layout.separator()

    def execute(self, context):
        scene = context.scene
        props = scene.UAS_shot_manager_props
        # grid = props.stb_frameTemplate.frameGrid
        selectedShotInd = props.getSelectedShotIndex()
        newShotInd = selectedShotInd + 1
        firstCreatedShotInd = newShotInd

        cam = None

        # if "" != self.cameraName:
        #     cam = bpy.context.scene.objects[self.cameraName]
        #     if props.use_camera_color:
        #         col[0] = cam.color[0]
        #         col[1] = cam.color[1]
        #         col[2] = cam.color[2]

        for i in range(1, self.count + 1):
            # startFrame = self.start + (i - 1) * (self.duration - 1 + self.offsetFromPrevious)
            startFrame = self.start
            endFrame = startFrame + self.duration - 1

            col = (uniform(0, 1), uniform(0, 1), uniform(0, 1), 1.0)

            cam = utils.create_new_camera("Cam_" + self.name)

            newShot = props.addShot(
                shotType="STORYBOARD",
                atIndex=newShotInd,
                name=props.getShotPrefix((len(props.getShotsList()) + 1) * 10),
                # name=props.getUniqueShotName(props.project_shot_format.split("_")[2]).format(
                #     (len(props.getShotsList()) + 1) * 10
                # ),
                start=startFrame,
                end=endFrame,
                camera=cam,
                color=col,
                addGreasePencilStoryboard=True,
            )

            # create storyboard grease pencil
            # newShot.addGreasePencil(mode="STORYBOARD")

            newShotInd += 1

        props.updateStoryboardGrid()
        # props.setCurrentShotByIndex(newShotInd - 1)
        # props.setSelectedShotByIndex(newShotInd - 1)
        props.setCurrentShotByIndex(firstCreatedShotInd)
        props.setSelectedShotByIndex(firstCreatedShotInd)
        bpy.ops.uas_shot_manager.scenerangefromtake("INVOKE_DEFAULT")
        bpy.ops.uas_shot_manager.frame_time_range("INVOKE_DEFAULT")
        bpy.ops.ed.undo_push()
        return {"INTERFACE"}


_classes = (UAS_ShotManager_CreateNStoryboardShots,)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
