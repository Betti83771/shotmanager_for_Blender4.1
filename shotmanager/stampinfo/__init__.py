# GPLv3 License
#
# Copyright (C) 2022 Ubisoft
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
Main init
"""

import bpy
import bpy.utils.previews
from bpy.props import PointerProperty


from .utils import utils_operators
from .utils.utils_render import Utils_LaunchRender
from .utils import utils_vse_render
from .properties import stampInfoSettings
from .operators import debug
from .properties import stamper
from .ui import si_ui

import importlib

importlib.reload(stampInfoSettings)
importlib.reload(stamper)
importlib.reload(debug)

from shotmanager.config import sm_logging

_logger = sm_logging.getLogger(__name__)


classes = (
    stampInfoSettings.UAS_StampInfoSettings,
    Utils_LaunchRender,
)


def stampInfo_resetProperties():
    from .utils.utils_inspectors import resetAttrs

    # print("stampInfo_resetProperties...")
    # print(f"Scene name: {bpy.context.scene.name}")

    props = bpy.context.scene.UAS_SM_StampInfo_Settings
    resetAttrs(props)


def register():

    from .utils import utils_ui

    utils_ui.register()

    # if install went right then register other packages
    ###################
    # from stampinfo import ui
    from . import ui
    from .operators import render_operators

    ###################
    # update data
    ###################

    for cls in classes:
        bpy.utils.register_class(cls)

    render_operators.register()
    si_ui.register()
    ui.register()
    utils_vse_render.register()
    utils_operators.register()

    bpy.types.Scene.UAS_SM_StampInfo_Settings = PointerProperty(type=stampInfoSettings.UAS_StampInfoSettings)

    # debug tools
    debug.register()

    print("")


def unregister():
    print("\n*** --- Unregistering Stamp Info  --- ***")
    from .utils import utils_ui

    # Unregister packages that were registered if the install went right
    ###################

    # debug tools
    debug.unregister()

    from . import ui
    from .operators import render_operators

    utils_operators.unregister()
    utils_vse_render.unregister()
    ui.unregister()
    si_ui.unregister()
    render_operators.unregister()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    utils_ui.unregister()
