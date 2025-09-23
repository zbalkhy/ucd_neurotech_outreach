from userModel import UserModel
from classifier import Classifier
from composedStream import ComposedStream 
from dataStream import StreamType
from xrpControlStream import XRPControlStream

class ClassifierViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    def train_classifier(self, name: str) -> None:
        classifier = self.user_model.get_classifier(name)
        classifier.train_model()
        self.user_model.add_classifier(name, classifier)
        self.start_classifier_stream(name)

    def start_classifier_stream(self, name: str) -> None:
        # this will need a major refactor, this is hacky, dont use this
        openbci = self.user_model.get_stream('openbci')
        classifier = self.user_model.get_classifier(name)
        classifier_stream = ComposedStream(openbci, [classifier], name+"_stream", StreamType.CONTROL, 1)
        self.user_model.add_stream(classifier_stream)

        xrp_stream = XRPControlStream(classifier_stream, "/dev/tty.usbmodem1301", 9600, 1, "xrp", StreamType.DEVICE, 100)
        self.user_model.add_stream(xrp_stream)

    def create_classifier(
        self,
        name: str,
        datasets0: list[str],
        datasets1: list[str],
        features: list[str],
        filters: list[str]
    ) -> None:
        # get datasets, features, and filters from user model
        label0_datasets = {ds: self.user_model.get_dataset(ds) for ds in datasets0}
        label1_datasets = {ds: self.user_model.get_dataset(ds) for ds in datasets1}
        feature_objs = [self.user_model.get_features()[feat] for feat in features]
        filter_objs = [self.user_model.filters[f] for f in filters]

        # build and store classifier
        classifier = Classifier(
            label0_datasets=label0_datasets,
            label1_datasets=label1_datasets,
            features=feature_objs,
            filters=filter_objs,
        )

        self.user_model.add_classifier(name, classifier)