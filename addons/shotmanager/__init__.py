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
__init__
"""

from .config import config

from .install_and_register import register_addon


bl_info = {
    "name": "Eddy Shot Manager",
    "author": """ Eddy - Betti Abbattista
Shotmanager: Ubisoft - Julien Blervaque (aka Werwack), Romain Carriquiry Borchiari
Blender Kitsu: Blender Foundation - Paul Golter""",
    "description": "Customized pipeline tool for previz at Eddy Studio",
    "blender": (4, 0, 0),
    "version": (1, 0, 0),
    "location": "View3D > Shot Mng",
    "doc_url": "",
    "tracker_url": "",
    # "warning": "BETA Version",
    # "warning": "Pre-Release",
    "category": "Eddy",
}

__version__ = ".".join(str(i) for i in bl_info["version"])
display_version = __version__


def register():
    config.initGlobalVariables()
    register_addon.register()



def unregister():
    register_addon.unregister()
    config.releaseGlobalVariables()
  
