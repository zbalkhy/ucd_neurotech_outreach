from __future__ import annotations #needed for class self reference in addObserver and removeObserver
from collections import deque
from enum import Enum

class EventType(Enum):
    DEVICELISTUPDATE = 1
    STREAMUPDATE = 2
    DATASETUPDATE = 3
    FILTERUPDATE = 4
    FEATUREUPDATE = 5


""" This class implements an event sending / receiving mechanism. 
    It is inteded to be used as a base class for other classes which need event functionality
"""
class EventClass(object):
    def __init__(self):
        self.observers = deque()
        self.subjects = deque()

    def __del__(self):
        for subject in self.subjects:
            subject.remove_observer(self)
    
    def add_observer(self, observer: EventClass) -> None:
        self.observers.append(observer)

    def remove_observer(self, observer: EventClass) -> None:
        self.observers.remove(observer)

    def subscribe_to_subject(self, subject: EventClass) -> None:
        self.subjects.append(subject)
        subject.add_observer(self)
    
    def unsubscribe_from_subject(self, subject: EventClass) -> None:
        self.subjects.remove(subject)
        subject.remove_observer(self)
    
    def on_notify(self, eventData: any, event: EventType ) -> None:
        # This function is meant to be implemented by the inheriting class.
        return
    
    def notify(self, eventData: any, event: EventType) -> None:
        for observer in self.observers:
            observer.on_notify(eventData, event)