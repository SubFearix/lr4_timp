import React from 'react';
import EntityCrudPage from '../components/EntityCrudPage';
import { staffLabel } from '../utils/options';
import { canWriteOperationalData, canDeleteOperationalData } from '../utils/permissions';

const staffSource = { endpoint: '/staff', valueField: 'id_s', labelFn: staffLabel };
const incidentSource = {
  endpoint: '/incidents',
  valueField: 'id_inc',
  labelFn: (inc) => `#${inc.id_inc} — ${inc.inc_type} (${inc.inc_date})`,
};
const measureSource = { endpoint: '/response-measures', valueField: 'id_meas', labelFn: (m) => m.meas_name };

const findLabel = (list, id, valueField, labelFn) => {
  const found = (list || []).find((item) => item[valueField] === id);
  return found ? labelFn(found) : `#${id}`;
};

const config = {
  title: 'Журнал реагирования',
  entityLabel: 'запись журнала реагирования',
  endpoint: '/response-logs',
  idField: 'id_log',
  canCreate: canWriteOperationalData,
  canEdit: canWriteOperationalData,
  canDelete: canDeleteOperationalData,
  columns: [
    { key: 'id_log', label: 'ID' },
    {
      key: 'id_inc',
      label: 'Инцидент',
      render: (item, lookups) => findLabel(lookups['/incidents'], item.id_inc, 'id_inc', incidentSource.labelFn),
    },
    {
      key: 'id_meas',
      label: 'Мера',
      render: (item, lookups) => findLabel(lookups['/response-measures'], item.id_meas, 'id_meas', measureSource.labelFn),
    },
    {
      key: 'id_s',
      label: 'Исполнитель',
      render: (item, lookups) => findLabel(lookups['/staff'], item.id_s, 'id_s', staffLabel),
    },
    { key: 'date_exec', label: 'Дата выполнения' },
    { key: 'time_exec', label: 'Время выполнения' },
  ],
  filters: [
    { name: 'id_inc', label: 'Инцидент', type: 'select', optionsSource: incidentSource },
    { name: 'id_meas', label: 'Мера реагирования', type: 'select', optionsSource: measureSource },
    { name: 'id_s', label: 'Исполнитель', type: 'select', optionsSource: staffSource },
  ],
  fields: [
    { name: 'id_inc', label: 'Инцидент', type: 'select', optionsSource: incidentSource, required: true },
    { name: 'id_meas', label: 'Мера реагирования', type: 'select', optionsSource: measureSource, required: true },
    { name: 'id_s', label: 'Исполнитель', type: 'select', optionsSource: staffSource, required: true },
    { name: 'date_exec', label: 'Дата выполнения', type: 'date', required: true },
    { name: 'time_exec', label: 'Время выполнения', type: 'time', required: true },
    { name: 'result', label: 'Результат', type: 'textarea', placeholder: 'Что было сделано / чем закончилось' },
  ],
};

const ResponseLogs = () => <EntityCrudPage config={config} />;

export default ResponseLogs;
