from typing import List, Dict


def calculate_stats(values: List[float]) -> Dict[str, float]:
    """
    Формирует набор данных для статистического отчета.

    :param values: Данные
    :return:
    """

    avg = sum(values) / len(values)
    return {
        'avg': round(avg, 2),
        'min': round(min(values), 2),
        'max': round(max(values), 2)
    }