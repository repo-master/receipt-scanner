from abc import ABC, abstractmethod


class ScannerPipeline(ABC):
    '''Base scanner Pipeline class'''
    @abstractmethod
    def __call__(self, image_data: bytes):
        pass
