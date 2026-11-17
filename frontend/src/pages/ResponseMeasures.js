import React from 'react';
import EntityCrudPage from '../components/EntityCrudPage';
import { canManageReferenceData } from '../utils/permissions';

const config = {
  title: 'Меры реагирования',
  entityLabel: 'мера реагирования',
  endpoint: '/response-measures',
  idField: 'id_meas',
  canCreate: canManageReferenceData,
  canEdit: canManageReferenceData,
  canDelete: canManageReferenceData,
  columns: [
    { key: 'id_meas', label: 'ID' },
    { key: 'meas_name', label: 'Название меры' },
    { key: 'time_reg', label: 'Регламент, мин', render: (item) => (item.time_reg ?? '—') },
  ],
  filters: [
    { name: 'search', label: 'Поиск по названию', type: 'text', placeholder: 'Название меры...' },
  ],
  fields: [
    { name: 'meas_name', label: 'Название меры', type: 'text', required: true, placeholder: 'Например: Вызов охраны, оповещение администрации' },
    { name: 'time_reg', label: 'Регламент времени (мин)', type: 'number', min: 0, helpText: 'Необязательно' },
  ],
};

const ResponseMeasures = () => <EntityCrudPage config={config} />;

export default ResponseMeasures;
