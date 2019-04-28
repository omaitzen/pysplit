import tkinter as tk
import time

from view import View
from timeutils import format_time, parse_time


class App(tk.Tk):
    commands = ['reset', 'toggle', 'split', 'save', 'close']
    default_hotkey = {
        'reset': 'cmd+r',
        'toggle': 'cmd+t',
        'split': 'e',
        'save': 'cmd+s',
        'close': 'cmd+c'
    }

    target_fps = 30

    def __init__(self):
        tk.Tk.__init__(self)
        self.geometry('+%s+%s' % (3000, 0))

        self.run_name = ''
        self.running = False
        self.toggle_time, self.toggle_timer = 0, 0
        self.splits = []

        self.current_hotkey = {}

        self.view = View(self)

        self.view.select_run.selection_set(0)
        self.load_run(self.view.get_selected_run())

        self.after(1000 // self.target_fps, self.update)

    def current_timer(self):
        if self.running:
            return self.toggle_timer + time.time() - self.toggle_time
        return self.toggle_timer

    def current_split_index(self):
        for index, split in enumerate(self.splits):
            if 'actual' not in split:
                return index
        return len(self.splits)

    def delta_split_time(self, index):
        try:
            return sum(
                split['actual'] - split['projected']
                for split in self.splits[:index + 1]
            )
        except KeyError:
            pass

    def projected_split_time(self, index=None):
        try:
            return sum(
                split['actual'] if 'actual' in split else split['projected']
                for split in (self.splits if index is None else self.splits[:index + 1])
            )
        except KeyError:
            pass

    def update(self):
        self.view.update_timer()
        self.after(1000 // self.target_fps, self.update)

    def load_run(self, filename):
        print('load', filename)

        with open(filename) as file:
            self.run_name = file.readline().replace('\n', '')
            self.subtitle = file.readline().replace('\n', '')
            file.readline()

            self.splits = []

            for line in file.readlines():
                columns = line.replace('\n', '').split('\t')
                if columns[0] == '':
                    break

                split = {'name': columns[0]}
                if len(columns) > 1:
                    split['projected'] = parse_time(columns[1]) - (self.projected_split_time() if len(self.splits) > 0 else 0)

                self.splits.append(split)

        self.view.on_load(filename)
        self.reset()

    def save_run(self, filename):
        with open(filename, 'w') as file:
            file.write(self.run_name + '\n')
            file.write(self.subtitle + '\n\n')
            for index, split in enumerate(self.splits):
                projected = self.projected_split_time(index)
                file.write(split['name'] + (
                    '' if projected is None else ('\t' + format_time(projected))
                ) + '\n')

    def reset(self):
        print('reset')

        self.toggle_timer = 0
        self.toggle_time = 0
        self.running = False

        for split in self.splits:
            if 'actual' in split:
                del split['actual']

        self.view.update_timer()
        self.view.update_frame_splits()

    def toggle(self):
        print('stop' if self.running else 'start')

        self.toggle_timer = self.current_timer()
        self.toggle_time = time.time()
        self.running = not self.running

        self.view.update_timer()
        self.view.update_frame_splits()

    def split(self):
        if self.running:
            index = self.current_split_index()

            previous_split_time = self.projected_split_time(index - 1) if index > 0 else 0
            self.splits[index]['actual'] = self.current_timer() - previous_split_time

            print('split', format_time(self.current_timer()))

            if index == len(self.splits) - 1:
                self.toggle()

            self.view.update_frame_splits()

    def save(self):
        filename = self.view.get_selected_run()
        print('save', filename)

        for split in self.splits:
            if 'actual' in split:
                split['projected'] = split['actual']

        self.save_run(filename)

        self.reset()

    def close(self):
        print('close')

        self.quit()
        exit(0)
