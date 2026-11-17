import React from 'react';
import { Link } from 'react-router-dom';
import EntityCrudPage from '../components/EntityCrudPage';
import { INCIDENT_STATE_OPTIONS, INCIDENT_TYPE_OPTIONS, objectLabel, staffLabel } from '../utils/options';
import { canWriteOperationalData, canDeleteOperationalData } from '../utils/permissions';

const objectSource = { endpoint: '/objects', valueField: 'id_obj', labelFn: objectLabel };
const staffSource = { endpoint: '/staff', valueField: 'id_s', labelFn: staffLabel };

const findLabel = (list, id, valueField, labelFn) => {
  const found = (list || []).find((item) => item[valueField] === id);
  return found ? labelFn(found) : `#${id}`;
};

const config = {
  title: 'Журнал инцидентов',
  entityLabel: 'инцидент',
  endpoint: '/incidents',
  idField: 'id_inc',
  canCreate: canWriteOperationalData,
  canEdit: canWriteOperationalData,
  canDelete: canDeleteOperationalData,
  columns: [
    { key: 'id_inc', label: 'ID' },
    { key: 'inc_type', label: 'Тип' },
    { key: 'inc_date', label: 'Дата' },
    { key: 'inc_time', label: 'Время' },
    {
      key: 'id_obj',
      label: 'Объект',
      render: (item, lookups) => findLabel(lookups['/objects'], item.id_obj, 'id_obj', objectLabel),
    },
    {
      key: 'id_s',
      label: 'Ответственный',
      render: (item, lookups) => findLabel(lookups['/staff'], item.id_s, 'id_s', staffLabel),
    },
    {
      key: 'threat_lvl',
      label: 'Угроза',
      render: (item) => <span className="severity-tag" style={{ '--tab-color': threatColor(item.threat_lvl) }}>{item.threat_lvl}/10</span>,
    },
    {
      key: 'state',
      label: 'Состояние',
      render: (item) => (
        <span className={`status-tag ${item.state === 'закрыт' ? 'status-closed' : 'status-open'}`}>
          {INCIDENT_STATE_OPTIONS.find((s) => s.value === item.state)?.label || item.state}
        </span>
      ),
    },
  ],
  filters: [
    { name: 'state', label: 'Состояние', type: 'select', options: INCIDENT_STATE_OPTIONS },
    { name: 'inc_type', label: 'Тип инцидента', type: 'select', options: INCIDENT_TYPE_OPTIONS },
    { name: 'id_obj', label: 'Объект', type: 'select', optionsSource: objectSource },
    { name: 'id_s', label: 'Ответственный', type: 'select', optionsSource: staffSource },
    { name: 'threat_lvl_min', label: 'Угроза от', type: 'number' },
    { name: 'threat_lvl_max', label: 'Угроза до', type: 'number' },
  ],
  fields: [
    { name: 'id_obj', label: 'Объект', type: 'select', optionsSource: objectSource, required: true },
    { name: 'id_s', label: 'Ответственный сотрудник', type: 'select', optionsSource: staffSource, required: true },
    { name: 'inc_type', label: 'Тип инцидента', type: 'select', options: INCIDENT_TYPE_OPTIONS, required: true },
    { name: 'inc_date', label: 'Дата инцидента', type: 'date', required: true },
    { name: 'inc_time', label: 'Время инцидента', type: 'time', required: true },
    { name: 'threat_lvl', label: 'Уровень угрозы (1–10)', type: 'number', min: 1, max: 10, required: true },
    { name: 'state', label: 'Состояние', type: 'select', options: INCIDENT_STATE_OPTIONS, required: true, defaultValue: 'новый' },
  ],
  renderExtraActions: (item) => (
    <Link to={`/incidents/${item.id_inc}`} className="link-button">
      Подробнее
    </Link>
  ),
};

function threatColor(level) {
  if (level >= 8) return '#8C2F2F';
  if (level >= 5) return '#B5522A';
  if (level >= 3) return '#96792E';
  return '#4B6358';
}

const Incidents = () => <EntityCrudPage config={config} />;

export default Incidents;
