import React from 'react';

const Pagination = ({ page, pages, total, onChange }) => {
  if (pages <= 1) return null;

  const goTo = (p) => {
    if (p >= 1 && p <= pages && p !== page) onChange(p);
  };

  return (
    <div className="pagination">
      <button type="button" className="btn btn-cancel" onClick={() => goTo(page - 1)} disabled={page <= 1}>
        ← Назад
      </button>
      <span className="pagination-info">
        Страница {page} из {pages} · всего записей: {total}
      </span>
      <button type="button" className="btn btn-cancel" onClick={() => goTo(page + 1)} disabled={page >= pages}>
        Вперёд →
      </button>
    </div>
  );
};

export default Pagination;
