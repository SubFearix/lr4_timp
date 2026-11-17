import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/axios';
import { getErrorMessage } from '../api/errors';
import Spinner from '../components/Spinner';
import { INCIDENT_STATE_OPTIONS } from '../utils/options';

const IncidentDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [incident, setIncident] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [detailResp, logsResp] = await Promise.all([
        api.get(`/incidents/${id}/detail`),
        api.get('/response-logs', { params: { id_inc: id, page: 1, page_size: 50 } }),
      ]);
      setIncident(detailResp.data);
      setLogs(logsResp.data.items);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <Spinner text="Загрузка данных об инциденте..." />;

  if (error) {
    return (
      <div className="detail-container">
        <div className="error-banner">
          {error}
          <button className="error-close" onClick={() => navigate('/incidents')}>Назад к списку</button>
        </div>
      </div>
    );
  }

  if (!incident) return null;

  const stateLabel = INCIDENT_STATE_OPTIONS.find((s) => s.value === incident.state)?.label || incident.state;

  return (
    <div className="detail-container">
      <div className="detail-header">
        <Link to="/incidents" className="back-link">← Назад к журналу инцидентов</Link>
      </div>

      <div className="detail-card">
        <div className="detail-title-row">
          <h2>Инцидент №{incident.id_inc}: {incident.inc_type}</h2>
          <span className={`status-tag ${incident.state === 'закрыт' ? 'status-closed' : 'status-open'}`}>
            {stateLabel}
          </span>
        </div>

        <p className="detail-type">Уровень угрозы: {incident.threat_lvl}/10</p>

        <div className="detail-info">
          <p><strong>Дата и время</strong>{incident.inc_date} {incident.inc_time}</p>
          <p>
            <strong>Объект</strong>
            {incident.related_object ? `${incident.related_object.obj_name} (${incident.related_object.obj_type})` : '—'}
            {incident.related_object?.location ? `, ${incident.related_object.location}` : ''}
          </p>
          <p>
            <strong>Ответственный сотрудник</strong>
            {incident.responsible
              ? `${incident.responsible.surname} ${incident.responsible.name} — ${incident.responsible.position}`
              : '—'}
          </p>
        </div>
      </div>

      <div className="home-incidents-section" style={{ marginTop: 24 }}>
        <h3>Журнал реагирования по инциденту</h3>
        {logs.length === 0 ? (
          <p className="no-data">Записей о реагировании пока нет</p>
        ) : (
          <div className="entity-table-wrap">
            <table className="entity-table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Время</th>
                  <th>Результат</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id_log}>
                    <td>{log.date_exec}</td>
                    <td>{log.time_exec}</td>
                    <td>{log.result || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="home-hint">
          Добавить запись о реагировании можно в разделе{' '}
          <Link to="/response-logs">«Журнал реагирования»</Link>.
        </p>
      </div>
    </div>
  );
};

export default IncidentDetail;
