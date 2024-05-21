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
UI in BGL for the Interactive Shots Stack overlay tool
"""

from collections import defaultdict

import os
from mathutils import Vector

import bgl
import gpu


from ..shots_stack_bgl import get_lane_origin_y

from shotmanager.utils import utils_editors_dopesheet
from shotmanager.utils.utils import color_to_linear

# from shotmanager.gpu.gpu_2d.class_Mesh2D import Mesh2D
from shotmanager.gpu.gpu_2d.class_Mesh2D import build_rectangle_mesh
from shotmanager.gpu.gpu_2d.class_QuadObject import QuadObject
from shotmanager.gpu.gpu_2d.class_Component2D import Component2D
from shotmanager.gpu.gpu_2d.class_Text2D import Text2D

from shotmanager.overlay_tools.workspace_info import workspace_info

from shotmanager.overlay_tools.interact_shots_stack.widgets.shots_stack_clip_component import ShotClipComponent
from shotmanager.overlay_tools.interact_shots_stack.widgets.shots_stack_info_component import InfoComponent

from shotmanager.config import config
from shotmanager.config import sm_logging

_logger = sm_logging.getLogger(__name__)

UNIFORM_SHADER_2D = gpu.shader.from_builtin("UNIFORM_COLOR")


class ShotStackWidget:
    def __init__(self, target_area=None):
        prefs = config.getAddonPrefs()

        self.useDebugComponents = False

        self.context = None
        self.target_area = target_area

        self.ui_shots = list()
        self.shotComponents = []
        self.infoComponent = None

        self.prev_mouse_x = 0
        self.prev_mouse_y = 0
        self.frame_under_mouse = -1

        self.mouseFrame = -1
        self.previousMouseFrame = -1

        self.previousDrawWasInAClip = False
        self.manipulatedComponent = None

        self.debug_mesh = None
        self.debug_quadObject = None
        self.debug_quadObject_Ruler = None
        self.debug_quadObject_test = None

        self.color_currentShot_border = color_to_linear((0.92, 0.55, 0.18, 0.99))
        # self.color_currentShot_border = (1, 0, 0, 1)
        self.color_currentShot_border_mix = (0.94, 0.3, 0.1, 0.99)

        # prefs settings ###################
        self.opacity = prefs.shtStack_opacity
        self.color_text = (0.0, 0.0, 0.0, 1)

    def init(self, context):
        self.context = context

        self.rebuildShotComponents()

        self.currentShotBorder = QuadObject(
            posXIsInRegionCS=False,
            posYIsInRegionCS=False,
            widthIsInRegionCS=False,
            heightIsInRegionCS=False,
            alignment="BOTTOM_LEFT",
            alignmentToRegion="TOP_LEFT",
        )
        self.currentShotBorder.hasFill = False
        self.currentShotBorder.hasLine = True
        self.currentShotBorder.colorLine = self.color_currentShot_border_mix
        self.currentShotBorder.lineThickness = 2
        self.currentShotBorder.isVisible = False
        # self.currentShotBorder.lineOffsetPerEdge = [0, -1, -1, 0]

        # wip not super clean
        config.gRedrawShotStack = True
        config.gRedrawShotStack_preDrawOnly = True

        self.infoComponent = InfoComponent(shotsStack=self)
        self.infoComponent.init(context)

        if self.useDebugComponents:
            ###############################################
            # debug
            ###############################################
            # height = 20
            # lane = 3
            # startframe = 120
            # numFrames = 15
            # origin = Vector([startframe, get_lane_origin_y(lane)])
            # self.debug_mesh = build_rectangle_mesh(origin, numFrames, height)

            # this quad is supposed to cover the time ruler all the time to check the top clipping zone
            # BOTTOM_LEFT TOP_LEFT
            self.debug_quadObject_Ruler = QuadObject(
                posXIsInRegionCS=True,
                posX=0,
                posYIsInRegionCS=True,
                posY=0,
                widthIsInRegionCS=True,
                width=1900,
                heightIsInRegionCS=True,
                height=utils_editors_dopesheet.getRulerHeight(),
                alignment="TOP_LEFT",
                alignmentToRegion="TOP_LEFT",
                displayOverRuler=True,
            )
            self.debug_quadObject_Ruler.color = (0.4, 0.0, 0.0, 0.5)

            self.debug_quadObject_test = QuadObject(
                posXIsInRegionCS=False,
                posX=20,
                posYIsInRegionCS=False,
                posY=1,
                widthIsInRegionCS=False,
                width=40,
                heightIsInRegionCS=False,
                height=10,
                alignment="TOP_LEFT",
                alignmentToRegion="TOP_LEFT",
            )
            self.debug_quadObject_test.color = (0.0, 0.4, 0.0, 0.5)
            imgFile = os.path.join(os.path.dirname(__file__), "../../../icons/ShotMan_EnabledCurrentCam.png")
            self.debug_quadObject_test.setImageFromFile(imgFile)
            self.debug_quadObject_test.hasTexture = True

            self.debug_quadObject = QuadObject(
                posXIsInRegionCS=True,
                posX=60,
                posYIsInRegionCS=True,
                posY=90,
                widthIsInRegionCS=False,
                width=25,
                heightIsInRegionCS=True,
                height=70,
                alignment="TOP_LEFT",
                alignmentToRegion="BOTTOM_RIGHT",
            )

            self.debug_component2D = Component2D(
                self.target_area,
                posXIsInRegionCS=False,
                posX=15,
                posYIsInRegionCS=False,
                posY=3,
                widthIsInRegionCS=False,
                width=20,
                heightIsInRegionCS=False,
                height=2,
                alignment="BOTTOM_LEFT",
                alignmentToRegion="BOTTOM_LEFT",
            )
            self.debug_component2D.color = (0.7, 0.5, 0.6, 0.6)
            self.debug_component2D.hasLine = True
            self.debug_component2D.colorLine = (0.7, 0.8, 0.8, 0.9)
            self.debug_component2D.lineThickness = 3

            self.debug_Text2D = Text2D(
                posXIsInRegionCS=False,
                posX=25,
                posYIsInRegionCS=False,
                posY=6,
                alignment="BOTTOM_LEFT",
                alignmentToRegion="BOTTOM_LEFT",
                text="MyText",
                fontSize=20,
            )

    def rebuildShotComponents(self, forceRebuild=False):
        props = self.context.scene.UAS_shot_manager_props
        shots = props.get_shots()
        # lenShots = len(shots)

        if not len(shots):
            self.shotComponents = []
            return

        rebuildList = forceRebuild or len(self.shotComponents) != len(shots)

        # check if the components list matches the shots list
        if not rebuildList:
            shotCompoInd = 0
            for _i, shot in enumerate(shots):
                if self.shotComponents[shotCompoInd].shot != shot:
                    rebuildList = True
                    break
                shotCompoInd += 1

        # rebuild the list with ALL the shots
        if rebuildList:
            self.shotComponents = []

            lane = 1
            for _i, shot in enumerate(shots):
                shotCompo = ShotClipComponent(self.target_area, posY=lane, shot=shot, shotsStack=self)
                shotCompo.opacity = self.opacity
                shotCompo.color_text = self.color_text

                self.shotComponents.append(shotCompo)
                lane += 1

    def drawCurrentShotDecoration(self, shotCompoCurrent, preDrawOnly=False):
        """Draw the quad lines for the current shot"""
        if shotCompoCurrent:
            self.currentShotBorder.posX = shotCompoCurrent.posX
            self.currentShotBorder.posY = shotCompoCurrent.posY
            self.currentShotBorder.width = shotCompoCurrent.width
            self.currentShotBorder.height = shotCompoCurrent.height
            self.currentShotBorder.isVisible = True
            self.currentShotBorder.draw(None, self.context.region, preDrawOnly=preDrawOnly)
        else:
            self.currentShotBorder.isVisible = False

    def drawShots(self, preDrawOnly=False):
        props = self.context.scene.UAS_shot_manager_props
        prefs = config.getAddonPrefs()
        self.rebuildShotComponents()

        currentShotInd = props.getCurrentShotIndex()
        selectedShotInd = props.getSelectedShotIndex()

        debug_maxShots = 5000  # 6

        lane = 1 + prefs.shtStack_firstLineIndex
        shotCompoCurrent = None
        for i, shotCompo in enumerate(self.shotComponents):
            shotCompo.isCurrent = i == currentShotInd

            # NOTE: we use _isSelected instead of the property isSelected in order
            # to avoid the call of the callback function _on_selected_changed, otherwise
            # the event loops and keep redrawing all the time
            shotCompo._isSelected = i == selectedShotInd

            if debug_maxShots < i:
                shotCompo.isVisible = False
                continue
            if not shotCompo.shot.enabled and not props.interactShotsStack_displayDisabledShots:
                shotCompo.isVisible = False
                continue

            if i == currentShotInd:
                shotCompoCurrent = shotCompo
            shotCompo.isVisible = True
            shotCompo.posY = lane

            shotCompo.draw(None, self.context.region, preDrawOnly=preDrawOnly)
            lane += 1

        # draw quad for current shot over the result
        self.drawCurrentShotDecoration(shotCompoCurrent, preDrawOnly=preDrawOnly)

    def drawShots_compactMode(self, preDrawOnly=False):
        # return
        props = self.context.scene.UAS_shot_manager_props
        prefs = config.getAddonPrefs()
        self.rebuildShotComponents()

        currentShot = props.getCurrentShot()
        selectedShot = props.getSelectedShot()

        shotComponentsSorted = sorted(self.shotComponents, key=lambda shotCompo: shotCompo.shot.start)

        shots_from_lane = defaultdict(list)

        shotCompoCurrent = None
        for i, shotCompo in enumerate(shotComponentsSorted):
            if not props.interactShotsStack_displayDisabledShots and not shotCompo.shot.enabled:
                shotCompo.isVisible = False
                continue
            lane = 1 + prefs.shtStack_firstLineIndex
            if i > 0:
                for ln, shots_in_lane in shots_from_lane.items():
                    for s in shots_in_lane:
                        if s.start <= shotCompo.shot.start <= s.end:
                            break
                    else:
                        lane = ln
                        break
                else:
                    if len(shots_from_lane):
                        lane = max(shots_from_lane) + 1  # No free lane, make a new one.
                    else:
                        #   lane = ln
                        pass
            shots_from_lane[lane].append(shotCompo.shot)

            shotCompo.isCurrent = shotCompo.shot == currentShot

            # NOTE: we use _isSelected instead of the property isSelected in order
            # to avoid the call of the callback function _on_selected_changed, otherwise
            # the event loops and keep redrawing all the time
            shotCompo._isSelected = shotCompo.shot == selectedShot

            if shotCompo.isCurrent:
                shotCompoCurrent = shotCompo
            shotCompo.isVisible = True
            shotCompo.posY = lane
            shotCompo.draw(None, self.context.region, preDrawOnly=preDrawOnly)

        # draw quad for current shot over the result
        self.drawCurrentShotDecoration(shotCompoCurrent, preDrawOnly=preDrawOnly)

    def draw(self, preDrawOnly=False):
        if self.target_area is not None and self.context.area != self.target_area:
            return

        props = self.context.scene.UAS_shot_manager_props

        # Debug - red rectangle ####################
        if self.useDebugComponents:
            height = 20
            lane = 5
            startframe = 160
            numFrames = 15
            origin = Vector([startframe, get_lane_origin_y(lane)])
            self.debug_mesh = build_rectangle_mesh(origin, numFrames, height)

            bgl.glEnable(bgl.GL_BLEND)
            UNIFORM_SHADER_2D.bind()
            color = (0.9, 0.0, 0.0, 0.9)
            UNIFORM_SHADER_2D.uniform_float("color", color)

            # self.debug_mesh.draw(UNIFORM_SHADER_2D, self.context.region)

            # Quad object
            ###############################

            # self.debug_quadObject_Ruler.draw(None, self.context.region)
            self.debug_quadObject_test.draw(None, self.context.region)
            # self.debug_quadObject.draw(None, self.context.region)
            self.debug_component2D.draw(None, self.context.region)
            self.debug_Text2D.draw(None, self.context.region)

            # draw text
            ###############################

            workspace_info.draw_callback__dopesheet_size(self, self.context, self.target_area)
            workspace_info.draw_callback__dopesheet_mouse_pos(self, self.context, self.target_area)
            workspace_info.draw_callback__dopesheet_lane_numbers(self, self.context, self.target_area)

            # return

        self.infoComponent.draw(None, self.context.region)

        if props.interactShotsStack_displayInCompactMode:
            self.drawShots_compactMode(preDrawOnly=preDrawOnly)
        else:
            self.drawShots(preDrawOnly=preDrawOnly)

    def validateAction(self):
        _logger.debug_ext("Validating Shot Stack action", col="GREEN", tag="SHOTSTACK_EVENT")
        pass

    def cancelAction(self):
        # TODO restore the initial
        _logger.debug_ext("Canceling Shot Stack action 22", col="ORANGE", tag="SHOTSTACK_EVENT")
        pass

    def handle_event(self, context, event, region):
        """Return True if the event is handled for ShotStackWidget"""
        # props = config.getAddonProps(context.scene)
        # prefs = config.getAddonPrefs()

        # _logger.debug_ext("*** handle event for ShotStackWidget", col="GREEN", tag="SHOTSTACK_EVENT")
        if not context.window_manager.UAS_shot_manager_toggle_shots_stack_interaction:
            return False

        event_handled = False
        # if event.type not in ["MOUSEMOVE", "INBETWEEN_MOUSEMOVE", "TIMER"]:
        #     _logger.debug_ext(f"  *** event in ShotStackWidget: {event.type}", col="GREEN", tag="SHOTSTACK_EVENT")

        # NOTE: context is different. Normal?
        context = self.context

        mouse_x, mouse_y = region.view2d.region_to_view(event.mouse_x - region.x, event.mouse_y - region.y)

        # update info component
        self.infoComponent.updateFromEvent(event)
        # if event.shift:
        #     # self.infoComponent.posY = 80
        #     # self.infoComponent.textLine01.posX = 40
        #     self.infoComponent.setText("Ctrl")
        #     self.infoComponent.setModifierKeyState(True)
        # else:
        #     # self.infoComponent.posY = 20
        #     # self.infoComponent.textLine01.posX = 10
        #     self.infoComponent.setText("4")
        #     self.infoComponent.setModifierKeyState(False)

        if event.type not in ["TIMER"]:
            _logger.debug_ext(f"event: type: {event.type}, value: {event.value}", col="GREEN", tag="SHOTSTACK_EVENT")

        for shotCompo in self.shotComponents:
            if not shotCompo.isVisible:
                continue
            event_handled = shotCompo.handle_event(context, event)
            if event_handled:
                break

        # debug
        if not event_handled:
            if self.useDebugComponents:
                event_handled = self.debug_component2D.handle_event(context, event)

        self.prev_mouse_x = event.mouse_x - region.x
        self.prev_mouse_y = event.mouse_y - region.y

        return event_handled
