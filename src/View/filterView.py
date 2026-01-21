import tkinter as tk
from tkinter import *
from ViewModel.filterViewModel import filterViewModel
from Classes.eventClass import *

class filterView(EventClass):
    def __init__(self, frame: tk.Frame, view_model: filterViewModel):
        super().__init__()

         # set class variables
        self.frame: tk.Frame = frame
        self.view_model = view_model
        self.filter_count = 0
        self.filter_boxes = {'filter': [], 'order': [], 'frequency': []}

        self.subscribe_to_subject(self.view_model.user_model)

        #new filter frame
        self.new_filter_frame = tk.Frame(frame, borderwidth=1, relief="solid")
        self.new_filter_frame.pack(side="top", fill="both", expand=True)
        
        #create dropdown
        self.create_dropdown()

        #create a filter add frame
        self.filter_mod_frame = tk.Frame(frame, borderwidth=1, relief="solid")
        self.filter_mod_frame.pack(side="top", fill="both", expand=True)

        #add filter button
        self.filter_add_button = tk.Button(self.filter_mod_frame, 
                                           text="Add Filter", 
                                           command=self.add_filter_box, 
                                           width=6, height=1, 
                                           bg='green')
        self.filter_add_button.pack(pady=10, padx=10, anchor="e", side = RIGHT)
        
        #clear filters button
        self.filter_remove_button = tk.Button(self.filter_mod_frame, 
                                              text="Clear Filters", 
                                              command=self.clear_filter_box, 
                                              width=6, height=1, bg='red')
        self.filter_remove_button.pack(pady=10, padx=10, anchor="e", side = RIGHT)

        #create filter stream button
        self.create_filter_stream_button = tk.Button(self.filter_mod_frame, 
                                                     text="Make Filter", 
                                                     command=self.create_filter_stream, 
                                                     width=6, height=1, bg='yellow')
        self.create_filter_stream_button.pack(pady=10, padx=10, anchor="e", side = LEFT)

        #create a filter naming label
        self.filter_name_label = tk.Label(self.filter_mod_frame, 
                                          text="Name:", 
                                          anchor='e')
        self.filter_name_label.pack(pady=10, padx=(10, 0), anchor="e", side=LEFT)
        
        #create filter naming entry
        self.filter_name_entry = tk.Entry(self.filter_mod_frame, width = 20)
        self.filter_name_entry.pack(pady=10, padx=2, anchor = "e", side = LEFT)
        
        #add a frame with all of the filters
        self.filter_list_frame = tk.Frame(frame, borderwidth=1, relief="solid")
        self.filter_list_frame.pack(side="top", fill="both", expand=True)
        
    def add_filter_box(self):
        #add onto filter count
        self.filter_count += 1
        self.update_filter_frame()
        
    def clear_filter_box(self):
        self.filter_count = 0
        self.filter_boxes = {'filter': [], 'order': [], 'frequency': []}
        self.update_filter_frame()
        
    def update_filter_frame(self):
        for child in self.filter_list_frame.winfo_children():
            child.destroy()
        self.filter_list_canvas = tk.Canvas(self.filter_list_frame)
        self.filter_list_scrollbar = tk.Scrollbar(self.filter_list_frame, 
                                                  orient="vertical", 
                                                  command=self.filter_list_canvas.yview)
        
        # create scrollable frame to hold filter list
        self.scrollable_frame = tk.Frame(self.filter_list_canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.filter_list_canvas.configure(
                scrollregion=self.filter_list_canvas.bbox("all")
            )
        )

        self.filter_list_canvas.create_window((0, 0), 
                                              window=self.scrollable_frame, 
                                              anchor="nw")
        self.filter_list_canvas.configure(yscrollcommand=self.filter_list_scrollbar.set)

        # pack canvas and scrollbar
        self.filter_list_canvas.pack(side="left", fill="both", expand=True)
        self.filter_list_scrollbar.pack(side="right", fill="y")

        #populate grid
        #need to do this in a way that saves previous information
        #note, I know I can do this more efficiently but it's like 2am and tkinter is kicking my butt -Andy

        #creates objects to interact with but holds actual value in a stringvar object to keep saved
        for i in range(self.filter_count):
            label1 = tk.Label(self.scrollable_frame, text='Filter Type:', anchor="w")
            label1.grid(row=i, column=0, padx=3, pady=5, sticky="w")
            filter_types = ['lowpass', 'highpass', 'bandpass', 'bandstop']
            filter_type = StringVar(self.scrollable_frame)
            filter_type.set(filter_types[0])
            self.filter_boxes['filter'].append(filter_type)
            entry1 = OptionMenu(self.scrollable_frame, self.filter_boxes['filter'][i], *filter_types)
            entry1.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            
            label2 = tk.Label(self.scrollable_frame, text='Order:', anchor="w")
            label2.grid(row=i, column=2, padx=3, pady=5, sticky="w")
            order = StringVar(self.scrollable_frame)
            self.filter_boxes['order'].append(order)
            entry2 = tk.Entry(self.scrollable_frame, width=2, textvariable = self.filter_boxes['order'][i])
            entry2.grid(row=i, column=3, padx=5, pady=5, sticky="w")
            
            label3 = tk.Label(self.scrollable_frame, text='Frequency:', anchor="w")
            label3.grid(row=i, column=4, padx=3, pady=5, sticky="w")
            frequency = StringVar(self.scrollable_frame)
            self.filter_boxes['frequency'].append(frequency)
            entry3 = tk.Entry(self.scrollable_frame, width=7, textvariable = self.filter_boxes['frequency'][i])
            entry3.grid(row=i, column=5, padx=5, pady=5, sticky="w")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
    def create_dropdown(self):
        #reference stream using dropdown
        for child in self.new_filter_frame.winfo_children():
            child.destroy()

        #add all of the stream names into a list
        streams = self.view_model.get_streams()
        self.stream_names = []
        for stream in streams:
            self.stream_names.append(stream.stream_name)

        #create dropdown
        master = self.new_filter_frame
        self.reference_stream = StringVar(master)
        self.reference_stream.set(self.stream_names[0])
        self.dropdown = OptionMenu(master, self.reference_stream, *self.stream_names)
        self.dropdown.pack(anchor='ne', side = RIGHT, padx=10)
        
        #put label and dropdown next to each other
        dropdown_label = tk.Label(master, text="Reference Stream")
        dropdown_label.pack(anchor='n', side = LEFT, padx = 10, pady = 5)

               
    def on_notify(self, eventData: any, event: EventType ) -> None:
        if event == EventType.STREAMUPDATE:
            self.create_dropdown()
        return

    def create_filter_stream(self):
        #creates the filtered stream
        for i in range(self.filter_count):
            #processes saved values
            filter_hold = self.filter_boxes['filter'][i].get()
            order_hold = float(self.filter_boxes['order'][i].get())
            frequency_hold = self.filter_boxes['frequency'][i].get()
            frequency_hold = frequency_hold.split(',')
            frequency_hold_float = [float(item) for item in frequency_hold]
            self.view_model.add_filter(self.filter_name_entry.get(), filter_hold.lower(), order_hold, frequency_hold_float)
        
        self.view_model.create_filter_stream(self.filter_name_entry.get(), self.reference_stream.get())
        self.filter_name_entry.delete(0, tk.END)
        self.clear_filter_box()

            
            