import React, { useState, useEffect, useCallback, useMemo } from 'react';
import api from '../api/axios';
import { getErrorMessage } from '../api/errors';
import { useAuth } from '../context/AuthContext';
import Spinner from './Spinner';
import Pagination from './Pagination';

const PAGE_SIZE = 5;

const emptyFormData = (fields) => {
  const data = {};
  fields.forEach((f) => {
    data[f.name] = f.defaultValue !== undefined ? f.defaultValue : '';
  });
  return data;
};

/**
 * config = {
 *   title, entityLabel, endpoint, idField,
 *   columns: [{ key, label, render?(item, lookups) }],
 *   filters: [{ name, label, type, options?, optionsSource? }],
 *   fields:  [{ name, label, type, required?, requiredOnCreate?, options?, optionsSource?, placeholder?, helpText? }],
 *   renderExtraActions?(item) -> node (например, ссылка "Подробнее"),
 * }
 */
const EntityCrudPage = ({ config }) => {
  const { title, entityLabel, endpoint, idField, columns, filters = [], fields } = config;
  const { currentUser } = useAuth();
  const role = currentUser?.role;
  const canCreate = config.canCreate ? config.canCreate(role) : true;
  const canEdit = config.canEdit ? config.canEdit(role) : true;
  const canDelete = config.canDelete ? config.canDelete(role) : true;

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [filterValues, setFilterValues] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [optionsMap, setOptionsMap] = useState({});

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState('create');
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState(() => emptyFormData(fields));
  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const optionSources = useMemo(() => {
    const sources = {};
    [...fields, ...filters].forEach((f) => {
      if (f.optionsSource) sources[f.optionsSource.endpoint] = f.optionsSource;
    });
    return sources;
  }, [fields, filters]);

  useEffect(() => {
    let cancelled = false;
    const loadOptions = async () => {
      const entries = await Promise.all(
        Object.entries(optionSources).map(async ([sourceEndpoint]) => {
          try {
            const response = await api.get(sourceEndpoint, { params: { page: 1, page_size: 50 } });
            return [sourceEndpoint, response.data.items];
          } catch (err) {
            return [sourceEndpoint, []];
          }
        })
      );
      if (!cancelled) {
        setOptionsMap(Object.fromEntries(entries));
      }
    };
    if (Object.keys(optionSources).length > 0) {
      loadOptions();
    }
    return () => {
      cancelled = true;
    };
  }, [endpoint]);

  const getOptionsFor = useCallback(
    (fieldConfig) => {
      if (fieldConfig.options) return fieldConfig.options;
      if (fieldConfig.optionsSource) {
        const { endpoint: srcEndpoint, valueField, labelFn } = fieldConfig.optionsSource;
        const list = optionsMap[srcEndpoint] || [];
        return list.map((item) => ({ value: item[valueField], label: labelFn(item) }));
      }
      return [];
    },
    [optionsMap]
  );

  const fetchItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, page_size: PAGE_SIZE };
      Object.entries(filterValues).forEach(([key, value]) => {
        if (value !== '' && value !== undefined && value !== null) {
          params[key] = value;
        }
      });
      const response = await api.get(endpoint, { params });
      setItems(response.data.items);
      setTotal(response.data.total);
      setPages(response.data.pages);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [endpoint, page, filterValues]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const handleFilterChange = (name, value) => {
    setPage(1);
    setFilterValues((prev) => ({ ...prev, [name]: value }));
  };

  const openCreateForm = () => {
    setFormMode('create');
    setEditingId(null);
    setFormData(emptyFormData(fields));
    setFormErrors({});
    setFormOpen(true);
  };

  const openEditForm = (item) => {
    setFormMode('edit');
    setEditingId(item[idField]);
    const data = {};
    fields.forEach((f) => {
      if (f.type === 'password') {
        data[f.name] = '';
      } else {
        data[f.name] = item[f.name] ?? '';
      }
    });
    setFormData(data);
    setFormErrors({});
    setFormOpen(true);
  };

  const closeForm = () => {
    setFormOpen(false);
    setFormErrors({});
  };

  const handleFieldChange = (name, value) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
    setFormErrors((prev) => ({ ...prev, [name]: '' }));
  };

  const validate = () => {
    const errors = {};
    fields.forEach((f) => {
      if (f.disabledOnEdit && formMode === 'edit') return;
      const isRequired = formMode === 'create' ? (f.required || f.requiredOnCreate) : f.required;
      const value = formData[f.name];
      if (isRequired && (value === '' || value === undefined || value === null)) {
        errors[f.name] = 'Обязательное поле';
        return;
      }
      // Кастомный валидатор поля (например, формат телефона или сила
      // пароля) — вызывается, только если значение вообще заполнено,
      // чтобы необязательные пустые поля не считались ошибкой.
      if (f.validate && value !== '' && value !== undefined && value !== null) {
        const message = f.validate(value, formMode);
        if (message) {
          errors[f.name] = message;
        }
      }
    });
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const buildPayload = () => {
    const payload = {};
    fields.forEach((f) => {
      const value = formData[f.name];
      if (f.disabledOnEdit && formMode === 'edit') {
        return; // поле нельзя менять после создания (например, логин)
      }
      if (f.type === 'password' && formMode === 'edit' && !value) {
        return; // пароль не меняем, если поле оставлено пустым
      }
      if (f.type === 'checkbox') {
        payload[f.name] = Boolean(value);
        return;
      }
      if (value === '' && !f.required) {
        payload[f.name] = null;
        return;
      }
      payload[f.name] = f.type === 'number' ? (value === '' ? null : Number(value)) : value;
    });
    return payload;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      const payload = buildPayload();
      if (formMode === 'create') {
        await api.post(endpoint, payload);
      } else {
        await api.put(`${endpoint}/${editingId}`, payload);
      }
      closeForm();
      if (formMode === 'create' && page !== 1) {
        setPage(1);
      } else {
        fetchItems();
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (item) => {
    const confirmed = window.confirm(
      `Удалить «${entityLabel}» (id=${item[idField]})? Это действие нельзя отменить.`
    );
    if (!confirmed) return;
    try {
      await api.delete(`${endpoint}/${item[idField]}`);
      fetchItems();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const renderField = (f) => {
    const value = formData[f.name];
    const hasError = Boolean(formErrors[f.name]);
    const isDisabled = Boolean(f.disabledOnEdit && formMode === 'edit');
    const commonProps = {
      id: `field-${f.name}`,
      name: f.name,
      className: hasError ? 'input-error' : '',
      value: value ?? '',
      onChange: (e) => handleFieldChange(f.name, e.target.value),
      disabled: isDisabled,
    };

    let control;
    if (f.type === 'checkbox') {
      control = (
        <label className="checkbox-label">
          <input
            type="checkbox"
            id={`field-${f.name}`}
            name={f.name}
            checked={Boolean(value)}
            disabled={isDisabled}
            onChange={(e) => handleFieldChange(f.name, e.target.checked)}
          />
          {f.checkboxLabel || f.label}
        </label>
      );
    } else if (f.type === 'textarea') {
      control = <textarea rows={3} placeholder={f.placeholder} {...commonProps} />;
    } else if (f.type === 'select') {
      const options = getOptionsFor(f);
      control = (
        <select {...commonProps}>
          <option value="">— не выбрано —</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      );
    } else {
      control = (
        <input
          type={f.type === 'password' ? 'password' : f.type === 'number' ? 'number' : f.type === 'date' ? 'date' : f.type === 'time' ? 'time' : 'text'}
          placeholder={f.type === 'password' && formMode === 'edit' ? 'Оставьте пустым, чтобы не менять' : f.placeholder}
          min={f.min}
          max={f.max}
          {...commonProps}
        />
      );
    }

    return (
      <div className={`form-group ${f.type === 'checkbox' ? 'form-group-checkbox' : ''} ${hasError ? 'has-error' : ''}`} key={f.name}>
        {f.type !== 'checkbox' && (
          <label htmlFor={`field-${f.name}`}>
            {f.label} {(formMode === 'create' ? (f.required || f.requiredOnCreate) : f.required) && <span className="required">*</span>}
          </label>
        )}
        {control}
        {f.helpText && <span className="field-help">{f.helpText}</span>}
        {hasError && <span className="validation-error">{formErrors[f.name]}</span>}
      </div>
    );
  };

  const renderFilter = (f) => {
    const value = filterValues[f.name] ?? '';
    if (f.type === 'select') {
      const options = getOptionsFor(f);
      return (
        <div className="filter-group" key={f.name}>
          <label>{f.label}</label>
          <select value={value} onChange={(e) => handleFilterChange(f.name, e.target.value)}>
            <option value="">Все</option>
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      );
    }
    return (
      <div className="filter-group" key={f.name}>
        <label>{f.label}</label>
        <input
          type={f.type === 'number' ? 'number' : 'text'}
          value={value}
          placeholder={f.placeholder}
          onChange={(e) => handleFilterChange(f.name, e.target.value)}
        />
      </div>
    );
  };

  return (
    <div className="entity-page">
      <div className="entity-page-header">
        <div>
          <h2>{title}</h2>
          <p className="page-description">Всего записей: {total}</p>
        </div>
        {canCreate && (
          <button type="button" className="btn btn-primary" onClick={openCreateForm}>
            + Добавить
          </button>
        )}
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button className="error-close" onClick={() => setError(null)}>Закрыть</button>
        </div>
      )}

      {filters.length > 0 && (
        <div className="filter-bar">
          {filters.map(renderFilter)}
        </div>
      )}

      {formOpen && (
        <form className="incident-form entity-inline-form" onSubmit={handleSubmit} noValidate>
          <h3>{formMode === 'create' ? `Добавить: ${entityLabel}` : `Редактировать: ${entityLabel}`}</h3>
          {fields.map(renderField)}
          <div className="form-actions">
            <button type="submit" className="btn btn-save" disabled={submitting}>
              {submitting ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button type="button" className="btn btn-cancel" onClick={closeForm}>
              Отмена
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <Spinner text="Загрузка..." />
      ) : items.length === 0 ? (
        <p className="no-data">Записи не найдены</p>
      ) : (
        <div className="entity-table-wrap">
          <table className="entity-table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col.key}>{col.label}</th>
                ))}
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item[idField]}>
                  {columns.map((col) => (
                    <td key={col.key}>{col.render ? col.render(item, optionsMap) : String(item[col.key] ?? '')}</td>
                  ))}
                  <td className="entity-row-actions">
                    {config.renderExtraActions && config.renderExtraActions(item)}
                    {canEdit && (
                      <button type="button" className="link-button" onClick={() => openEditForm(item)}>
                        Изменить
                      </button>
                    )}
                    {canDelete && (
                      <button type="button" className="link-button link-button-danger" onClick={() => handleDelete(item)}>
                        Удалить
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination page={page} pages={pages} total={total} onChange={setPage} />
    </div>
  );
};

export default EntityCrudPage;
