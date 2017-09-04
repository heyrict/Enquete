import kivy
import csv
import pmdf, os
#from functools import partial

from kivy.config import Config
Config.set('kivy', 'default_font', [
    './wqy-microhei.ttc',
    './wqy-microhei.ttc',
    './wqy-microhei.ttc',
    './wqy-microhei.ttc',
    './wqy-microhei.ttc'
])

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.modalview import ModalView
from kivy.uix.filechooser import FileChooser
from kivy.uix.listview import ListView, ListItemLabel, ListItemButton
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.adapters.listadapter import ListAdapter
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.lang import Builder


class OpenDialog(ModalView):
    load = ObjectProperty()
    cancel = ObjectProperty()


class MenuScreen(Screen):
    userDataDir = StringProperty()

    def openFileChooser(self):
        self.view = ModalView()
        self.view.add_widget(OpenDialog(size_hint=(1,1),
            load = self.load, cancel = self.cancel))
        self.view.open()

    def load(self, path, filename):
        if len(filename) != 1:
            print("Please select at least one file")
            pu = WarningPopup(warnTxt="Please select at least one file",
                    onok=lambda:1, oncancel=lambda:1)
            pu.open()
            return
        fname, fext = os.path.splitext(filename[0])
        folderString, fname = os.path.split(fname)
        data_filter = pmdf.PMDFParser(filename[0]).parse()

        csvfile = os.path.join(self.userDataDir,fname+".csv")
        if os.path.exists(csvfile):
            with open(csvfile) as f:
                dataframe = list(csv.DictReader(f))
        else:
            dataframe = []

        dataframe.append({})
        for i in data_filter.field_list:
            dataframe[-1][i] = ""

        mainscr = MainScreen(name="main")
        mainscr.csvfile = csvfile
        mainscr.data_filter = data_filter
        mainscr.dataframe = dataframe

        self.view.dismiss()
        self.manager.switch_to(mainscr)

    def cancel(self):
        self.view.dismiss()


class DataItemCanel(Widget):
    valueVal = StringProperty()


class Toolbar(BoxLayout):
    index = NumericProperty()
    root = ObjectProperty()

    #def new_data(self):
    #    self.root.load_data()
    #    self.index = -1

    def save_data(self):
        data2add = [self.root.data_adapter.get_view(i) for i in
                range(self.root.data_adapter.get_count())]
        data2add = dict([(self.root.data_filter.field_list[i],
            data2add[i].valueVal if data2add[i].valueVal
            else self.root.data_adapter.data[i][1])
            for i in range(len(data2add))])

        try: self.root.data_filter.filter_all(data2add)
        except ValueError as e:
            pu = WarningPopup(warnTxt=str(e)[:100],
                    onok=lambda:1, oncancel=lambda:1)
            pu.open()
            return

        print(data2add)
        #if self.index == -1:
        #    self.root.dataframe = self.root.dataframe + [data2add]
        #else:
        #    temp = list(self.root.dataframe)
        #    temp[self.index] = data2add
        #    self.root.dataframe = temp
        temp = list(self.root.dataframe)
        temp[self.index] = data2add
        self.root.dataframe = temp

    def del_data(self):
        def delRow():
            print("DEL:",self.root.dataframe[self.index])
            temp = list(self.root.dataframe)
            temp.pop(self.index)
            self.root.dataframe = temp
        pu = WarningPopup(warnTxt="Make sure you want to delete!",
            onok = delRow, oncancel = lambda:1)
        pu.open()


class WarningPopup(Popup):
    warnTxt = StringProperty()
    onok = ObjectProperty()
    oncancel = ObjectProperty()


class DropDownInput(ListItemButton):
    labels = ListProperty()

    def __init__(self, *args, **kwargs):
        super(DropDownInput, self).__init__(*args, **kwargs)
        self.menu = DropDown()
        self.on_release = lambda: self.menu.open(self)
        self.menu.bind(on_select=lambda instance, x: setattr(self, 'text', x))

    def on_labels(self, instance, labels):
        for i in labels:
            btn = Button(text=i,size_hint_y=None, height=100, font_size=30)
            btn.bind(on_release=lambda btn:self.menu.select(btn.text))
            self.menu.add_widget(btn)


