#!/usr/bin/env python
# coding: utf-8

r"""Tree widget"""

import logging
from os import listdir
from os.path import exists, isdir, normpath, join, basename

import wx
import wx.lib.agw.customtreectrl
from wx.lib.pubsub import pub

from corelib.core.files import p_

from osvcad.ui.utils import get_file_extension

logger = logging.getLogger(__name__)


class Tree(wx.lib.agw.customtreectrl.CustomTreeCtrl):
    """wx.lib.agw.customtreectrl.CustomTreeCtrl
    tailored for osvcad cases manipulation"""
    def __init__(self,
                 parent,
                 model,
                 root_directory=None,
                 checkable_extensions=None,
                 disabled_extensions=None,
                 excluded_extensions=None,
                 agw_style=wx.TR_DEFAULT_STYLE,
                 context_menu=False):

        wx.lib.agw.customtreectrl.CustomTreeCtrl.__init__(self,
                                                          parent,
                                                          id=-1,
                                                          pos=(-1, -1),
                                                          size=(-1, -1),
                                                          agwStyle=agw_style)

        self.model = model
        self.model.observe("root_folder_changed", self.on_root_folder_changed)

        self.selected_item = None

        if checkable_extensions is None:
            checkable_extensions = []
        if disabled_extensions is None:
            disabled_extensions = []
        if excluded_extensions is None:
            excluded_extensions = []
        self.context_menu = context_menu

        # bind events
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.TreeItemExpanding)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.TreeItemCollapsing)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSelChanged)
        # self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnEvtTreeItemRightClick)
        # self.Bind(wx.lib.agw.customtreectrl.EVT_TREE_ITEM_CHECKED,
        #           self.OnItemChecked)

        # some hack-ish code here to deal with imagelists
        self.iconentries = {}
        self.imagelist = wx.ImageList(16, 16)

        self.checkable_extensions = checkable_extensions
        self.disabled_extensions = disabled_extensions
        self.excluded_extensions = excluded_extensions

        self.add_icon(p_(__file__, './icons/folder.png'),
                      wx.BITMAP_TYPE_PNG,
                      'FOLDER')
        self.add_icon(p_(__file__, './icons/python_icon.png'),
                      wx.BITMAP_TYPE_PNG,
                      'python')
        # set default image
        self.add_icon(p_(__file__, './icons/file_icon.png'),
                      wx.BITMAP_TYPE_PNG,
                      'default')

        # self.set_root_dir(root_directory)

        pub.subscribe(self.tree_modified_listener, "tree_modified")

        # if root_directory in [None, ""]:
        #     from os import getcwd
        #     root_directory = getcwd()
        # self.model.set_root_folder(root_directory)
        # self.root_directory = root_directory

    def on_root_folder_changed(self, evt):
        r"""Callback for a change of root folder"""
        self.set_root_dir(self.model.root_folder)

    def tree_modified_listener(self, tree_object_reference):
        """Listener function to make sure various trees can know that
        some modifications have been made by other trees operating on the
        same folder/case(s) structure
        """
        if tree_object_reference == self:
            # The modifications have already been made
            pass
        else:
            # Simplest option: delete the children at the root
            self.GetRootItem().DeleteChildren(self)
            # self._load_dir(self.GetRootItem(), self.root_directory)
            self._load_dir(self.GetRootItem(), self.model.root_folder)

    def add_icon(self, filepath, wxBitmapType, name):
        """ Adds an icon to the imagelist and registers it with the
        iconentries dict using the given name.
        Use so that you can assign custom icons to the tree just by passing
        in the value stored in self.iconentries[name]

        Arguments:
        filepath -- path to the image
        wxBitmapType -- wx constant for the file type - eg wx.BITMAP_TYPE_PNG
        name -- name to use as a key in the self.iconentries dict
                -> get your imagekey by calling self.iconentries[name]
        """
        try:
            if exists(filepath):
                key = self.imagelist.Add(wx.Image(filepath,
                                                  wx.BITMAP_TYPE_PNG).Scale(16, 16).ConvertToBitmap())
                self.iconentries[name] = key
                self.SetImageList(self.imagelist)
        except Exception as e:
            logger.warning(e)

    def set_root_dir(self, root_directory):
        """
        Sets the root GenericTreeItem of this CustomTreeCtrl
        """
        if not isdir(root_directory):
            # raise Exception("%s is not a valid directory" % directory)
            raise Exception("%s is not a valid directory" % root_directory)

        self.DeleteAllItems()  # delete existing root, if any

        # add directory as root, load direct children and expand
        root_item = self.AddRoot(basename(root_directory),
                                 ct_type=0,
                                 image=self.iconentries['FOLDER'],
                                 selImage=-1,
                                 data=normpath(root_directory))
        self._load_dir(root_item, root_directory)

        # to be able to expand the root item again after it has been collapsed
        root_item.SetHasPlus(True)

        self.Expand(root_item)

    def _load_dir(self, item, directory):
        """Private function that gets called to load the file list
        for the given directory and append the items to the tree.
        Throws an exception if the directory is invalid.

        Note
        ----
        Does not add items if the node already has children
        """
        # check if directory exists and is a directory
        logger.debug("_load_dir(%s)" % directory)
        if not isdir(directory):
            msg = "%s is not a valid directory" % directory
            logger.error(msg)
            raise Exception(msg)

        # check if node already has children
        if self.GetChildrenCount(item) == 0:
            files_and_dirs = listdir(directory)  # get files in directory
            logger.debug("Directory %s contains : %s" % (directory,
                                                         str(files_and_dirs)))
            files = []
            dirs = []
            for f in files_and_dirs:
                if f != "__pycache__":
                    if isdir(join(directory, f)):
                        dirs.append(f)
                    else:
                        files.append(f)

            # add nodes to tree
            for f in sorted(dirs):
                # imagekey = self.process_file_extension(join(directory, f))
                child = self.AppendItem(item,
                                        f,
                                        ct_type=0,
                                        image=self.iconentries['FOLDER'],
                                        selImage=-1,
                                        data=normpath(join(directory, f)))
                self.SetItemHasChildren(child, True)

            for f in sorted(files):
                imagekey = self.process_file_extension(join(directory, f))
                if get_file_extension(f) not in self.excluded_extensions:
                    child = self.AppendItem(item,
                                            f,
                                            ct_type=0 if get_file_extension(
                                                f) not in self.checkable_extensions
                                            else 1,
                                            image=imagekey,
                                            selImage=-1,
                                            data=normpath(join(directory, f)))
                    # GF : add the data because it is retrieved by the
                    # selectionChanged handler
                    # self.SetPyData(child, Directory(normpath(
                    #                          join(directory, f))))
                    if get_file_extension(f) in self.disabled_extensions:
                        self.EnableItem(child, enable=False, torefresh=False)

    def process_file_extension(self, filename):
        """Helper function.
        Called for files and collects all the necessary icons into an image
        list which is re-passed into the tree every time
        (imagelists are a lame way to handle images)
        """
        ext = get_file_extension(filename)
        ext = ext.lower()
        logger.debug("Processing file extension : %s" % ext)
        excluded = ['', '.exe', '.ico', '.py']
        # do nothing if no extension found or in excluded list
        if ext not in excluded:
            # only add if we don't already have an entry for this item
            if ext not in self.iconentries.keys():
                # sometimes it just crashes
                try:
                    # use mimemanager to get filetype and icon
                    # lookup extension
                    filetype = wx.TheMimeTypesManager.GetFileTypeFromExtension(ext)

                    if hasattr(filetype, 'GetIconInfo'):
                        info = filetype.GetIconInfo()

                        if info is not None:
                            icon = info[0]
                            if icon.Ok():
                                # add to imagelist and store returned key
                                iconkey = self.imagelist.Add(icon)
                                self.iconentries[ext] = iconkey

                                # update tree with new imagelist - inefficient
                                self.SetImageList(self.imagelist)
                                return iconkey  # return new key
                except:
                    return self.iconentries['default']

            # already have icon, return key
            else:
                return self.iconentries[ext]

        # if exe, get first icon out of it
        elif ext == '.exe':
            # TODO: get icon out of exe withOUT using weird winpy BS
            pass
        # if ico just use it
        elif ext == '.ico':
            try:
                icon = wx.Icon(filename, wx.BITMAP_TYPE_ICO)
                if icon.IsOk():
                    return self.imagelist.Add(icon)
            except Exception as e:
                logger.exception("Error while adding icons")
                # logger.warning(e)
                return self.iconentries['default']
        elif ext == '.py':
            return self.iconentries['python']

        # if no key returned already, return default
        return self.iconentries['default']

    def TreeItemExpanding(self, event):
        """Called when a node is about to expand.
        Loads the node's files from the file system.
        """
        item = event.GetItem()

        # check if item has directory data
        d = self.GetPyData(item)
        self._load_dir(item, d)

        event.Skip()

    def TreeItemCollapsing(self, event):
        """Called when a node is about to collapse."""
        item = event.GetItem()

        # 0 children -> _load() reloads the children when re-expanded
        item.DeleteChildren(self)

        event.Skip()

    def OnTreeSelChanged(self, evt):
        """Called when the GenericTreeItem selected in the tree changes"""
        logger.debug("OnTreeSelChanged")
        item = evt.GetItem()

        # data is the path to the selected file or folder
        data = self.GetPyData(item)

        self.model.set_selected(data)
        self.selected_item = evt.GetItem()
        pub.sendMessage("tree_selection_changed", tree_object_reference=self)
        evt.Skip()

if __name__ == '__main__':

    from osvcad.ui.model import Model

    class TestFrame(wx.Frame):
        r"""Frame for testing"""
        def __init__(self):
            wx.Frame.__init__(self, None, title="test", size=(400, 600))
            from os import getcwd
            self.tree = Tree(self,
                             Model(),
                             root_directory=getcwd(),
                             checkable_extensions=['.tsv'],
                             disabled_extensions=['.dat'],
                             excluded_extensions=['.pyc', '.txt'],
                             agw_style=wx.TR_DEFAULT_STYLE,
                             context_menu=True)
    app = wx.App()
    frame = TestFrame()
    frame.Show()
    app.MainLoop()
