#install scikit-image  
  
import tkinter as tk  
from tkinter import ttk  
from tkinter import *  
  
import cv2  
from PIL import Image, ImageTk  
  
import numpy as np  
from skimage.color import rgb2gray  
from skimage.filters import laplace  
from scipy.ndimage import variance  
  
import threading  
import time  
import atexit  
import pickle  
  
  
class MousePositionTracker(tk.Frame):  
    """ Tkinter Canvas mouse position widget. """  
  
    def __init__(self, canvas):  
        self.canvas = canvas  
        self.canv_width = self.canvas.cget('width')  
        self.canv_height = self.canvas.cget('height')  
        self.reset()  
  
        # Create canvas cross-hair lines.  
        xhair_opts = dict(dash=(3, 2), fill='white', state=tk.HIDDEN)  
        self.lines = (self.canvas.create_line(0, 0, 0, self.canv_height, **xhair_opts),  
                      self.canvas.create_line(0, 0, self.canv_width,  0, **xhair_opts))  
  
    def cur_selection(self):  
        return (self.start, self.end)  
  
    def begin(self, event):  
        self.hide()  
        self.start = (event.x, event.y)  # Remember position (no drawing).  
  
    def update(self, event):  
        self.end = (event.x, event.y)  
        self._update(event)  
        self._command(self.start, (event.x, event.y))  # User callback.  
  
    def _update(self, event):  
        # Update cross-hair lines.  
        self.canvas.coords(self.lines[0], event.x, 0, event.x, self.canv_height)  
        self.canvas.coords(self.lines[1], 0, event.y, self.canv_width, event.y)  
        self.show()  
  
    def reset(self):  
        self.start = self.end = None  
  
    def hide(self):  
        self.canvas.itemconfigure(self.lines[0], state=tk.HIDDEN)  
        self.canvas.itemconfigure(self.lines[1], state=tk.HIDDEN)  
  
    def show(self):  
        self.canvas.itemconfigure(self.lines[0], state=tk.NORMAL)  
        self.canvas.itemconfigure(self.lines[1], state=tk.NORMAL)  
  
    def autodraw(self, command=lambda *args: None):  
        #Setup automatic drawing; supports command option 
        self.reset()  
        self._command = command  
        self.canvas.bind("<Button-1>", self.begin)  
        self.canvas.bind("<B1-Motion>", self.update)  
        self.canvas.bind("<ButtonRelease-1>", self.quit)  
  
    def quit(self, event):  
        self.hide()  # Hide cross-hairs.  
        self.reset()  
  
  
class SelectionObject:  
    """ Widget to display a rectangular area on given canvas defined by two points 
        representing its diagonal. 
    """  
      
    def __init__(self, canvas, select_opts):  
          
        # Create a selection objects for updating.  
        self.canvas = canvas  
        self.select_opts1 = select_opts  
        self.width = self.canvas.cget('width')  
        self.height = self.canvas.cget('height')  
  
        # Options for areas outside rectanglar selection.  
        select_opts1 = self.select_opts1.copy()  
        select_opts1.update({'state': tk.HIDDEN})  # Hide initially (red backgound)  
        # Separate options for area inside rectanglar selection.  
        select_opts2 = dict(dash=(2, 2), fill='', outline='white', state=tk.HIDDEN)  
  
        # Initial extrema of inner and outer rectangles.  
        imin_x, imin_y,  imax_x, imax_y = 0, 0,  1, 1  
        omin_x, omin_y,  omax_x, omax_y = 0, 0,  self.width, self.height  
  
        self.rects = (  
            # Area *outside* selection (inner) rectangle.  
            self.canvas.create_rectangle(omin_x, omin_y,  omax_x, imin_y, **select_opts1),  
            self.canvas.create_rectangle(omin_x, imin_y,  imin_x, imax_y, **select_opts1),  
            self.canvas.create_rectangle(imax_x, imin_y,  omax_x, imax_y, **select_opts1),  
            self.canvas.create_rectangle(omin_x, imax_y,  omax_x, omax_y, **select_opts1),  
            # Inner rectangle.  
            self.canvas.create_rectangle(imin_x, imin_y,  imax_x, imax_y, **select_opts2)  
        )  
  
    def update(self, start, end):  
          
        global imin_x, imin_y,  imax_x, imax_y  
          
        # Current extrema of inner and outer rectangles.  
        imin_x, imin_y,  imax_x, imax_y = self._get_coords(start, end)  
        omin_x, omin_y,  omax_x, omax_y = 0, 0,  self.width, self.height  
  
        # Update coords of all rectangles based on these extrema.  
        self.canvas.coords(self.rects[0], omin_x, omin_y,  omax_x, imin_y),  
        self.canvas.coords(self.rects[1], omin_x, imin_y,  imin_x, imax_y),  
        self.canvas.coords(self.rects[2], imax_x, imin_y,  omax_x, imax_y),  
        self.canvas.coords(self.rects[3], omin_x, imax_y,  omax_x, omax_y),  
        self.canvas.coords(self.rects[4], imin_x, imin_y,  imax_x, imax_y),  
  
        for rect in self.rects:  # Make sure all are now visible.  
            self.canvas.itemconfigure(rect, state=tk.NORMAL)  
              
      
    def _get_coords(self, start, end):  
        """ Determine coords of a polygon defined by the start and 
            end points one of the diagonals of a rectangular area. 
        """  
        return (min((start[0], end[0])), min((start[1], end[1])),  
                max((start[0], end[0])), max((start[1], end[1])))  
  
    def hide(self):  
        for rect in self.rects:  
            self.canvas.itemconfigure(rect, state=tk.HIDDEN)  
          
  
