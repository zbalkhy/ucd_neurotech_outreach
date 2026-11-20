from Models.userModel import UserModel
from Classes.classifierClass import Classifier, DEFAULT_MODEL
from Stream.composedStream import ComposedStream
from Stream.dataStream import StreamType
from Stream.xrpControlStream import XRPControlStream


class ClassifierViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    def create_classifier(
        self,
        name: str,
        datasets0: list[str],
        datasets1: list[str],
        features: list[str],
        filters: list[str],
        model_name: str = DEFAULT_MODEL,
        source_stream: str | None = None
    ) -> None:
        # get datasets, features, and filters from user model
        label0_datasets = {
            ds: self.user_model.get_dataset(ds) for ds in datasets0}
        label1_datasets = {
            ds: self.user_model.get_dataset(ds) for ds in datasets1}
        feature_objs = [self.user_model.get_features()[feat]
                        for feat in features]
        filter_objs = [self.user_model.filters[f] for f in filters]

        # build and store classifier
        classifier = Classifier(
            label0_datasets=label0_datasets,
            label1_datasets=label1_datasets,
            features=feature_objs,
            filters=filter_objs,
            model_name=model_name,
            source_stream=source_stream,
        )

        self.user_model.add_classifier(name, classifier)

    def get_source_stream_names(self) -> list[str]:
        """Streams that carry signal data a classifier can read."""
        return [s.stream_name for s in self.user_model.get_streams()
                if s.stream_type in (StreamType.DEVICE, StreamType.FILTER,
                                     StreamType.SOFTWARE)
                and not isinstance(s, XRPControlStream)]

    def get_active_stream_name(self) -> str | None:
        """Stream the plotter is showing."""
        return self.user_model.active_stream_name
