import os
os.environ['PATH'] += os.pathsep + 'C:\ffmpeg\bin'

import shutil
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pydub import AudioSegment

class CueSplitterApp:
    def __init__(self, master):
        self.master = master
        master.title('Cue Splitter')
        self.cancelled = False
        self.create_cue_file = tk.BooleanVar(value=True)
        self.create_m3u8_file = tk.BooleanVar(value=True)

        # Create input file label and entry
        self.input_file_label = tk.Label(master, text='Input File:')
        self.input_file_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.input_file_entry = tk.Entry(master, width=50)
        self.input_file_entry.grid(row=0, column=1, padx=5, pady=5)
        self.input_file_button = tk.Button(master, text='Browse', command=self.browse_input_file)
        self.input_file_button.grid(row=0, column=2, padx=5, pady=5)

        # Create output directory label and entry
        self.output_dir_label = tk.Label(master, text='Output Directory:')
        self.output_dir_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.output_dir_entry = tk.Entry(master, width=50)
        self.output_dir_entry.grid(row=1, column=1, padx=5, pady=5)
        self.output_dir_button = tk.Button(master, text='Browse', command=self.browse_output_dir)
        self.output_dir_button.grid(row=1, column=2, padx=5, pady=5)

        # Create output format label and dropdown
        self.output_format_label = tk.Label(master, text='Output Format:')
        self.output_format_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.output_format_var = tk.StringVar(value='wav')
        self.output_format_dropdown = tk.OptionMenu(master, self.output_format_var, 'mp3', 'wav', 'flac')
        self.output_format_dropdown.grid(row=2, column=1, padx=5, pady=5)
        
        # casilla cue create
        self.create_cue_file_checkbox = tk.Checkbutton(master, text='Create CUE file', variable=self.create_cue_file)
        self.create_cue_file_checkbox.grid(row=3, column=0, padx=5, pady=5, sticky='w')
        
        # casilla m3u8 create
        self.create_m3u8_file_checkbox = tk.Checkbutton(master, text='Create M3U8 file', variable=self.create_m3u8_file)
        self.create_m3u8_file_checkbox.grid(row=4, column=0, padx=5, pady=5, sticky='w')

        # split button
        self.split_button = tk.Button(master, text='Split', command=self.split_cue_file)
        self.split_button.grid(row=3, column=1, padx=5, pady=5)

    def browse_input_file(self):
        file_path = filedialog.askopenfilename(filetypes=[('CUE Files', '*.cue')])
        self.input_file_entry.delete(0, tk.END)
        self.input_file_entry.insert(0, file_path)

    def browse_output_dir(self):
        dir_path = filedialog.askdirectory()
        self.output_dir_entry.delete(0, tk.END)
        self.output_dir_entry.insert(0, dir_path)

    def split_cue_file(self):
        # Get the input file path and output directory path
        input_file_path = self.input_file_entry.get()
        output_dir_path = self.output_dir_entry.get()
        
        # Create progress window
        self.progress_window = tk.Toplevel()
        self.progress_window.title('Splitting...')
        self.progress_window.geometry('300x50')
        self.progress_window.resizable(False, False)

        # Create progress bar
        self.progress_bar = tk.ttk.Progressbar(self.progress_window, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill='x', padx=5, pady=5)
        
        # botton cancel
        self.cancel_button = tk.Button(self.progress_window, text='Cancel', command=self.cancel_split)
        self.cancel_button.pack(side='right', padx=5, pady=5)

        # Load the cue file
        with open(input_file_path, 'r', encoding='utf-8') as cue_file:
            cue_data = cue_file.read()

        # Split the cue data into individual tracks
        tracks = cue_data.split('TRACK')

        # Load the audio file
        audio = AudioSegment.from_file(os.path.splitext(input_file_path)[0] + '.flac')

        # Show progress window
        self.progress_window.deiconify()

        # Iterate over each track and split the audio file
        for i, track in enumerate(tracks[1:]):
            # Get the track start time
            start_time = track.split('INDEX 01')[1].strip()

            # Convert the start time to milliseconds
            minutes, seconds, frames = start_time.split(':')
            start_ms = (int(minutes) * 60 + int(seconds)) * 1000 + int(frames) * 1000 // 75

            # the end time
            if i >= len(tracks) - 2:
                end_ms = len(audio)
            else:
                if i >= len(tracks):
                    break
                end_time = tracks[i+1].split('INDEX 01')[1].strip()
                minutes, seconds, frames = end_time.split(':')
                end_ms = (int(minutes) * 60 + int(seconds)) * 1000 + int(frames) * 1000 // 75
                
            # Extract the track from the audio file
            track_audio = audio[start_ms:end_ms]

            # Save the track to disk
            output_file_path = os.path.join(output_dir_path, f'{nombre_cancion}.{i+1}.{self.output_format_var.get()}')
            track_audio.export(output_file_path, format=self.output_format_var.get())
            
            # Update progress bar
            self.progress_bar['value'] = (i+1) / len(tracks) * 100
            self.progress_window.update()

            # Check if cancel button was pressed
            for i, track in enumerate(tracks[1:]):
                if self.cancelled:
                    break

        # Hide progress window
        self.progress_window.withdraw()
            
        # Generate new cue and m3u8 files in the output directory
        cue_file_name = os.path.basename(input_file_path)
        cue_file_output_path = os.path.join(output_dir_path, cue_file_name)
        with open(cue_file_output_path, 'w') as cue_file:
            cue_file.write(cue_data)

        m3u8_file_name = os.path.splitext(cue_file_name)[0] + '.m3u8'
        m3u8_file_output_path = os.path.join(output_dir_path, m3u8_file_name)
        with open(m3u8_file_output_path, 'w') as m3u8_file:
            for i in range(1, len(tracks)):
                if i >= len(tracks):
                    break
                output_file_name = '{:02d}.{}'.format(i, self.output_format_var.get())
                m3u8_file.write(f'{output_file_name}\n')

        # Show a success message
        success_message = f'Successfully split {len(tracks)-1} tracks from {input_file_path} to {self.output_format_var.get()} format.'
        tk.messagebox.showinfo('Success', success_message)


if __name__ == '__main__':
    root = tk.Tk()
    app = CueSplitterApp(root)
    root.mainloop()
