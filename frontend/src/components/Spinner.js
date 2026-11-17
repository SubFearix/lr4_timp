import React from 'react';
import './Spinner.css';

const Spinner = ({ text = 'Загрузка...' }) => (
  <div className="spinner-container">
    <div className="spinner"></div>
    <p className="spinner-text">{text}</p>
  </div>
);

export default Spinner;
