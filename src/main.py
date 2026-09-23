import tkinter as tk
from tkinter import ttk

from scipy.io import loadmat

from Classes.editorClass import EditorClass
from Classes.eventClass import EventClass
from Classes.featureClass import FeatureClass, FeatureType
from common import ALPHA, MODAL_WIDGET_TITLE, create_grid, resource_path
from Game.week1_game import App, InfiniteRunner
from Models.saveModel import SaveModel
from Models.userModel import UserModel
from Stream.composedStream import ComposedStream
from Stream.dataStream import StreamType
from Stream.softwareStream import SoftwareStream
from View.classifierView import ClassifierView
from View.dataCollectionView import dataCollectionView
from View.featureView import FeatureView
from View.filterView import filterView
from View.inventoryView import InventoryView
from View.modalView import TextEntryModalView
from View.plotterView import create_plotter
from ViewModel.classifierViewModel import ClassifierViewModel
from ViewModel.dataCollectionViewModel import dataCollectionViewModel
from ViewModel.featureViewModel import FeatureViewModel
from ViewModel.filterViewModel import filterViewModel
from ViewModel.inventoryViewModel import InventoryViewModel


# 0 = Default
# 1 = Plotter UI for Session 1
# 2 = Plotter UI for Session 2
DEFAULT_SESSION_ID = 0
SESSION_OPTIONS = [
    ("Default", 0),
    ("Session 1", 1),
    ("Session 2", 2),
    ("Session 3", 3),
    ("Session 4", 4),
]

top_grid_names = [["Inventory", "Visualizer"]]
bottom_grid_names = [["Data Collector", "Filter Maker", "Classifier"]]


def open_feature_viewer(root, view_model):
    t = tk.Toplevel(root)
    t.wm_title("Feature Viewer")
    FeatureView(t, view_model)


def open_function_editor(root, user_model):
    t = tk.Toplevel(root)
    t.wm_title("Function Editor")
    editor = EditorClass(t)
    editor.add_observer(user_model)


def open_text_entry_modal(root):
    """Open the app's reusable text-entry modal."""
    TextEntryModalView(
        root,
        title=MODAL_WIDGET_TITLE,
        on_submit=lambda first, second: print(
            f"Modal entry submitted: {first}, {second}"))


def open_game(root, user_model):
    t = tk.Toplevel(root)
    t.wm_title("EEG RUNNNER")
    game = InfiniteRunner(
        size=(800, 600),
        fps=80,
        parent=t,
        user_model=user_model)
    game.start()
    game_ui = App(game, width=800, height=700, parent_window=t)
    t.protocol("WM_DELETE_WINDOW", game_ui.on_close)


def initialize_user_model(save_model, session_id):
    user_model = save_model.load() if save_model.save_exists() else UserModel()
    user_model.add_observer(save_model)

    data_stream = SoftwareStream("eeg stream", StreamType.SOFTWARE, 250)
    user_model.add_stream(data_stream)

    for feature_type in FeatureType:
        if feature_type != FeatureType.CUSTOM:
            user_model.add_feature(FeatureClass(feature_type))

    apply_startup_session_defaults(user_model, session_id)
    return user_model


def apply_startup_session_defaults(user_model, session_id):
    # temp load gold standard data.mat
    if session_id >= 2:
        data = loadmat(resource_path("data.mat"))
        for key in data.keys():
            if key in ["eyesOpen", "eyesClosed"]:
                user_model.add_dataset(key, data[key])

    # make alpha filter stream
    if session_id <= 2:
        user_model.add_filter("alpha", "bandpass", 4, ALPHA)
        filter_obj = user_model.get_filter("alpha")
        filtered_stream = ComposedStream(
            user_model.get_stream("eeg stream"),
            [filter_obj],
            "alpha eeg stream",
            StreamType.FILTER,
            250)
        user_model.add_stream(filtered_stream)


