from typing import Literal
from .resolve import get_resolve
from .project import DVRProject
from utils.p_print import *


DbType = Literal['Disk', 'PostgreSQL']
Pages = Literal["media", "cut", "edit", "fusion", "color", "fairlight", "deliver"]


class DVR:
    def __init__(self):
        self._resolve = get_resolve()
        self.pm = self._resolve.GetProjectManager()
        self._project = None
        self._version = self._resolve.GetVersionString()


    def quit(self):
        self._resolve.Quit()


    def version(self) -> str:
        return self._version


    def database_names(self) -> list[str]:
        database_list = self.pm.GetDatabaseList()
        return list([db['DbName'] for db in database_list])


    def current_database(self) -> dict[str, str]:
        return self.pm.GetCurrentDatabase()


    def current_database_name(self) -> str:
        return self.pm.GetCurrentDatabase()['DbName']


    def set_current_database(
        self,
        name: str,
        type: DbType = 'Disk',
        ip_address: str = ""
    ) -> bool:
        current_db = {
            'DbType': type,
            'DbName': name,
        }
        if ip_address:
            current_db['IpAddress'] = ip_address
        try:
            return self.pm.SetCurrentDatabase(current_db)
        except:
            raise ValueError(f"Failed to set current database to {name}")


    def load_project(self, name: str) -> DVRProject:
        try:
            self._project: DVRProject = DVRProject(self.pm.LoadProject(name))
        except Exception as e:
            raise ValueError(f"Failed to load project: {type(e)}")
        return self._project


    def project(self) -> DVRProject:
        if self._project is None:
            raise ValueError(f"No project loaded")
        return self._project


    def current_project_name(self) -> str:
        try:
            return self.pm.GetCurrentProject().Name()
        except:
            return ""


    def current_project(self) -> DVRProject:
        if self._project is None:
            try:
                dvr_project = self.pm.GetCurrentProject()
            except:
                raise ValueError(red("Failed to get current project"))
            self._project: DVRProject = DVRProject(dvr_project=dvr_project)
        return self._project


    def select_page(self, name: Pages) -> None:
        self._resolve.OpenPage(name)



# Resolve
#   Fusion()                                        --> Fusion             # Returns the Fusion object. Starting point for Fusion scripts.
#   GetMediaStorage()                               --> MediaStorage       # Returns the media storage object to query and act on media locations.
#   GetProjectManager()                             --> ProjectManager     # Returns the project manager object for currently open database.
#   OpenPage(pageName)                              --> Bool               # Switches to indicated page in DaVinci Resolve. Input can be one of ("media", "cut", "edit", "fusion", "color", "fairlight", "deliver").
#   GetCurrentPage()                                --> String             # Returns the page currently displayed in the main window. Returned value can be one of ("media", "cut", "edit", "fusion", "color", "fairlight", "deliver", None).
#   GetProductName()                                --> string             # Returns product name.
#   GetVersion()                                    --> [version fields]   # Returns list of product version fields in [major, minor, patch, build, suffix] format.
#   GetVersionString()                              --> string             # Returns product version in "major.minor.patch[suffix].build" format.
#   LoadLayoutPreset(presetName)                    --> Bool               # Loads UI layout from saved preset named 'presetName'.
#   UpdateLayoutPreset(presetName)                  --> Bool               # Overwrites preset named 'presetName' with current UI layout.
#   ExportLayoutPreset(presetName, presetFilePath)  --> Bool               # Exports preset named 'presetName' to path 'presetFilePath'.
#   DeleteLayoutPreset(presetName)                  --> Bool               # Deletes preset named 'presetName'.
#   SaveLayoutPreset(presetName)                    --> Bool               # Saves current UI layout as a preset named 'presetName'.
#   ImportLayoutPreset(presetFilePath, presetName)  --> Bool               # Imports preset from path 'presetFilePath'. The optional argument 'presetName' specifies how the preset shall be named. If not specified, the preset is named based on the filename.
#   Quit()                                          --> None               # Quits the Resolve App.
#   ImportRenderPreset(presetPath)                  --> Bool               # Import a preset from presetPath (string) and set it as current preset for rendering.
#   ExportRenderPreset(presetName, exportPath)      --> Bool               # Export a preset to a given path (string) if presetName(string) exists.
#   ImportBurnInPreset(presetPath)                  --> Bool               # Import a data burn in preset from a given presetPath (string)
#   ExportBurnInPreset(presetName, exportPath)      --> Bool               # Export a data burn in preset to a given path (string) if presetName (string) exists.
#   GetKeyframeMode()                               --> keyframeMode       # Returns the currently set keyframe mode (int). Refer to section 'Keyframe Mode information' below for details.
#   SetKeyframeMode(keyframeMode)                   --> Bool               # Returns True when 'keyframeMode'(enum) is successfully set. Refer to section 'Keyframe Mode information' below for details.

