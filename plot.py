from datetime import datetime, timedelta, date
import pathlib
import pandas as pd
import numpy as np
from util import strfdelta
import sys
import matplotlib.pyplot as plt

import globals
import util

def get_data(data_dir: pathlib.Path, t_begin, t_end=datetime.max):
    csv_path_list = list(data_dir.glob("*.csv"))
    df = pd.DataFrame()
    for csv_path in csv_path_list:
        df1 = pd.read_csv(csv_path,sep=",",parse_dates=["start", "end"], )
        df = df.append(df1)
    df = df.set_index("start")
    if t_end > df.index.max():
        t_end = df.index.max()
    return df[t_begin: t_end]

class DataProcessor:
    def __init__(self, opt) -> None:
        self.opt = opt
        data_dir = util.get_data_dir()
        self.t_begin = util.today() - timedelta(days=opt.days-1)
        self.t_end = datetime.max
        self.df = get_data(data_dir, self.t_begin, self.t_end)
    
    def task_time(self, task):
        """
        return: float in seconds
        """
        mask = self.df["task"] == task
        df2 = self.df.loc[mask]
        end_time_arr = np.array(df2["end"])
        start_time_arr = np.array(df2.index)
        total_time = np.sum(end_time_arr - start_time_arr)
        return total_time/ np.timedelta64(1,'s')
    
    @property
    def task_set(self):
        return sorted(list(set(self.df["task"])))
    
    @property
    def task_time_list(self):
        l = [self.task_time(task) for task in self.task_set]
        return l

    def print_stat(self):
        print(f"Statistics for previous {self.opt.days} days")
        fmt = "{hours:02d} hours {minutes:02d} minutes"
        task_time_list = [timedelta(seconds=t) for t in self.task_time_list]
        for (task, t) in zip(self.task_set, task_time_list):
            t_str = strfdelta(t, fmt)
            print(f"[{task:10s}]:\t {t_str}")

        total = np.sum(task_time_list)
        t_str = strfdelta(total, fmt)
        print(f"[Total time]:\t {t_str}")
        t_str = strfdelta(total/self.opt.days, fmt)
        print(f"[Time per day]:\t {t_str}")
        print("done")
    
    def plot_pie(self):
        """
        plot pie chart
        refer to https://matplotlib.org/3.1.1/gallery/pie_and_polar_charts/pie_and_donut_labels.html#sphx-glr-gallery-pie-and-polar-charts-pie-and-donut-labels-py
        """
        fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(aspect="equal"))
        # The offset 
        fmt = "{hours:02d} h {minutes:02d} m"
        def func(pct):
            total = np.sum(self.task_time_list)
            # absolute = timedelta(seconds=pct/100*total)
            str_list = [f"{t:.1f}" for t in self.task_time_list]
            tar_s = f"{pct/100*total:.1f}"
            idx = str_list.index(tar_s)
            # return "{:.1f}%\n({:s})".format(pct, strfdelta(absolute, "{hours:02d} h {minutes:02d} min"))
            # return "{:.1f}%".format(pct)
            return text(idx)

        def text(i):
            total = np.sum(self.task_time_list)
            pct = self.task_time_list[i] / total * 100
            task = self.task_set[i]
            t = timedelta(seconds=self.task_time_list[i])
            t_str = strfdelta(t, fmt)
            return f"{task}\n{t_str}"

        explode = np.zeros(len(self.task_set))
        # wedges, texts, autotexts = ax.pie(self.task_time_list, explode=explode, labels=self.task_set, shadow=True, startangle=90, colors=globals.color_list, autopct=func)
        wedges, texts, autotext = ax.pie(self.task_time_list, explode=explode, wedgeprops=dict(width=1.0), startangle=-90, colors=globals.color_list, autopct=func, shadow=False)

        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        total = np.sum(self.task_time_list)
        t_str = strfdelta(total, fmt)
        ax.set_title(f"Total: {t_str}")
        fig.subplots_adjust(bottom=0.0, left=0.0, right=0.99, top=0.90)        
        #fig.suptitle(f"Total: {t_str}", verticalalignment='bottom')
        self.savefig(fig, f"pie.{self.opt.days}day.png")
    
    def savefig(self, fig, name):
        # fig.subplots_adjust(bottom=0.15, left=0.1, right=0.99, top=0.97, wspace=0.25, hspace=0)
        fig_dir = util.get_fig_dir()
        fig_path = fig_dir.joinpath(name)
        fig.savefig(fig_path)

def read_command(argv):
    from optparse import OptionParser
    usage_str = """
        USAGE:      python main.py --task [taskname]
        """
    parser = OptionParser(usage_str)
    parser.add_option('--days', dest='days', type=int, default=1)
    options, otherjunk = parser.parse_args(argv)
    if len(otherjunk) != 0:
        raise Exception('Command line input not understood: ' + str(otherjunk))
   
    return options


if __name__ == "__main__":
    opt = read_command(sys.argv[1:])
    t_begin = util.today()
    dp = DataProcessor(opt)
    dp.print_stat()
    dp.plot_pie()
    print("plot.py done.")