def build_main_content(root, user_model, session_id):
    content_frame = tk.Frame(root)
    content_frame.pack(side="top", fill="both", expand=True)

    # create paned window for each row, this allows them to be adjustable
    inner_paned_window = ttk.PanedWindow(content_frame, orient="vertical")
    inner_paned_window.pack(side="top", fill="both", expand=True)

    # create top and bottom panes
    top_pane = tk.Frame(inner_paned_window, borderwidth=2, relief="solid")
    bottom_pane = tk.Frame(inner_paned_window, borderwidth=2, relief="solid")
    inner_paned_window.add(top_pane)
    inner_paned_window.add(bottom_pane)

    # create a grid in each pane to hold our widgets
    top_grid_frames = create_grid(top_pane, 1, 2, top_grid_names)
    bottom_grid_frames = create_grid(bottom_pane, 1, 3, bottom_grid_names)

    data_collection_view_model = dataCollectionViewModel(user_model)
    data_collection_module = dataCollectionView(
        bottom_grid_frames[0][0],
        data_collection_view_model,
        session_id=session_id)

    filter_view_model = filterViewModel(user_model)
    filter_module = filterView(
        bottom_grid_frames[0][1],
        filter_view_model,
        session_id=session_id)

    classifier_view_model = ClassifierViewModel(user_model)
    classifier_view = ClassifierView(
        bottom_grid_frames[0][2],
        classifier_view_model,
        session_id=session_id)

    inventory_view_model = InventoryViewModel(user_model)
    inventory_view = InventoryView(top_grid_frames[0][0], inventory_view_model)

    plotter_view_model, plotter_view = create_plotter(
        top_grid_frames[0][1],
        user_model,
        session_id=session_id)

    feature_view_model = FeatureViewModel(user_model)

    return {
        "content_frame": content_frame,
        "data_collection_module": data_collection_module,
        "filter_module": filter_module,
        "classifier_view": classifier_view,
        "inventory_view": inventory_view,
        "plotter_view_model": plotter_view_model,
        "plotter_view": plotter_view,
        "feature_view_model": feature_view_model,
    }


def dispose_event_object(obj):
    if isinstance(obj, EventClass):
        obj.dispose()


def teardown_main_content(context):
    plotter_view = context.get("plotter_view")
    if plotter_view is not None:
        plotter_view.stop()

    for key in [
            "data_collection_module",
            "filter_module",
            "classifier_view",
            "inventory_view",
            "plotter_view",
            "plotter_view_model"]:
        dispose_event_object(context.get(key))

    content_frame = context.get("content_frame")
    if content_frame is not None:
        content_frame.destroy()

    context.clear()


def create_menu(root, user_model, context, current_session, reload_session):
    menubar = tk.Menu(root)

    session_menu = tk.Menu(menubar, tearoff=0)
    session_var = tk.IntVar(value=current_session["id"])
    for label, session_id in SESSION_OPTIONS:
        session_menu.add_radiobutton(
            label=label,
            variable=session_var,
            value=session_id,
            command=lambda value=session_id: reload_session(value))
    menubar.add_cascade(label="Session", menu=session_menu)

    actions = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Actions", menu=actions)
    actions.add_command(
        label="Open Feature Viewer",
        command=lambda: open_feature_viewer(
            root,
            context["feature_view_model"]))
    actions.add_command(
        label="Open Code Editor",
        command=lambda: open_function_editor(root, user_model))
    actions.add_command(
        label="Play EEG RUNNER",
        command=lambda: open_game(root, user_model))
    actions.add_command(
        label="Connect EEG Device",
        command=lambda: open_text_entry_modal(root))

    root.config(menu=menubar)
    return session_var


def shutdown_app(root, user_model, save_model, context):
    teardown_main_content(context)

    # send shutdown event to each stream thread
    for data_stream in user_model.get_streams():
        data_stream.shutdown_event.set()

    # wait for each thread to exit before shutdown
    for data_stream in user_model.get_streams():
        if data_stream.is_alive():
            data_stream.join()

    save_model.dump(user_model)
    print("Saved User")
    root.destroy()


def create_root():
    root = tk.Tk()
    root.wm_title("main window")
    try:
        root.state("zoomed")  # make the window take up the whole screen
    except tk.TclError:
        # probably on a linux system
        print(Exception)
    return root


if __name__ == "__main__":
    print("main app starting")

    save_model = SaveModel()
    current_session = {"id": DEFAULT_SESSION_ID}
    user_model = initialize_user_model(save_model, current_session["id"])

    root = create_root()
    current_context = build_main_content(
        root,
        user_model,
        current_session["id"])

    def reload_session(new_session_id):
        if new_session_id == current_session["id"]:
            return

        current_session["id"] = new_session_id
        teardown_main_content(current_context)
        current_context.update(
            build_main_content(
                root,
                user_model,
                current_session["id"]))
        session_var.set(current_session["id"])

    session_var = create_menu(
        root,
        user_model,
        current_context,
        current_session,
        reload_session)

    root.protocol(
        "WM_DELETE_WINDOW",
        lambda: shutdown_app(root, user_model, save_model, current_context))

    # Show the modal once when this application session first starts.
    root.after(0, lambda: open_text_entry_modal(root))

    # clicking (x) on main window prevents program from quiting while commands are queued.
    # we'll need a quit event to propagate through the program to kill any
    # future queued commands.
    root.mainloop()
