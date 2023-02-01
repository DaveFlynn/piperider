import {
  Flex,
  Text,
  Box,
  Icon,
  Accordion,
  AccordionButton,
  AccordionItem,
  AccordionPanel,
  Grid,
  Link as ChakraLink,
  Tag,
  TagLabel,
} from '@chakra-ui/react';
import { useState } from 'react';
import { FiChevronDown, FiChevronRight } from 'react-icons/fi';
import {
  IoEye,
  IoEyeOutline,
  IoFilterCircle,
  IoFilterCircleOutline,
  IoSearchCircle,
  IoSearchCircleOutline,
} from 'react-icons/io5';
import { useLocalStorage } from 'react-use';

import { ColumnSchema } from '../../../sdlc/single-report-schema';
import { Comparable, ComparableData, Selectable } from '../../../types';
import {
  MASTER_LIST_DISPLAY_MODE,
  MASTER_LIST_SHOW_EXTRA,
} from '../../../utils';
import { formatColumnValueWith, formatNumber } from '../../../utils/formatters';
import {
  CompColEntryItem,
  CompTableColEntryItem,
  CompTableWithColEntryOverwrite,
} from '../../../utils/store';
import { SearchTextInput } from '../../Layouts/SearchTextInput';
import { TableRowColDeltaSummary } from '../../Tables/TableList/TableRowColDeltaSummary';
import { getIconForColumnType } from '../utils';
import { ColumnDetailListItem } from './ColumnDetailListItem';

type ProfilerGenericTypes = ColumnSchema['type'];
interface Props extends Selectable, Comparable {
  currentTable: string;
  currentColumn: string;
  tableColEntry: CompTableColEntryItem;
  tableColEntryList?: CompTableColEntryItem[];
  onNavToAssertions?: () => void;
  onNavToBM?: () => void;
  onToggleShowExtra?: () => void;
}
/**
 * A master list UI for showing a top-level, navigable, filterable, list of all tables and columns from datasource. Belongs in the profiling column details page to view in-depth metrics and visualizations
 */
export function ColumnDetailMasterList({
  tableColEntryList = [],
  tableColEntry,
  currentTable,
  currentColumn,
  singleOnly,
  onSelect,
  onNavToAssertions = () => {},
  onNavToBM = () => {},
  onToggleShowExtra = () => {},
}: Props) {
  const [showExtra, setShowExtra] = useLocalStorage(MASTER_LIST_SHOW_EXTRA, '');
  const [displayMode, setDisplayMode] = useLocalStorage(
    MASTER_LIST_DISPLAY_MODE,
    '',
  );

  //FIXME: Update the filters! (unplugged)
  const [filterString, setFilterString] = useState<string>('');
  const [filterState, setFilterState] = useState<
    Map<ProfilerGenericTypes | undefined, boolean>
  >(
    new Map([
      ['string', true],
      ['numeric', true],
      ['integer', true],
      ['datetime', true],
      ['boolean', true],
      ['other', true],
    ]),
  );
  const quickFilters = Array.from(filterState.keys());
  const [, { base: baseTable, target: targetTable }] = tableColEntry;
  // target is placed before fallback as it represents the target of change

  const fallbackTable = targetTable || baseTable;
  const fallbackColumns = fallbackTable?.columns || [];

  //FIXME: Later (confirm if apply to table+col)
  const filteredTableColumnEntries = fallbackColumns
    .filter(([, { base, target }]) => {
      // Logic: base-first lookup (tag filter UI)
      return filterState.get(base?.type) || filterState.get(target?.type);
    })
    .filter(([key]) =>
      filterString ? key.search(new RegExp(filterString, 'gi')) > -1 : true,
    );

  const SEARCH_KEY = 'search';
  const SearchIcon =
    displayMode === SEARCH_KEY ? (
      <IoSearchCircle size={'1.5rem'} />
    ) : (
      <IoSearchCircleOutline size={'1.5rem'} />
    );

  const SCHEMA_FILTER_KEY = 'schema-filter';
  const FilterIcon =
    displayMode === SCHEMA_FILTER_KEY ? (
      <IoFilterCircle size={'1.5rem'} />
    ) : (
      <IoFilterCircleOutline size={'1.5rem'} />
    );

  const SHOW_EXTRA_KEY = 'show-extra';
  const ShowExtraIcon = showExtra ? (
    <IoEye size={'1.5rem'} />
  ) : (
    <IoEyeOutline size={'1.5rem'} />
  );
  const hasShowExtra = showExtra === SHOW_EXTRA_KEY;

  return (
    <Box w={'100%'} p={3} pb={0} zIndex={150} bg={'inherit'}>
      {/* HEADER - Label + Toggle/Filters */}
      <Flex justifyContent={'space-between'} mb={2}>
        <Text color={'gray.500'} size={'md'}>
          Tables
        </Text>
        {/* Show More info Header */}
        <Flex gap={2}>
          <Box
            _hover={{ cursor: 'pointer' }}
            onClick={() => {
              const result = displayMode === SEARCH_KEY ? '' : SEARCH_KEY;
              setDisplayMode(result);
            }}
          >
            {SearchIcon}
          </Box>
          <Box
            _hover={{ cursor: 'pointer' }}
            onClick={() => {
              const result =
                displayMode === SCHEMA_FILTER_KEY ? '' : SCHEMA_FILTER_KEY;
              setDisplayMode(result);
            }}
          >
            {FilterIcon}
          </Box>
          <Box
            _hover={{ cursor: 'pointer' }}
            onClick={() => {
              const result = showExtra === SHOW_EXTRA_KEY ? '' : SHOW_EXTRA_KEY;
              setShowExtra(result);
              onToggleShowExtra && onToggleShowExtra(); // to inform parent about layout changes e.g. change grid-templates
            }}
          >
            {ShowExtraIcon}
          </Box>
        </Flex>
      </Flex>
      {/* BODY - Filter contents */}
      <Box p={2}>
        {/* Search Text Filter */}
        {displayMode === 'search' && (
          <SearchTextInput
            onChange={setFilterString}
            filterString={filterString}
          />
        )}
        {/* Tag Toggle Filters */}
        {displayMode === 'schema-filter' && (
          <Grid templateColumns={'1fr 1fr'} gap={3}>
            {quickFilters.map((v) => {
              const { icon } = getIconForColumnType({ type: v });
              const itemValue = filterState.get(v);

              return (
                <Tag
                  borderRadius={'xl'}
                  key={v}
                  py={3}
                  size={'lg'}
                  bg={itemValue ? 'piperider.100' : 'gray.200'}
                  onClick={() => {
                    const newState = new Map(filterState).set(v, !itemValue);
                    setFilterState(newState);
                  }}
                  cursor={'pointer'}
                >
                  <TagLabel fontSize={'lg'}>
                    <Flex alignItems={'center'} gap={2}>
                      <Icon as={icon} />
                      {v}
                    </Flex>
                  </TagLabel>
                </Tag>
              );
            })}
          </Grid>
        )}
      </Box>

      <Accordion reduceMotion allowMultiple>
        {/* TODO: Filtered? */}
        {tableColEntryList.map(([tableName, compTableColItem, meta]) => {
          const fallbackTableEntries =
            compTableColItem.target || compTableColItem.base;
          const fallbackColEntries = fallbackTableEntries?.columns;

          const isTableActive = Boolean(
            currentColumn === '' && currentTable === tableName,
          );
          return (
            <AccordionItem key={tableName}>
              {({ isExpanded }) => (
                <>
                  <TableItemAccordionButton
                    onSelect={onSelect}
                    isActive={isTableActive}
                    isExpanded={isExpanded}
                    compTableColItem={compTableColItem}
                    hasShowExtra={hasShowExtra}
                    singleOnly={singleOnly}
                  />
                  <ColumnListAccordionPanel
                    compColList={fallbackColEntries}
                    hasShowExtra={hasShowExtra}
                    singleOnly={singleOnly}
                    currentColumn={currentColumn}
                    currentTable={currentTable}
                    onSelect={onSelect}
                  />
                </>
              )}
            </AccordionItem>
          );
        })}
      </Accordion>

      <Flex py={3} mt={5}>
        <ChakraLink
          onClick={() => {
            onNavToBM();
          }}
        >
          All Metrics
        </ChakraLink>
      </Flex>
      <Flex py={3}>
        <ChakraLink
          onClick={() => {
            onNavToAssertions();
          }}
        >
          All Assertions
        </ChakraLink>
      </Flex>
    </Box>
  );
}