# ProjectManager
#   ArchiveProject(projectName,
#                  filePath,
#                  isArchiveSrcMedia=True,
#                  isArchiveRenderCache=True,
#                  isArchiveProxyMedia=False)       --> Bool               # Archives project to provided file path with the configuration as provided by the optional arguments
#   CreateProject(projectName)                      --> Project            # Creates and returns a project if projectName (string) is unique, and None if it is not.
#   DeleteProject(projectName)                      --> Bool               # Delete project in the current folder if not currently loaded
#   LoadProject(projectName)                        --> Project            # Loads and returns the project with name = projectName (string) if there is a match found, and None if there is no matching Project.
#   GetCurrentProject()                             --> Project            # Returns the currently loaded Resolve project.
#   SaveProject()                                   --> Bool               # Saves the currently loaded project with its own name. Returns True if successful.
#   CloseProject(project)                           --> Bool               # Closes the specified project without saving.
#   CreateFolder(folderName)                        --> Bool               # Creates a folder if folderName (string) is unique.
#   DeleteFolder(folderName)                        --> Bool               # Deletes the specified folder if it exists. Returns True in case of success.
#   GetProjectListInCurrentFolder()                 --> [project names...] # Returns a list of project names in current folder.
#   GetFolderListInCurrentFolder()                  --> [folder names...]  # Returns a list of folder names in current folder.
#   GotoRootFolder()                                --> Bool               # Opens root folder in database.
#   GotoParentFolder()                              --> Bool               # Opens parent folder of current folder in database if current folder has parent.
#   GetCurrentFolder()                              --> string             # Returns the current folder name.
#   OpenFolder(folderName)                          --> Bool               # Opens folder under given name.
#   ImportProject(filePath, projectName=None)       --> Bool               # Imports a project from the file path provided with given project name, if any. Returns True if successful.
#   ExportProject(projectName, filePath, withStillsAndLUTs=True) --> Bool  # Exports project to provided file path, including stills and LUTs if withStillsAndLUTs is True (enabled by default). Returns True in case of success.
#   RestoreProject(filePath, projectName=None)      --> Bool               # Restores a project from the file path provided with given project name, if any. Returns True if successful.
#   GetCurrentDatabase()                            --> {dbInfo}           # Returns a dictionary (with keys 'DbType', 'DbName' and optional 'IpAddress') corresponding to the current database connection
#   GetDatabaseList()                               --> [{dbInfo}]         # Returns a list of dictionary items (with keys 'DbType', 'DbName' and optional 'IpAddress') corresponding to all the databases added to Resolve
#   SetCurrentDatabase({dbInfo})                    --> Bool               # Switches current database connection to the database specified by the keys below, and closes any open project.
#                                                                          # 'DbType': 'Disk' or 'PostgreSQL' (string)
#                                                                          # 'DbName': database name (string)
#                                                                          # 'IpAddress': IP address of the PostgreSQL server (string, optional key - defaults to '127.0.0.1')
#   CreateCloudProject({cloudSettings})             --> Project            # Creates and returns a cloud project.
#                                                                          # '{cloudSettings}': Check 'Cloud Projects Settings' subsection below for more information.
#   LoadCloudProject({cloudSettings})               --> Project            # Loads and returns a cloud project with the following cloud settings if there is a match found, and None if there is no matching cloud project.
#                                                                          # '{cloudSettings}': Check 'Cloud Projects Settings' subsection below for more information.
#   ImportCloudProject(filePath, {cloudSettings})   --> Bool               # Returns True if import cloud project is successful; False otherwise
#                                                                          # 'filePath': String; filePath of file to import
#                                                                          # '{cloudSettings}': Check 'Cloud Projects Settings' subsection below for more information.
#   RestoreCloudProject(folderPath, {cloudSettings}) --> Bool              # Returns True if restore cloud project is successful; False otherwise
#                                                                          # 'folderPath': String; path of folder to restore
#                                                                          # '{cloudSettings}': Check 'Cloud Projects Settings' subsection below for more information.