class myGUI(tk.Tk):  
  
    def __init__(self, *args, **kwargs):  
          
        tk.Tk.__init__(self, *args, **kwargs)  
        container = tk.Frame(self)  
          
        container.pack(side="top", fill="both", expand = True)  
        container.grid_rowconfigure(0, weight=1)  
        container.grid_columnconfigure(0, weight=1)  
        self.title("     VIKI Camera Focus     ")  # set window title  
        self.frames = {}  
      
        F = StartPage  
        ##  
        frame = F(container, self)  
        self.frames[F] = frame  
  
        frame.grid(row=0, column=0, sticky="nsew")  
        img = Image.open("realtra_logo.jpg")  
        img2 = img.resize((int(699/1.8), int(176/1.8)), Image.ANTIALIAS)  
        self.img3=ImageTk.PhotoImage(img2)  
        imglabel = tk.Label(self, image=self.img3)  
        imglabel.place(relx=0.2,rely=0.0, anchor='n')   
        ##  
        self.show_frame(StartPage)  
  
    def show_frame(self, cont):  
  
        frame = self.frames[cont]  
        frame.tkraise()  
          
          
class StartPage(tk.Frame):  
      
    # Default selection object options.  
    SELECT_OPTS = dict(dash=(2, 2), stipple='gray25', fill='red',  
                          outline='')  
  
    def __init__(self, parent, controller):  
        tk.Frame.__init__(self,parent)  
        label = tk.Label(self, text="Camera Focus Application", font=("Verdana", 30, 'bold'))  
        label.place(relx=0.5,rely=0.2, anchor='center')  
          
        self.option_label = Label(self, text="Select VCAM Number", font=("Verdana", 12, 'bold'))  
        self.option_label.place(relx=0.5, rely=0.45, anchor='center')  
        OPTIONS = ['1', '2', '3', '4', '5', '6']  
        self.option = tk.StringVar(self)  
        self.option.set(OPTIONS[0]) # default value  
        self.drpdwn = tk.OptionMenu(self, self.option, *OPTIONS)  
        self.drpdwn.place(relx=0.5, rely=0.48, anchor='n')  
          
        self.button0 = ttk.Button(self, text="VCAM Selected", command=self.Begin)  
        self.button0.place(relx=0.5,rely=0.53, anchor='center')  
          
      
    def Begin(self):  
        global udp  
          
        self.option_label.destroy()  
        self.button0.destroy()  
        self.drpdwn.destroy()  
        udp = 'udp://@239.100.1.1:810{}'.format(str(int(self.option.get())-1)) #What VCAM UDP stream to observe  
          
        self.button1 = ttk.Button(self, text="Take Picture", command=self.TakePicture)  
        self.button1.place(relx=0.5,rely=0.45, anchor='center')  
          
      
    def TryCrop(self):  
          
        try:  
            self.CropImage()  
        except:  
            self.label2 = tk.Label(self, text="**No area selected for cropping**", font=("Verdana", 12, 'bold'), bg='red')  
            self.label2.place(relx=0.5,rely=0.8, anchor='center')  
            self.SelectPicture()  
      
      
    def TakePicture(self):  
        global imgtk, udp  
          
        try: #Incase this function is called in from 'TakePicture'  
            self.label3.destroy()  
            self.button3.destroy()  
            self.canvas.destroy()  
            self.button2.destroy()  
        except:  
            pass  
          
        self.vs = cv2.VideoCapture(udp)  
          
        ok, frame = self.vs.read()  
        frame = cv2.resize(frame, (int(1920/2.3), int(1080/2.3)))  
        self.cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)  # convert colors from BGR to RGBA  
        current_image = Image.fromarray(self.cv2image)  # convert image for PIL  
        imgtk = ImageTk.PhotoImage(image=current_image)  # convert image for tkinter  
        self.vs.release() #Close camera stream  
          
        self.SelectPicture()  
          
      
    def SelectPicture(self):  
          
        self.label3 = tk.Label(self, text="Drag mouse over area to crop for focusing.", font=("Verdana", 10, 'bold'))  
        self.label3.place(relx=0.5,rely=0.27, anchor='center')  
          
        self.button1.destroy()  
        self.button2 = ttk.Button(self, text="Crop Image", command=self.TryCrop)  
        self.button2.place(relx=0.5,rely=0.9, anchor='center')  
        self.button3 = ttk.Button(self, text="Retake Picture (if picture is bad)", command=self.TakePicture)  
        self.button3.place(relx=0.5,rely=0.95, anchor='center')  
          
        ''' Cropping Code
        Sections taken from:
        https://stackoverflow.com/questions/55636313/selecting-an-area-of-an-image-with-a-mouse-and-recording-the-dimensions-of-the-s
        '''
          
        self.canvas = tk.Canvas(app, width=imgtk.width(), height=imgtk.height(),  
                                borderwidth=0, highlightthickness=0)  
        self.canvas.place(relx=0.5,rely=0.3,anchor='n')   
        self.myCan = self.canvas.create_image(0, 0, image=imgtk, anchor=tk.NW)  
        self.canvas.imgtk = imgtk  # Keep reference.  
  
        # Create selection object to show current selection boundaries.  
        self.selection_obj = SelectionObject(self.canvas, self.SELECT_OPTS)  
          
        # Callback function to update it given two points of its diagonal.  
        def on_drag(start, end, **kwarg):  # Must accept these arguments.  
            self.selection_obj.update(start, end)  
  
        # Create mouse position tracker that uses the function.  
        self.posn_tracker = MousePositionTracker(self.canvas)  
        self.posn_tracker.autodraw(command=on_drag)  # Enable callbacks.  
      
      
    def ReCrop(self):  
        self.button4.destroy()  
        self.button5.destroy()  
        self.canvas.destroy()  
        self.SelectPicture()  
          
      
    def CropImage(self):  
        global imin_x, imin_y, imax_x, imax_y, new_width, new_height  
          
        higher = False  
        wider = False  
          
        try:  
            self.label2.destroy() #This may give error if not present  
        except:  
            pass  
          
        self.label3.destroy()  
        self.canvas.destroy()  
        self.button2.destroy()  
        self.button3.destroy()  
                  
        if (imax_x-imin_x)/834 < (imax_y-imin_y)/469: #Ratio of x and y domesions to initial dimensions  
            higher = True  
        else:  
            wider = True  
          
        width = int(1920/2.3)  
        height = int(1080/2.3)  
          
        if higher == True:  
            new_width = int((height/(imax_y-imin_y))*(imax_x-imin_x))  
            new_height = height  
        elif wider == True:  
            new_width = width  
            new_height =int((width/(imax_x-imin_x))*(imax_y-imin_y))  
          
        cropped = self.cv2image[imin_y:imax_y, imin_x:imax_x]  
        resized = cv2.resize(cropped, (new_width, new_height))  
        current_image = Image.fromarray(resized)  
        imgtk2 = ImageTk.PhotoImage(image=current_image)  # convert image for tkinter  
          
        self.canvas = tk.Canvas(app, width=imgtk2.width(), height=imgtk2.height(),  
                                borderwidth=0, highlightthickness=0)  
        self.canvas.place(relx=0.5,rely=0.3,anchor='n')   
        self.canvas.create_image(0, 0, image=imgtk2, anchor=tk.NW)  
        self.canvas.imgtk = imgtk2  # Keep reference.  
          
        self.button4 = ttk.Button(self, text="Begin Focusing", command=self.Setup)  
        self.button4.place(relx=0.5,rely=0.9, anchor='center')  
        self.button5 = ttk.Button(self, text="Re-Crop", command=self.ReCrop)  
        self.button5.place(relx=0.5,rely=0.93, anchor='center')  
          
        if (imax_x-imin_x)/834 < (imax_y-imin_y)/469: #Ratio of x and y domesions to initial dimensions  
            higher = True  
        else:  
            wider = True  
  
  
    def importML_model(self):  
        with open('focus_model.pkl', 'rb') as f:  
            self.clf2 = pickle.load(f)  
          
          
    def Setup(self):  
          
        self.canvas.destroy()  
        self.button4.destroy()  
        try:  
            self.button5.destroy()  
        except:  
            pass  
          
        self.guess = tk.Label(self, text='', font=('Verdana',14))  
        self.guess.place(relx=0.5, rely=0.85, anchor='n')  
        self.howsure = tk.Label(self, text='', font=('Verdana',14))  
        self.howsure.place(relx=0.5, rely=0.88, anchor='n')  
          
        self.progressbar = ttk.Progressbar(self,orient=HORIZONTAL,length=300,mode='determinate')  
        self.progressbar.place(relx=0.5, rely=0.91, anchor='n')  
          
        self.importML_model()  
        self.ShowVideo()          
          
          
    def ShowVideo(self):  
          
        global imin_x, imin_y, imax_x, imax_y, new_width, new_height, udp  
  
        self.vs = cv2.VideoCapture(udp) #cv2.VideoCapture(0) # capture video frames, 0 is your default video camera  
        self.vs.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  
        self.vs.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  
        self.output_path = "./"  # store output path  
        self.current_image = None  # current image from the camera  
        defaultbg = self.cget('bg') # set default grey color to use in labels background  
  
        self.panel = tk.Label(self)  # initialize image panel  
        self.panel.place(relx=0.5,rely=0.3,anchor='n')     
  
        ok, frame = self.vs.read()  
        width = int(1920/2.3)  
        height = int(1080/2.3)  
        frame = cv2.resize(frame, (width, height))  
        cropped = frame[imin_y:imax_y, imin_x:imax_x]  
        resized = cv2.resize(cropped, (new_width, new_height))  
        cv2image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGBA)  # convert colors from BGR to RGBA  
        self.current_image = Image.fromarray(cv2image)  # convert image for PIL  
        imgtk = ImageTk.PhotoImage(image=self.current_image)  # convert image for tkinter  
        self.panel.imgtk = imgtk  # anchor imgtk so it does not be deleted by garbage-collector  
        self.panel.config(image=imgtk)  # show the image  
          
        img = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)  
        edge_laplace = laplace(img, ksize=3)  
  
        self.variance = variance(edge_laplace)  
        self.maximum = np.amax(edge_laplace)  
  
        prediction = self.clf2.predict([[self.variance, self.maximum]])  
        sure_percent = self.clf2.predict_proba([[self.variance, self.maximum]])  
        self.howsure['text'] = round(sure_percent[0][1],2)  
        self.progressbar['value'] = 100*sure_percent[0][1]  
          
        if prediction == 1:  
                     self.guess['text'] = 'Image Status: Focused'  
                     self.guess['fg'] = 'green'  
        elif prediction == 0:  
                     self.guess['text'] = 'Image Status: Blurry'  
                     self.guess['fg'] = 'black'  
          
        self.vs.release()  
        self.after(30, self.ShowVideo)   
          
  
def exit_handler():  
    global x  
      
    x = False  
  
  
if __name__ == "__main__":  
      
    thread = None          
    switch = False  
  
    app = myGUI()  
    app.geometry('1000x1000+0+0')  
    app.mainloop()  
    atexit.register(exit_handler())  
