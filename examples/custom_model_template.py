"""Copy this file into user_models/ and implement predict.

Register it from the AcoustiBench interface as:
    user_models.my_model:MyModel

This template is not a trained model and it is not registered automatically.
Importing a registered model runs local Python. Register only code you trust.
"""

from __future__ import annotations

from acousticbench.models.base import AcousticModel, Prediction


class MyModel(AcousticModel):
    model_id = "my-model"
    name = "My acoustic classifier"
    task = "classification"
    description = "Replace this description with what the model predicts."

    def __init__(self, **params: object) -> None:
        self.params = params

    def predict(self, audio, sample_rate: int) -> Prediction:
        raise NotImplementedError(
            "Replace predict() with your model. Return Prediction(label=..., scores={...})."
        )
