import wx
import wx.dataview
from . import view_addrule
from pubsub import pub
from ..Sorter import configurator as config_tool
from ..Sorter import sorter as sorter_tool
import os.path

class MainWindow(wx.Frame):
    ''' Fereastra principala '''
    config = config_tool.Configurator()

    def getSetupData(self):
        data = dict()
        data["path_downloads"]=self.textbox_download_folder.GetValue()
        rules = []
        for row in range(self.dataview.GetItemCount()):
            temp_row = []
            for col in range(2):
                temp_row.append(self.dataview.GetValue(row,col))

            rules.append(temp_row)

        data["rules"]=rules
        print(data)
        return data

    def OnBtnDownloadFolder(self, event):
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.textbox_download_folder.SetValue(dlg.GetPath())
        dlg.Destroy()

    def OnBtnAddItem(self, event):
        add_rule_window = view_addrule.AddRuleWindow()
        add_rule_window.Show()

    def OnBtnRemoveItem(self, event):
        selected_item = self.dataview.GetSelectedRow()
        self.dataview.DeleteItem(selected_item)

    def OnBtnImportConfig(self, event):
        dlg = wx.FileDialog(
            self, message="Choose a configuration file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="JSON files (*.json)|*.json",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            config_path = dlg.GetPath()
            # Subscribe to import results
            pub.subscribe(self.on_config_import_result, "configImportResult")
            # Send message to import the config
            pub.sendMessage("configuratorListener", message="import_config", arg2=config_path)
        
        dlg.Destroy()

    def on_config_import_result(self, message, config=None):
        # Unsubscribe to avoid double handling
        pub.unsubscribe(self.on_config_import_result, "configImportResult")
        
        if message == "invalid_format":
            wx.MessageBox("The selected file is not a valid TidyCobra configuration file.", 
                         "Invalid Configuration Format", wx.OK | wx.ICON_ERROR)
            return
        
        if message == "invalid_json":
            wx.MessageBox("The selected file contains invalid JSON.", 
                         "Invalid JSON", wx.OK | wx.ICON_ERROR)
            return
            
        if message == "file_not_found":
            wx.MessageBox("The selected configuration file could not be found.", 
                         "File Not Found", wx.OK | wx.ICON_ERROR)
            return
        
        if message == "success" and config:
            # Validate paths in the imported config
            path_validation = self.config.validate_paths(config)
            
            # Handle downloads path if it doesn't exist
            if not path_validation["downloads_exists"]:
                dlg = wx.MessageDialog(self, 
                                      f"The downloads path '{config['path_downloads']}' does not exist. Would you like to select a different one?",
                                      "Downloads Path Not Found",
                                      wx.YES_NO | wx.ICON_QUESTION)
                if dlg.ShowModal() == wx.ID_YES:
                    dir_dlg = wx.DirDialog(self, f"Choose directory to replace: {config['path_downloads']}", style=wx.DD_DEFAULT_STYLE)
                    if dir_dlg.ShowModal() == wx.ID_OK:
                        config["path_downloads"] = dir_dlg.GetPath()
                    else:
                        # User canceled, abort import
                        return
                    dir_dlg.Destroy()
                else:
                    # User chose not to select a new downloads path, abort import
                    return
                dlg.Destroy()
            
            # Handle destination paths
            for i, path_info in enumerate(path_validation["destination_paths"]):
                if not path_info["exists"]:
                    # Create a custom dialog with clear options
                    dlg = wx.Dialog(self, title="Destination Path Not Found", size=(450, 180))
                    panel = wx.Panel(dlg)
                    
                    # Message about missing path
                    message = wx.StaticText(panel, label=f"The destination path does not exist:\n{path_info['path']}")
                    
                    # Create three distinct buttons with clear labels
                    btn_create = wx.Button(panel, label="Create Directory")
                    btn_choose = wx.Button(panel, label="Choose Different Directory")
                    btn_cancel = wx.Button(panel, label="Cancel Import")
                    
                    # Set up sizers for layout
                    main_sizer = wx.BoxSizer(wx.VERTICAL)
                    button_sizer = wx.BoxSizer(wx.HORIZONTAL)
                    
                    main_sizer.Add(message, 0, wx.ALL | wx.EXPAND, 15)
                    button_sizer.Add(btn_create, 0, wx.ALL, 5)
                    button_sizer.Add(btn_choose, 0, wx.ALL, 5)
                    button_sizer.Add(btn_cancel, 0, wx.ALL, 5)
                    
                    # Make sure button_sizer is centered
                    main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
                    
                    panel.SetSizer(main_sizer)
                    main_sizer.Fit(panel)
                    
                    # Define button behaviors
                    def on_create(event):
                        try:
                            os.makedirs(path_info["path"], exist_ok=True)
                            dlg.EndModal(wx.ID_YES)  # Using ID_YES for "create"
                        except Exception as e:
                            wx.MessageBox(f"Failed to create directory: {str(e)}", 
                                         "Error Creating Directory", wx.OK | wx.ICON_ERROR)
                    
                    def on_choose(event):
                        dlg.EndModal(wx.ID_NO)  # Using ID_NO for "choose different"
                    
                    def on_cancel(event):
                        dlg.EndModal(wx.ID_CANCEL)
                    
                    # Bind events
                    btn_create.Bind(wx.EVT_BUTTON, on_create)
                    btn_choose.Bind(wx.EVT_BUTTON, on_choose)
                    btn_cancel.Bind(wx.EVT_BUTTON, on_cancel)
                    
                    # Show dialog and handle result
                    result = dlg.ShowModal()
                    dlg.Destroy()
                    
                    if result == wx.ID_YES:  # Created directory
                        # Continue with next path
                        pass
                            
                    elif result == wx.ID_NO:  # Choose different directory
                        # Include the invalid path in the dialog title
                        invalid_path = path_info["path"]
                        dir_dlg = wx.DirDialog(
                            self, 
                            f"Choose directory to replace: {invalid_path}",
                            style=wx.DD_DEFAULT_STYLE
                        )
                        
                        if dir_dlg.ShowModal() == wx.ID_OK:
                            config["rules"][i][0] = dir_dlg.GetPath()
                        else:
                            # User canceled, abort import
                            return
                        dir_dlg.Destroy()
                        
                    else:  # Cancel import
                        return
            
            # Clear existing data
            self.dataview.DeleteAllItems()
            
            # Apply the validated config
            self.textbox_download_folder.SetValue(config["path_downloads"])
            for rule in config["rules"]:
                self.dataview.AppendItem(rule)
                
            self.SetStatusText("Configuration imported successfully!")
            
            # Save the validated configuration
            pub.sendMessage("configuratorListener", message="save_config", arg2=config)

    def OnBtnSaveConfig(self, event):
        data = self.getSetupData()
        pub.sendMessage("configuratorListener", message="save_config", arg2=data)
        self.SetStatusText("Configuration saved!")

    def OnBtnRunManual(self, event):
        sorter = sorter_tool.Sorter()
        return -1  # not implemented

    def OnBtnRunAuto(self, event):
        return -1  # not implemented

    '''Listeners!'''
    def listener_addrule(self, message, arg2=None):
        self.dataview.AppendItem(message)

    def __init__(self):
        wx.Frame.__init__(self, None, title="Tidy Cobra", style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER
                                                                                           | wx.MAXIMIZE_BOX))

        self.payload = []
        self.SetMinSize(self.GetSize())
        self.panel = wx.Panel(self)
        self.CreateStatusBar()
        self.SetStatusText("Ready!")
        pub.subscribe(self.listener_addrule, "addRuleListener")

        ''' Logo '''
        script_dir = os.path.dirname(__file__)
        logo_path = os.path.join(script_dir, os.pardir, 'Resources', 'logo.png')
        logo_path = os.path.abspath(logo_path)
        self.img_logo = wx.Image(logo_path, wx.BITMAP_TYPE_ANY)
        self.sb1 = wx.StaticBitmap(self.panel, -1, wx.Bitmap(self.img_logo))
        ''' Text labels '''

        self.text_step1 = wx.StaticText(self.panel, label="Step 1: Choose your Downloads folder")
        self.text_step2 = wx.StaticText(self.panel, label="Step 2: Set up destination folders and their extensions")
        self.text_step3 = wx.StaticText(self.panel, label="Step 3: Save/Run")

        ''' Dividers '''
        self.sizer_main = wx.BoxSizer(wx.VERTICAL)  # main sizer

        '''horizontal boxes'''
        self.hbox_downloads = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_dataview_controls = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_save_controls = wx.BoxSizer(wx.HORIZONTAL)

        ''' Buttons '''
        self.btn_download_folder = wx.Button(self.panel, label="Browse")
        self.btn_download_folder.Bind(wx.EVT_BUTTON, self.OnBtnDownloadFolder)

        self.btn_add_item = wx.Button(self.panel, label="Add rule")
        self.btn_add_item.Bind(wx.EVT_BUTTON, self.OnBtnAddItem)

        self.btn_remove_item = wx.Button(self.panel, label="Remove selected")
        self.btn_remove_item.Bind(wx.EVT_BUTTON, self.OnBtnRemoveItem)

        self.btn_import_config = wx.Button(self.panel, label="Import configuration")
        self.btn_import_config.Bind(wx.EVT_BUTTON, self.OnBtnImportConfig)

        self.btn_save_config = wx.Button(self.panel, label="Save configuration file")
        self.btn_save_config.Bind(wx.EVT_BUTTON, self.OnBtnSaveConfig)

        self.btn_run_manual = wx.Button(self.panel, label="Run sorter")
        self.btn_run_manual.Bind(wx.EVT_BUTTON, self.OnBtnRunManual)

        self.btn_run_auto = wx.Button(self.panel, label="Run on startup")
        self.btn_run_auto.Bind(wx.EVT_BUTTON, self.OnBtnRunAuto)

        ''' Textboxes '''
        self.textbox_download_folder = wx.TextCtrl(self.panel)

        ''' DataView '''
        self.dataview = wx.dataview.DataViewListCtrl(self.panel, size=(200, 200))

        self.dataview.AppendTextColumn("Folder Path", width=225)
        self.dataview.AppendTextColumn("Extensions")

        ''' Layout '''
        self.sizer_main.Add(self.sb1, wx.SizerFlags().Border(wx.TOP | wx.BOTTOM, 20).Center())

        ''' Step 1 : Select download folder'''
        self.sizer_main.Add(self.text_step1, wx.SizerFlags().Border(wx.TOP | wx.LEFT, 10))

        self.hbox_downloads.Add(self.textbox_download_folder, proportion=1)
        self.hbox_downloads.Add(self.btn_download_folder, wx.SizerFlags().Border(wx.LEFT | wx.RIGHT, 5))
        self.sizer_main.Add(self.hbox_downloads, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, border=10)

        ''' Step 2: Set up rules '''
        self.sizer_main.Add(self.text_step2, wx.SizerFlags().Border(wx.TOP | wx.LEFT, 10))
        self.sizer_main.Add(self.dataview, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, border=10)
        self.hbox_dataview_controls.Add(self.btn_add_item, wx.SizerFlags().Border(wx.RIGHT, 2).Proportion(1))
        self.hbox_dataview_controls.Add(self.btn_remove_item, wx.SizerFlags().Proportion(1).Border(wx.LEFT | wx.RIGHT, 2))
        self.hbox_dataview_controls.Add(self.btn_import_config, wx.SizerFlags().Proportion(1).Border(wx.LEFT, 2))
        self.sizer_main.Add(self.hbox_dataview_controls, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        ''' Step 3: Save/Run '''
        self.sizer_main.Add(self.text_step3, wx.SizerFlags().Border(wx.TOP | wx.LEFT | wx.BOTTOM, 10))

        self.hbox_save_controls.Add(self.btn_save_config, wx.SizerFlags().Border(wx.RIGHT, 2).Proportion(1))
        self.hbox_save_controls.Add(self.btn_run_manual, wx.SizerFlags().Proportion(1).Border(wx.LEFT | wx.RIGHT, 2))
        self.hbox_save_controls.Add(self.btn_run_auto, wx.SizerFlags().Proportion(1).Border(wx.LEFT, 2))
        self.sizer_main.Add(self.hbox_save_controls, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        self.panel.SetSizer(self.sizer_main)

        self.panel.SetSizer(self.sizer_main)
        self.Center()
        self.SetSize(self.GetBestSize())
        self.sizer_main.Fit(self)
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.Center()

        config_dir = os.path.join(os.path.dirname(__file__), os.pardir, 'Sorter')
        self.default_config_path = os.path.join(config_dir, 'config.json')
        self.default_config_path = os.path.abspath(self.default_config_path)

        if os.path.isfile(self.default_config_path):
            config_display_data = self.config.load_config()
            self.textbox_download_folder.SetValue(config_display_data["path_downloads"])
            for rule in config_display_data["rules"]:
                print(rule)
                self.dataview.AppendItem(rule)
                self.SetStatusText("Loaded pre-existent configuration. Ready!")
        else:
            self.SetStatusText("Ready!")
        self.Show(True)


def render_GUI():
    app = wx.App()
    frame = MainWindow()
    app.MainLoop()


if __name__ == '__main__':
    render_GUI()
