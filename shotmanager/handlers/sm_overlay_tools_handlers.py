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
Handlers specific to overlay tools
"""

import bpy
from bpy.app.handlers import persistent

from shotmanager.utils import utils
from shotmanager.utils import utils_handlers

from shotmanager.config import sm_logging

_logger = sm_logging.getLogger(__name__)


def install_handler_for_shot(self, context):
    """Called in the update function of WindowManager.UAS_shot_manager_shots_play_mode
    """
    scene = context.scene

    scene.UAS_shot_manager_props.setResolutionToScene()

    if (
        self.UAS_shot_manager_shots_play_mode
        and shotMngHandler_frame_change_pre_jumpToShot not in bpy.app.handlers.frame_change_pre
    ):
        shots = scene.UAS_shot_manager_props.get_shots()
        for i, shot in enumerate(shots):
            if shot.start <= scene.frame_current <= shot.end:
                scene.UAS_shot_manager_props.current_shot_index = i
                break
        bpy.app.handlers.frame_change_pre.append(shotMngHandler_frame_change_pre_jumpToShot)
    #     bpy.app.handlers.frame_change_post.append(shotMngHandler_frame_change_pre_jumpToShot__frame_change_post)

    #    bpy.ops.uas_shot_manager.sequence_timeline ( "INVOKE_DEFAULT" )
    elif (
        not self.UAS_shot_manager_shots_play_mode
        and shotMngHandler_frame_change_pre_jumpToShot in bpy.app.handlers.frame_change_pre
    ):
        utils_handlers.removeAllHandlerOccurences(
            shotMngHandler_frame_change_pre_jumpToShot, handlerCateg=bpy.app.handlers.frame_change_pre
        )
        # utils_handlers.removeAllHandlerOccurences(
        #     shotMngHandler_frame_change_pre_jumpToShot__frame_change_post, handlerCateg=bpy.app.handlers.frame_change_post
        # )


def toggle_overlay_tools_display(context):
    # print("  toggle_overlay_tools_display:  self.UAS_shot_manager_display_overlay_tools: ", self.UAS_shot_manager_display_overlay_tools)
    prefs = context.preferences.addons["shotmanager"].preferences
    from shotmanager.overlay_tools.interact_shots_stack.shots_stack_toolbar import display_state_changed_intShStack

    if context.window_manager.UAS_shot_manager_display_overlay_tools:

        if context.window_manager.UAS_shot_manager__useSequenceTimeline:
            if prefs.toggle_overlays_turnOn_sequenceTimeline:
                a = bpy.ops.uas_shot_manager.sequence_timeline("INVOKE_DEFAULT")

        if prefs.toggle_overlays_turnOn_interactiveShotsStack:
            display_state_changed_intShStack(context)
    ###         context.window_manager.UAS_shot_manager__useInteracShotsStack = True

    # bpy.ops.uas_shot_manager.draw_camera_hud_in_viewports("INVOKE_DEFAULT")
    else:
        if prefs.toggle_overlays_turnOn_interactiveShotsStack:
            ###         context.window_manager.UAS_shot_manager__useInteracShotsStack = False
            display_state_changed_intShStack(context)

        pass
        # print(f"a operator timeline not updated")

        # bpy.ops.uas_shot_manager.sequence_timeline.cancel(context)
        # print(f"a b operator timeline not updated")
    # pistes pour killer un operateur:
    #   - mettre un Poll
    #   - faire un return Cancel dans le contenu
    #   - killer, d'une maniere ou d'une autre


def shotMngHandler_frame_change_pre_jumpToShot(scene):
    props = scene.UAS_shot_manager_props

    def get_previous_shot(shots, current_shot):
        index = props.getShotIndex(current_shot)
        if index > 0:
            previous_shots = [s for s in shots[:index] if s.enabled]
            if len(previous_shots):
                return previous_shots[-1]

        return None

    def get_next_shot(shots, current_shot):
        index = props.getShotIndex(current_shot)
        if index < len(shots) - 1:
            next_shots = [s for s in shots[index + 1 :] if s.enabled]
            if len(next_shots):
                return next_shots[0]

        return None

    shotList = props.get_shots()
    if len(shotList) <= 0:
        return

    current_shot_index = props.current_shot_index
    props.restartPlay = False

    current_shot = shotList[current_shot_index]
    current_frame = scene.frame_current

    # clip shot to scene timeframe. Might not be necessary
    current_shot_start = current_shot.start
    current_shot_end = current_shot.end

    scene_frame_start = scene.frame_preview_start if scene.use_preview_range else scene.frame_start
    scene_frame_end = scene.frame_preview_end if scene.use_preview_range else scene.frame_end

    if not bpy.context.screen.is_animation_playing:
        return

    if bpy.app.version[1] >= 90:
        not_scrubbing = not bpy.context.screen.is_scrubbing
    else:
        not_scrubbing = bpy.context.screen.is_animation_playing

    if not_scrubbing:
        # Order of if clauses is very important.

        if (
            current_frame == scene_frame_end and get_previous_shot(shotList, current_shot) is None
        ):  # While backward playing if we hit the last frame and we are playing the first shot jump to the last shot.
            last_enabled = [s for s in shotList if s.enabled][-1]
            props.setCurrentShot(last_enabled)
            scene.frame_current = last_enabled.end
        elif current_frame > current_shot_end:
            disp = current_frame - current_shot_end
            next_shot = get_next_shot(shotList, current_shot)
            while next_shot is not None:
                if disp < next_shot.getDuration():
                    props.setCurrentShot(next_shot)
                    scene.frame_current = next_shot.start + disp
                    break
                disp -= next_shot.getDuration()
                next_shot = get_next_shot(shotList, next_shot)
            else:
                # Scene end is farther than the last shot so loop back.
                props.setCurrentShot([s for s in shotList if s.enabled][0])
        elif (
            current_frame == scene_frame_start and get_next_shot(shotList, current_shot) is None
        ):  # While forward playing if we hit the first frame and we are playing the last shot jump to the first shot.
            # Seems that the first frame is always hit even in frame dropping playblack
            props.setCurrentShot([s for s in shotList if s.enabled][0])
        elif current_frame < current_shot_start:
            disp = current_shot_start - current_frame
            previous_shot = get_previous_shot(shotList, current_shot)
            while previous_shot is not None:
                if disp < previous_shot.getDuration():
                    props.setCurrentShot(previous_shot)
                    scene.frame_current = previous_shot.end - disp
                    break
                disp -= previous_shot.getDuration()
                previous_shot = get_previous_shot(shotList, previous_shot)
            else:
                # Scene end is farther than the first shot so loop back.
                last_enabled = [s for s in shotList if s.enabled][-1]
                props.setCurrentShot(last_enabled)
                scene.frame_current = last_enabled.end
    else:
        # User is scrubbing in the timeline so try to guess a shot in the range of the timeline.
        if not (current_shot.start <= current_frame <= current_shot.end):
            candidates = list()
            for i, shot in enumerate(shotList):
                if shot.start <= current_frame <= shot.end:
                    candidates.append((i, shot))

            if 0 < len(candidates):
                props.setCurrentShot(candidates[0][1], changeTime=False)
                scene.frame_current = current_frame
            else:
                # case were the new current time is out of every shots
                # we then get the first shot after current time, or the very first shot if there is no shots after
                nextShotInd = props.getFirstShotIndexAfterFrame(current_frame, ignoreDisabled=True)
                if -1 != nextShotInd:
                    props.setCurrentShot(shotList[nextShotInd], changeTime=False)
                    # don't change current time in order to let the user see changes in the scene
                    # scene.frame_current = shotList[nextShotInd].start
                else:
                    prevShotInd = props.getFirstShotIndexBeforeFrame(current_frame, ignoreDisabled=True)
                    if -1 != prevShotInd:
                        props.setCurrentShot(shotList[prevShotInd], changeTime=False)
                        # don't change current time in order to let the user see changes in the scene
                        # scene.frame_current = shotList[prevShotInd].start
                    else:
                        # paf what to do?
                        # props.setCurrentShot(candidates[0][1])
                        print("SM: Paf in shotMngHandler_frame_change_pre_jumpToShot: No valid shot found")

