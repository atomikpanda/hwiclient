from .dimmer import DimmerActions, DimmerDeviceType, DimmerDevice
class LightDimmerActions(DimmerActions):
    pass


class LightDimmerType(DimmerDeviceType):
    @classmethod
    def type_id(cls) -> str:
        return "DIMMER"

    @property
    def is_dimmable(self) -> bool:
        return True

    def actions(self, device: DimmerDevice) -> LightDimmerActions:
        return LightDimmerActions(device)
