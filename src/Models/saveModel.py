from Stream.dataStream import DataStream, StreamType
from Classes.eventClass import EventClass, EventType
from Classes.filterClass import FilterClass
from Classes.featureClass import FeatureClass
from Classes.classifierClass import Classifier
from Models.userModel import UserModel
from numpy import ndarray
import os
import threading
import json
import tkinter as tk
from tkinter import ttk

USER_SAVE_PATH = 'user_save.json'


class SaveModel(EventClass):
    def __init__(self):
        super().__init__()
        self.tk = None

    def on_notify(self, eventData: any, event: EventType) -> None:
        if isinstance(eventData, UserModel):
            match event:
                case EventType.STREAMUPDATE:
                    self.dump(eventData)
                case EventType.DATASETUPDATE:
                    self.dump(eventData)
                case EventType.FILTERUPDATE:
                    self.dump(eventData)
                case EventType.FEATUREUPDATE:
                    self.dump(eventData)
                case EventType.STREAMLISTUPDATE:
                    self.dump(eventData)
                case EventType.CLASSIFIERUPDATE:
                    self.dump(eventData)

    def dump(self, user_model: UserModel):
        try:
            data = user_model.to_dict()
            with open(USER_SAVE_PATH, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving model: {e}")

    def load(self):
        try:
            if not self.save_exists():
                return UserModel()

            with open(USER_SAVE_PATH, 'r') as f:
                data = json.load(f)
                return UserModel.from_dict(data)
        except Exception as e:
            print(f"Error loading model: {e}")
            return UserModel()

    def set_tk(self, tk):
        self.tk = tk

    def save_exists(self):
        return os.path.exists(USER_SAVE_PATH)