# Looking up Project and Clip properties
# --------------------------------------
# This section covers additional notes for the functions "Project:GetSetting",
# "Project:SetSetting", "Timeline:GetSetting", "Timeline:SetSetting",
# "MediaPoolItem:GetClipProperty" and "MediaPoolItem:SetClipProperty".
# These functions are used to get and set properties otherwise available to the user
# through the Project Settings and the Clip Attributes dialogs.

# The functions follow a key-value pair format, where each property is identified
# by a key (the settingName or propertyName parameter) and possesses a value
# (typically a text value). Keys and values are designed to be easily correlated with
# parameter names and values in the Resolve UI.
# Explicitly enumerated values for some parameters are listed below.

# Some properties may be read only - these include intrinsic clip properties like date
# created or sample rate, and properties that can be disabled in specific application
# contexts (e.g. custom colorspaces in an ACES workflow, or output sizing parameters when
# behavior is set to match timeline)

# Getting values:
# Invoke "Project:GetSetting", "Timeline:GetSetting" or "MediaPoolItem:GetClipProperty"
# with the appropriate property key.
# To get a snapshot of all queryable properties (keys and values), you can call
# "Project:GetSetting", "Timeline:GetSetting" or "MediaPoolItem:GetClipProperty" without
# parameters (or with a NoneType or a blank property key). Using specific keys to query
# individual properties will be faster. Note that getting a property using an invalid key
# will return a trivial result.

# Setting values:
# Invoke "Project:SetSetting", "Timeline:SetSetting" or "MediaPoolItem:SetClipProperty"
# with the appropriate property key and a valid value. When setting a parameter,
# please check the return value to ensure the success of the operation.
# You can troubleshoot the validity of keys and values by setting the desired result
# from the UI and checking property snapshots before and after the change.

# The following Project properties have specifically enumerated values:
# "superScale" - the property value is an enumerated integer between 0 and 4 with
#               these meanings: 0=Auto, 1=no scaling, and 2, 3 and 4 represent the
#               Super Scale multipliers 2x, 3x and 4x.
#                for super scale multiplier '2x Enhanced', exactly 4 arguments must be
#                passed as outlined below. If less than 4 arguments are passed,
#               it will default to 2x.
# Affects:
# • x = Project:GetSetting('superScale') and Project:SetSetting('superScale', x)
# • for '2x Enhanced' --> Project:SetSetting('superScale', 2, sharpnessValue, noiseReductionValue), where sharpnessValue is a float in the range [0.0, 1.0] and noiseReductionValue is a float in the range [0.0, 1.0]

# "timelineFrameRate" - the property value is one of the frame rates available to the user in project settings under "Timeline frame rate" option. Drop Frame can be configured for supported frame rates
#                       by appending the frame rate with "DF", e.g. "29.97 DF" will enable drop frame and "29.97" will disable drop frame
# Affects:
# • x = Project:GetSetting('timelineFrameRate') and Project:SetSetting('timelineFrameRate', x)

# The following Clip properties have specifically enumerated values:
# "Super Scale" - the property value is an enumerated integer between 1 and 4 with
#                   these meanings: 1=no scaling, and 2, 3 and 4 represent the Super Scale
#                   multipliers 2x, 3x and 4x.
#                 for super scale multiplier '2x Enhanced', exactly 4 arguments
#                 must be passed as outlined below. If less than 4 arguments are passed,
#                   it will default to 2x.
# Affects:
# • x = MediaPoolItem:GetClipProperty('Super Scale') and MediaPoolItem:SetClipProperty('Super Scale', x)
# • for '2x Enhanced' --> MediaPoolItem:SetClipProperty('Super Scale', 2, sharpnessValue, noiseReductionValue), where sharpnessValue is a float in the range [0.0, 1.0] and noiseReductionValue is a float in the range [0.0, 1.0]
