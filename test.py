import platform
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import vlc
import time


class VideoPlayer:
    def __init__(self, master, video_id, parent):
        self.video_id = video_id
        self.mediaPlayer = None
        self.is_user_seeking = False

        # Контейнер для видео и управления
        self.container = tk.Frame(master, bg="#23272a", relief=tk.RAISED, bd=2)
        self.container.grid_propagate(False)

        # Видео панель
        self.videoFrame = tk.LabelFrame(self.container, text=f"Video {video_id + 1}",
                                        bg="black", fg="white", font=("Arial", 8), labelanchor="n", width=240, height=210)
        self.videoFrame.pack(side=tk.TOP, padx=3, pady=3)
        self.videoFrame.pack_propagate(False)

        # Кнопка для перехода в полноэкранный режим
        self.fullscreen_btn = tk.Button(self.container, text="🔄", command=lambda: parent.toggle_fullscreen(self.video_id),
                                        bg="#5865F2", fg="white", font=("Arial", 8))
        self.fullscreen_btn.pack(side=tk.TOP, pady=5)

        # Кнопка выхода из полноэкранного режима (скрыта изначально)
        self.exit_fullscreen_btn = tk.Button(self.container, text="❌", command=lambda: parent.toggle_fullscreen(self.video_id),
                                             bg="red", fg="white", font=("Arial", 12, "bold"))
        self.exit_fullscreen_btn.place_forget()

        # Ползунок перемотки
        seekFrame = tk.Frame(self.container, bg="#2c2f33")
        seekFrame.pack(side=tk.BOTTOM, fill=tk.X, pady=3)
        self.seekScale = tk.Scale(seekFrame, from_=0, to=100, orient=tk.HORIZONTAL,
                                  sliderlength=8, bd=0, length=200, bg="#2c2f33", fg="white",
                                  troughcolor="#5865F2", highlightbackground="#2c2f33")
        self.seekScale.pack(side=tk.LEFT, padx=3)

        # Метка времени
        self.timeLabel = tk.Label(seekFrame, text="00:00 / 00:00", bg="#2c2f33", fg="white", font=("Arial", 8))
        self.timeLabel.pack(side=tk.RIGHT, padx=5)

        # Панель управления (кнопки в ряд)
        controlFrame = tk.Frame(self.container, bg="#2c2f33")
        controlFrame.pack(side=tk.BOTTOM, fill=tk.X, padx=3, pady=3)

        btn_style = {
            "bg": "#5865F2",
            "fg": "white",
            "font": ("Arial", 8, "bold"),
            "relief": tk.RAISED,
            "bd": 2,
            "width": 8
        }
        tk.Button(controlFrame, text="Open", command=self.OpenFile, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(controlFrame, text="Play", command=self.PlayMovie, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(controlFrame, text="Pause", command=self.PauseMovie, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(controlFrame, text="Stop", command=self.StopMovie, **btn_style).pack(side=tk.LEFT, padx=2)

        # Ползунок громкости
        tk.Label(controlFrame, text="Volume", bg="#2c2f33", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=5)
        self.volumeScale = tk.Scale(controlFrame, from_=0, to=100, orient=tk.HORIZONTAL,
                                    command=self.MovieVolume, sliderlength=8, bd=0, showvalue=0, length=80,
                                    bg="#2c2f33", fg="white", troughcolor="#5865F2", highlightbackground="#2c2f33")
        self.volumeScale.pack(side=tk.LEFT, padx=2)
        self.volumeScale.set(50)

        # Метка для отображения даты изменения файла
        self.modificationDateLabel = tk.Label(self.container, text="Last modified: N/A",
                                              bg="#2c2f33", fg="white", font=("Arial", 8), wraplength=200)
        self.modificationDateLabel.pack(pady=2)

        # Кнопки скорости
        speedFrame = tk.Frame(self.container, bg="#2c2f33")
        speedFrame.pack(side=tk.BOTTOM, pady=3)
        speed_btn_style = {
            "bg": "#5865F2",
            "fg": "white",
            "font": ("Arial", 8),
            "relief": tk.RAISED,
            "bd": 2,
            "width": 6
        }
        tk.Button(speedFrame, text="0.5x", command=lambda: self.setSpeed(0.5), **speed_btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(speedFrame, text="1x", command=lambda: self.setSpeed(1.0), **speed_btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(speedFrame, text="2x", command=lambda: self.setSpeed(2.0), **speed_btn_style).pack(side=tk.LEFT, padx=2)

        # Связывание событий с ползунком
        self.seekScale.bind("<Button-1>", self.startSeeking)  # Начало перемотки
        self.seekScale.bind("<ButtonRelease-1>", self.stopSeeking)  # Конец перемотки
        self.seekScale.bind("<B1-Motion>", self.SeekMovie)  # Перемотка при движении

        # Обновление состояния ползунка
        self.updateSeek()

    def simulate_fullscreen(self, fullscreen, parent):
        """Имитация полноэкранного режима."""
        if fullscreen:
            self.container.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.container.tkraise()
            self.fullscreen_btn.pack_forget()
            self.exit_fullscreen_btn.place(relx=0.95, rely=0.02, anchor="ne")
            self.videoFrame.configure(width=parent.tk_instance.winfo_width(), height=parent.tk_instance.winfo_height())
            self.videoFrame.pack_propagate(False)
            if self.mediaPlayer:
                self.mediaPlayer.set_hwnd(self.GetHandle())
        else:
            self.container.place_forget()
            self.exit_fullscreen_btn.place_forget()
            self.fullscreen_btn.pack(side=tk.TOP, pady=5)
            self.videoFrame.configure(width=240, height=210)
            parent.update_layout()


    def OpenFile(self):
        file = filedialog.askopenfilename(filetypes=[
            ("Video files", "*.mp4 *.avi *.mkv *.mov *.ifv"),
            ("All files", "*.*")
        ])
        if file:
            try:
                self.mediaPlayer = vlc.MediaPlayer(file)
                if platform.system() == 'Windows':
                    self.mediaPlayer.set_hwnd(self.GetHandle())
                elif platform.system() == 'Linux':
                    self.mediaPlayer.set_xwindow(self.GetHandle())
                elif platform.system() == 'Darwin':  # macOS
                    self.mediaPlayer.set_nsobject(self.GetHandle())
                self.seekScale.set(0)
                modification_time = os.path.getmtime(file)
                formatted_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modification_time))
                self.modificationDateLabel.config(text=f"Last modified: {formatted_date}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")

    def PlayMovie(self):
        if self.mediaPlayer:
            self.mediaPlayer.play()

    def PauseMovie(self):
        if self.mediaPlayer:
            self.mediaPlayer.pause()

    def StopMovie(self):
        if self.mediaPlayer:
            self.mediaPlayer.stop()
            self.seekScale.set(0)

    def MovieVolume(self, event=None):
        if self.mediaPlayer:
            self.mediaPlayer.audio_set_volume(self.volumeScale.get())

    def setSpeed(self, speed):
        if self.mediaPlayer:
            self.mediaPlayer.set_rate(speed)

    def SeekMovie(self, event=None):
        if self.mediaPlayer and self.is_user_seeking:
            total_length = self.mediaPlayer.get_length()
            new_time = int(self.seekScale.get() / 100 * total_length)
            self.mediaPlayer.set_time(new_time)

    def startSeeking(self, event=None):
        self.is_user_seeking = True

    def stopSeeking(self, event=None):
        self.is_user_seeking = False
        self.SeekMovie()

    def updateSeek(self):
        if self.mediaPlayer and not self.is_user_seeking:
            current_time = self.mediaPlayer.get_time()
            total_length = self.mediaPlayer.get_length()
            if total_length > 0:
                self.seekScale.set((current_time / total_length) * 100)
                self.timeLabel.config(text=f"{self.format_time(current_time)} / {self.format_time(total_length)}")
        self.container.after(100, self.updateSeek)

    @staticmethod
    def format_time(milliseconds):
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02}:{seconds:02}"

    def GetHandle(self):
        return self.videoFrame.winfo_id()


class MultiVideoPlayerApp:
    

    def __init__(self):
        self.tk_instance = tk.Tk()
        self.tk_instance.title("Multi Video Player")
        self.tk_instance.geometry("800x600")
        self.tk_instance.configure(bg="#2c2f33")

        self.scrollable_canvas = tk.Canvas(self.tk_instance, bg="#2c2f33")
        self.scrollable_frame = tk.Frame(self.scrollable_canvas, bg="#2c2f33")
        self.scrollbar = tk.Scrollbar(self.tk_instance, orient=tk.VERTICAL, command=self.scrollable_canvas.yview)

        self.scrollable_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollable_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.scrollable_frame.bind("<Configure>", self.update_scrollregion)

        self.players = []
        self.fullscreen_player_id = None

        self.var1 = 0
        self.var2 = 0
        self.var3 = 0

        varFrame = tk.Frame(self.tk_instance, bg="#2c2f33")
        varFrame.pack(side=tk.TOP, pady=5)

        self.var1Label = tk.Label(varFrame, text=f"100% = {self.var1}", bg="#ff4500", fg="white",
                                             font=("Arial", 12, "bold"), relief=tk.RAISED, bd=1, padx=2)
        self.var1Label.pack(side=tk.LEFT, padx=0)

        self.var2Label = tk.Label(varFrame, text=f"50% = {self.var2}", bg="#32cd32", fg="white",
                                             font=("Arial", 12, "bold"), relief=tk.RAISED, bd=1, padx=2)
        self.var2Label.pack(side=tk.LEFT, padx=0)

        self.var3Label = tk.Label(varFrame, text=f"0% = {self.var3}", bg="#1e90ff", fg="white",
                                             font=("Arial", 12, "bold"), relief=tk.RAISED, bd=1, padx=2)
        self.var3Label.pack(side=tk.LEFT, padx=0)

        add_btn = tk.Button(self.tk_instance, text="Add Video", command=self.addPlayer,
                            bg="#5865F2", fg="white", font=("Arial", 10, "bold"), relief=tk.RAISED, bd=3, width=10)
        add_btn.pack(side=tk.TOP, pady=5)

        remove_btn = tk.Button(self.tk_instance, text="Remove Last Screen", command=self.removeLastPlayer,
                               bg="red", fg="white", font=("Arial", 10, "bold"), relief=tk.RAISED, bd=3, width=15)
        remove_btn.pack(side=tk.TOP, pady=5)

        self.tk_instance.bind("<space>", self.pauseAllPlayers)
        self.tk_instance.bind("<Return>", self.playAllPlayers)
        self.tk_instance.bind("z", self.increaseVar1)
        self.tk_instance.bind("x", self.increaseVar2)
        self.tk_instance.bind("c", self.increaseVar3)
        self.tk_instance.bind("a", self.decreaseVar1)
        self.tk_instance.bind("s", self.decreaseVar2)
        self.tk_instance.bind("d", self.decreaseVar3)

    def update_scrollregion(self, event=None):
        self.scrollable_canvas.configure(scrollregion=self.scrollable_canvas.bbox("all"))

    def toggle_fullscreen(self, video_id):
        if self.fullscreen_player_id is not None:
            self.players[self.fullscreen_player_id].simulate_fullscreen(False, self)
            self.fullscreen_player_id = None
        else:
            self.fullscreen_player_id = video_id
            self.players[video_id].simulate_fullscreen(True, self)

    def update_layout(self):
        for i, player in enumerate(self.players):
            max_columns = 3
            row = i // max_columns
            column = i % max_columns
            player.container.grid(row=row, column=column, padx=5, pady=5)

    def addPlayer(self):
        player = VideoPlayer(self.scrollable_frame, len(self.players), self)
        self.players.append(player)
        max_columns = 3
        column = len(self.players) - 1
        row = column // max_columns
        column = column % max_columns
        player.container.grid(row=row, column=column, padx=5, pady=5)

    def removeLastPlayer(self):
        if self.players:
            player = self.players.pop()
            player.container.destroy()
            self.update_scrollregion()

    def playAllPlayers(self, event=None):
        for player in self.players:
            if player.mediaPlayer:
                player.PlayMovie()

    def pauseAllPlayers(self, event=None):
        for player in self.players:
            if player.mediaPlayer:
                player.PauseMovie()

    def increaseVar1(self, event=None):
        self.var1 += 1
        self.var1Label.config(text=f"100% = {self.var1}")

    def decreaseVar1(self, event=None):
        if self.var1 > 0:
            self.var1 -= 1
            self.var1Label.config(text=f"100% = {self.var1}")

    def increaseVar2(self, event=None):
        self.var2 += 1
        self.var2Label.config(text=f"50% = {self.var2}")

    def decreaseVar2(self, event=None):
        if self.var2 > 0:
            self.var2 -= 1
            self.var2Label.config(text=f"50% = {self.var2}")

    def increaseVar3(self, event=None):
        self.var3 += 1
        self.var3Label.config(text=f"0% = {self.var3}")

    def decreaseVar3(self, event=None):
        if self.var3 > 0:
            self.var3 -= 1
            self.var3Label.config(text=f"0% = {self.var3}")

    def run(self):
        self.tk_instance.mainloop()


if __name__ == "__main__":
    app = MultiVideoPlayerApp()
    app.run()
    


    


