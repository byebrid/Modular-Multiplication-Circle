import tkinter as tk
from math import pi, sin, cos
from random import randint
import queue
import threading
import time
import random

WIDTH = 700
PADDING = 25
radius = (WIDTH/2 - PADDING)


class GUI:
    def __init__(self, master, queue):
        self.queue = queue
        self.master = master

        # Frames
        self.canvas_frame = tk.Frame(master)
        self.canvas_frame.pack()
        self.sliders_frame = tk.Frame(master)
        self.sliders_frame.pack()

        # Canvas
        self.canvas = tk.Canvas(self.canvas_frame, width=WIDTH, height=WIDTH)
        self.canvas.pack()

        # Multiplier slider
        self.multiplier = tk.Scale(self.sliders_frame, 
            from_=1, to=200, 
            orient=tk.HORIZONTAL, 
            length=200,
            label="Multiplier",
            command=self.on_change)
        self.multiplier.set(2)
        self.multiplier.pack(side=tk.LEFT)

        # Multiplier entry
        def multiplier_callback(event):
            self.multiplier.set(multiplier_entry.get())

        multiplier_entry = tk.Entry(self.sliders_frame, 
            textvariable=self.multiplier,
            width=4
            )
        multiplier_entry.pack(side=tk.LEFT)
        multiplier_entry.bind("<Return>", multiplier_callback)

        # Number of points slider
        self.n_points = tk.Scale(self.sliders_frame, 
            from_=1, to=1000, 
            orient=tk.HORIZONTAL, 
            length=200,
            label="Number of points",
            command=self.on_change)
        self.n_points.set(100)
        self.n_points.pack(side=tk.RIGHT)

        # Number of points entry
        def n_points_callback(event):
            self.n_points.set(n_points_entry.get())

        n_points_entry = tk.Entry(self.sliders_frame, 
            textvariable=self.n_points,
            width=4
            )
        n_points_entry.pack(side=tk.LEFT)
        n_points_entry.bind("<Return>", n_points_callback)

    def processIncoming(self):
        """Handle all messages currently in the queue, if any."""
        while self.queue.qsize():
            try:
                msg = self.queue.get(0)
                # Check contents of message and do whatever is needed. As a
                # simple test, print it (in real life, you would
                # suitably update the GUI's display in a richer fashion).
                
                if msg[0] == "clear":
                    self.canvas.delete(tk.ALL)
                elif msg[0] == "update":
                    self.canvas.update()
                elif msg[0] == "create_circle":
                    self.canvas.create_oval(PADDING, PADDING, WIDTH-PADDING, WIDTH-PADDING)
                elif msg[0] == "create_line":
                    coords = msg[1:5]
                    self.canvas.create_line(*coords)
            except queue.Empty:
                # just on general principles, although we don't
                # expect this branch to be taken in this case
                pass

    def on_change(self, *args):
        self.canvas.delete(tk.ALL)
        client.draw() # Not a fan of calling from client like this


class ThreadedClient:
    """
    Launch the main part of the GUI and the worker thread. periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means that you have all the thread controls in a single place.
    """
    def __init__(self, master):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI as well. We spawn a new thread for the worker (I/O).
        """
        self.master = master

        # Create the queue
        self.queue = queue.Queue()

        # Set up the GUI part
        self.gui = GUI(master, self.queue)

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall()

    def periodicCall(self):
        """
        Check every 200 ms if there is something new in the queue.
        """
        self.gui.processIncoming()
        self.master.after(50, self.periodicCall)

    def draw(self):
        """Starts new thread to draw points."""
        thread = threading.Thread(target=self._draw)
        thread.start()

    def _draw(self):
        """
        Decides where to draw lines based on current parameters
        """
        self.queue.put(("clear",))
        self.queue.put(("create_circle",))
        # Creating dict of points' coords on circle to possible increase speed?
        coords = {}
        n_points = self.gui.n_points.get()
        multiplier = self.gui.multiplier.get()

        for i in range(n_points):
            angle = pi/2 - i * 2 * pi / n_points
            x = WIDTH/2 + radius * cos(angle)
            y = WIDTH/2 - radius * sin(angle)
            point = (x, y)
            coords[i] = point # Storing coordinates

        # Drawing lines on circle using modular multiplication
        for i in range(n_points):
            i2 = (i * multiplier) % n_points
            msg = ("create_line", *coords[i], *coords[i2])
            self.queue.put(msg)

        self.queue.put(("update"))   

root = tk.Tk()

client = ThreadedClient(root)
root.mainloop()