class MainScreen(Screen):
    data_filter = ObjectProperty(baseclass=pmdf.PMDF)
    dataframe = ObjectProperty()
    csvfile = StringProperty()

    index_adapter = ObjectProperty()
    data_adapter = ObjectProperty()
    cIndexView = ObjectProperty()
    cDataView = ObjectProperty()
    cDataData = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super(MainScreen, self).__init__(*args, **kwargs)
        self.box = BoxLayout()
        self.add_widget(self.box)

        def getStrRangeInd(obj):
            try: strRangeInd = [type(i) for i in self.data_filter.getRestriction(
                obj[0])].index(pmdf.PMStrRangeRestriction)
            except ValueError: strRangeInd = -1
            return strRangeInd

        self.data_args_converter = lambda row_index, obj: {
                'key': obj[0],
                'value': obj[1],
                'strRangeInd': getStrRangeInd(obj),
                'rest': self.data_filter.getRestriction(obj[0])}
        self.index_args_converter = lambda row_index, obj: {
                'id': obj[self.data_filter.field_list[0]],
                'load_data': lambda x,y: self.load_data(x,y)}

    def on_dataframe(self, instance, data):
        if self.cIndexView == None:
            self.oninit(self.dataframe)
        else:
            if sum([i[1] != "" for i in self.dataframe[-1].items()]) > 0:
                self.dataframe.append({})
                for i in self.data_filter.field_list:
                    self.dataframe[-1][i] = ""

            self.index_adapter.data = self.dataframe
            #data.to_excel(self.fname+".xlsx",index=False)
            try:
                with open(self.csvfile,'w') as f:
                    writer = csv.DictWriter(f,self.data_filter.field_list)
                    writer.writeheader()
                    writer.writerows(self.dataframe[:-1])
            except:
                pu = WarningPopup(warnTxt="Cannot write to "+self.csvfile,
                        onok=lambda:1, oncancel=lambda:1)
                pu.open()
                return

    def oninit(self, data):
        self.box.clear_widgets()

        self.index_adapter = ListAdapter(
                data=data,
                args_converter=self.index_args_converter,
                template="IndexItem")

        self.cIndexView = ListView(adapter=self.index_adapter,
                size_hint_x=.3)
        self.box.add_widget(self.cIndexView)

    def load_data(self, index=-1, is_selected=True):
        if is_selected == False:
            if self.cDataView != None:
                self.box.remove_widget(self.cDataView)
            return

        curRow = self.dataframe[index]

        if self.cDataView == None or self.cDataView.parent == None:
            self.data_adapter = ListAdapter(
                    data=[(i,curRow[i]) for i in self.data_filter.field_list],
                    args_converter=self.data_args_converter,
                    template="DataItem")

            self.cDataView = BoxLayout(orientation="vertical")
            self.toolbar = Toolbar()
            self.toolbar.index = index
            self.toolbar.root = self
            self.cDataView.add_widget(self.toolbar)
            self.cDataView.add_widget(ListView(adapter=self.data_adapter))
            self.box.add_widget(self.cDataView)
        else:
            self.toolbar.index = index
            self.data_adapter.data = [(i,curRow[i]) for i in self.data_filter.field_list]
        #if self.cDataView != None:
        #    self.box.remove_widget(self.cDataView)
        #if is_selected == False: return

        #if index == -1:
        #    curRow = pd.Series(index=self.dataframe.columns).fillna("")
        #else:
        #    curRow = list(self.dataframe.iterrows())[index][1]

        #self.data_adapter = ListAdapter(
        #        data=curRow.iteritems(),
        #        args_converter=self.data_args_converter,
        #        template="DataItem")

        #self.cDataView = BoxLayout(orientation="vertical")
        #toolbar = Toolbar()
        #toolbar.index = index
        #toolbar.root = self
        #self.cDataView.add_widget(toolbar)
        #self.cDataView.add_widget(ListView(adapter=self.data_adapter))
        #self.box.add_widget(self.cDataView)


class EnqueteApp(App):
    def build(self):
        print("## UserDataDir:",self.user_data_dir)
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu', userDataDir=self.user_data_dir))
        return sm


if __name__ == '__main__':
    EnqueteApp().run()

