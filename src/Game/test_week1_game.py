import sys
import os
import scipy.io as sio


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from time import sleep
from Stream.softwareStream import SoftwareStream
from Stream.composedStream import ComposedStream
from Stream.gameControlStream import GameControlStream, MatFileStream
from Stream.dataStream import DataStream, StreamType, QUEUE_LENGTH
from Classes.classifierClass import Classifier
from Classes.featureClass import FeatureClass, FeatureType
from week1_game import InfiniteRunner, App
import numpy as np

# === STEP 1: Load mat file EEG stream ===
print("Starting EEG simulation from mat file...")
MAT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.mat')
eeg_stream = MatFileStream(mat_path=MAT_PATH)
eeg_stream.start()
sleep(1)

# === STEP 2: Set up and TRAIN classifier on mat file data ===
print("Setting up and training classifier...")

# Load mat data
mat = sio.loadmat(MAT_PATH)

# Create alpha power feature
alpha_power = FeatureClass(FeatureType.ALPHA)

# Create classifier with the mat data already loaded in
classifier = Classifier(
    features=[alpha_power],
    label0_datasets={'eyesClosed': mat['eyesClosed']},  # shape (10, 250)
    label1_datasets={'eyesOpen': mat['eyesOpen']}        # shape (10, 250)
)

# Train for real
classifier.train_model()
print("Classifier trained!")
print(f"  - Features: {[str(f) for f in classifier.features]}")

# === STEP 3: Create composed stream ===
print("\nCreating classification stream...")
classification_stream = ComposedStream(
    reference_stream=eeg_stream,
    transformations=[classifier],
    stream_name="Brain_State_Classifier",
    stream_type=StreamType.FILTER,
    #window_size=50
)
classification_stream.start()
sleep(3)
print(f"[DEBUG] eeg_stream queue size: {len(eeg_stream.data)}")
print(f"[DEBUG] classification_stream queue size: {len(classification_stream.data)}")

# DEBUG: Check composed stream data
print("\n=== DEBUG: Composed Stream (Classifier Output) ===")
composed_data = list(classification_stream.data)
print(f"Total samples in composed stream: {len(composed_data)}")
print(f"First 5 samples from composed stream:")
for i, sample in enumerate(composed_data[:5]):
    print(f"  Sample {i}: {sample}")
print()

# === STEP 4: Start the game ===
print("Starting game...")
game = InfiniteRunner(size=(800, 600), fps=60)
game.start()

# === STEP 5: Connect brain control ===
print("Connecting brain control...")
brain_controller = GameControlStream(
    reference_stream=classification_stream,
    game=game,
    active_label='eyesOpen',
    stream_name="Brain_Game_Controller"
)
brain_controller.start()

# Collect all streams so they can be shut down
all_streams = [eeg_stream, classification_stream, brain_controller]

# === STEP 6: Start GUI ===
print("Launching game window...")
print("\n=== BRAIN-CONTROLLED GAME ACTIVE ===")
print("Watch for [ALPHA DEBUG] messages to see alpha power values!")
try:
    app = App(game, width=850, height=700)
finally:
    print("\nShutting down...")
    for stream in all_streams:
        stream.stop()
    game.stop()
    print("All streams stopped.")