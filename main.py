import sys
import os

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from PyQt5 import QtGui, QtWidgets

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
def getpasturetime(df, probe):
    mask = (df[probe] >= 62.5)
    pastrange = df.index[mask].tolist()
    return pastrange[0], pastrange[-1]
def is_pasteurized(df):
    #takes a resampled DataFrame
    tempmask = (df['min'] > 62.5)
    return len(df.loc[tempmask]) >= 30
MINUTES5 = mdates.MinuteLocator(interval=5)
MINUTES10 = mdates.MinuteLocator(interval=10)
M_FMT = "%H:%M"
def generate_raw_graph(df, probe, batch):
    fig, ax = plt.subplots()
    ax.set_title(f"Batch: {batch} Raw Data")
    ax.plot(df.index, df[probe])
    ax.set_xlabel('Time')
    ax.set_ylabel('Temperature °C')
    ax.xaxis.set_major_locator(MINUTES10)
    ax.xaxis.set_major_formatter(M_FMT)
    fig.autofmt_xdate()
    fig.savefig(f'{batch}/{batch} raw.png')
    return None
# coding: utf-8
def generate_min_max(rdf, batch, pstart, pstop):
    fig, (ax1, ax2) = plt.subplots(2,1 sharex=True)

    ax1.plot(rdf['max'], label="Max at Time")
    ax1.axhline(62.5, label="62.5°C", color="blue")
    ax1.axhline(64.5, label='64.5°C', color="red")
    ax1.set_title(f"Batch: {batch} Max Readings")
    ax1.set_xlabel("Time")
    ax1.set_xlim(pstart, pstop)
    ax1.xaxis.set_major_locator(MINUTES5)
    ax1.xaxis.set_major_formatter(M_FMT)
    ax1.set_ylabel('Temperature °C')
    ax1.set_ylim(60,65)
    ax1.legend()

    ax2.plot(rdf['min'], label="Min at Time")
    ax2.axhline(62.5, label="62.5°C", color="blue")
    ax2.axhline(64.5, label='64.5°C', color="red")
    ax2.set_title(f"Batch: {batch} Max Readings")
    ax2.set_xlabel("Time")
    ax2.set_xlim(pstart, pstop)
    ax2.xaxis.set_major_locator(MINUTES5)
    ax2.xaxis.set_major_formatter(M_FMT)
    ax2.set_ylabel('Temperature °C')
    ax2.set_ylim(60,65)
    ax2.legend()

    fig.autofmt_xdate()
    fig.savefig(f'{batch}/{batch} minmax.png')
    return None
def generate_full(df, start, stop, , probe, batch):
    try:
        os.mkdir(batch)
    except FileExistsError:
        pass

    tmask = (df.index >= start) & (df.index <= stop)
    pstart, pstop = getpasturetime(df.loc[tmask], probe)
    df.loc[tmask][probe].to_csv(f'{batch}/{batch} raw.csv')
    generate_raw_graph(df.loc[tmask], probe, batch)
    rdf = resample_data(df,start,stop,probe)
    generate_min_max(rdf,batch,pstart,pstop)
    cols = ['date','time'] + list(rdf)
    rdf['date'] = [d.date() for d in rdf.index]
    rdf['time'] = [d.time() for d in rdf.index]
    rdf = rdf.loc[:,cols]
    rdf.to_csv(f'{batch}/{batch}.csv', index=False)
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
