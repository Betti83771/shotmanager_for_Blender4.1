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
Camera HUD
"""

from collections import defaultdict

import bpy
import bpy_extras.view3d_utils as view3d_utils

import mathutils


import gpu
import bgl, blf
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d


from shotmanager.utils.utils_ogl import get_region_at_xy, Square, Rect

# font_info = {"font_id": 0, "handler": None}


def draw_shots_names(context):
    scn = context.scene

    # For all camera which have a shot draw on the ui a list of shots associated with it.
    for obj in scn.objects:
        if obj.type == "CAMERA":
            if not (context.space_data.region_3d.view_perspective == "CAMERA" and obj == context.scene.camera):
                pos_2d = view3d_utils.location_3d_to_region_2d(
                    context.region, context.space_data.region_3d, mathutils.Vector(obj.location)
                )
                if pos_2d is not None:
                    # print("pos x:", pos_2d[0])
                    # print("pos y:", pos_2d[1])
                    pass
                    draw_all_shots_names(context, obj, pos_2d[0], pos_2d[1], vertical=True)


def draw_all_shots_names(context, cam, pos_x, pos_y, vertical=False):
    props = context.scene.UAS_shot_manager_props
    prefs = context.preferences.addons["shotmanager"].preferences
    current_shot = props.getCurrentShot()
    # hud_offset_x = 19
    hud_offset_x = 8
    hud_offset_y = 0

    font_size = prefs.cameraHUD_shotNameSize

    blf.color(0, 1, 1, 1, 1)
    # blf.size(0, 12, 72)
    blf.size(0, font_size, 72)
    # Take maximum font height
    _, font_height = blf.dimensions(0, "A")
    # font_height = font_height * 0.8

    x_horizontal_offset = 80

    shotsList_allCams = props.getShotsUsingCamera(cam)
    if 0 == len(shotsList_allCams):
        return ()

    # keep only shots with visible cameras
    shotsList = list()
    for shot in shotsList_allCams:
        if shot.isCameraValid() and shot.camera.visible_get():
            shotsList.append(shot)

    shot_names_by_camera = defaultdict(list)
    for shot in shotsList:
        shot_names_by_camera[shot.camera.name].append(shot)

    #
    # Filter out shots in order to restrict the number of shots to be displayed as a list
    #
    shot_trim_info = dict()
    shot_trim_length = 2  # Limit the display of x shot before and after the current_shot

    for c, shots in shot_names_by_camera.items():
        shot_trim_info[c] = [False, False]

        current_shot_index = 0
        if current_shot in shots:
            current_shot_index = shots.index(current_shot)

        before_range = max(current_shot_index - shot_trim_length, 0)
        after_range = min(current_shot_index + shot_trim_length + 1, len(shots))
        shot_names_by_camera[c] = shots[before_range:after_range]

        if before_range > 0:
            shot_trim_info[c][0] = True
        if after_range < len(shots):
            shot_trim_info[c][1] = True

    # For all camera which have a shot draw on the ui a list of shots associated with it
    # blf.size(0, font_size, 72)

    blf.color(0, 0.9, 0.9, 0.9, 0.9)

    # Move underneath object name
    x_offset = hud_offset_x
    y_offset = hud_offset_y + int(cam.show_name) * -12

    # Draw ... if we don't display previous shots
    if shot_trim_info[cam.name][0]:
        blf.position(0, pos_x + x_offset, pos_y + y_offset, 0)
        blf.draw(0, "...")
        if vertical:
            y_offset -= font_size  # Seems to do the trick for this value
        else:
            x_offset += x_horizontal_offset

    # Draw the shot names.
    for s in shot_names_by_camera[cam.name]:
        drawShotName(
            pos_x + x_offset,
            pos_y + y_offset,
            s.name,
            s.color,
            font_height,
            is_current=current_shot == s,
            is_disabled=not s.enabled,
        )
        if vertical:
            y_offset -= font_size  # Seems to do the trick for this value
        else:
            x_offset += x_horizontal_offset

    # Draw ... if we don't display next shots
    if shot_trim_info[cam.name][1]:
        blf.position(0, pos_x + x_offset, pos_y + y_offset, 0)
        blf.draw(0, "...")

    ### #wkip random pos for debug in case of display remanence
    # num_cams = len(bpy.data.cameras)
    # blf.position(0, pos_x + x_offset + num_cams * 10, pos_y + y_offset + num_cams * 10, 0)
    # blf.draw(0, str(num_cams))


def drawShotName(pos_x, pos_y, shot_name, shot_color, font_height, is_current=False, is_disabled=False):
    square_size = 4.0
    square_size = font_height * 1.2

    # square
    gamma = 1.0 / 2.2
    linColor = (pow(shot_color[0], gamma), pow(shot_color[1], gamma), pow(shot_color[2], gamma), shot_color[3])
    Rect(pos_x, pos_y - square_size * 0.1, square_size, square_size, linColor, "BOTTOM_LEFT").draw()

    # shot name
    blf.position(0, pos_x + square_size * 1.25, pos_y, 0)
    if is_current:
        blf.color(0, 0.4, 0.9, 0.1, 1)
    elif is_disabled:
        blf.color(0, 0.6, 0.6, 0.6, 1)
    else:
        blf.color(0, 0.9, 0.9, 0.9, 0.9)
    blf.draw(0, shot_name)


def view3d_camera_border(context):
    obj = context.scene.camera
    cam = obj.data

    frame = cam.view_frame(scene=context.scene)

    # move from object-space into world-space
    frame = [obj.matrix_world @ v for v in frame]

    # move into pixelspace

    frame_px = [location_3d_to_region_2d(context.region, context.space_data.region_3d, v) for v in frame]
    return frame_px
