
def check_dependencies() -> bool:
    # install dependencies and required Python libraries
    ###################
    # try to install dependencies and collect the errors in case of troubles
    # If some mandatory libraries cannot be loaded then an alternative Add-on Preferences panel
    # is used and provide some visibility to the user to solve the issue
    # Pillow lib is installed there

    from ..install_and_register.install_dependencies import install_dependencies

    # PIL library - for Stamp Info and image writing
    installErrorCode = install_dependencies([("PIL", "pillow")], retries=1, timeout=5)
    if 0 != installErrorCode:
        print("  *** Pillow Imaging Library (PIL) install failed for Ubisoft Shot Manager ***")
        return False
    else:
        print("  Pillow Imaging Library (PIL) correctly installed for Ubisoft Stamp Info")
        return True
