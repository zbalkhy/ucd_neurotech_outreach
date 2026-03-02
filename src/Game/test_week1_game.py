import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from time import sleep
from Stream.softwareStream import SoftwareStream
from Stream.composedStreamedited import ComposedStream
from Stream.gameControlStream import GameControlStream
from Stream.dataStream import StreamType
from Classes.classifierClass import Classifier
from Classes.featureClass import FeatureClass, FeatureType
from week1_game import InfiniteRunner, App
import numpy as np

# === STEP 1: Create synthetic EEG stream ===
print("Starting EEG simulation...")
eeg_stream = SoftwareStream(
    stream_name="EEG_Simulator",
    stream_type=StreamType.SOFTWARE
)
eeg_stream.start()
sleep(1)

# DEBUG: Check raw stream data
print("\n=== DEBUG: Raw EEG Stream ===")
raw_data = list(eeg_stream.data)
print(f"Total samples in raw stream: {len(raw_data)}")
print(f"First 5 samples from raw stream:")
for i, sample in enumerate(raw_data[:5]):
    print(f"  Sample {i}: {sample}")
print()

# === STEP 2: Set up classifier ===
print("Setting up classifier...")

# Create alpha power feature
alpha_power = FeatureClass(FeatureType.ALPHA)

# Create classifier
classifier = Classifier(
    features=[alpha_power]
)

# Bypass model check
class DummyModel:
    pass
classifier.model = DummyModel()

# Override the threshold WITH DEBUG OUTPUT
prediction_count = [0]  # Use list to modify in inner function

def new_predict_sample(sample):
    features = np.array(classifier.generate_features(sample)).reshape(1, -1)
    alpha_power_val = features[0][0]
    threshold = 70000.0  # Adjust based on output
    prediction = (alpha_power_val < threshold)
    
    # Print every 5 predictions to see alpha power values
    if prediction_count[0] % 5 == 0:
        print(f"[ALPHA DEBUG] Power: {alpha_power_val:.2f} | Threshold: {threshold} | Result: {'eyesOpen' if prediction else 'eyesClosed'}")
    prediction_count[0] += 1
    
    return int(prediction)

classifier.predict_sample = new_predict_sample

print(f"Classifier configured with:")
print(f"  - Features: {[str(f) for f in classifier.features]}")

# === STEP 3: Create composed stream ===
print("\nCreating classification stream...")
classification_stream = ComposedStream(
    reference_stream=eeg_stream,
    transformations=[classifier],
    stream_name="Brain_State_Classifier",
    stream_type=StreamType.FILTER,
    window_size=50
)
classification_stream.start()
sleep(2)

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
sleep(0.5)

# === STEP 5: Connect brain control ===
print("Connecting brain control...")
brain_controller = GameControlStream(
    reference_stream=classification_stream,
    game=game,
    active_label='eyesOpen',
    stream_name="Brain_Game_Controller"
)
brain_controller.start()

# === STEP 6: Start GUI ===
print("Launching game window...")
print("\n=== BRAIN-CONTROLLED GAME ACTIVE ===")
print("Watch for [ALPHA DEBUG] messages to see alpha power values!")
app = App(game, width=850, height=700)