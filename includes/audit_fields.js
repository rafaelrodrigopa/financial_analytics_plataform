// Utilitário Dataform para reutilização dos campos padrão de auditoria e governança técnica da camada Silver

function selectAuditFields() {
  return `
    CAST(_ingested_at AS TIMESTAMP) AS _ingested_at,
    CAST(_source AS STRING) AS _source,
    CAST(_execution_id AS STRING) AS _execution_id,
    CAST(_row_hash AS STRING) AS _row_hash,
    _raw_payload
  `;
}

module.exports = {
  selectAuditFields,
};
