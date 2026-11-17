import React from 'react';
import EntityCrudPage from '../components/EntityCrudPage';
import { OBJECT_TYPE_OPTIONS } from '../utils/options';
import { canManageReferenceData } from '../utils/permissions';

const config = {
  title: 'Объекты и помещения учреждения',
  entityLabel: 'объект',
  endpoint: '/objects',
  idField: 'id_obj',
  canCreate: canManageReferenceData,
  canEdit: canManageReferenceData,
  canDelete: canManageReferenceData,
  columns: [
    { key: 'id_obj', label: 'ID' },
    { key: 'obj_name', label: 'Название' },
    { key: 'obj_type', label: 'Тип' },
    { key: 'location', label: 'Расположение' },
  ],
  filters: [
    { name: 'obj_type', label: 'Тип объекта', type: 'select', options: OBJECT_TYPE_OPTIONS },
    { name: 'search', label: 'Поиск по названию', type: 'text', placeholder: 'Название объекта...' },
  ],
  fields: [
    { name: 'obj_name', label: 'Название объекта', type: 'text', required: true, placeholder: 'Например: Учебный корпус №2' },
    { name: 'obj_type', label: 'Тип объекта', type: 'select', options: OBJECT_TYPE_OPTIONS, required: true },
    { name: 'location', label: 'Расположение', type: 'text', placeholder: 'Например: 2 этаж, крыло Б' },
  ],
};

const Objects = () => <EntityCrudPage config={config} />;

export default Objects;