/**
 * TableItem: Accordion UI parent
 */
interface TableItemAccordionButtonProps extends Comparable, Selectable {
  compTableColItem: ComparableData<CompTableWithColEntryOverwrite>;
  hasShowExtra: boolean;
  isActive: boolean;
  isExpanded: boolean;
}
function TableItemAccordionButton({
  compTableColItem: { base: baseTable, target: targetTable },
  isActive,
  isExpanded,
  singleOnly,
  hasShowExtra,
  onSelect,
}: TableItemAccordionButtonProps) {
  const fallbackTable = targetTable || baseTable;

  return (
    <h2>
      <AccordionButton>
        <Flex
          p={3}
          w={'100%'}
          justify={'space-between'}
          onClick={() => {
            onSelect({ tableName: fallbackTable?.name, columnName: '' });
          }}
        >
          <Flex alignItems={'center'} gap={2} fontSize={'sm'}>
            <Icon as={isExpanded ? FiChevronDown : FiChevronRight} />
            <Text noOfLines={1}>{fallbackTable?.name}</Text>
          </Flex>
          {hasShowExtra && (
            <Flex color={'gray.500'} fontSize={'sm'}>
              <Text mr={4}>Rows</Text>
              {singleOnly ? (
                <Text>
                  {formatColumnValueWith(
                    fallbackTable?.row_count,
                    formatNumber,
                  )}
                </Text>
              ) : (
                <TableRowColDeltaSummary
                  baseCount={baseTable?.row_count}
                  targetCount={targetTable?.row_count}
                />
              )}
            </Flex>
          )}
        </Flex>
      </AccordionButton>
    </h2>
  );
}

/**
 * ColumnItemList: Accordion UI Child Body
 */
interface ColumnListAccordionPanelProps extends Comparable, Selectable {
  compColList?: CompColEntryItem[];
  hasShowExtra: boolean;
  currentColumn: string;
  currentTable: string;
}
function ColumnListAccordionPanel({
  compColList = [],
  onSelect,
  singleOnly,
  hasShowExtra,
  currentColumn,
  currentTable,
}: ColumnListAccordionPanelProps) {
  //TODO: active currentColumn (even when all accordions are expanded state)
  return (
    <AccordionPanel>
      <Box mt={2}>
        {compColList.map(([colKey, { base, target }]) => {
          return (
            <Box key={colKey}>
              {/* LIST - Columns */}
              <ColumnDetailListItem
                isActive={(target || base)?.name === currentColumn}
                tableName={currentTable}
                baseColumnDatum={base}
                targetColumnDatum={target}
                onSelect={(data) => {
                  onSelect(data);
                }}
                singleOnly={singleOnly}
                showExtra={hasShowExtra}
                p={3}
              />
            </Box>
          );
        })}
      </Box>
    </AccordionPanel>
  );
}
