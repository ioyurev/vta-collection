from pydantic import BaseModel


class Standard(BaseModel):
    """Стандарт калибровки - точка с именем и температурами"""

    name: str  # Имя стандарта
    t_theor: float  # Теоретическая температура
    t_exp: float  # Экспериментальная температура
