
def check_dependencies():
    # install dependencies and required Python libraries
    ###################
    # try to install dependencies and collect the errors in case of troubles
    # If some mandatory libraries cannot be loaded then an alternative Add-on Preferences panel
    # is used and provide some visibility to the user to solve the issue
    # Pillow lib is installed there

    from ..install_and_register.install_otio_local_dist import install_otio_local_dist
    from ..install_and_register.install_dependencies import install_dependencies

    if not install_otio_local_dist():

       # installErrorCode = install_dependencies([("opentimelineio", "opentimelineio")], retries=1, timeout=10)
        
        installErrorCode = 0
        if 0 != installErrorCode:
            # utils_handlers.removeAllHandlerOccurences(shotMngHandler_frame_change_pre_jumpToShot, handlerCateg=bpy.app.handlers.frame_change_pre)
            # return installErrorCode
            print("  *** OpenTimelineIO install failed for Ubisoft Shot Manager ***")
            return False
        else:
            print("  OpenTimelineIO correctly installed for Ubisoft Shot Manager")

    # otio
    try:
       # from .. import otio
        pass
       # otio.register()

        # from shotmanager.otio import importOpenTimelineIOLib

        # if importOpenTimelineIOLib():
        #     otio.register()
        # else:
        #     print("       *** OTIO Package import failed ***")
    except ModuleNotFoundError:
        print("       *** OTIO Package import failed ****")

    # PIL library - for Stamp Info and image writing
    installErrorCode = install_dependencies([("PIL", "pillow")], retries=1, timeout=5)
    if 0 != installErrorCode:
        print("  *** Pillow Imaging Library (PIL) install failed for Ubisoft Shot Manager ***")
    else:
        print("  Pillow Imaging Library (PIL) correctly installed for Ubisoft Stamp Info")

    #try:
       # pil_logger = logging.getLogger("PIL")
      #  pil_logger.setLevel(logging.INFO)
   # except Exception:
    #    pass
