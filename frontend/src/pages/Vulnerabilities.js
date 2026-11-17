import React from 'react';
import EntityCrudPage from '../components/EntityCrudPage';
import { FIX_STATUS_OPTIONS, staffLabel } from '../utils/options';
import { canWriteOperationalData, canDeleteOperationalData } from '../utils/permissions';

const staffSource = { endpoint: '/staff', valueField: 'id_s', labelFn: staffLabel };
const vulTypeSource = { endpoint: '/vulnerability-types', valueField: 'id_vultype', labelFn: (t) => t.type_name };

const findLabel = (list, id, valueField, labelFn) => {
  const found = (list || []).find((item) => item[valueField] === id);
  return found ? labelFn(found) : `#${id}`;
};

const config = {
  title: 'Уязвимости',
  entityLabel: 'уязвимость',
  endpoint: '/vulnerabilities',
  idField: 'id_vul',
  canCreate: canWriteOperationalData,
  canEdit: canWriteOperationalData,
  canDelete: canDeleteOperationalData,
  columns: [
    { key: 'id_vul', label: 'ID' },
    {
      key: 'id_vultype',
      label: 'Тип уязвимости',
      render: (item, lookups) => findLabel(lookups['/vulnerability-types'], item.id_vultype, 'id_vultype', (t) => t.type_name),
    },
    { key: 'sw_ver', label: 'Версия ПО', render: (item) => item.sw_ver || '—' },
    { key: 'fix_status', label: 'Статус исправления' },
    {
      key: 'id_s',
      label: 'Нашёл',
      render: (item, lookups) => findLabel(lookups['/staff'], item.id_s, 'id_s', staffLabel),
    },
  ],
  filters: [
    { name: 'fix_status', label: 'Статус исправления', type: 'select', options: FIX_STATUS_OPTIONS },
    { name: 'id_vultype', label: 'Тип уязвимости', type: 'select', optionsSource: vulTypeSource },
    { name: 'id_s', label: 'Кто нашёл', type: 'select', optionsSource: staffSource },
  ],
  fields: [
    { name: 'id_vultype', label: 'Тип уязвимости', type: 'select', optionsSource: vulTypeSource, required: true },
    { name: 'id_s', label: 'Сотрудник, нашедший уязвимость', type: 'select', optionsSource: staffSource, required: true },
    { name: 'sw_ver', label: 'Версия ПО', type: 'text', placeholder: 'Необязательно' },
    { name: 'fix_status', label: 'Статус исправления', type: 'select', options: FIX_STATUS_OPTIONS, required: true },
  ],
};

const Vulnerabilities = () => <EntityCrudPage config={config} />;

export default Vulnerabilities;
