import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import jspreadsheet from 'jspreadsheet-ce';
import 'jspreadsheet-ce/dist/jspreadsheet.css';
import './input-form.css';
import { backend_url } from '../../App';
import { tableColumns, statColumns } from './const'


const ConcentrateQualitySystem = () => {
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [data, setData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [mode, setMode] = useState('input'); 
  const spreadsheetRef = useRef(null);

  // Загрузка данных при изменении месяца/года или режима
  useEffect(() => {
    if (mode === 'input') {
      // fetchInputData();
    } else {
      fetchSummaryData();
    }
  }, [month, year, mode]);

  // Инициализация таблицы Jspreadsheet
  useEffect(() => {
     if (mode === 'input') {
      // Уничтожаем предыдущий экземпляр, если он есть
      if (spreadsheetRef.current) {
        spreadsheetRef.current = null;
      }
    }

    if (mode === 'input' && !spreadsheetRef.current) {
        if (document.getElementById('spreadsheet')) {
            const options = { worksheets: [{
              data: data.length > 0 ? data : [['', '', '', '', '', '']],
              columns: tableColumns,
              minDimensions: [6, 10],
              allowInsertColumn: false,
              allowDeleteColumn: false,
              tableOverflow: true,
              onchange: (instance, cell, x, y, value) => handleDataChange(instance),
              style: { margin: '20px 0' }
            }]};
      
            const instance = jspreadsheet(document.getElementById('spreadsheet'), options)[0];
            spreadsheetRef.current = instance;
          }
    }
  }, [mode, data]);

  const fetchInputData = async () => {
    try {
      const response = await axios.get(backend_url + '/api/concentrate-quality', {
        params: { month, year },
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}` 
        }
      });
      setData(response.data);
    } catch (error) {
      console.error('Error fetching input data:', error);
      setData([]);
    }
  };

  const fetchSummaryData = async () => {
    try {
      const response = await axios.get(backend_url + '/api/concentrate-quality/summary', {
        params: { month, year }
      });
      setSummary(response.data);
    } catch (error) {
      console.error('Error fetching summary data:', error);
      setSummary(null);
    }
  };

  const handleDataChange = (instance) => {
    const newData = instance.getJson();
    setData(newData);
  };

  const getTableData = () => {
    if (!spreadsheetRef.current) return { data: [] };
  
    // Получаем все данные из таблицы
    const spreadsheetData = spreadsheetRef.current.getData();

    // Преобразуем в нужный формат
    const transformedData = spreadsheetData
      .filter(row => row.some(item => String(item || '').trim() !== '')) // Игнорируем пустые строки
      .map(row => ({
        name: row[0] || '',
        iron: parseFloat(row[1]) || 0,
        silicon: parseFloat(row[2]) || 0,
        aluminum: parseFloat(row[3]) || 0,
        calcium: parseFloat(row[4]) || 0,
        sulfur: parseFloat(row[5]) || 0,
      }));
  
    return transformedData
  };

  const saveData = async () => {
    try {
      const structure = getTableData()
      await axios.post(backend_url + '/api/concentrate-quality',
        {
            "month": month,
            "year": year,
            data: structure
      });
      alert('Данные успешно сохранены');
    } catch (error) {
      console.error('Ошибка при сохранении данных:', error);
      alert('Ошибка при сохранении данных');
    }
  };

  const handleMonthChange = (e) => {
    setMonth(parseInt(e.target.value));
  };

  const handleYearChange = (e) => {
    setYear(parseInt(e.target.value));
  };

  const renderInputForm = () => (
    <div>
      <h2>Внесение данных</h2>
      <div id="spreadsheet"></div>
      <button onClick={saveData} className="btn btn-primary">
        Сохранить данные
      </button>
      <div className="mt-3">
        <small>Совет: Вы можете копировать/вставлять данные прямо из Excel</small>
      </div>
    </div>
  );

  const renderReport = () => (
    <div>
      <h2>Сводный отчет за {month}/{year}</h2>
      {summary ? (
        <table className="table table-bordered table-striped">
          <thead className="thead-dark">
            <tr>
              {statColumns.map(column => <th>{column}</th>)}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Содержание железа (%)</td>
              <td>{summary.iron.avg.toFixed(2)}</td>
              <td>{summary.iron.min.toFixed(2)}</td>
              <td>{summary.iron.max.toFixed(2)}</td>
              <td>{summary.count}</td>
            </tr>
            <tr>
              <td>Содержание кремния (%)</td>
              <td>{summary.silicon.avg.toFixed(2)}</td>
              <td>{summary.silicon.min.toFixed(2)}</td>
              <td>{summary.silicon.max.toFixed(2)}</td>
              <td>{summary.count}</td>
            </tr>
            <tr>
              <td>Содержание алюминия (%)</td>
              <td>{summary.aluminum.avg.toFixed(2)}</td>
              <td>{summary.aluminum.min.toFixed(2)}</td>
              <td>{summary.aluminum.max.toFixed(2)}</td>
              <td>{summary.count}</td>
            </tr>
            <tr>
              <td>Содержание кальция (%)</td>
              <td>{summary.calcium.avg.toFixed(2)}</td>
              <td>{summary.calcium.min.toFixed(2)}</td>
              <td>{summary.calcium.max.toFixed(2)}</td>
              <td>{summary.count}</td>
            </tr>
            <tr>
              <td>Содержание серы (%)</td>
              <td>{summary.sulfur.avg.toFixed(2)}</td>
              <td>{summary.sulfur.min.toFixed(2)}</td>
              <td>{summary.sulfur.max.toFixed(2)}</td>
              <td>{summary.count}</td>
            </tr>
          </tbody>
        </table>
      ) : (
        <p>Нет данных для отображения</p>
      )}
    </div>
  );

  return (
    <div className="container mt-4">
      <div className="row mb-4">
        <div className="col-md-4">
          <label className="form-label">Месяц:</label>
          <select className="form-select" id="month" value={month} onChange={handleMonthChange}>
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i + 1} value={i + 1}>
                {new Date(2000, i, 1).toLocaleString('ru', { month: 'long' })}
              </option>
            ))}
          </select>
        </div>
        <div className="col-md-4">
          <label className="form-label">Год:</label>
          <select className="form-select" id="year" value={year} onChange={handleYearChange}>
            {Array.from({ length: 10 }, (_, i) => (
              <option key={i} value={new Date().getFullYear() - 5 + i}>
                {new Date().getFullYear() - 5 + i}
              </option>
            ))}
          </select>
        </div>
        <div className="col-md-4 d-flex align-items-end top-padding-20">
          <div className="btn-group" role="group">
            <button
              className={`btn ${mode === 'input' ? 'btn-primary' : 'btn-outline-primary'}`}
              onClick={() => setMode('input')}
              style={{ marginRight: '20px' }}
            >
              Ввод данных
            </button>
            <button
              className={`btn ${mode === 'report' ? 'btn-primary' : 'btn-outline-primary'}`}
              onClick={() => setMode('report')}
            >
              Просмотр отчета
            </button>
          </div>
        </div>
      </div>

      {mode === 'input' ? renderInputForm() : renderReport()}
    </div>
  );
};

export default ConcentrateQualitySystem;