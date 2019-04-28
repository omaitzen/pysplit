import tkinter as tk
import os
import keyboard

from timeutils import format_time


RED = '#ff2222'
YELLOW = '#ffcc22'
GREEN = '#22ff99'
BLUE = '#222299'
WHITE = '#dbdbdb'
BLACK = '#000000'


def cfg(**kwargs):
    defaults = {
        'background': BLACK,
        'font': ('Roboto', 15),
        'foreground': WHITE
    }

    defaults.update(**kwargs)
    return defaults


class View(tk.Toplevel):
    def __init__(self, app, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.overrideredirect(True)

        self.app = app

        self.wm_title('pysplit')
        self.config(background=BLACK)
        self.grid_rowconfigure(1, minsize=40)
        self.grid_rowconfigure(2, minsize=660)
        self.grid_rowconfigure(3, minsize=80)

        self.frame_splits, self.frame_hotkeys, self.frame_runs = None, None, None
        self.init_frame_hotkeys()
        self.init_frame_runs()

        self.label_title = tk.Label(self, **cfg(text='Untitled Run', font=('Roboto', 24)))
        self.label_subtitle = tk.Label(self, **cfg(text='Untitled Run', font=('Roboto', 15)))
        self.label_timer = tk.Label(self, **cfg(text='0:00.00', font=('Roboto', 48)))

        self.label_title.grid(row=0, sticky='N')
        self.label_subtitle.grid(row=1, sticky='N')
        self.label_timer.grid(row=3, sticky='N')

        self.label_title.bind('<ButtonPress-1>', self.start_move)
        self.label_title.bind('<ButtonRelease-1>', self.stop_move)
        self.label_title.bind('<B1-Motion>', self.on_move)

    def on_load(self, filename):
        self.label_title.config(text=self.app.run_name)
        self.label_subtitle.config(text=self.app.subtitle)

        if self.frame_splits is not None:
            self.frame_splits.destroy()

        self.frame_splits = tk.Frame(self, background=BLACK)
        self.label_split_name, self.label_split_diff, self.label_split_projected = [], [], []

        for index, split in enumerate(self.app.splits):
            self.label_split_name.append(tk.Label(self.frame_splits, **cfg(text=split['name'], anchor='w')))
            self.label_split_diff.append(tk.Label(self.frame_splits, **cfg(text='', anchor='e')))
            self.label_split_projected.append(tk.Label(self.frame_splits, **cfg(
                text=format_time(self.app.projected_split_time(index)),
                anchor='e'
            )))

        self.frame_splits.grid(row=2, sticky='NWE')
        self.frame_splits.grid_columnconfigure(0, minsize=200)
        self.frame_splits.grid_columnconfigure(1, minsize=80)
        self.frame_splits.grid_columnconfigure(2, minsize=80)

        for index, split in enumerate(self.app.splits):
            self.label_split_name[index].grid(row=index + 1, column=0, sticky='WE')
            self.label_split_diff[index].grid(row=index + 1, column=1, sticky='WE')
            self.label_split_projected[index].grid(row=index + 1, column=2, sticky='WE')

    def init_frame_hotkeys(self):
        self.frame_hotkeys = tk.Frame(self, background=BLACK)
        self.label_hotkey, self.entry_hotkey = {}, {}

        for command in self.app.commands:
            self.label_hotkey[command] = tk.Label(self.frame_hotkeys, **cfg(text=command + ':', width=10, anchor='e'))
            self.entry_hotkey[command] = tk.Entry(self.frame_hotkeys, **cfg(width=10, highlightbackground=BLACK))
            self.app.current_hotkey[command] = ''

            self.entry_hotkey[command].insert(0, self.app.default_hotkey[command])

        self.button_apply_hotkeys = tk.Button(self.frame_hotkeys, **cfg(
            text='Apply',
            highlightbackground=BLACK,
            command=self.apply_hotkeys
        ))

        # self.frame_hotkeys.grid(row=4)
        for index, command in enumerate(self.app.commands):
            self.label_hotkey[command].grid(row=index, column=0)
            self.entry_hotkey[command].grid(row=index, column=1)
        self.button_apply_hotkeys.grid(row=len(self.app.commands), column=0, columnspan=2)

        self.apply_hotkeys()

    def init_frame_runs(self):
        self.frame_runs = tk.Frame(self, background=BLACK)

        self.label_runs_heading = tk.Label(self.frame_runs, **cfg(text='Runs', font=('Roboto', 24)))
        self.select_run = tk.Listbox(self.frame_runs, **cfg(height=4, highlightcolor=BLUE, selectbackground=BLUE, selectmode=tk.SINGLE))
        for filename in os.listdir(os.getcwd()):
            if filename.endswith('.txt'):
                self.select_run.insert(tk.END, filename)

        self.select_run.bind('<<ListboxSelect>>', lambda e: self.app.load_run(self.get_selected_run()))

        self.frame_runs.grid(row=54, sticky='NWE')
        self.label_runs_heading.pack()
        self.select_run.pack(fill=tk.BOTH, expand=True)

    def get_selected_run(self):
        return self.select_run.get(int(self.select_run.curselection()[0]))

    def update_timer(self):
        current_timer = self.app.current_timer()

        self.label_timer.config(
            text=format_time(current_timer),
            foreground=GREEN if self.app.running else WHITE if current_timer == 0 else YELLOW
        )

    def update_frame_splits(self):
        current_split_index = self.app.current_split_index()

        for index, split in enumerate(self.app.splits):
            delta_split_time = self.app.delta_split_time(index)
            self.label_split_diff[index].config(
                text=format_time(delta_split_time, difference=True),
                foreground=GREEN if (delta_split_time is not None and delta_split_time < 0) else RED
            )

            projected_split_time = self.app.projected_split_time(index)
            self.label_split_projected[index].config(
                text=format_time(projected_split_time)
            )

            for widget in [
                self.label_split_name[index],
                self.label_split_diff[index],
                self.label_split_projected[index]
            ]:
                widget.config(
                    background=BLUE if (index == current_split_index and self.app.running) else BLACK
                )

    def apply_hotkeys(self):
        print('apply hotkeys')
        for command in self.app.commands:
            hotkey = self.entry_hotkey[command].get()
            if hotkey != self.app.current_hotkey[command]:
                try:
                    keyboard.remove_hotkey(self.app.current_hotkey[command])
                except KeyError:
                    pass

                try:
                    keyboard.add_hotkey(hotkey, getattr(self.app, command))
                    self.app.current_hotkey[command] = hotkey
                    print('assign hotkey', hotkey, 'to command', command)
                except ValueError:
                    self.app.current_hotkey[command] = ''

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        delta_x = event.x - self.x
        delta_y = event.y - self.y
        x = self.winfo_x() + delta_x
        y = self.winfo_y() + delta_y
        self.geometry('+%s+%s' % (x, y))
