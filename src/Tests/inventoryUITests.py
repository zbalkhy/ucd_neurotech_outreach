import tkinter as tk
import tkinter.ttk as ttk
from Models.userModel import UserModel
from src.ViewModel.inventoryViewModel import InventoryViewModel
from View.inventoryView import InventoryView 
from Stream.softwareStream import SoftwareStream
from scipy.io import loadmat

class App:
    def __init__(self):
        self.root = tk.Tk()

        # create user model
        self.user_model = UserModel()

        # create a software stream and add to user model
        software_stream = SoftwareStream("Software Stream 1", 250)
        self.user_model.add_stream(software_stream)

        software_stream2 = SoftwareStream("Software Stream 2", 250)
        self.user_model.add_stream(software_stream2)

        import os
        data_path = os.path.join(os.path.dirname(__file__), '../data.mat')
        data = loadmat(data_path)
        for key in data.keys():
            if key in ['eyesOpen', 'eyesClosed']:
                self.user_model.add_dataset(key, data[key])

        # create inventory view model
        self.inventory_view_model = InventoryViewModel(self.user_model)
        # create inventory view
        self.inventory_view = InventoryView(self.root, self.inventory_view_model)
        self.root.mainloop()

    

if __name__ == "__main__":
    app = App()