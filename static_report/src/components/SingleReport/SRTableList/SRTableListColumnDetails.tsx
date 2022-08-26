import { TableSchema } from '../../../sdlc/single-report-schema';
import { getIconForColumnType } from '../../../utils/transformers';
import { SRTableListColumnDetail } from './SRTableListColumnDetail';

export function SRTableColumnDetails({ table }: { table: TableSchema }) {
  const mergedAssertionColumns = Object.keys(
    table.piperider_assertion_result?.columns || {},
  ).map((colName) => {
    const mergedColAssertions = [
      ...(table.piperider_assertion_result?.columns?.[colName] || []),
      ...(table.dbt_assertion_result?.columns?.[colName] || []),
    ];

    const { icon: colIcon } = getIconForColumnType(table.columns[colName]);

    return {
      colName,
      mergedColAssertions,
      colIcon,
    };
  });

  return (
    <>
      {mergedAssertionColumns.map(
        ({ colName, colIcon, mergedColAssertions }) => (
          <SRTableListColumnDetail
            key={colName}
            name={colName}
            data={table.columns[colName]}
            colAssertions={mergedColAssertions}
            icon={colIcon}
          />
        ),
      )}
    </>
  );
}
