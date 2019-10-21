import tkinter as tk

class MainMenu(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text='Video steganography', font='none 24 bold').grid(row=0, columnspan=2, sticky=tk.W+tk.E)

        ins_vid_button = tk.Button(
            self, 
            text='Hide Message to Video         ',
            command=lambda: master.open_hide_vid_form()
        )
        ext_vid_button = tk.Button(
            self,
            text='Extract Message from Video ',
            command=lambda: master.open_extract_vid_form()
        )
        ins_vid_button.grid(row=1, column=0, sticky=tk.W)
        ext_vid_button.grid(row=1, column=1, sticky=tk.W)

        ins_aud_button = tk.Button(
            self,
            text='Hide Message to Audio        ',
            command=lambda: master.open_hide_audio_form(),
        )
        ext_aud_button = tk.Button(
            self,
            text='Extract Message from Audio',
            command=lambda: master.open_extract_audio_form(),
        )
        ins_aud_button.grid(row=2, column=0, sticky=tk.W)
        ext_aud_button.grid(row=2, column=1, sticky=tk.W)

        exit_button = tk.Button(self, text='Exit', command=master.destroy,height = 3,width = 10)
        exit_button.grid(row=10, column=0, columnspan=5)