from PyQt5 import QtGui, QtWidgets
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def parse_csv(f):
    df = pd.read_csv(f)
    print(df.columns)
    df.set_index("Date/Time", inplace=True)
    df.index = pd.to_datetime(df.index)
    for column in df.columns:
        if column == "Date/Time":
            pass
        else:
            df[column] = pd.to_numeric(df[column], errors='coerce')
    df = df.loc[~df.index.duplicated(keep='first')]
    print(df.index.dtype)
    return df
def resample_data(df,start,stop,probe):
    timemask = (df.index > start) & (df.index <= stop)
    masked = df.loc[timemask][probe]
    return masked.resample('1T').apply(["first","max","min","last","mean"])
# coding: utf-8

def generate_graph(df, path):

    minutes = mdates.MinuteLocator(interval = 5)
    m_fmt = mdates.DateFormatter('%H:%M')
    probe = df[df.columns.get_level_values(0)][0]
    batch = os.path.splitext(path)[1].split('.')[0]
    fig, ax = plt.subplots()
    ax.title(f"Temperature Values For Batch: {batch}")

    ax.plot(df.index, probe['first'], label="Value at Time")
    ax.plot(df.index, probe['mean'], label="Mean Value of Time")
    ax.xlabel('Time')
    ax.ylabel('Temperature °C')

    ax.xaxis.set_major_locator(minutes)
    ax.xaxis.set_major_formatter(m_fmt)

    ax.legend()
    fig.autofmt_xdate()
    fig.savefig(path+'.png')
    return None
class MainWindow(QtWidgets.QWidget):

    def __init__(self):

        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        grid = QtWidgets.QGridLayout()

        self.infile_name = QtWidgets.QLabel('No File Selected')

        self.probe_list = QtWidgets.QListWidget()
        self.probe_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)

        self.start_datetime = QtWidgets.QDateTimeEdit()
        self.stop_datetime = QtWidgets.QDateTimeEdit()
        start_label = QtWidgets.QLabel("Start Time")
        stop_label = QtWidgets.QLabel("End Time")

        open_button = QtWidgets.QPushButton("Open File")
        open_button.clicked.connect(self.open_file)

        generate_button = QtWidgets.QPushButton("Generate Report")
        generate_button.clicked.connect(self.generate_report)

        #Set Layout
        grid.addWidget(self.infile_name, 0,0)
        grid.addWidget(open_button,0,1)
        grid.addWidget(self.start_datetime,1,0)
        grid.addWidget(start_label,1,1)
        grid.addWidget(self.stop_datetime,2,0)
        grid.addWidget(stop_label,2,1)
        grid.addWidget(self.probe_list,3,0)
        grid.addWidget(generate_button,4,0,4,1)

        self.setLayout(grid)
        self.setWindowTitle("Pasteurization Report Generator")
        self.show()

    def open_file(self):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Open File',
            "",
            "Csv Files (*.csv)"
        )[0]
        if path:
            self.probe_list.clear()
            self.infile_name.setText(path.split('/')[-1])
            self.dataframe = parse_csv(path)
            for item in self.dataframe.columns:
                self.probe_list.addItem(item)

            self.start_datetime.setDateTime(
                self.dataframe.index.min().to_pydatetime()
                )
            self.stop_datetime.setDateTime(
                self.dataframe.index.max().to_pydatetime()
                )
        else:
            self.infile_name.setText("No File Selected")

    def generate_report(self):
        selection = self.probe_list.selectedItems()
        if selection:
            outpath = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Files",
                "",
                "Multiple Files"
            )
            if outpath:
                data = resample_data(self.dataframe,
                                     self.start_datetime.dateTime().toPyDateTime(),
                                     self.stop_datetime.dateTime().toPyDateTime()
                                     )
                data.to_csv(str(outpath[0])+".csv")
                generate_graph(data, str(outpath[0]))




            else:
                pass
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "No Probes Selected")

def main():
    app = QtWidgets.QApplication([])
    ex = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
