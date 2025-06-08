import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import './auth-form.css';
import { backend_url } from '../../App';

const AuthForm = ({ onLoginSuccess }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const url = isLogin ? '/token' : null;
      console.log(url)
      const response = await axios.post(backend_url + url, formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });

      if (isLogin) {
        const { access_token } = response.data;
        console.log(access_token)
        localStorage.setItem('token', access_token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        onLoginSuccess?.();

        // Перенаправление после успешного входа
        navigate('/input-form'); 
      } 
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        (isLogin ? `Ошибка входа - ${err}` : null)
      );
      console.error('Auth error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <h2>{isLogin ? 'Вход в систему' : 'Регистрация'}</h2>
      
      {error && <div className="auth-error">{error}</div>}

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="username">Имя пользователя:</label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
            minLength={3}
            maxLength={20}
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Пароль:</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            minLength={8}
          />
        </div>

        <button 
          type="submit" 
          disabled={isLoading}
          className="auth-button"
        >
          {isLoading ? 'Обработка...' : isLogin ? 'Войти' : null}
        </button>
      </form>
    </div>
  );
};

AuthForm.propTypes = {
  onLoginSuccess: PropTypes.func
};

export default AuthForm;