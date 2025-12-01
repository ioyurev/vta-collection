import json
from pathlib import Path
from typing import Type, TypeVar

from vta_collection.file_manager import FileManager

T = TypeVar("T", bound="SerializableMixin")


class SerializableMixin:
    def to_dict(self) -> dict:
        """Преобразовать объект в словарь"""
        return self.model_dump()  # type: ignore

    def to_json_file(self, file_path: Path) -> None:
        """Сохранить объект в JSON файл"""
        FileManager.save_json(self.to_dict(), file_path)

    def to_file(self, f) -> None:
        """Сохранить объект в файл (совместимость с TextIOWrapper)"""
        content = self.to_dict()
        json.dump(content, f)

    @classmethod
    def from_file(cls: Type[T], f) -> T:
        """Загрузить объект из файла (совместимость с TextIOWrapper)"""
        data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls: Type[T], data: dict) -> T:
        """Создать объект из словаря данных"""
        return cls.model_validate(data)  # type: ignore

    @classmethod
    def from_json_file(cls: Type[T], file_path: Path) -> T:
        """Загрузить объект из JSON файла"""
        data = FileManager.load_json(file_path)
        return cls.from_dict(data)
