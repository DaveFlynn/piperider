import { SearchIcon } from '@chakra-ui/icons';
import { InputGroup, InputLeftElement, Input, Flex } from '@chakra-ui/react';
import { useState } from 'react';
import { Main } from '../components/shared/Layouts/Main';
import { AssertionListWidget } from '../components/shared/Widgets/AssertionListWidget';
import { SaferSRSchema } from '../types';
import { useReportStore } from '../utils';
import { tableListWidth } from '../utils/layout';

interface Props {
  data: SaferSRSchema;
}
export function SRAssertionListPage({ data }: Props) {
  const [filterString, setFilterString] = useState<string>('');
  const setRawReport = useReportStore((s) => s.setReportRawData);
  setRawReport({ base: data });
  const { tableColumnAssertionsOnly } = useReportStore.getState();

  return (
    <Main isSingleReport>
      <Flex justify={'center'} w={tableListWidth} m={14}>
        <InputGroup my={2}>
          <InputLeftElement
            pointerEvents={'none'}
            children={<SearchIcon color={'gray.300'} />}
          />
          <Input
            bg={'white'}
            color={'black'}
            type={'text'}
            placeholder="Find By Assertion or Test Subject (Table, Column)"
            value={filterString}
            onChange={({ target }) => setFilterString(target.value)}
          />
        </InputGroup>
      </Flex>
      <AssertionListWidget
        singleOnly
        filterString={filterString}
        assertionList={tableColumnAssertionsOnly}
      />
    </Main>
  );
}
