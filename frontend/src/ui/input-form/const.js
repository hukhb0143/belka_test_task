export const tableColumns = [
    { title: 'Наименование сырья', type: 'text', width: 200 },
    { title: 'Содержание железа (%)', type: 'numeric', width: 150, decimal: ',' },
    { title: 'Содержание кремния (%)', type: 'numeric', width: 150, decimal: ',' },
    { title: 'Содержание алюминия (%)', type: 'numeric', width: 150, decimal: ',' },
    { title: 'Содержание кальция (%)', type: 'numeric', width: 150, decimal: ',' },
    { title: 'Содержание серы (%)', type: 'numeric', width: 150, decimal: ',' },
  ] 

export const statColumns = [
    'Показатель', 
    'Среднее значение',
    'Минимальное значение',
    'Максимальное значение',
    'Количество записей',
]

export const statRows = [
    'Содержание железа (%)',
    'Содержание кремния (%)',
    'Содержание алюминия (%)',
    'Содержание кальция (%)',
    'Содержание серы (%)',
]